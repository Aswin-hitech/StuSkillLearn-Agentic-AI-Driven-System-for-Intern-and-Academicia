from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student_profile: Mapped[StudentProfile | None] = relationship(back_populates="user", cascade="all, delete-orphan")
    company_profile: Mapped[CompanyProfile | None] = relationship(back_populates="user", cascade="all, delete-orphan")
    academician_profile: Mapped[AcademicianProfile | None] = relationship(back_populates="user", cascade="all, delete-orphan")
    institution_profile: Mapped[InstitutionProfile | None] = relationship(back_populates="user", cascade="all, delete-orphan")


class InstitutionProfile(TimestampMixin, Base):
    __tablename__ = "institution_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    institution_name: Mapped[str] = mapped_column(String(255), default="Institution")
    institution_code: Mapped[str] = mapped_column(String(40), unique=True, index=True, default=lambda: f"INST-{uuid4().hex[:8].upper()}")
    city: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(120), default="")
    departments: Mapped[list[str]] = mapped_column(JSON, default=list)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    verification_notes: Mapped[str] = mapped_column(Text, default="")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="institution_profile")
    students: Mapped[list[StudentProfile]] = relationship(back_populates="institution")
    academicians: Mapped[list[AcademicianProfile]] = relationship(back_populates="institution_profile")


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    institution_profile_id: Mapped[int | None] = mapped_column(ForeignKey("institution_profiles.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="Student")
    college: Mapped[str] = mapped_column(String(255), default="")
    university: Mapped[str] = mapped_column(String(255), default="")
    degree: Mapped[str] = mapped_column(String(120), default="")
    department: Mapped[str] = mapped_column(String(120), default="")
    current_year: Mapped[int] = mapped_column(Integer, default=1)
    cgpa: Mapped[float] = mapped_column(Float, default=0)
    city: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(120), default="")
    reservation_category: Mapped[str] = mapped_column(String(32), default="GENERAL")
    reservation_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED", index=True)
    reservation_source: Mapped[str] = mapped_column(String(255), default="")
    reservation_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    projects: Mapped[list[dict]] = mapped_column(JSON, default=list)
    certifications: Mapped[list[dict]] = mapped_column(JSON, default=list)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    general_pool_opt_in: Mapped[bool] = mapped_column(Boolean, default=True)
    profile_completion: Mapped[int] = mapped_column(Integer, default=0)
    resume_text: Mapped[str] = mapped_column(Text, default="")
    resume_sha256: Mapped[str] = mapped_column(String(64), default="")

    user: Mapped[User] = relationship(back_populates="student_profile")
    institution: Mapped[InstitutionProfile | None] = relationship(back_populates="students")
    lsrw_assessments: Mapped[list[LSRWAssessment]] = relationship(back_populates="student", cascade="all, delete-orphan")
    applications: Mapped[list[Application]] = relationship(back_populates="student", cascade="all, delete-orphan")
    matches: Mapped[list[MatchResult]] = relationship(back_populates="student", cascade="all, delete-orphan")
    allocations: Mapped[list[Allocation]] = relationship(back_populates="student", cascade="all, delete-orphan")
    badges: Mapped[list[DigitalBadge]] = relationship(back_populates="student", cascade="all, delete-orphan")
    learning_recommendations: Mapped[list[LearningRecommendation]] = relationship(back_populates="student", cascade="all, delete-orphan")


class CompanyProfile(TimestampMixin, Base):
    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), default="Company")
    industry: Mapped[str] = mapped_column(String(120), default="")
    website: Mapped[str] = mapped_column(String(500), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    recruiter_name: Mapped[str] = mapped_column(String(255), default="")
    office_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    verification_notes: Mapped[str] = mapped_column(Text, default="")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="company_profile")
    opportunities: Mapped[list[Opportunity]] = relationship(back_populates="company", cascade="all, delete-orphan")
    learning_programs: Mapped[list[IndustryLearningProgram]] = relationship(back_populates="company", cascade="all, delete-orphan")


class AcademicianProfile(TimestampMixin, Base):
    __tablename__ = "academician_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    institution_profile_id: Mapped[int | None] = mapped_column(ForeignKey("institution_profiles.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="Academician")
    institution: Mapped[str] = mapped_column(String(255), default="")
    department: Mapped[str] = mapped_column(String(120), default="")
    designation: Mapped[str] = mapped_column(String(120), default="")
    expertise: Mapped[list[str]] = mapped_column(JSON, default=list)
    interests: Mapped[list[str]] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="academician_profile")
    institution_profile: Mapped[InstitutionProfile | None] = relationship(back_populates="academicians")
    applications: Mapped[list[AcademicianOpportunityApplication]] = relationship(back_populates="academician", cascade="all, delete-orphan")


