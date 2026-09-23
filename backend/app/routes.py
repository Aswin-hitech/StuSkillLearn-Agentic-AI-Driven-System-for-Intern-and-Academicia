from __future__ import annotations

import io
import hashlib
import zipfile
from datetime import datetime, timezone
from xml.etree import ElementTree

from typing import Any

from fastapi import APIRouter, Cookie, Depends, File, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import (
    ActionTokenPayload,
    AuthPayload,
    EmailAddressPayload,
    LoginPayload,
    PasswordResetPayload,
    TokenResponse,
    UserResponse,
    authenticate,
    consume_email_action_token,
    create_email_action_token,
    clear_auth_cookies,
    get_current_user,
    issue_session,
    register_user,
    revoke_all_refresh_sessions,
    require_roles,
    revoke_refresh_session,
    rotate_refresh_session,
)
from app.db import get_db
from app.config import settings
from app.rate_limit import clear_login_rate_limit, enforce_login_rate_limit
from app.models import (
    AcademicianOpportunity,
    AcademicianOpportunityApplication,
    AcademicianProfile,
    AgentRun,
    Allocation,
    Application,
    AuditEvent,
    CompanyFeedback,
    CompanyProfile,
    DigitalBadge,
    IndustryLearningProgram,
    InstitutionProfile,
    LearningRecommendation,
    LSRWAssessment,
    MatchResult,
    Opportunity,
    StudentProfile,
    User,
)
from app.nim import nim_client
from app.notifications import send_email
from app.security import hash_password
from app.integrations import learning_provider_status, notification_status, mongodb_status
from app.services import (
    academician_dashboard,
    academician_match_score,
    allocate_opportunity,
    assess_lsrw,
    audit,
    company_dashboard,
    current_lsrw,
    ensure_application,
    institution_dashboard,
    parse_resume_into_profile,
    profile_completion,
    rank_applicants,
    refresh_curriculum_insights,
    refresh_learning_recommendations,
    refresh_student_matches,
    respond_to_allocation,
    run_seven_agent_cycle,
    serialize_allocation,
    serialize_allocation_for_company,
    serialize_candidate_for_company,
    serialize_badge,
    serialize_match,
    serialize_opportunity,
    serialize_student,
    skill_gap_report,
    stored_student_matches,
    student_dashboard,
    opportunity_is_open,
)

from app.timeutils import ensure_utc, utc_now

router = APIRouter()


# ---------- auth ----------
@router.post("/auth/register/{role}", response_model=TokenResponse, status_code=201, tags=["auth"])
def register(role: str, payload: AuthPayload, request: Request, response: Response, db: Session = Depends(get_db)):
    user = register_user(db, payload.email, payload.password, role)
    if settings.require_email_verification:
        token = create_email_action_token(db, user, "VERIFY_EMAIL", settings.email_token_minutes)
        verify_url = f"{settings.public_app_url.rstrip('/')}/verify-email?token={token}"
        send_email(user.email, "Verify your StuSkillLink email", f"Verify your StuSkillLink account using this link:\n\n{verify_url}\n\nThis link expires in {settings.email_token_minutes} minutes.")
    return issue_session(db, user, request, response)


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginPayload, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_login_rate_limit(request, payload.email)
    user = authenticate(db, payload.email, payload.password)
    clear_login_rate_limit(request, payload.email)
    return issue_session(db, user, request, response)


@router.post("/auth/refresh", response_model=TokenResponse, tags=["auth"])
def refresh_auth_session(
    request: Request, response: Response,
    refresh_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
    db: Session = Depends(get_db),
):
    if not refresh_cookie:
        raise HTTPException(status_code=401, detail="Refresh session required")
    return rotate_refresh_session(db, refresh_cookie, request, response)


@router.post("/auth/logout", status_code=204, tags=["auth"])
def logout(
    response: Response,
    refresh_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
    db: Session = Depends(get_db),
):
    revoke_refresh_session(db, refresh_cookie)
    clear_auth_cookies(response)


@router.get("/auth/me", response_model=UserResponse, tags=["auth"])
def me(user: User = Depends(get_current_user)):
    return UserResponse(public_id=user.public_id, email=user.email, role=user.role, email_verified=user.email_verified)


@router.post("/auth/email/verify/request", status_code=202, tags=["auth"])
def request_email_verification(payload: EmailAddressPayload, request: Request, db: Session = Depends(get_db)):
    enforce_login_rate_limit(request, f"verify:{payload.email}")
    user = db.scalar(select(User).where(User.email == payload.email))
    if user and user.is_active and not user.email_verified:
        token = create_email_action_token(db, user, "VERIFY_EMAIL", settings.email_token_minutes)
        verify_url = f"{settings.public_app_url.rstrip('/')}/verify-email?token={token}"
        send_email(user.email, "Verify your StuSkillLink email", f"Verify your StuSkillLink account using this link:\n\n{verify_url}\n\nThis link expires in {settings.email_token_minutes} minutes.")
    return {"message": "If the account requires verification, a verification link has been sent."}


@router.post("/auth/email/verify", tags=["auth"])
def verify_email(payload: ActionTokenPayload, db: Session = Depends(get_db)):
    user = consume_email_action_token(db, payload.token, "VERIFY_EMAIL")
    user.email_verified = True
    audit(db, user=user, event_type="EMAIL_VERIFIED", entity_type="user", entity_id=user.id)
    db.commit()
    return {"verified": True, "email": user.email}


