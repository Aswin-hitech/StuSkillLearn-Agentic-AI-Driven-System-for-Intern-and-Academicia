from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.db import get_db
from app.integrations import learning_provider_status, mongodb_status, notification_status
from app.models import (
    AcademicianProfile,
    AgentRun,
    Allocation,
    AuditEvent,
    CompanyProfile,
    DigitalBadge,
    InstitutionProfile,
    Opportunity,
    PlatformPolicy,
    StudentProfile,
    User,
)
from app.nim import nim_client
from app.services import (
    audit,
    get_platform_policy,
    refresh_curriculum_insights,
    run_seven_agent_cycle,
    serialize_opportunity,
)

from app.timeutils import ensure_utc, utc_now

router = APIRouter(prefix="/sih/admin", tags=["admin"])


class VerificationPayload(BaseModel):
    status: str = Field(pattern="^(VERIFIED|REJECTED|SUSPENDED|PENDING)$")
    notes: str = Field(default="", max_length=2000)


class UserStatusPayload(BaseModel):
    active: bool


class BadgeVerificationPayload(BaseModel):
    status: str = Field(pattern="^(VERIFIED|REJECTED|PENDING|SELF_REPORTED)$")
    notes: str = Field(default="", max_length=2000)


class TenantAssignmentPayload(BaseModel):
    institution_profile_id: int | None = None


class ReservationVerificationPayload(BaseModel):
    category: str = Field(min_length=2, max_length=32)
    status: str = Field(pattern="^(VERIFIED|REJECTED|UNVERIFIED)$")
    source: str = Field(default="", max_length=255)


class OpportunityModerationPayload(BaseModel):
    moderation_status: str = Field(pattern="^(APPROVED|REJECTED|PENDING)$")
    status: str | None = Field(default=None, pattern="^(DRAFT|OPEN|PAUSED|CLOSED|CANCELLED)$")
    reservation_policy: dict[str, int] = {}
    reservation_policy_approved: bool = False


class PolicyPayload(BaseModel):
    policy_version: str = Field(min_length=1, max_length=40)
    reservation_policy: dict[str, int] = {}
    allow_reserved_seat_conversion: bool = True
    minimum_profile_completion: int = Field(default=55, ge=0, le=100)
    minimum_required_skill_coverage: float = Field(default=40, ge=0, le=100)


def _serialize_user(db: Session, user: User) -> dict:
    profile_status = None
    display_name = ""
    tenant_id = None
    if user.role == "COMPANY":
        profile = db.scalar(select(CompanyProfile).where(CompanyProfile.user_id == user.id))
        if profile:
            profile_status = profile.verification_status
            display_name = profile.company_name
    elif user.role == "INSTITUTION":
        profile = db.scalar(select(InstitutionProfile).where(InstitutionProfile.user_id == user.id))
        if profile:
            profile_status = profile.verification_status
            display_name = profile.institution_name
            tenant_id = profile.id
    elif user.role == "STUDENT":
        profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
        if profile:
            display_name = profile.name
            tenant_id = profile.institution_profile_id
    elif user.role == "ACADEMICIAN":
        profile = db.scalar(select(AcademicianProfile).where(AcademicianProfile.user_id == user.id))
        if profile:
            display_name = profile.name
            tenant_id = profile.institution_profile_id
    return {
        "id": user.id,
        "public_id": user.public_id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "email_verified": user.email_verified,
        "profile_status": profile_status,
        "display_name": display_name,
        "institution_profile_id": tenant_id,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


@router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    role_counts = {
        role: db.scalar(select(func.count()).select_from(User).where(User.role == role)) or 0
        for role in ("STUDENT", "COMPANY", "ACADEMICIAN", "INSTITUTION", "ADMIN")
    }
    pending_companies = db.scalar(select(func.count()).select_from(CompanyProfile).where(CompanyProfile.verification_status == "PENDING")) or 0
    pending_institutions = db.scalar(select(func.count()).select_from(InstitutionProfile).where(InstitutionProfile.verification_status == "PENDING")) or 0
    pending_opportunities = db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.moderation_status == "PENDING")) or 0
    allocations = {
        status: db.scalar(select(func.count()).select_from(Allocation).where(Allocation.status == status)) or 0
        for status in ("OFFERED", "ACCEPTED", "IN_PROGRESS", "COMPLETED", "REJECTED")
    }
    latest_events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(12)).all()
    return {
        "metrics": {
            "roles": role_counts,
            "pending_companies": pending_companies,
            "pending_institutions": pending_institutions,
            "pending_opportunities": pending_opportunities,
            "allocations": allocations,
        },
        "provider": nim_client.status(),
        "integrations": {
            "learning": learning_provider_status(),
            "notifications": notification_status(),
            "mongodb": mongodb_status(),
        },
        "recent_audit": [
            {"id": x.id, "actor_role": x.actor_role, "event_type": x.event_type, "entity_type": x.entity_type, "entity_id": x.entity_id, "details": x.details, "created_at": x.created_at}
            for x in latest_events
        ],
    }


