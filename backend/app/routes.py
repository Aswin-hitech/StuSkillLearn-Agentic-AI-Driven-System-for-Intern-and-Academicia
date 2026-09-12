from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import (
    AuthPayload,
    LoginPayload,
    TokenResponse,
    UserResponse,
    authenticate,
    get_current_user,
    register_user,
    require_roles,
    token_response,
)
from app.db import get_db
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
    Opportunity,
    StudentProfile,
    User,
)
from app.nim import nim_client
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
    run_six_agent_cycle,
    serialize_allocation,
    serialize_badge,
    serialize_match,
    serialize_opportunity,
    serialize_student,
    skill_gap_report,
    student_dashboard,
)

router = APIRouter()


# ---------- auth ----------
@router.post("/auth/register/{role}", response_model=TokenResponse, status_code=201, tags=["auth"])
def register(role: str, payload: AuthPayload, db: Session = Depends(get_db)):
    return token_response(register_user(db, payload.email, payload.password, role))


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    return token_response(authenticate(db, payload.email, payload.password))


@router.get("/auth/me", response_model=UserResponse, tags=["auth"])
def me(user: User = Depends(get_current_user)):
    return UserResponse(public_id=user.public_id, email=user.email, role=user.role)


# ---------- payloads ----------
class StudentProfilePayload(BaseModel):
    name: str = ""
    college: str = ""
    university: str = ""
    degree: str = ""
    department: str = ""
    current_year: int = Field(default=1, ge=1, le=8)
    cgpa: float = Field(default=0, ge=0, le=10)
    city: str = ""
    state: str = ""
    reservation_category: str = "GENERAL"
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
    deadline: str = ""
    reservation_policy: dict[str, int] = {}


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
    deadline: str = ""


class InstitutionProfilePayload(BaseModel):
    institution_name: str
    city: str = ""
    state: str = ""
    departments: list[str] = []


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


def _extract_resume_text(filename: str, data: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if len(data) > 3 * 1024 * 1024:
        raise HTTPException(413, "Resume file exceeds 3 MB")
    if suffix == "txt":
        return data.decode("utf-8", errors="ignore")
    if suffix == "pdf":
        try:
            from pypdf import PdfReader
            return "\n".join((page.extract_text() or "") for page in PdfReader(io.BytesIO(data)).pages)
        except Exception as exc:
            raise HTTPException(400, "Unable to read PDF resume") from exc
    if suffix == "docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                xml = archive.read("word/document.xml")
            root = ElementTree.fromstring(xml)
            texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
            return " ".join(texts)
        except Exception as exc:
            raise HTTPException(400, "Unable to read DOCX resume") from exc
    raise HTTPException(415, "Use PDF, DOCX or TXT resume files")


# ---------- shared/system ----------
@router.get("/sih/system/provider", tags=["system"])
def provider_status():
    return nim_client.status()


@router.get("/sih/badges/{badge_id}/verify", tags=["portfolio"])
def verify_badge(badge_id: int, db: Session = Depends(get_db)):
    badge = db.get(DigitalBadge, badge_id)
    if not badge:
        raise HTTPException(404, "Badge not found")
    student = db.get(StudentProfile, badge.student_profile_id)
    return {"verified": bool(badge.verified), "badge_id": badge.id, "title": badge.title, "issuer": badge.issuer, "student_name": student.name if student else "", "credential_url": badge.credential_url}


@router.get("/sih/system/provider/models", tags=["system"])
def provider_models():
    return nim_client.models()


@router.get("/sih/system/integrations", tags=["system"])
def integration_status():
    return {
        "learning": learning_provider_status(),
        "notifications": notification_status(),
        "mongodb": mongodb_status(),
    }


@router.get("/sih/system/agents", tags=["system"])
def agent_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    runs = db.scalars(select(AgentRun).order_by(AgentRun.created_at.desc()).limit(24)).all()
    return [
        {"id": x.id, "agent_name": x.agent_name, "responsibility": x.responsibility, "status": x.status, "input_data": x.input_data, "output_data": x.output_data, "created_at": x.created_at}
        for x in runs
    ]


@router.get("/sih/system/audit", tags=["system"])
def audit_log(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION", "COMPANY"))):
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100)).all()
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
    text = _extract_resume_text(filename, data).strip()
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
    report = skill_gap_report(db, student_for_user(db, user))
    db.commit()
    return report