@router.post("/auth/password/forgot", status_code=202, tags=["auth"])
def forgot_password(payload: EmailAddressPayload, request: Request, db: Session = Depends(get_db)):
    enforce_login_rate_limit(request, f"reset:{payload.email}")
    user = db.scalar(select(User).where(User.email == payload.email))
    if user and user.is_active:
        token = create_email_action_token(db, user, "RESET_PASSWORD", settings.password_reset_minutes)
        reset_url = f"{settings.public_app_url.rstrip('/')}/reset-password?token={token}"
        send_email(user.email, "Reset your StuSkillLink password", f"Reset your StuSkillLink password using this link:\n\n{reset_url}\n\nThis link expires in {settings.password_reset_minutes} minutes. If you did not request this, ignore this message.")
    return {"message": "If an account exists for this email, a password reset link has been sent."}


@router.post("/auth/password/reset", tags=["auth"])
def reset_password(payload: PasswordResetPayload, response: Response, db: Session = Depends(get_db)):
    user = consume_email_action_token(db, payload.token, "RESET_PASSWORD")
    user.password_hash = hash_password(payload.password)
    revoke_all_refresh_sessions(db, user.id)
    audit(db, user=user, event_type="PASSWORD_RESET", entity_type="user", entity_id=user.id)
    clear_auth_cookies(response)
    db.commit()
    return {"reset": True}


# ---------- payloads ----------
class StudentProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = ""
    college: str = ""
    university: str = ""
    degree: str = ""
    department: str = ""
    current_year: int = Field(default=1, ge=1, le=8)
    cgpa: float = Field(default=0, ge=0, le=10)
    city: str = ""
    state: str = ""
    skills: list[str] = []
    projects: list[dict[str, Any]] = []
    certifications: list[dict[str, Any]] = []


class ResumePayload(BaseModel):
    text: str = Field(min_length=20, max_length=30000)


class PreferencePayload(BaseModel):
    preferred_domains: list[str] = []
    preferred_locations: list[str] = []
    work_modes: list[str] = []
    ranked_opportunity_ids: list[int] = []
    ranked_company_ids: list[int] = []
    general_pool_opt_in: bool = True


class LSRWPayload(BaseModel):
    listening_correct: int = Field(ge=0)
    listening_total: int = Field(gt=0)
    reading_correct: int = Field(ge=0)
    reading_total: int = Field(gt=0)
    speaking_text: str = Field(min_length=20, max_length=5000)
    writing_text: str = Field(min_length=20, max_length=8000)

    @model_validator(mode="after")
    def validate_counts(self):
        if self.listening_correct > self.listening_total:
            raise ValueError("listening_correct cannot exceed listening_total")
        if self.reading_correct > self.reading_total:
            raise ValueError("reading_correct cannot exceed reading_total")
        return self


class OfferResponsePayload(BaseModel):
    response: str


class CompanyProfilePayload(BaseModel):
    company_name: str
    industry: str = ""
    website: str = ""
    description: str = ""
    recruiter_name: str = ""
    office_locations: list[str] = []


class OpportunityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_type: str = "INTERNSHIP"
    title: str
    domain: str
    description: str = ""
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    seats: int = Field(default=1, ge=1, le=500)
    stipend: int = Field(default=0, ge=0)
    location: str = ""
    work_mode: str = "ONSITE"
    min_cgpa: float = Field(default=0, ge=0, le=10)
    duration: str = ""
    deadline: datetime | None = None


class LearningProgramPayload(BaseModel):
    title: str
    skills: list[str] = []
    provider: str = "Industry"
    duration: str = ""
    resource_url: str = ""
    badge_title: str = ""


class FeedbackPayload(BaseModel):
    rating: int = Field(ge=1, le=5)
    strengths: list[str] = []
    improvement_skills: list[str] = []
    comments: str = ""
    recommend_for_placement: bool = False


class AcademicianProfilePayload(BaseModel):
    name: str
    institution: str
    department: str
    designation: str = ""
    expertise: list[str] = []
    interests: list[str] = []


class AcademicianOpportunityPayload(BaseModel):
    opportunity_type: str
    title: str
    host_name: str
    description: str = ""
    required_expertise: list[str] = []
    location: str = ""
    mode: str = "HYBRID"
    deadline: datetime | None = None


class InstitutionProfilePayload(BaseModel):
    institution_name: str
    city: str = ""
    state: str = ""
    departments: list[str] = []


class OpportunityStatusPayload(BaseModel):
    status: str = Field(pattern="^(DRAFT|OPEN|PAUSED|CLOSED|CANCELLED)$")


class AllocationLifecyclePayload(BaseModel):
    status: str = Field(pattern="^(IN_PROGRESS|COMPLETED)$")


class InstitutionJoinPayload(BaseModel):
    institution_code: str = Field(min_length=4, max_length=40)


class ReservationVerificationPayload(BaseModel):
    category: str = Field(min_length=2, max_length=32)
    status: str = Field(pattern="^(VERIFIED|REJECTED|UNVERIFIED)$")
    source: str = Field(default="Institution verification", max_length=255)


# ---------- helpers ----------
def student_for_user(db: Session, user: User) -> StudentProfile:
    item = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if not item:
        raise HTTPException(404, "Student profile not found")
    return item


def company_for_user(db: Session, user: User) -> CompanyProfile:
    item = db.scalar(select(CompanyProfile).where(CompanyProfile.user_id == user.id))
    if not item:
        raise HTTPException(404, "Company profile not found")
    return item


def academician_for_user(db: Session, user: User) -> AcademicianProfile:
    item = db.scalar(select(AcademicianProfile).where(AcademicianProfile.user_id == user.id))
    if not item:
        raise HTTPException(404, "Academician profile not found")
    return item