class Opportunity(TimestampMixin, Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_profile_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id"), index=True)
    opportunity_type: Mapped[str] = mapped_column(String(32), default="INTERNSHIP")
    title: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    seats: Mapped[int] = mapped_column(Integer, default=1)
    stipend: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str] = mapped_column(String(120), default="")
    work_mode: Mapped[str] = mapped_column(String(32), default="ONSITE")
    min_cgpa: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True)
    moderation_status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    duration: Mapped[str] = mapped_column(String(80), default="")
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    reservation_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    reservation_policy_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped[CompanyProfile] = relationship(back_populates="opportunities")
    applications: Mapped[list[Application]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")
    matches: Mapped[list[MatchResult]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")
    allocations: Mapped[list[Allocation]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")


class LSRWAssessment(TimestampMixin, Base):
    __tablename__ = "lsrw_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    listening: Mapped[float] = mapped_column(Float)
    speaking: Mapped[float] = mapped_column(Float)
    reading: Mapped[float] = mapped_column(Float)
    writing: Mapped[float] = mapped_column(Float)
    overall: Mapped[float] = mapped_column(Float)
    details: Mapped[dict] = mapped_column(JSON, default=dict)

    student: Mapped[StudentProfile] = relationship(back_populates="lsrw_assessments")


class LearningRecommendation(TimestampMixin, Base):
    __tablename__ = "learning_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    skill: Mapped[str] = mapped_column(String(120))
    reason: Mapped[str] = mapped_column(Text, default="")
    action: Mapped[str] = mapped_column(Text, default="")
    resource_url: Mapped[str] = mapped_column(String(500), default="")
    priority: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    student: Mapped[StudentProfile] = relationship(back_populates="learning_recommendations")


class Application(TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("student_profile_id", "opportunity_id", name="uq_application_student_opportunity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    preference_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="SUBMITTED")

    student: Mapped[StudentProfile] = relationship(back_populates="applications")
    opportunity: Mapped[Opportunity] = relationship(back_populates="applications")


class MatchResult(TimestampMixin, Base):
    __tablename__ = "match_results"
    __table_args__ = (UniqueConstraint("student_profile_id", "opportunity_id", name="uq_match_student_opportunity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    skill_score: Mapped[float] = mapped_column(Float)
    required_coverage: Mapped[float] = mapped_column(Float)
    communication_score: Mapped[float] = mapped_column(Float)
    project_score: Mapped[float] = mapped_column(Float)
    academic_score: Mapped[float] = mapped_column(Float)
    location_score: Mapped[float] = mapped_column(Float)
    preference_score: Mapped[float] = mapped_column(Float)
    portfolio_score: Mapped[float] = mapped_column(Float)
    total_score: Mapped[float] = mapped_column(Float, index=True)
    algorithm_version: Mapped[str] = mapped_column(String(40), default="match-v2")
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)

    student: Mapped[StudentProfile] = relationship(back_populates="matches")
    opportunity: Mapped[Opportunity] = relationship(back_populates="matches")


class Allocation(TimestampMixin, Base):
    __tablename__ = "allocations"
    __table_args__ = (UniqueConstraint("opportunity_id", "student_profile_id", name="uq_allocation_opportunity_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    round: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="OFFERED", index=True)
    category_slot: Mapped[str] = mapped_column(String(32), default="OPEN")
    algorithm_version: Mapped[str] = mapped_column(String(40), default="allocation-v2")
    policy_version: Mapped[str] = mapped_column(String(40), default="policy-v1")
    decision_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped[StudentProfile] = relationship(back_populates="allocations")
    opportunity: Mapped[Opportunity] = relationship(back_populates="allocations")
    feedback: Mapped[CompanyFeedback | None] = relationship(back_populates="allocation", cascade="all, delete-orphan")


class CompanyFeedback(TimestampMixin, Base):
    __tablename__ = "company_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    allocation_id: Mapped[int] = mapped_column(ForeignKey("allocations.id"), unique=True)
    rating: Mapped[int] = mapped_column(Integer, default=0)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list)
    improvement_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    comments: Mapped[str] = mapped_column(Text, default="")
    recommend_for_placement: Mapped[bool] = mapped_column(Boolean, default=False)

    allocation: Mapped[Allocation] = relationship(back_populates="feedback")


class DigitalBadge(TimestampMixin, Base):
    __tablename__ = "digital_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    issuer: Mapped[str] = mapped_column(String(255))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="SELF_REPORTED", index=True)
    verification_notes: Mapped[str] = mapped_column(Text, default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    credential_url: Mapped[str] = mapped_column(String(500), default="")
    evidence_url: Mapped[str] = mapped_column(String(500), default="")
    credential_id: Mapped[str] = mapped_column(String(120), default="")
    standards: Mapped[dict] = mapped_column(JSON, default=dict)

    student: Mapped[StudentProfile] = relationship(back_populates="badges")


class IndustryLearningProgram(TimestampMixin, Base):
    __tablename__ = "industry_learning_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_profile_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    provider: Mapped[str] = mapped_column(String(255), default="Industry")
    duration: Mapped[str] = mapped_column(String(80), default="")
    resource_url: Mapped[str] = mapped_column(String(500), default="")
    badge_title: Mapped[str] = mapped_column(String(255), default="")

    company: Mapped[CompanyProfile] = relationship(back_populates="learning_programs")


class AcademicianOpportunity(TimestampMixin, Base):
    __tablename__ = "academician_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_profile_id: Mapped[int | None] = mapped_column(ForeignKey("institution_profiles.id"), nullable=True, index=True)
    opportunity_type: Mapped[str] = mapped_column(String(48))
    title: Mapped[str] = mapped_column(String(255))
    host_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    required_expertise: Mapped[list[str]] = mapped_column(JSON, default=list)
    location: Mapped[str] = mapped_column(String(120), default="")
    mode: Mapped[str] = mapped_column(String(32), default="HYBRID")
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")

    applications: Mapped[list[AcademicianOpportunityApplication]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")


class AcademicianOpportunityApplication(TimestampMixin, Base):
    __tablename__ = "academician_opportunity_applications"
    __table_args__ = (UniqueConstraint("academician_profile_id", "opportunity_id", name="uq_academic_application"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    academician_profile_id: Mapped[int] = mapped_column(ForeignKey("academician_profiles.id"), index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("academician_opportunities.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="APPLIED")
    match_score: Mapped[float] = mapped_column(Float, default=0)

    academician: Mapped[AcademicianProfile] = relationship(back_populates="applications")
    opportunity: Mapped[AcademicianOpportunity] = relationship(back_populates="applications")


class CurriculumInsightRun(TimestampMixin, Base):
    __tablename__ = "curriculum_insight_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_profile_id: Mapped[int | None] = mapped_column(ForeignKey("institution_profiles.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED")
    algorithm_version: Mapped[str] = mapped_column(String(40), default="curriculum-v2")
    source_summary: Mapped[dict] = mapped_column(JSON, default=dict)


class CurriculumInsight(TimestampMixin, Base):
    __tablename__ = "curriculum_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("curriculum_insight_runs.id"), nullable=True, index=True)
    institution_profile_id: Mapped[int | None] = mapped_column(ForeignKey("institution_profiles.id"), nullable=True, index=True)
    department: Mapped[str] = mapped_column(String(120), index=True)
    skill: Mapped[str] = mapped_column(String(120), index=True)
    gap_percent: Mapped[float] = mapped_column(Float)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    recommendation: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(120), default="Hiring outcomes + skill gaps")


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    student_profile_id: Mapped[int | None] = mapped_column(ForeignKey("student_profiles.id"), nullable=True, index=True)
    company_profile_id: Mapped[int | None] = mapped_column(ForeignKey("company_profiles.id"), nullable=True, index=True)
    institution_profile_id: Mapped[int | None] = mapped_column(ForeignKey("institution_profiles.id"), nullable=True, index=True)
    agent_name: Mapped[str] = mapped_column(String(120), index=True)
    responsibility: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED")
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)
    output_data: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditEvent(TimestampMixin, Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    actor_role: Mapped[str] = mapped_column(String(32), default="SYSTEM")
    institution_profile_id: Mapped[int | None] = mapped_column(ForeignKey("institution_profiles.id"), nullable=True, index=True)
    company_profile_id: Mapped[int | None] = mapped_column(ForeignKey("company_profiles.id"), nullable=True, index=True)
    student_profile_id: Mapped[int | None] = mapped_column(ForeignKey("student_profiles.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(80), default="")
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class PlatformPolicy(TimestampMixin, Base):
    __tablename__ = "platform_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    policy_version: Mapped[str] = mapped_column(String(40), default="policy-v1")
    reservation_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    allow_reserved_seat_conversion: Mapped[bool] = mapped_column(Boolean, default=True)
    minimum_profile_completion: Mapped[int] = mapped_column(Integer, default=55)
    minimum_required_skill_coverage: Mapped[float] = mapped_column(Float, default=40.0)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class EmailActionToken(TimestampMixin, Base):
    __tablename__ = "email_action_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(32), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RefreshSession(TimestampMixin, Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), default="")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