@router.get("/sih/student/learning", tags=["student"])
def get_learning(db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    items = refresh_learning_recommendations(db, student)
    db.commit()
    return [{"id": x.id, "skill": x.skill, "reason": x.reason, "action": x.action, "resource_url": x.resource_url, "priority": x.priority, "completed": x.completed} for x in items]


@router.post("/sih/student/learning/{recommendation_id}/complete", tags=["student"])
def complete_learning(recommendation_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    rec = db.get(LearningRecommendation, recommendation_id)
    if not rec or rec.student_profile_id != student.id:
        raise HTTPException(404, "Learning recommendation not found")
    rec.completed = True
    if not any(b.title.lower() == f"{rec.skill} readiness".lower() for b in student.badges):
        db.add(DigitalBadge(student_profile_id=student.id, title=f"{rec.skill} Readiness", issuer="StuSkillLink Learning Path", verified=True, credential_url=""))
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
    matches = {m.opportunity_id: m for m in refresh_student_matches(db, student)}
    opportunities = db.scalars(select(Opportunity).options(selectinload(Opportunity.company)).where(Opportunity.status == "OPEN")).all()
    applied_ids = set(
        db.scalars(select(Application.opportunity_id).where(Application.student_profile_id == student.id)).all()
    )
    db.commit()
    rows = [{**serialize_opportunity(x, matches.get(x.id)), "applied": x.id in applied_ids} for x in opportunities]
    return sorted(rows, key=lambda x: -(x["match"]["total_score"] if x["match"] else 0))


@router.post("/sih/student/opportunities/{opportunity_id}/apply", tags=["student"])
def apply_opportunity(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("STUDENT"))):
    student = student_for_user(db, user)
    opportunity = db.get(Opportunity, opportunity_id)
    if not opportunity or opportunity.status != "OPEN":
        raise HTTPException(404, "Opportunity not available")
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
    runs = run_six_agent_cycle(db, student_for_user(db, user), user)
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
        badge = DigitalBadge(student_profile_id=student.id, title=title, issuer=program.provider, verified=True, credential_url=program.resource_url)
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
    company = company_for_user(db, user)
    item = Opportunity(company_profile_id=company.id, status="OPEN", **payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, user=user, event_type="OPPORTUNITY_CREATED", entity_type="opportunity", entity_id=item.id, details={"type": item.opportunity_type, "seats": item.seats})
    db.commit()
    db.refresh(item)
    return serialize_opportunity(item)


@router.put("/sih/company/opportunities/{opportunity_id}", tags=["company"])
def update_opportunity(opportunity_id: int, payload: OpportunityPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = company_for_user(db, user)
    item = db.get(Opportunity, opportunity_id)
    if not item or item.company_profile_id != company.id:
        raise HTTPException(404, "Opportunity not found")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    audit(db, user=user, event_type="OPPORTUNITY_UPDATED", entity_type="opportunity", entity_id=item.id)
    db.commit()
    return serialize_opportunity(item)


@router.get("/sih/company/opportunities/{opportunity_id}/rankings", tags=["company"])
def company_rankings(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = company_for_user(db, user)
    opp = db.get(Opportunity, opportunity_id)
    if not opp or opp.company_profile_id != company.id:
        raise HTTPException(404, "Opportunity not found")
    rows = rank_applicants(db, opp)
    db.commit()
    return [
        {"rank": r["rank"], "student": serialize_student(r["student"]), "match": serialize_match(r["match"]), "application_id": r["application"].id, "preference_rank": r["application"].preference_rank}
        for r in rows
    ]


@router.post("/sih/company/opportunities/{opportunity_id}/allocate", tags=["company"])
def company_allocate(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = company_for_user(db, user)
    opp = db.get(Opportunity, opportunity_id)
    if not opp or opp.company_profile_id != company.id:
        raise HTTPException(404, "Opportunity not found")
    items = allocate_opportunity(db, opp, user)
    return [serialize_allocation(db, x) for x in items]


@router.get("/sih/company/allocations", tags=["company"])
def company_allocations(db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = company_for_user(db, user)
    items = db.scalars(select(Allocation).join(Opportunity).where(Opportunity.company_profile_id == company.id).order_by(Allocation.created_at.desc())).all()
    return [serialize_allocation(db, x) for x in items]


@router.post("/sih/company/learning-programs", status_code=201, tags=["company"])
def create_learning_program(payload: LearningProgramPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = company_for_user(db, user)
    item = IndustryLearningProgram(company_profile_id=company.id, **payload.model_dump())
    db.add(item)
    audit(db, user=user, event_type="INDUSTRY_LEARNING_PROGRAM_CREATED", entity_type="learning_program")
    db.commit()
    db.refresh(item)
    return {"id": item.id, **payload.model_dump()}


@router.post("/sih/company/allocations/{allocation_id}/feedback", tags=["company"])
def create_feedback(allocation_id: int, payload: FeedbackPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("COMPANY"))):
    company = company_for_user(db, user)
    allocation = db.get(Allocation, allocation_id)
    if not allocation:
        raise HTTPException(404, "Allocation not found")
    opp = db.get(Opportunity, allocation.opportunity_id)
    if not opp or opp.company_profile_id != company.id:
        raise HTTPException(403, "Not your allocation")
    existing = db.scalar(select(CompanyFeedback).where(CompanyFeedback.allocation_id == allocation.id))
    if existing:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
        feedback = existing
    else:
        feedback = CompanyFeedback(allocation_id=allocation.id, **payload.model_dump())
        db.add(feedback)
    db.flush()
    refresh_curriculum_insights(db)
    student = db.get(StudentProfile, allocation.student_profile_id)
    if student:
        refresh_student_matches(db, student)
    audit(db, user=user, event_type="COMPANY_FEEDBACK_SUBMITTED", entity_type="allocation", entity_id=allocation.id, details={"rating": payload.rating, "recommend_for_placement": payload.recommend_for_placement})
    db.commit()
    return {"saved": True, "allocation_id": allocation.id}


# ---------- academician ----------
@router.get("/sih/academician/dashboard", tags=["academician"])
def get_academician_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("ACADEMICIAN"))):
    refresh_curriculum_insights(db)
    db.commit()
    return academician_dashboard(db, academician_for_user(db, user))


@router.put("/sih/academician/profile", tags=["academician"])
def update_academician_profile(payload: AcademicianProfilePayload, db: Session = Depends(get_db), user: User = Depends(require_roles("ACADEMICIAN"))):
    profile = academician_for_user(db, user)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    audit(db, user=user, event_type="ACADEMICIAN_PROFILE_UPDATED", entity_type="academician", entity_id=profile.id)
    db.commit()
    return academician_dashboard(db, profile)["profile"]


@router.post("/sih/academician/opportunities/{opportunity_id}/apply", tags=["academician"])
def apply_academician_opportunity(opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("ACADEMICIAN"))):
    profile = academician_for_user(db, user)
    opp = db.get(AcademicianOpportunity, opportunity_id)
    if not opp or opp.status != "OPEN":
        raise HTTPException(404, "Opportunity not found")
    existing = db.scalar(select(AcademicianOpportunityApplication).where(AcademicianOpportunityApplication.academician_profile_id == profile.id, AcademicianOpportunityApplication.opportunity_id == opp.id))
    if existing:
        return {"id": existing.id, "status": existing.status, "match_score": existing.match_score}
    item = AcademicianOpportunityApplication(academician_profile_id=profile.id, opportunity_id=opp.id, status="APPLIED", match_score=academician_match_score(profile, opp))
    db.add(item)
    audit(db, user=user, event_type="ACADEMICIAN_OPPORTUNITY_APPLIED", entity_type="academician_opportunity", entity_id=opp.id)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": item.status, "match_score": item.match_score}


# ---------- institution ----------
@router.get("/sih/institution/dashboard", tags=["institution"])
def get_institution_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    return institution_dashboard(db, institution_for_user(db, user))


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
    items = refresh_curriculum_insights(db)
    run_six_agent_cycle(db, None, user)
    db.commit()
    return {"generated": len(items), "message": "Curriculum insights refreshed from live role requirements, skill gaps and company feedback."}


@router.post("/sih/institution/academician-opportunities", status_code=201, tags=["institution"])
def create_academician_opportunity(payload: AcademicianOpportunityPayload, db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    item = AcademicianOpportunity(**payload.model_dump(), status="OPEN")
    db.add(item)
    audit(db, user=user, event_type="ACADEMICIAN_OPPORTUNITY_CREATED", entity_type="academician_opportunity")
    db.commit()
    db.refresh(item)
    return {"id": item.id, **payload.model_dump(), "status": item.status}

@router.get("/sih/institution/students", tags=["institution"])
def institution_students(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    institution_for_user(db, user)
    students = db.scalars(select(StudentProfile).order_by(StudentProfile.department, StudentProfile.name)).all()
    rows = []
    for student in students:
        matches = refresh_student_matches(db, student)
        lsrw = current_lsrw(db, student.id)
        allocations = db.scalars(select(Allocation).where(Allocation.student_profile_id == student.id)).all()
        rows.append({
            "profile": serialize_student(student),
            "readiness": round(sum(x.total_score for x in matches[:5]) / max(1, len(matches[:5])), 1) if matches else 0,
            "communication": lsrw.overall if lsrw else 0,
            "accepted_allocations": sum(1 for x in allocations if x.status == "ACCEPTED"),
            "active_offers": sum(1 for x in allocations if x.status == "OFFERED"),
        })
    db.commit()
    return rows


@router.get("/sih/institution/academician-opportunities", tags=["institution"])
def institution_academician_opportunities(db: Session = Depends(get_db), user: User = Depends(require_roles("INSTITUTION"))):
    institution_for_user(db, user)
    items = db.scalars(select(AcademicianOpportunity).order_by(AcademicianOpportunity.created_at.desc())).all()
    result = []
    for item in items:
        applications = db.scalars(select(AcademicianOpportunityApplication).where(AcademicianOpportunityApplication.opportunity_id == item.id)).all()
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