def institution_for_user(db: Session, user: User) -> InstitutionProfile:
    item = db.scalar(select(InstitutionProfile).where(InstitutionProfile.user_id == user.id))
    if not item:
        raise HTTPException(404, "Institution profile not found")
    return item


def require_verified_company(db: Session, user: User) -> CompanyProfile:
    company = company_for_user(db, user)
    if not company.verified or company.verification_status != "VERIFIED":
        raise HTTPException(status_code=403, detail="Company verification is required for this action")
    return company


def require_verified_institution(db: Session, user: User) -> InstitutionProfile:
    institution = institution_for_user(db, user)
    if not institution.verified or institution.verification_status != "VERIFIED":
        raise HTTPException(status_code=403, detail="Institution verification is required for this action")
    return institution


def _extract_resume_text(filename: str, data: bytes, content_type: str | None = None) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if len(data) > settings.max_resume_bytes:
        raise HTTPException(413, f"Resume file exceeds {settings.max_resume_bytes // (1024 * 1024)} MB")
    if not data:
        raise HTTPException(400, "Resume file is empty")
    if suffix == "txt":
        if b"\x00" in data[:4096]:
            raise HTTPException(415, "Invalid text resume")
        return data.decode("utf-8", errors="strict")
    if suffix == "pdf":
        if not data.startswith(b"%PDF-"):
            raise HTTPException(415, "File extension and PDF signature do not match")
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data), strict=False)
            if len(reader.pages) > 25:
                raise HTTPException(400, "Resume PDF exceeds 25 pages")
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(400, "Unable to read PDF resume") from exc
    if suffix == "docx":
        if not data.startswith(b"PK"):
            raise HTTPException(415, "File extension and DOCX signature do not match")
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = archive.namelist()
                if len(names) > 500 or sum(info.file_size for info in archive.infolist()) > 20 * 1024 * 1024:
                    raise HTTPException(400, "DOCX archive is too large after decompression")
                xml = archive.read("word/document.xml")
            root = ElementTree.fromstring(xml)
            texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
            return " ".join(texts)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(400, "Unable to read DOCX resume") from exc
    raise HTTPException(415, "Use PDF, DOCX or TXT resume files")


# ---------- shared/system ----------
@router.get("/sih/system/provider", tags=["system"])
def provider_status(user: User = Depends(get_current_user)):
    return nim_client.status()


@router.get("/sih/badges/{badge_id}/verify", tags=["portfolio"])
def verify_badge(badge_id: int, db: Session = Depends(get_db)):
    badge = db.get(DigitalBadge, badge_id)
    if not badge:
        raise HTTPException(404, "Badge not found")
    student = db.get(StudentProfile, badge.student_profile_id)
    return {
        "verified": bool(badge.verified), "verification_status": badge.verification_status, "badge_id": badge.id,
        "title": badge.title, "issuer": badge.issuer, "student_name": student.name if student else "",
        "reviewed_at": badge.reviewed_at,
        "credential_url": badge.credential_url, "evidence_url": badge.evidence_url, "credential_id": badge.credential_id,
        "standards": badge.standards,
    }


@router.get("/sih/system/provider/models", tags=["system"])
def provider_models(user: User = Depends(require_roles("ADMIN"))):
    return nim_client.models()


@router.get("/sih/system/integrations", tags=["system"])
def integration_status(user: User = Depends(get_current_user)):
    return {
        "learning": learning_provider_status(),
        "notifications": notification_status(),
        "mongodb": mongodb_status(),
    }


@router.get("/sih/system/agents", tags=["system"])
def agent_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(24)
    if user.role == "STUDENT":
        query = query.where(AgentRun.student_profile_id == student_for_user(db, user).id)
    elif user.role == "COMPANY":
        query = query.where(AgentRun.company_profile_id == company_for_user(db, user).id)
    elif user.role == "INSTITUTION":
        query = query.where(AgentRun.institution_profile_id == institution_for_user(db, user).id)
    elif user.role == "ACADEMICIAN":
        profile = academician_for_user(db, user)
        query = query.where(AgentRun.institution_profile_id == profile.institution_profile_id)
    elif user.role != "ADMIN":
        raise HTTPException(403, "Agent activity is not available")
    runs = db.scalars(query).all()
    return [
        {"id": x.id, "agent_name": x.agent_name, "responsibility": x.responsibility, "status": x.status, "output_data": x.output_data, "created_at": x.created_at}
        for x in runs
    ]