@router.get("/users")
def admin_users(
    role: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    query = select(User).order_by(User.created_at.desc()).limit(limit)
    if role:
        query = query.where(User.role == role.upper())
    if active is not None:
        query = query.where(User.is_active.is_(active))
    return [_serialize_user(db, row) for row in db.scalars(query).all()]


@router.patch("/users/{user_id}/status")
def admin_user_status(user_id: int, payload: UserStatusPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == user.id and not payload.active:
        raise HTTPException(409, "You cannot deactivate your own admin account")
    target.is_active = payload.active
    paused_opportunities = 0
    if target.role == "COMPANY" and not payload.active:
        company = db.scalar(select(CompanyProfile).where(CompanyProfile.user_id == target.id))
        if company:
            rows = db.scalars(
                select(Opportunity).where(
                    Opportunity.company_profile_id == company.id,
                    Opportunity.status == "OPEN",
                )
            ).all()
            for opportunity in rows:
                opportunity.status = "PAUSED"
                paused_opportunities += 1
    audit(
        db,
        user=user,
        event_type="ADMIN_USER_STATUS_CHANGED",
        entity_type="user",
        entity_id=target.id,
        details={"active": payload.active, "paused_company_opportunities": paused_opportunities},
    )
    db.commit()
    return _serialize_user(db, target)


@router.get("/companies")
def admin_companies(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    rows = db.scalars(select(CompanyProfile).order_by(CompanyProfile.created_at.desc())).all()
    return [{
        "id": x.id, "company_name": x.company_name, "industry": x.industry, "website": x.website,
        "verified": x.verified, "verification_status": x.verification_status, "verification_notes": x.verification_notes,
        "user_id": x.user_id, "created_at": x.created_at,
    } for x in rows]


@router.patch("/companies/{company_id}/verification")
def verify_company(company_id: int, payload: VerificationPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    company = db.get(CompanyProfile, company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    company.verification_status = payload.status
    company.verified = payload.status == "VERIFIED"
    company.verification_notes = payload.notes
    company.verified_at = utc_now() if company.verified else None

    # Trust revocation must immediately stop public recruitment activity. Re-verifying a
    # company never reopens roles automatically; an administrator/company must make an
    # explicit publishing decision after review.
    affected = 0
    if payload.status != "VERIFIED":
        next_status = "CANCELLED" if payload.status == "REJECTED" else "PAUSED"
        rows = db.scalars(
            select(Opportunity).where(
                Opportunity.company_profile_id == company.id,
                Opportunity.status == "OPEN",
            )
        ).all()
        for opportunity in rows:
            opportunity.status = next_status
            if next_status == "CANCELLED":
                opportunity.closed_at = utc_now()
            affected += 1

    audit(
        db,
        user=user,
        event_type="ADMIN_COMPANY_VERIFICATION",
        entity_type="company",
        entity_id=company.id,
        details={"status": payload.status, "affected_open_opportunities": affected},
    )
    db.commit()
    return {"id": company.id, "verified": company.verified, "verification_status": company.verification_status, "affected_open_opportunities": affected}


@router.get("/institutions")
def admin_institutions(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    rows = db.scalars(select(InstitutionProfile).order_by(InstitutionProfile.created_at.desc())).all()
    return [{
        "id": x.id, "institution_name": x.institution_name, "institution_code": x.institution_code, "city": x.city, "state": x.state,
        "verified": x.verified, "verification_status": x.verification_status, "verification_notes": x.verification_notes,
        "created_at": x.created_at,
    } for x in rows]


@router.patch("/institutions/{institution_id}/verification")
def verify_institution(institution_id: int, payload: VerificationPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    institution = db.get(InstitutionProfile, institution_id)
    if not institution:
        raise HTTPException(404, "Institution not found")
    institution.verification_status = payload.status
    institution.verified = payload.status == "VERIFIED"
    institution.verification_notes = payload.notes
    institution.verified_at = utc_now() if institution.verified else None
    audit(db, user=user, event_type="ADMIN_INSTITUTION_VERIFICATION", entity_type="institution", entity_id=institution.id, details={"status": payload.status})
    db.commit()
    return {"id": institution.id, "verified": institution.verified, "verification_status": institution.verification_status}


@router.patch("/students/{student_id}/institution")
def assign_student_institution(student_id: int, payload: TenantAssignmentPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    student = db.get(StudentProfile, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    if payload.institution_profile_id is not None and not db.get(InstitutionProfile, payload.institution_profile_id):
        raise HTTPException(404, "Institution not found")
    student.institution_profile_id = payload.institution_profile_id
    audit(db, user=user, event_type="ADMIN_STUDENT_TENANT_ASSIGNED", entity_type="student", entity_id=student.id, details={"institution_profile_id": payload.institution_profile_id})
    db.commit()
    return {"id": student.id, "institution_profile_id": student.institution_profile_id}


@router.patch("/academicians/{academician_id}/institution")
def assign_academician_institution(academician_id: int, payload: TenantAssignmentPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    academician = db.get(AcademicianProfile, academician_id)
    if not academician:
        raise HTTPException(404, "Academician not found")
    if payload.institution_profile_id is not None and not db.get(InstitutionProfile, payload.institution_profile_id):
        raise HTTPException(404, "Institution not found")
    academician.institution_profile_id = payload.institution_profile_id
    audit(db, user=user, event_type="ADMIN_ACADEMICIAN_TENANT_ASSIGNED", entity_type="academician", entity_id=academician.id, details={"institution_profile_id": payload.institution_profile_id})
    db.commit()
    return {"id": academician.id, "institution_profile_id": academician.institution_profile_id}


@router.patch("/students/{student_id}/reservation")
def verify_reservation(student_id: int, payload: ReservationVerificationPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    student = db.get(StudentProfile, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    student.reservation_category = payload.category.strip().upper()
    student.reservation_status = payload.status
    student.reservation_source = payload.source.strip()
    student.reservation_verified_at = utc_now() if payload.status == "VERIFIED" else None
    audit(db, user=user, event_type="ADMIN_RESERVATION_VERIFICATION", entity_type="student", entity_id=student.id, details={"status": payload.status, "category": student.reservation_category})
    db.commit()
    return {"student_id": student.id, "reservation_category": student.reservation_category, "reservation_status": student.reservation_status}




@router.get("/students")
def admin_students(
    institution_profile_id: int | None = Query(default=None),
    reservation_status: str | None = Query(default=None),
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    query = select(StudentProfile).order_by(StudentProfile.created_at.desc()).limit(limit)
    if institution_profile_id is not None:
        query = query.where(StudentProfile.institution_profile_id == institution_profile_id)
    if reservation_status:
        query = query.where(StudentProfile.reservation_status == reservation_status.upper())
    rows = db.scalars(query).all()
    result = []
    for student in rows:
        account = db.get(User, student.user_id)
        institution = db.get(InstitutionProfile, student.institution_profile_id) if student.institution_profile_id else None
        result.append({
            "id": student.id,
            "public_user_id": account.public_id if account else None,
            "email": account.email if account else "",
            "is_active": account.is_active if account else False,
            "email_verified": account.email_verified if account else False,
            "name": student.name,
            "degree": student.degree,
            "department": student.department,
            "current_year": student.current_year,
            "cgpa": student.cgpa,
            "profile_completion": student.profile_completion,
            "institution_profile_id": student.institution_profile_id,
            "institution_name": institution.institution_name if institution else "Unassigned",
            "reservation_category": student.reservation_category,
            "reservation_status": student.reservation_status,
            "reservation_source": student.reservation_source,
            "created_at": student.created_at,
        })
    return result


@router.get("/academicians")
def admin_academicians(
    institution_profile_id: int | None = Query(default=None),
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    query = select(AcademicianProfile).order_by(AcademicianProfile.created_at.desc()).limit(limit)
    if institution_profile_id is not None:
        query = query.where(AcademicianProfile.institution_profile_id == institution_profile_id)
    rows = db.scalars(query).all()
    result = []
    for academician in rows:
        account = db.get(User, academician.user_id)
        institution = db.get(InstitutionProfile, academician.institution_profile_id) if academician.institution_profile_id else None
        result.append({
            "id": academician.id,
            "email": account.email if account else "",
            "is_active": account.is_active if account else False,
            "name": academician.name,
            "department": academician.department,
            "designation": academician.designation,
            "institution_profile_id": academician.institution_profile_id,
            "institution_name": institution.institution_name if institution else "Unassigned",
            "expertise": academician.expertise,
            "created_at": academician.created_at,
        })
    return result


@router.get("/badges")
def admin_badges(
    verification_status: str | None = Query(default=None),
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    query = select(DigitalBadge).order_by(DigitalBadge.created_at.desc()).limit(limit)
    if verification_status:
        query = query.where(DigitalBadge.verification_status == verification_status.upper())
    rows = db.scalars(query).all()
    result = []
    for badge in rows:
        student = db.get(StudentProfile, badge.student_profile_id)
        result.append({
            "id": badge.id,
            "student_profile_id": badge.student_profile_id,
            "student_name": student.name if student else "Unknown student",
            "title": badge.title,
            "issuer": badge.issuer,
            "verified": badge.verified,
            "verification_status": badge.verification_status,
            "verification_notes": badge.verification_notes,
            "reviewed_at": badge.reviewed_at,
            "reviewed_by_user_id": badge.reviewed_by_user_id,
            "credential_url": badge.credential_url,
            "evidence_url": badge.evidence_url,
            "credential_id": badge.credential_id,
            "standards": badge.standards,
            "created_at": badge.created_at,
        })
    return result


@router.get("/allocations")
def admin_allocations(
    status: str | None = Query(default=None),
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    query = select(Allocation).order_by(Allocation.created_at.desc()).limit(limit)
    if status:
        query = query.where(Allocation.status == status.upper())
    rows = db.scalars(query).all()
    result = []
    for allocation in rows:
        student = db.get(StudentProfile, allocation.student_profile_id)
        opportunity = db.get(Opportunity, allocation.opportunity_id)
        company = db.get(CompanyProfile, opportunity.company_profile_id) if opportunity else None
        result.append({
            "id": allocation.id,
            "student_profile_id": allocation.student_profile_id,
            "student_name": student.name if student else "Unknown student",
            "opportunity_id": allocation.opportunity_id,
            "opportunity_title": opportunity.title if opportunity else "Unknown opportunity",
            "company_name": company.company_name if company else "Unknown company",
            "rank": allocation.rank,
            "round": allocation.round,
            "status": allocation.status,
            "category_slot": allocation.category_slot,
            "algorithm_version": allocation.algorithm_version,
            "policy_version": allocation.policy_version,
            "created_at": allocation.created_at,
            "completed_at": allocation.completed_at,
        })
    return result


@router.get("/opportunities")
def admin_opportunities(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    rows = db.scalars(select(Opportunity).order_by(Opportunity.created_at.desc())).all()
    return [serialize_opportunity(x) for x in rows]


@router.patch("/opportunities/{opportunity_id}/moderation")
def moderate_opportunity(opportunity_id: int, payload: OpportunityModerationPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    opportunity = db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(404, "Opportunity not found")
    policy = {str(k).strip().upper(): max(0, int(v)) for k, v in payload.reservation_policy.items() if int(v) > 0}
    if sum(policy.values()) > opportunity.seats:
        raise HTTPException(422, "Reserved seat counts cannot exceed total opportunity seats")
    if payload.reservation_policy_approved and payload.moderation_status != "APPROVED":
        raise HTTPException(422, "Reservation policy can be approved only with an approved opportunity")
    if payload.status == "OPEN":
        if payload.moderation_status != "APPROVED":
            raise HTTPException(409, "Only approved opportunities can be opened")
        if policy and not payload.reservation_policy_approved:
            raise HTTPException(409, "Reservation policy approval is required before opening this opportunity")
        company = db.get(CompanyProfile, opportunity.company_profile_id)
        company_user = db.get(User, company.user_id) if company else None
        if not company or not company.verified or company.verification_status != "VERIFIED" or not company_user or not company_user.is_active:
            raise HTTPException(409, "Only an active, verified company can publish opportunities")
        if opportunity.deadline and ensure_utc(opportunity.deadline) <= utc_now():
            raise HTTPException(409, "Expired opportunities cannot be opened")
    opportunity.moderation_status = payload.moderation_status
    opportunity.reservation_policy = policy
    opportunity.reservation_policy_approved = bool(payload.reservation_policy_approved)
    if payload.status:
        opportunity.status = payload.status
        if payload.status == "OPEN":
            opportunity.published_at = opportunity.published_at or utc_now()
            opportunity.closed_at = None
        elif payload.status in {"CLOSED", "CANCELLED"}:
            opportunity.closed_at = utc_now()
    audit(db, user=user, event_type="ADMIN_OPPORTUNITY_MODERATED", entity_type="opportunity", entity_id=opportunity.id, details={"moderation_status": payload.moderation_status, "status": opportunity.status})
    db.commit()
    return serialize_opportunity(opportunity)


@router.get("/policy")
def admin_policy(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    policy = get_platform_policy(db)
    db.commit()
    return {
        "policy_version": policy.policy_version,
        "reservation_policy": policy.reservation_policy,
        "allow_reserved_seat_conversion": policy.allow_reserved_seat_conversion,
        "minimum_profile_completion": policy.minimum_profile_completion,
        "minimum_required_skill_coverage": policy.minimum_required_skill_coverage,
    }


@router.put("/policy")
def update_admin_policy(payload: PolicyPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    policy = get_platform_policy(db)
    policy.policy_version = payload.policy_version
    policy.reservation_policy = {str(k).upper(): max(0, int(v)) for k, v in payload.reservation_policy.items() if int(v) >= 0}
    policy.allow_reserved_seat_conversion = payload.allow_reserved_seat_conversion
    policy.minimum_profile_completion = payload.minimum_profile_completion
    policy.minimum_required_skill_coverage = payload.minimum_required_skill_coverage
    policy.updated_by_user_id = user.id
    audit(db, user=user, event_type="ADMIN_POLICY_UPDATED", entity_type="platform_policy", entity_id=policy.id, details=payload.model_dump())
    db.commit()
    return payload.model_dump()


@router.get("/audit")
def admin_audit(limit: int = Query(default=200, ge=1, le=1000), db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)).all()
    return [{
        "id": x.id, "actor_role": x.actor_role, "actor_user_id": x.actor_user_id, "event_type": x.event_type,
        "entity_type": x.entity_type, "entity_id": x.entity_id, "institution_profile_id": x.institution_profile_id,
        "company_profile_id": x.company_profile_id, "student_profile_id": x.student_profile_id,
        "request_id": x.request_id, "details": x.details, "created_at": x.created_at,
    } for x in events]


@router.get("/agents")
def admin_agents(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    rows = db.scalars(select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)).all()
    return [{
        "id": x.id, "agent_name": x.agent_name, "responsibility": x.responsibility, "status": x.status,
        "student_profile_id": x.student_profile_id, "company_profile_id": x.company_profile_id,
        "institution_profile_id": x.institution_profile_id, "output_data": x.output_data, "created_at": x.created_at,
    } for x in rows]


@router.post("/agents/run-ecosystem")
def admin_run_agents(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    rows = run_seven_agent_cycle(db, None, user)
    return [{"id": x.id, "agent_name": x.agent_name, "status": x.status, "output_data": x.output_data} for x in rows]


@router.post("/curriculum/refresh")
def admin_refresh_curriculum(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    items = refresh_curriculum_insights(db, None)
    audit(db, user=user, event_type="ADMIN_CURRICULUM_REFRESH", entity_type="curriculum", details={"generated": len(items)})
    db.commit()
    return {"generated": len(items)}


@router.patch("/badges/{badge_id}/verification")
def admin_verify_badge(badge_id: int, payload: BadgeVerificationPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    badge = db.get(DigitalBadge, badge_id)
    if not badge:
        raise HTTPException(404, "Badge not found")
    badge.verification_status = payload.status
    badge.verified = payload.status == "VERIFIED"
    badge.verification_notes = payload.notes
    if payload.status in {"VERIFIED", "REJECTED"}:
        badge.reviewed_at = utc_now()
        badge.reviewed_by_user_id = user.id
    else:
        badge.reviewed_at = None
        badge.reviewed_by_user_id = None
    audit(
        db,
        user=user,
        event_type="ADMIN_BADGE_VERIFICATION",
        entity_type="badge",
        entity_id=badge.id,
        details={"status": payload.status, "notes": payload.notes},
    )
    db.commit()
    return {
        "id": badge.id,
        "verified": badge.verified,
        "verification_status": badge.verification_status,
        "verification_notes": badge.verification_notes,
        "reviewed_at": badge.reviewed_at,
    }