@router.get("/sih/system/audit", tags=["system"])
def audit_log(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION", "COMPANY"))):
    if user.role == "COMPANY":
        company = company_for_user(db, user)
        query = select(AuditEvent).where(AuditEvent.company_profile_id == company.id)
    else:
        institution = institution_for_user(db, user)
        query = select(AuditEvent).where(AuditEvent.institution_profile_id == institution.id)
    events = db.scalars(query.order_by(AuditEvent.created_at.desc()).limit(100)).all()
    return [{"id": x.id, "actor_role": x.actor_role, "event_type": x.event_type, "entity_type": x.entity_type, "entity_id": x.entity_id, "details": x.details, "created_at": x.created_at} for x in events]


# ---------- student ----------
@router.get("/sih/student/dashboard", tags=["student"])
def get_student_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    return student_dashboard(db, student_for_user(db, user))


@router.get("/sih/student/profile", tags=["student"])
def get_student_profile(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    return serialize_student(student_for_user(db, user))


@router.put("/sih/student/profile", tags=["student"])
def update_student_profile(payload: StudentProfilePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    for key, value in payload.model_dump().items():
        setattr(student, key, value)
    student.profile_completion = profile_completion(student)
    refresh_student_matches(db, student)
    audit(db, user=user, event_type="STUDENT_PROFILE_UPDATED", entity_type="student", entity_id=student.id)
    db.commit()
    return serialize_student(student)


@router.post("/sih/student/resume/upload", tags=["student"])
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    filename = file.filename or "resume.txt"
    data = await file.read()
    text = _extract_resume_text(filename, data, file.content_type).strip()
    student.resume_sha256 = hashlib.sha256(data).hexdigest()
    if len(text) < 20:
        raise HTTPException(400, "Resume does not contain enough readable text")
    result = parse_resume_into_profile(student, text[:30000])
    refresh_student_matches(db, student)
    refresh_learning_recommendations(db, student)
    audit(db, user=user, event_type="RESUME_FILE_ANALYZED", entity_type="student", entity_id=student.id, details={"filename": filename, "size": len(data), "skills": result.get("extracted_skills", [])})
    db.commit()
    return {**result, "filename": filename, "profile": serialize_student(student)}


@router.post("/sih/student/resume/analyze", tags=["student"])
def analyze_resume(payload: ResumePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    result = parse_resume_into_profile(student, payload.text)
    refresh_student_matches(db, student)
    refresh_learning_recommendations(db, student)
    audit(db, user=user, event_type="RESUME_SKILLS_EXTRACTED", entity_type="student", entity_id=student.id, details=result)
    db.commit()
    return {**result, "profile": serialize_student(student)}


@router.put("/sih/student/preferences", tags=["student"])
def update_preferences(payload: PreferencePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    student.preferences = {k: v for k, v in payload.model_dump().items() if k != "general_pool_opt_in"}
    student.general_pool_opt_in = payload.general_pool_opt_in
    refresh_student_matches(db, student)
    audit(db, user=user, event_type="PREFERENCES_UPDATED", entity_type="student", entity_id=student.id, details={"general_pool_opt_in": student.general_pool_opt_in})
    db.commit()
    return {"preferences": student.preferences, "general_pool_opt_in": student.general_pool_opt_in}


@router.post("/sih/student/lsrw/assess", tags=["student"])
def run_lsrw(payload: LSRWPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    item = assess_lsrw(db, student, user=user, **payload.model_dump())
    refresh_student_matches(db, student)
    db.commit()
    return {"id": item.id, "listening": item.listening, "speaking": item.speaking, "reading": item.reading, "writing": item.writing, "overall": item.overall, "details": item.details}


@router.get("/sih/student/skill-gap", tags=["student"])
def get_skill_gap(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    return skill_gap_report(db, student_for_user(db, user))


@router.get("/sih/student/learning", tags=["student"])
def get_learning(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    items = db.scalars(select(LearningRecommendation).where(LearningRecommendation.student_profile_id == student.id).order_by(LearningRecommendation.id)).all()
    return [{"id": x.id, "skill": x.skill, "reason": x.reason, "action": x.action, "resource_url": x.resource_url, "priority": x.priority, "completed": x.completed} for x in items]


@router.post("/sih/student/readiness/refresh", tags=["student"])
def refresh_student_readiness(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    matches = refresh_student_matches(db, student)
    learning = refresh_learning_recommendations(db, student)
    audit(db, user=user, event_type="STUDENT_READINESS_REFRESHED", entity_type="student", entity_id=student.id, details={"matches": len(matches), "learning": len(learning)})
    db.commit()
    return {"matches": len(matches), "learning": len(learning), "skill_gap": skill_gap_report(db, student)}


@router.post("/sih/student/learning/{recommendation_id}/complete", tags=["student"])
def complete_learning(recommendation_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    rec = db.get(LearningRecommendation, recommendation_id)
    if not rec or rec.student_profile_id != student.id:
        raise HTTPException(404, "Learning recommendation not found")
    rec.completed = True
    if not any(b.title.lower() == f"{rec.skill} readiness".lower() for b in student.badges):
        db.add(DigitalBadge(
            student_profile_id=student.id, title=f"{rec.skill} Readiness", issuer="StuSkillLink Learning Path",
            verified=False, verification_status="PENDING_VERIFICATION", credential_url="",
            standards={"type": "OpenBadges3-compatible", "status": "pending issuer verification"},
        ))
    audit(db, user=user, event_type="LEARNING_COMPLETED", entity_type="learning_recommendation", entity_id=rec.id, details={"skill": rec.skill})
    db.commit()
    return {"completed": True, "skill": rec.skill}


@router.get("/sih/student/portfolio", tags=["student"])
def get_portfolio(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    return {"profile": serialize_student(student), "badges": [serialize_badge(x) for x in student.badges], "lsrw": current_lsrw(db, student.id) and {"overall": current_lsrw(db, student.id).overall}}


@router.get("/sih/student/opportunities", tags=["student"])
def student_opportunities(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    matches = {m.opportunity_id: m for m in stored_student_matches(db, student)}
    opportunities = db.scalars(
        select(Opportunity).options(selectinload(Opportunity.company)).where(Opportunity.status == "OPEN", Opportunity.moderation_status == "APPROVED")
    ).all()
    opportunities = [item for item in opportunities if opportunity_is_open(item)]
    applied_ids = set(db.scalars(select(Application.opportunity_id).where(Application.student_profile_id == student.id)).all())
    rows = [{**serialize_opportunity(x, matches.get(x.id)), "applied": x.id in applied_ids} for x in opportunities]
    return sorted(rows, key=lambda x: -(x["match"]["total_score"] if x["match"] else 0))


@router.post("/sih/student/opportunities/{opportunity_id}/apply", tags=["student"])
def apply_opportunity(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    opportunity = db.get(Opportunity, opportunity_id)
    if not opportunity or not opportunity_is_open(opportunity):
        raise HTTPException(409, "Opportunity is closed, expired, paused or not approved")
    prefs = student.preferences or {}
    ranked = prefs.get("ranked_opportunity_ids", [])
    rank = ranked.index(opportunity_id) + 1 if opportunity_id in ranked else None
    app = ensure_application(db, student, opportunity, rank)
    refresh_student_matches(db, student)
    audit(db, user=user, event_type="APPLICATION_SUBMITTED", entity_type="opportunity", entity_id=opportunity.id)
    db.commit()
    db.refresh(app)
    return {"application_id": app.id, "status": app.status, "opportunity_id": opportunity.id}


@router.get("/sih/student/offers/{allocation_id}/letter", tags=["student"])
def student_offer_letter(allocation_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    allocation = db.get(Allocation, allocation_id)
    if not allocation or allocation.student_profile_id != student.id:
        raise HTTPException(404, "Offer not found")
    opportunity = db.get(Opportunity, allocation.opportunity_id)
    if not opportunity:
        raise HTTPException(404, "Opportunity not found")
    company = opportunity.company
    letter = (
        f"Offer Letter\n\nDear {student.name},\n\n"
        f"{company.company_name if company else 'Industry Partner'} is pleased to offer you the role of {opportunity.title}. "
        f"This offer was generated through StuSkillLink company rank #{allocation.rank}, allocation round {allocation.round}, "
        f"under the {allocation.category_slot} seat slot.\n\n"
        f"Location: {opportunity.location} ({opportunity.work_mode})\nDuration: {opportunity.duration or 'As specified by employer'}\n"
        f"Status: {allocation.status}\n\nRegards,\nStuSkillLink Allocation System"
    )
    return {"allocation_id": allocation.id, "student_name": student.name, "company_name": company.company_name if company else "", "title": opportunity.title, "status": allocation.status, "letter_text": letter}


@router.post("/sih/student/offers/{allocation_id}/respond", tags=["student"])
def student_offer_response(allocation_id: int, payload: OfferResponsePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    allocation = db.get(Allocation, allocation_id)
    if not allocation or allocation.student_profile_id != student.id:
        raise HTTPException(404, "Offer not found")
    item = respond_to_allocation(db, allocation, payload.response, user)
    return serialize_allocation(db, item)


@router.post("/sih/student/agents/run", tags=["student"])
def run_student_agents(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    runs = run_seven_agent_cycle(db, student_for_user(db, user), user)
    return [{"id": x.id, "agent_name": x.agent_name, "responsibility": x.responsibility, "status": x.status, "output_data": x.output_data} for x in runs]


@router.get("/sih/student/industry-learning", tags=["student"])
def student_industry_learning(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    student_skills = {x.lower() for x in student.skills}
    items = db.scalars(select(IndustryLearningProgram).order_by(IndustryLearningProgram.created_at.desc())).all()
    rows = []
    for item in items:
        overlap = len(student_skills & {str(x).lower() for x in item.skills})
        rows.append({
            "id": item.id, "title": item.title, "skills": item.skills, "provider": item.provider,
            "duration": item.duration, "resource_url": item.resource_url, "badge_title": item.badge_title,
            "relevance": min(100, 55 + overlap * 15),
            "completed": any(b.title == (item.badge_title or f"{item.title} Completion") for b in student.badges),
        })
    return sorted(rows, key=lambda x: -x["relevance"])


@router.post("/sih/student/industry-learning/{program_id}/complete", tags=["student"])
def complete_industry_learning(program_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    program = db.get(IndustryLearningProgram, program_id)
    if not program:
        raise HTTPException(404, "Industry learning program not found")
    title = program.badge_title or f"{program.title} Completion"
    badge = next((b for b in student.badges if b.title == title), None)
    if not badge:
        badge = DigitalBadge(
            student_profile_id=student.id, title=title, issuer=program.provider, verified=False,
            verification_status="PENDING_VERIFICATION", credential_url=program.resource_url, evidence_url=program.resource_url,
            standards={"type": "OpenBadges3-compatible", "status": "pending provider verification"},
        )
        db.add(badge)
    audit(db, user=user, event_type="INDUSTRY_LEARNING_COMPLETED", entity_type="learning_program", entity_id=program.id, details={"badge": title})
    db.commit()
    return {"completed": True, "badge": title}


# ---------- company / industry ----------
@router.get("/sih/company/dashboard", tags=["company"])
def get_company_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    return company_dashboard(db, company_for_user(db, user))


@router.put("/sih/company/profile", tags=["company"])
def update_company_profile(payload: CompanyProfilePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = company_for_user(db, user)
    for key, value in payload.model_dump().items():
        setattr(company, key, value)
    audit(db, user=user, event_type="COMPANY_PROFILE_UPDATED", entity_type="company", entity_id=company.id)
    db.commit()
    return company_dashboard(db, company)["profile"]


@router.post("/sih/company/opportunities", status_code=201, tags=["company"])
def create_opportunity(payload: OpportunityPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    item = Opportunity(
        company_profile_id=company.id,
        status="DRAFT",
        moderation_status="PENDING",
        reservation_policy={},
        reservation_policy_approved=False,
        **payload.model_dump(),
    )
    db.add(item)
    db.flush()
    audit(
        db,
        user=user,
        event_type="OPPORTUNITY_SUBMITTED_FOR_REVIEW",
        entity_type="opportunity",
        entity_id=item.id,
        details={"type": item.opportunity_type, "seats": item.seats},
    )
    db.commit()
    db.refresh(item)
    return serialize_opportunity(item)


@router.put("/sih/company/opportunities/{opportunity_id}", tags=["company"])
def update_opportunity(opportunity_id: int, payload: OpportunityPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    item = db.get(Opportunity, opportunity_id)
    if not item or item.company_profile_id != company.id:
        raise HTTPException(404, "Opportunity not found")
    if item.status in {"FILLED", "COMPLETED"}:
        raise HTTPException(409, "Completed opportunities cannot be edited")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    # Material edits must be reviewed again before they can be re-opened.
    item.status = "DRAFT"
    item.moderation_status = "PENDING"
    item.reservation_policy_approved = False
    item.published_at = None
    audit(db, user=user, event_type="OPPORTUNITY_UPDATED_REVIEW_REQUIRED", entity_type="opportunity", entity_id=item.id)
    db.commit()
    return serialize_opportunity(item)


@router.patch("/sih/company/opportunities/{opportunity_id}/status", tags=["company"])
def update_opportunity_status(opportunity_id: int, payload: OpportunityStatusPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    item = db.get(Opportunity, opportunity_id)
    if not item or item.company_profile_id != company.id:
        raise HTTPException(404, "Opportunity not found")
    requested = payload.status.upper()
    if requested == "OPEN" and item.moderation_status != "APPROVED":
        raise HTTPException(409, "Administrator approval is required before publishing")
    if requested == "OPEN" and item.deadline and ensure_utc(item.deadline) <= utc_now():
        raise HTTPException(409, "Expired opportunities cannot be opened")
    item.status = requested
    if requested == "OPEN":
        item.published_at = item.published_at or utc_now()
        item.closed_at = None
    elif requested in {"CLOSED", "CANCELLED"}:
        item.closed_at = utc_now()
    audit(db, user=user, event_type="OPPORTUNITY_STATUS_CHANGED", entity_type="opportunity", entity_id=item.id, details={"status": requested})
    db.commit()
    return serialize_opportunity(item)


def _company_ranking_rows(db: Session, opp: Opportunity) -> list[dict[str, Any]]:
    applications = db.scalars(
        select(Application)
        .where(Application.opportunity_id == opp.id, Application.status.in_(["SUBMITTED", "RANKING_ELIGIBLE"]))
        .order_by(Application.created_at.asc(), Application.id.asc())
    ).all()
    if not applications:
        return []
    student_ids = [a.student_profile_id for a in applications]
    students = {x.id: x for x in db.scalars(select(StudentProfile).where(StudentProfile.id.in_(student_ids))).all()}
    matches = {
        x.student_profile_id: x
        for x in db.scalars(select(MatchResult).where(MatchResult.opportunity_id == opp.id, MatchResult.student_profile_id.in_(student_ids))).all()
    }
    rows = []
    for application in applications:
        student = students.get(application.student_profile_id)
        match = matches.get(application.student_profile_id)
        if not student or not match or not bool((match.explanation or {}).get("eligible")):
            continue
        rows.append({"application": application, "student": student, "match": match})
    rows.sort(key=lambda row: (
        -row["match"].total_score,
        row["application"].preference_rank if row["application"].preference_rank is not None else 9999,
        row["application"].created_at,
        row["application"].id,
    ))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


@router.get("/sih/company/opportunities/{opportunity_id}/rankings", tags=["company"])
def company_rankings(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    opp = db.get(Opportunity, opportunity_id)
    if not opp or opp.company_profile_id != company.id:
        raise HTTPException(404, "Opportunity not found")
    rows = _company_ranking_rows(db, opp)
    return [
        {
            "rank": r["rank"],
            "student": serialize_candidate_for_company(r["student"]),
            "match": serialize_match(r["match"]),
            "application_id": r["application"].id,
            "preference_rank": r["application"].preference_rank,
        }
        for r in rows
    ]


@router.post("/sih/company/opportunities/{opportunity_id}/rankings/refresh", tags=["company"])
def refresh_company_rankings(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    opp = db.get(Opportunity, opportunity_id)
    if not opp or opp.company_profile_id != company.id:
        raise HTTPException(404, "Opportunity not found")
    if opp.moderation_status != "APPROVED":
        raise HTTPException(409, "Opportunity must be approved before ranking candidates")
    rank_applicants(db, opp)
    audit(db, user=user, event_type="COMPANY_RANKINGS_REFRESHED", entity_type="opportunity", entity_id=opp.id)
    db.commit()
    return company_rankings(opportunity_id, db, user)


@router.post("/sih/company/opportunities/{opportunity_id}/allocate", tags=["company"])
def company_allocate(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    opp = db.get(Opportunity, opportunity_id)
    if not opp or opp.company_profile_id != company.id:
        raise HTTPException(404, "Opportunity not found")
    items = allocate_opportunity(db, opp, user)
    return [serialize_allocation_for_company(db, x) for x in items]


@router.get("/sih/company/allocations", tags=["company"])
def company_allocations(db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    items = db.scalars(
        select(Allocation).join(Opportunity).where(Opportunity.company_profile_id == company.id).order_by(Allocation.created_at.desc())
    ).all()
    return [serialize_allocation_for_company(db, x) for x in items]


@router.patch("/sih/company/allocations/{allocation_id}/lifecycle", tags=["company"])
def update_allocation_lifecycle(allocation_id: int, payload: AllocationLifecyclePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    allocation = db.get(Allocation, allocation_id)
    if not allocation:
        raise HTTPException(404, "Allocation not found")
    opp = db.get(Opportunity, allocation.opportunity_id)
    if not opp or opp.company_profile_id != company.id:
        raise HTTPException(403, "Not your allocation")
    target = payload.status.upper()
    allowed = {"ACCEPTED": {"IN_PROGRESS"}, "IN_PROGRESS": {"COMPLETED"}}
    if target not in allowed.get(allocation.status, set()):
        raise HTTPException(409, f"Cannot move allocation from {allocation.status} to {target}")
    allocation.status = target
    if target == "COMPLETED":
        allocation.completed_at = utc_now()
    audit(db, user=user, event_type=f"ALLOCATION_{target}", entity_type="allocation", entity_id=allocation.id)
    db.commit()
    return serialize_allocation_for_company(db, allocation)


@router.post("/sih/company/learning-programs", status_code=201, tags=["company"])
def create_learning_program(payload: LearningProgramPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    item = IndustryLearningProgram(company_profile_id=company.id, **payload.model_dump())
    db.add(item)
    audit(db, user=user, event_type="INDUSTRY_LEARNING_PROGRAM_CREATED", entity_type="learning_program")
    db.commit()
    db.refresh(item)
    return {"id": item.id, **payload.model_dump()}


@router.post("/sih/company/allocations/{allocation_id}/feedback", tags=["company"])
def create_feedback(allocation_id: int, payload: FeedbackPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = require_verified_company(db, user)
    allocation = db.get(Allocation, allocation_id)
    if not allocation:
        raise HTTPException(404, "Allocation not found")
    opp = db.get(Opportunity, allocation.opportunity_id)
    if not opp or opp.company_profile_id != company.id:
        raise HTTPException(403, "Not your allocation")
    if allocation.status != "COMPLETED":
        raise HTTPException(409, "Feedback is allowed only after the internship/placement is completed")
    existing = db.scalar(select(CompanyFeedback).where(CompanyFeedback.allocation_id == allocation.id))
    if existing:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
    else:
        db.add(CompanyFeedback(allocation_id=allocation.id, **payload.model_dump()))
    db.flush()
    student = db.get(StudentProfile, allocation.student_profile_id)
    if student:
        refresh_curriculum_insights(db, student.institution_profile_id)
        refresh_student_matches(db, student)
    audit(
        db,
        user=user,
        event_type="COMPANY_FEEDBACK_SUBMITTED",
        entity_type="allocation",
        entity_id=allocation.id,
        details={"rating": payload.rating, "recommend_for_placement": payload.recommend_for_placement},
    )
    db.commit()
    return {"saved": True, "allocation_id": allocation.id}


# ---------- academician ----------
@router.get("/sih/academician/dashboard", tags=["academician"])
def get_academician_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("ACADEMICIAN"))):
    return academician_dashboard(db, academician_for_user(db, user))


@router.put("/sih/academician/profile", tags=["academician"])
def update_academician_profile(payload: AcademicianProfilePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ACADEMICIAN"))):
    profile = academician_for_user(db, user)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    audit(db, user=user, event_type="ACADEMICIAN_PROFILE_UPDATED", entity_type="academician", entity_id=profile.id)
    db.commit()
    return academician_dashboard(db, profile)["profile"]


@router.post("/sih/academician/institution/join", tags=["academician"])
def academician_join_institution(payload: InstitutionJoinPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ACADEMICIAN"))):
    profile = academician_for_user(db, user)
    institution = db.scalar(
        select(InstitutionProfile).where(
            InstitutionProfile.institution_code == payload.institution_code.strip().upper(),
            InstitutionProfile.verified.is_(True),
            InstitutionProfile.verification_status == "VERIFIED",
        )
    )
    if not institution:
        raise HTTPException(404, "Verified institution code not found")
    profile.institution_profile_id = institution.id
    profile.institution = institution.institution_name
    audit(db, user=user, event_type="ACADEMICIAN_JOINED_INSTITUTION", entity_type="academician", entity_id=profile.id, details={"institution_profile_id": institution.id})
    db.commit()
    return {"institution_profile_id": institution.id, "institution_name": institution.institution_name}


@router.post("/sih/academician/opportunities/{opportunity_id}/apply", tags=["academician"])
def apply_academician_opportunity(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("ACADEMICIAN"))):
    profile = academician_for_user(db, user)
    opp = db.get(AcademicianOpportunity, opportunity_id)
    now = utc_now()
    if not opp or opp.status != "OPEN" or (opp.deadline and ensure_utc(opp.deadline) <= now):
        raise HTTPException(404, "Open opportunity not found")
    if opp.institution_profile_id is not None and opp.institution_profile_id != profile.institution_profile_id:
        raise HTTPException(404, "Opportunity not found")
    existing = db.scalar(
        select(AcademicianOpportunityApplication).where(
            AcademicianOpportunityApplication.academician_profile_id == profile.id,
            AcademicianOpportunityApplication.opportunity_id == opp.id,
        )
    )
    if existing:
        return {"id": existing.id, "status": existing.status, "match_score": existing.match_score}
    item = AcademicianOpportunityApplication(
        academician_profile_id=profile.id,
        opportunity_id=opp.id,
        status="APPLIED",
        match_score=academician_match_score(profile, opp),
    )
    db.add(item)
    audit(db, user=user, event_type="ACADEMICIAN_OPPORTUNITY_APPLIED", entity_type="academician_opportunity", entity_id=opp.id)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": item.status, "match_score": item.match_score}


# ---------- institution ----------
@router.get("/sih/institution/dashboard", tags=["institution"])
def get_institution_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    institution = institution_for_user(db, user)
    return institution_dashboard(db, institution)


@router.put("/sih/institution/profile", tags=["institution"])
def update_institution_profile(payload: InstitutionProfilePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    profile = institution_for_user(db, user)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    audit(db, user=user, event_type="INSTITUTION_PROFILE_UPDATED", entity_type="institution", entity_id=profile.id)
    db.commit()
    return institution_dashboard(db, profile)["profile"]


@router.post("/sih/institution/curriculum/refresh", tags=["institution"])
def institution_refresh_curriculum(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    institution = require_verified_institution(db, user)
    items = refresh_curriculum_insights(db, institution.id)
    run_seven_agent_cycle(db, None, user)
    return {"generated": len(items), "message": "Curriculum insights refreshed from approved role requirements, verified tenant skill gaps and completed company feedback."}


@router.post("/sih/institution/academician-opportunities", status_code=201, tags=["institution"])
def create_academician_opportunity(payload: AcademicianOpportunityPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    institution = require_verified_institution(db, user)
    item = AcademicianOpportunity(institution_profile_id=institution.id, **payload.model_dump(), status="OPEN")
    db.add(item)
    db.flush()
    audit(db, user=user, event_type="ACADEMICIAN_OPPORTUNITY_CREATED", entity_type="academician_opportunity", entity_id=item.id)
    db.commit()
    db.refresh(item)
    return {"id": item.id, **payload.model_dump(), "status": item.status, "institution_profile_id": institution.id}


@router.get("/sih/institution/students", tags=["institution"])
def institution_students(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    institution = require_verified_institution(db, user)
    students = db.scalars(
        select(StudentProfile).where(StudentProfile.institution_profile_id == institution.id).order_by(StudentProfile.department, StudentProfile.name)
    ).all()
    ids = [x.id for x in students]
    if not ids:
        return []
    matches = db.scalars(
        select(MatchResult).where(MatchResult.student_profile_id.in_(ids)).order_by(MatchResult.student_profile_id, MatchResult.total_score.desc())
    ).all()
    matches_by_student: dict[int, list[MatchResult]] = {}
    for match in matches:
        matches_by_student.setdefault(match.student_profile_id, []).append(match)
    assessments = db.scalars(
        select(LSRWAssessment).where(LSRWAssessment.student_profile_id.in_(ids)).order_by(LSRWAssessment.created_at.desc())
    ).all()
    latest_lsrw: dict[int, LSRWAssessment] = {}
    for item in assessments:
        latest_lsrw.setdefault(item.student_profile_id, item)
    allocations = db.scalars(select(Allocation).where(Allocation.student_profile_id.in_(ids))).all()
    allocation_map: dict[int, list[Allocation]] = {}
    for item in allocations:
        allocation_map.setdefault(item.student_profile_id, []).append(item)
    rows = []
    for student in students:
        student_matches = matches_by_student.get(student.id, [])[:5]
        student_allocations = allocation_map.get(student.id, [])
        rows.append({
            "profile": serialize_student(student),
            "readiness": round(sum(x.total_score for x in student_matches) / max(1, len(student_matches)), 1) if student_matches else 0,
            "communication": latest_lsrw.get(student.id).overall if latest_lsrw.get(student.id) else 0,
            "accepted_allocations": sum(1 for x in student_allocations if x.status in {"ACCEPTED", "IN_PROGRESS", "COMPLETED"}),
            "active_offers": sum(1 for x in student_allocations if x.status == "OFFERED"),
        })
    return rows


@router.patch("/sih/institution/students/{student_id}/reservation", tags=["institution"])
def institution_verify_reservation(student_id: int, payload: ReservationVerificationPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    institution = require_verified_institution(db, user)
    student = db.get(StudentProfile, student_id)
    if not student or student.institution_profile_id != institution.id:
        raise HTTPException(404, "Student not found in this institution")
    student.reservation_category = payload.category.strip().upper()
    student.reservation_status = payload.status
    student.reservation_source = payload.source.strip() or f"Verified by {institution.institution_name}"
    student.reservation_verified_at = utc_now() if payload.status == "VERIFIED" else None
    audit(db, user=user, event_type="INSTITUTION_RESERVATION_VERIFICATION", entity_type="student", entity_id=student.id, details={"status": payload.status})
    db.commit()
    return {"student_id": student.id, "reservation_category": student.reservation_category, "reservation_status": student.reservation_status}


@router.get("/sih/institution/academician-opportunities", tags=["institution"])
def institution_academician_opportunities(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    institution = require_verified_institution(db, user)
    items = db.scalars(
        select(AcademicianOpportunity).where(AcademicianOpportunity.institution_profile_id == institution.id).order_by(AcademicianOpportunity.created_at.desc())
    ).all()
    result = []
    for item in items:
        applications = db.scalars(
            select(AcademicianOpportunityApplication).where(AcademicianOpportunityApplication.opportunity_id == item.id)
        ).all()
        result.append({
            "id": item.id,
            "opportunity_type": item.opportunity_type,
            "title": item.title,
            "host_name": item.host_name,
            "description": item.description,
            "required_expertise": item.required_expertise,
            "location": item.location,
            "mode": item.mode,
            "deadline": item.deadline,
            "status": item.status,
            "applications": len(applications),
        })
    return result


# ---------- tenant onboarding ----------
@router.post("/sih/student/institution/join", tags=["student"])
def student_join_institution(payload: InstitutionJoinPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    institution = db.scalar(
        select(InstitutionProfile).where(
            InstitutionProfile.institution_code == payload.institution_code.strip().upper(),
            InstitutionProfile.verified.is_(True),
            InstitutionProfile.verification_status == "VERIFIED",
        )
    )
    if not institution:
        raise HTTPException(404, "Verified institution code not found")
    student.institution_profile_id = institution.id
    student.college = institution.institution_name
    audit(db, user=user, event_type="STUDENT_JOINED_INSTITUTION", entity_type="student", entity_id=student.id, details={"institution_profile_id": institution.id})
    db.commit()
    return {"institution_profile_id": institution.id, "institution_name": institution.institution_name}
