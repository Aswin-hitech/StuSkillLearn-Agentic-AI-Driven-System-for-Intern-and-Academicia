from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

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
    CurriculumInsight,
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
from app.integrations import mirror_audit_event
from app.agent_graph import invoke_agent_graph


AGENTS = [
    ("Eligibility & Profile Agent", "Validates profile readiness and canonical student facts."),
    ("Skill & Communication Agent", "Maps skill gaps, LSRW readiness and learning actions."),
    ("Portfolio & Preference Agent", "Maintains verified portfolio signals and student preferences."),
    ("Matching & Allocation Agent", "Runs explainable matching, rank lists, seat allocation and tie-breaking."),
    ("Academic Engagement Agent", "Turns hiring outcomes into curriculum insights and academician opportunities."),
    ("Monitoring & Reallocation Agent", "Tracks offers, feedback, vacancies and continuous reallocation."),
]


def audit(db: Session, *, user: User | None, event_type: str, entity_type: str = "", entity_id: int | None = None, details: dict | None = None) -> None:
    payload = {
        "actor_role": user.role if user else "SYSTEM",
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.add(
        AuditEvent(
            actor_user_id=user.id if user else None,
            actor_role=payload["actor_role"],
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
    )
    # The relational database is authoritative. When MONGODB_URI is configured,
    # the same event is mirrored best-effort for document analytics/search.
    mirror_audit_event(payload)


def normalize_skill(value: str) -> str:
    aliases = {
        "postgre sql": "postgresql",
        "postgres": "postgresql",
        "rest api": "rest apis",
        "restful api": "rest apis",
        "ml": "machine learning",
        "dl": "deep learning",
        "js": "javascript",
        "ts": "typescript",
        "gen ai": "generative ai",
        "genai": "generative ai",
    }
    skill = re.sub(r"\s+", " ", value.strip().lower())
    return aliases.get(skill, skill)


def clean_skills(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = normalize_skill(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def human_skill(value: str) -> str:
    special = {"sql": "SQL", "api": "API", "apis": "APIs", "ai": "AI", "ml": "ML", "aws": "AWS", "ui": "UI", "ux": "UX"}
    return " ".join(special.get(part, part.capitalize()) for part in value.split())


def profile_completion(student: StudentProfile) -> int:
    signals = [
        bool(student.name), bool(student.college), bool(student.degree), bool(student.department),
        student.current_year > 0, student.cgpa > 0, bool(student.city), bool(student.skills),
        bool(student.projects), bool(student.preferences), bool(student.resume_text),
    ]
    return round(sum(signals) / len(signals) * 100)


def current_lsrw(db: Session, student_id: int) -> LSRWAssessment | None:
    return db.scalar(
        select(LSRWAssessment)
        .where(LSRWAssessment.student_profile_id == student_id)
        .order_by(LSRWAssessment.created_at.desc())
    )


def text_quality_score(text: str, target_words: int) -> float:
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text or "")
    if not words:
        return 30.0
    length_score = min(100, len(words) / max(1, target_words) * 100)
    diversity = len({w.lower() for w in words}) / max(1, len(words)) * 100
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    avg_sentence = len(words) / sentences
    structure = 100 - min(60, abs(avg_sentence - 16) * 3)
    return round(max(30, min(100, 0.45 * length_score + 0.35 * diversity + 0.20 * structure)), 1)


def assess_lsrw(
    db: Session,
    student: StudentProfile,
    *,
    listening_correct: int,
    listening_total: int,
    reading_correct: int,
    reading_total: int,
    speaking_text: str,
    writing_text: str,
    user: User,
) -> LSRWAssessment:
    listening = round(100 * listening_correct / max(1, listening_total), 1)
    reading = round(100 * reading_correct / max(1, reading_total), 1)
    speaking = text_quality_score(speaking_text, 80)
    writing = text_quality_score(writing_text, 130)
    overall = round((listening + speaking + reading + writing) / 4, 1)
    assessment = LSRWAssessment(
        student_profile_id=student.id,
        listening=listening,
        speaking=speaking,
        reading=reading,
        writing=writing,
        overall=overall,
        details={
            "speaking_feedback": "Focus on concise structure, role-specific vocabulary and evidence from projects." if speaking < 80 else "Strong structured speaking response.",
            "writing_feedback": "Use clearer topic sentences and quantify project outcomes." if writing < 80 else "Strong written clarity and vocabulary.",
            "method": "objective quiz scoring + deterministic rubric; NVIDIA NIM can enrich rubric feedback when configured",
        },
    )
    db.add(assessment)
    audit(db, user=user, event_type="LSRW_ASSESSED", entity_type="student", entity_id=student.id, details={"overall": overall})
    db.commit()
    db.refresh(assessment)
    return assessment


def parse_resume_into_profile(student: StudentProfile, resume_text: str) -> dict[str, Any]:
    known_skills = [
        "python", "java", "c++", "javascript", "typescript", "react", "fastapi", "django",
        "sql", "postgresql", "mongodb", "docker", "kubernetes", "aws", "azure", "machine learning",
        "deep learning", "pytorch", "tensorflow", "opencv", "nlp", "generative ai", "rag", "embeddings",
        "rest apis", "git", "linux", "power bi", "excel", "communication",
    ]
    lowered = resume_text.lower()
    extracted = [skill for skill in known_skills if skill in lowered]
    if extracted:
        student.skills = clean_skills(list(student.skills) + extracted)
    student.resume_text = resume_text[:30000]
    student.profile_completion = profile_completion(student)
    return {"extracted_skills": [human_skill(s) for s in extracted], "skill_count": len(student.skills)}


def project_overlap_score(student: StudentProfile, opportunity: Opportunity) -> float:
    required = set(clean_skills(opportunity.required_skills + opportunity.preferred_skills))
    if not required:
        return 100.0
    techs: set[str] = set()
    for project in student.projects or []:
        for tech in project.get("technologies", []):
            techs.add(normalize_skill(str(tech)))
        for token in re.findall(r"[A-Za-z+#.]+", str(project.get("description", ""))):
            techs.add(normalize_skill(token))
    overlap = required & techs
    return round(min(100, 40 + (len(overlap) / max(1, len(required))) * 60) if student.projects else 35, 1)


def preference_signal(student: StudentProfile, opportunity: Opportunity) -> tuple[float, int | None]:
    prefs = student.preferences or {}
    ranked_opps = [int(x) for x in prefs.get("ranked_opportunity_ids", []) if str(x).isdigit()]
    ranked_companies = [int(x) for x in prefs.get("ranked_company_ids", []) if str(x).isdigit()]
    if opportunity.id in ranked_opps:
        rank = ranked_opps.index(opportunity.id) + 1
        return max(60.0, 105.0 - rank * 10), rank
    if opportunity.company_profile_id in ranked_companies:
        rank = ranked_companies.index(opportunity.company_profile_id) + 1
        return max(55.0, 100.0 - rank * 10), rank
    preferred_domains = {normalize_skill(x) for x in prefs.get("preferred_domains", [])}
    if normalize_skill(opportunity.domain) in preferred_domains:
        return 75.0, None
    return (55.0 if student.general_pool_opt_in else 35.0), None


def match_tier(score: float, eligible: bool) -> str:
    """Human-readable, auditable tier used by the proposal's tiered ranking view."""
    if not eligible:
        return "NOT_ELIGIBLE"
    if score >= 85:
        return "TIER_1"
    if score >= 70:
        return "TIER_2"
    if score >= 55:
        return "TIER_3"
    return "TIER_4"


def compute_match(student: StudentProfile, opportunity: Opportunity, lsrw: LSRWAssessment | None) -> dict[str, Any]:
    student_skills = set(clean_skills(student.skills or []))
    required = set(clean_skills(opportunity.required_skills or []))
    preferred = set(clean_skills(opportunity.preferred_skills or []))
    matched_required = sorted(student_skills & required)
    missing_required = sorted(required - student_skills)
    matched_preferred = sorted(student_skills & preferred)

    required_coverage = 100.0 if not required else 100 * len(matched_required) / len(required)
    preferred_coverage = 100.0 if not preferred else 100 * len(matched_preferred) / len(preferred)
    skill_score = round(required_coverage * 0.8 + preferred_coverage * 0.2, 1)
    communication_score = round(lsrw.overall if lsrw else 60.0, 1)
    project_score = project_overlap_score(student, opportunity)
    academic_score = 100.0 if opportunity.min_cgpa <= 0 or student.cgpa >= opportunity.min_cgpa else max(0.0, student.cgpa / max(0.1, opportunity.min_cgpa) * 100)

    prefs = student.preferences or {}
    preferred_locations = {x.lower() for x in prefs.get("preferred_locations", [])}
    work_modes = {x.upper() for x in prefs.get("work_modes", [])}
    location_score = 100.0 if opportunity.work_mode.upper() == "REMOTE" or opportunity.location.lower() in preferred_locations else (85.0 if opportunity.work_mode.upper() in work_modes else 60.0)
    preference_score, preference_rank = preference_signal(student, opportunity)
    preference_allowed = student.general_pool_opt_in or preference_score > 55.0
    portfolio_score = min(100.0, 65 + 8 * len(student.projects or []) + 5 * len(student.certifications or []))

    total = round(
        0.40 * skill_score
        + 0.20 * required_coverage
        + 0.10 * communication_score
        + 0.10 * project_score
        + 0.05 * academic_score
        + 0.05 * location_score
        + 0.05 * preference_score
        + 0.05 * portfolio_score,
        1,
    )
    eligible = student.cgpa >= opportunity.min_cgpa and required_coverage >= 40 and lsrw is not None and preference_allowed
    tier = match_tier(total, eligible)
    explanation = {
        "eligible": eligible,
        "tier": tier,
        "tier_definition": {"TIER_1": "85-100", "TIER_2": "70-84.9", "TIER_3": "55-69.9", "TIER_4": "below 55"},
        "matched_required": [human_skill(x) for x in matched_required],
        "missing_required": [human_skill(x) for x in missing_required],
        "matched_preferred": [human_skill(x) for x in matched_preferred],
        "preference_rank": preference_rank,
        "summary": f"{required_coverage:.0f}% required-skill coverage, {communication_score:.0f}% communication readiness and {preference_score:.0f}% preference alignment.",
        "lsrw_completed": lsrw is not None,
        "allocation_prerequisites": {"cgpa": student.cgpa >= opportunity.min_cgpa, "required_skill_floor": required_coverage >= 40, "lsrw": lsrw is not None, "preference_or_general_pool": preference_allowed},
        "tie_break_order": ["match score", "student preference", "application timestamp", "stable application id"],
    }
    return {
        "skill_score": skill_score,
        "required_coverage": round(required_coverage, 1),
        "communication_score": communication_score,
        "project_score": project_score,
        "academic_score": round(academic_score, 1),
        "location_score": location_score,
        "preference_score": preference_score,
        "portfolio_score": portfolio_score,
        "total_score": total,
        "explanation": explanation,
    }


def upsert_match(db: Session, student: StudentProfile, opportunity: Opportunity) -> MatchResult:
    lsrw = current_lsrw(db, student.id)
    values = compute_match(student, opportunity, lsrw)
    # Successful internship outcomes feed into the next placement cycle. The
    # continuity signal is deliberately small and fully exposed in explanation.
    if opportunity.opportunity_type.upper() == "PLACEMENT":
        feedbacks = db.scalars(
            select(CompanyFeedback)
            .join(Allocation, CompanyFeedback.allocation_id == Allocation.id)
            .where(Allocation.student_profile_id == student.id, CompanyFeedback.recommend_for_placement.is_(True))
        ).all()
        if feedbacks:
            average_rating = sum(x.rating for x in feedbacks) / len(feedbacks)
            continuity_bonus = round(min(5.0, average_rating), 1)
            values["total_score"] = round(min(100.0, values["total_score"] + continuity_bonus), 1)
            values["explanation"]["placement_continuity"] = {
                "successful_internship_feedback": len(feedbacks),
                "average_rating": round(average_rating, 1),
                "bonus": continuity_bonus,
                "reason": "Verified company feedback recommended this student for placement continuity.",
            }
    match = db.scalar(
        select(MatchResult).where(
            MatchResult.student_profile_id == student.id,
            MatchResult.opportunity_id == opportunity.id,
        )
    )
    if not match:
        match = MatchResult(student_profile_id=student.id, opportunity_id=opportunity.id, **values)
        db.add(match)
    else:
        for key, value in values.items():
            setattr(match, key, value)
    return match


def refresh_student_matches(db: Session, student: StudentProfile) -> list[MatchResult]:
    opportunities = db.scalars(select(Opportunity).where(Opportunity.status == "OPEN")).all()
    matches = [upsert_match(db, student, opportunity) for opportunity in opportunities]
    db.flush()
    return sorted(matches, key=lambda m: (-m.total_score, m.opportunity_id))


def skill_gap_report(db: Session, student: StudentProfile) -> dict[str, Any]:
    matches = refresh_student_matches(db, student)
    top = matches[:5]
    missing: Counter[str] = Counter()
    for match in top:
        for skill in match.explanation.get("missing_required", []):
            missing[skill] += 1
    strongest = [human_skill(x) for x in clean_skills(student.skills)[:8]]
    gaps = [{"skill": skill, "demand_count": count, "priority": "HIGH" if count >= 2 else "MEDIUM"} for skill, count in missing.most_common(8)]
    return {
        "strongest_skills": strongest,
        "priority_gaps": gaps,
        "top_role_matches": [round(m.total_score, 1) for m in top],
        "readiness": round(sum(m.total_score for m in top) / max(1, len(top)), 1) if top else 0,
    }


def refresh_learning_recommendations(db: Session, student: StudentProfile, *, force_ai: bool = False) -> list[LearningRecommendation]:
    report = skill_gap_report(db, student)
    existing = {
        normalize_skill(item.skill): item
        for item in db.scalars(select(LearningRecommendation).where(LearningRecommendation.student_profile_id == student.id)).all()
    }
    recommendations: list[LearningRecommendation] = []
    active_skills: set[str] = set()
    for index, gap in enumerate(report["priority_gaps"][:6]):
        skill = gap["skill"]
        normalized = normalize_skill(skill)
        active_skills.add(normalized)
        fallback_action = f"Complete a focused hands-on module for {skill}, build one mini-project, then add evidence to your digital portfolio."
        rec = existing.get(normalized)
        if rec and not force_ai:
            action = rec.action
        else:
            action = nim_client.chat(
                "You are StuSkillLink's learning-path advisor. Give one short, practical action for a student skill gap. Do not invent certifications.",
                f"Student needs to improve: {skill}. Demand signal: {gap['demand_count']} top matched roles.",
                fallback=fallback_action,
            )
        if rec:
            rec.skill = skill
            rec.reason = f"Required by {gap['demand_count']} of the student's strongest current opportunity matches."
            rec.action = action
            rec.resource_url = "https://swayam.gov.in/" if index % 2 == 0 else "https://nptel.ac.in/"
            rec.priority = gap["priority"]
        else:
            rec = LearningRecommendation(
                student_profile_id=student.id,
                skill=skill,
                reason=f"Required by {gap['demand_count']} of the student's strongest current opportunity matches.",
                action=action,
                resource_url="https://swayam.gov.in/" if index % 2 == 0 else "https://nptel.ac.in/",
                priority=gap["priority"],
                completed=False,
            )
            db.add(rec)
        recommendations.append(rec)
    for normalized, obsolete in existing.items():
        if normalized not in active_skills:
            db.delete(obsolete)
    db.flush()
    return recommendations


def ensure_application(db: Session, student: StudentProfile, opportunity: Opportunity, preference_rank: int | None = None) -> Application:
    application = db.scalar(
        select(Application).where(
            Application.student_profile_id == student.id,
            Application.opportunity_id == opportunity.id,
        )
    )
    if application:
        if preference_rank is not None:
            application.preference_rank = preference_rank
        return application
    application = Application(
        student_profile_id=student.id,
        opportunity_id=opportunity.id,
        preference_rank=preference_rank,
        status="SUBMITTED",
    )
    db.add(application)
    return application


def rank_applicants(db: Session, opportunity: Opportunity) -> list[dict[str, Any]]:
    applications = db.scalars(
        select(Application)
        .where(Application.opportunity_id == opportunity.id, Application.status.in_(["SUBMITTED", "RANKING_ELIGIBLE"]))
        .order_by(Application.created_at.asc(), Application.id.asc())
    ).all()
    rows: list[dict[str, Any]] = []
    for application in applications:
        student = db.get(StudentProfile, application.student_profile_id)
        if not student:
            continue
        match = upsert_match(db, student, opportunity)
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


def active_allocations_for_opportunity(db: Session, opportunity_id: int) -> list[Allocation]:
    return db.scalars(
        select(Allocation).where(
            Allocation.opportunity_id == opportunity_id,
            Allocation.status.in_(["OFFERED", "ACCEPTED"]),
        )
    ).all()


def allocate_opportunity(db: Session, opportunity: Opportunity, actor: User | None = None) -> list[Allocation]:
    ranked = rank_applicants(db, opportunity)
    existing = active_allocations_for_opportunity(db, opportunity.id)
    existing_students = {a.student_profile_id for a in existing}
    remaining_total = max(0, opportunity.seats - len(existing))
    if remaining_total <= 0:
        return existing

    reservation = {str(k).upper(): int(v) for k, v in (opportunity.reservation_policy or {}).items() if int(v) > 0}
    active_by_category = Counter(a.category_slot for a in existing if a.category_slot != "OPEN")
    created: list[Allocation] = []

    def create_for(row: dict[str, Any], slot: str) -> Allocation:
        allocation = Allocation(
            opportunity_id=opportunity.id,
            student_profile_id=row["student"].id,
            rank=row["rank"],
            round=1,
            status="OFFERED",
            category_slot=slot,
            explanation={
                "match_score": row["match"].total_score,
                "rank": row["rank"],
                "slot": slot,
                "reason": "Selected from the deterministic company-wise rank list under the configured seat policy.",
            },
        )
        db.add(allocation)
        existing_students.add(row["student"].id)
        created.append(allocation)
        return allocation

    # Reserved category slots are configurable per opportunity; no statutory quota is hardcoded.
    for category, target in reservation.items():
        need = max(0, target - active_by_category[category])
        for row in ranked:
            if need <= 0 or remaining_total <= 0:
                break
            if row["student"].id in existing_students:
                continue
            if row["student"].reservation_category.upper() != category:
                continue
            if not row["match"].explanation.get("eligible", True):
                continue
            create_for(row, category)
            need -= 1
            remaining_total -= 1

    # Open seats are filled strictly by rank after reserved capacity is satisfied.
    for row in ranked:
        if remaining_total <= 0:
            break
        if row["student"].id in existing_students or not row["match"].explanation.get("eligible", True):
            continue
        create_for(row, "OPEN")
        remaining_total -= 1

    audit(
        db,
        user=actor,
        event_type="ALLOCATION_RUN",
        entity_type="opportunity",
        entity_id=opportunity.id,
        details={"created": len(created), "seat_capacity": opportunity.seats, "reservation_policy": reservation},
    )
    db.commit()
    return active_allocations_for_opportunity(db, opportunity.id)


def reallocate_after_rejection(db: Session, rejected: Allocation, actor: User | None = None) -> Allocation | None:
    opportunity = db.get(Opportunity, rejected.opportunity_id)
    if not opportunity:
        return None
    ranked = rank_applicants(db, opportunity)
    allocated_or_rejected = {
        a.student_profile_id
        for a in db.scalars(select(Allocation).where(Allocation.opportunity_id == opportunity.id)).all()
    }
    replacement_row = None
    for row in ranked:
        if row["student"].id in allocated_or_rejected:
            continue
        if rejected.category_slot != "OPEN" and row["student"].reservation_category.upper() != rejected.category_slot:
            continue
        if not row["match"].explanation.get("eligible", True):
            continue
        replacement_row = row
        break
    if replacement_row is None and rejected.category_slot != "OPEN":
        for row in ranked:
            if row["student"].id not in allocated_or_rejected and row["match"].explanation.get("eligible", True):
                replacement_row = row
                break
    if replacement_row is None:
        return None
    replacement = Allocation(
        opportunity_id=opportunity.id,
        student_profile_id=replacement_row["student"].id,
        rank=replacement_row["rank"],
        round=rejected.round + 1,
        status="OFFERED",
        category_slot=rejected.category_slot,
        explanation={
            "match_score": replacement_row["match"].total_score,
            "rank": replacement_row["rank"],
            "slot": rejected.category_slot,
            "reason": f"Automatically reallocated after allocation {rejected.id} was rejected.",
        },
    )
    db.add(replacement)
    audit(db, user=actor, event_type="AUTOMATIC_REALLOCATION", entity_type="allocation", entity_id=rejected.id, details={"replacement_student_id": replacement.student_profile_id})
    db.commit()
    db.refresh(replacement)
    return replacement


def respond_to_allocation(db: Session, allocation: Allocation, response: str, actor: User) -> Allocation:
    value = response.upper()
    if allocation.status != "OFFERED":
        raise HTTPException(status_code=409, detail="This offer has already been processed")
    if value not in {"ACCEPTED", "REJECTED"}:
        raise HTTPException(status_code=400, detail="Response must be ACCEPTED or REJECTED")
    allocation.status = value
    audit(db, user=actor, event_type=f"OFFER_{value}", entity_type="allocation", entity_id=allocation.id)
    db.commit()
    if value == "REJECTED":
        reallocate_after_rejection(db, allocation, actor)
    db.refresh(allocation)
    return allocation


def refresh_curriculum_insights(db: Session) -> list[CurriculumInsight]:
    students = db.scalars(select(StudentProfile)).all()
    opportunities = db.scalars(select(Opportunity).where(Opportunity.status == "OPEN")).all()
    demand = Counter()
    for opp in opportunities:
        demand.update(clean_skills(opp.required_skills))
    feedback_demand = Counter()
    for feedback in db.scalars(select(CompanyFeedback)).all():
        feedback_demand.update(clean_skills(feedback.improvement_skills))

    by_department: dict[str, list[StudentProfile]] = defaultdict(list)
    for student in students:
        by_department[student.department or "General"].append(student)

    db.execute(delete(CurriculumInsight))
    insights: list[CurriculumInsight] = []
    for department, group in by_department.items():
        for skill, demand_count in (demand + feedback_demand).most_common(12):
            if demand_count <= 0:
                continue
            have = sum(1 for student in group if skill in set(clean_skills(student.skills)))
            gap_percent = round((1 - have / max(1, len(group))) * 100, 1)
            if gap_percent < 15:
                continue
            rec = CurriculumInsight(
                department=department,
                skill=human_skill(skill),
                gap_percent=gap_percent,
                evidence_count=demand_count,
                recommendation=f"Add a practical {human_skill(skill)} module with industry-reviewed exercises and portfolio evidence.",
                source="Live opportunity requirements + company internship feedback",
            )
            db.add(rec)
            insights.append(rec)
    db.flush()
    return insights


def academician_match_score(profile: AcademicianProfile, opportunity: AcademicianOpportunity) -> float:
    expertise = set(clean_skills(profile.expertise))
    required = set(clean_skills(opportunity.required_expertise))
    if not required:
        return 75.0
    return round(40 + 60 * len(expertise & required) / len(required), 1)


def _agent_reasoning(name: str, responsibility: str, facts: dict[str, Any], preferred_provider: str | None = None) -> tuple[str, dict[str, Any]]:
    fallback = f"{name} completed its deterministic checks. Review the attached evidence before taking action."
    result = nim_client.generate(
        "You are one stage in StuSkillLink's audited agent workflow. Explain the supplied evidence in two concise sentences. "
        "Do not invent facts, change eligibility, rank candidates, or make allocation decisions.",
        f"Agent responsibility: {responsibility}\nVerified evidence: {json.dumps(facts, default=str)}",
        fallback=fallback,
        purpose=name,
        preferred_provider=preferred_provider,
    )
    return result.text, result.metadata()


def run_six_agent_cycle(db: Session, student: StudentProfile | None = None, actor: User | None = None) -> list[AgentRun]:
    """Run six isolated agent stages with honest per-stage status reporting.

    Every stage owns a concrete domain check. LLM output is advisory and carries
    provider provenance; deterministic facts remain the source of truth.
    """
    inputs = {"student_id": student.id if student else None, "actor_role": actor.role if actor else "SYSTEM"}

    def eligibility_stage() -> dict[str, Any]:
        if not student:
            return {"scope": "ecosystem", "ready": True}
        student.profile_completion = profile_completion(student)
        return {
            "profile_completion": student.profile_completion,
            "profile_ready": student.profile_completion >= 55,
            "cgpa": student.cgpa,
            "lsrw_completed": current_lsrw(db, student.id) is not None,
        }

    def skill_stage() -> dict[str, Any]:
        if not student:
            return {"scope": "ecosystem", "status": "no student-specific skill scan"}
        report = skill_gap_report(db, student)
        recommendations = refresh_learning_recommendations(db, student)
        return {
            "readiness": report["readiness"],
            "priority_gaps": report["priority_gaps"][:4],
            "learning_actions": len(recommendations),
        }

    def portfolio_stage() -> dict[str, Any]:
        if not student:
            return {"scope": "ecosystem", "status": "portfolio index available"}
        return {
            "projects": len(student.projects or []),
            "certifications": len(student.certifications or []),
            "verified_badges": sum(1 for badge in student.badges if badge.verified),
            "general_pool_opt_in": student.general_pool_opt_in,
            "preferences": student.preferences or {},
        }

    def matching_stage() -> dict[str, Any]:
        if not student:
            return {"scope": "ecosystem", "status": "company rank lists available", "decision_engine": "deterministic"}
        matches = refresh_student_matches(db, student)
        eligible = sum(1 for match in matches if match.explanation.get("eligible", False))
        return {
            "matches_generated": len(matches),
            "eligible_matches": eligible,
            "best_match_score": matches[0].total_score if matches else 0,
            "decision_engine": "deterministic",
        }

    def academic_stage() -> dict[str, Any]:
        insights = refresh_curriculum_insights(db)
        return {
            "curriculum_insights": len(insights),
            "academician_opportunities": db.scalar(select(func.count()).select_from(AcademicianOpportunity)) or 0,
        }

    def monitoring_stage() -> dict[str, Any]:
        counts = {
            status: db.scalar(select(func.count()).select_from(Allocation).where(Allocation.status == status)) or 0
            for status in ("OFFERED", "ACCEPTED", "REJECTED")
        }
        return {"allocation_status_counts": counts, "automatic_reallocation_on_rejection": True}

    handlers = [eligibility_stage, skill_stage, portfolio_stage, matching_stage, academic_stage, monitoring_stage]
    configured_providers = [
        provider["id"] for provider in nim_client.status()["providers"] if provider["configured"]
    ]
    from app.config import settings

    graph_state = invoke_agent_graph(
        stage_definitions=[
            (name, responsibility, handler)
            for (name, responsibility), handler in zip(AGENTS, handlers)
        ],
        reasoner=_agent_reasoning,
        configured_providers=configured_providers,
        student_id=student.id if student else None,
        actor_role=actor.role if actor else "SYSTEM",
        checkpoint_path=settings.langgraph_checkpoint_path,
    )
    inputs.update({"orchestration": "langgraph", "graph_run_id": graph_state["run_id"]})
    stage_rows = [graph_state["stage_results"][name] for name, _ in AGENTS]
    failures = int(graph_state.get("failed_stages") or 0)

    runs: list[AgentRun] = []
    for row in stage_rows:
        output = row["output"]
        status = row["status"]
        name = row["name"]
        responsibility = row["responsibility"]
        run = AgentRun(agent_name=name, responsibility=responsibility, status=status, input_data=inputs, output_data=output)
        db.add(run)
        runs.append(run)

    event_type = "SIX_AGENT_CYCLE_COMPLETED" if failures == 0 else "SIX_AGENT_CYCLE_PARTIAL_FAILURE"
    audit(
        db,
        user=actor,
        event_type=event_type,
        entity_type="student",
        entity_id=student.id if student else None,
        details={
            "failed_stages": failures,
            "live_llm_stages": sum(1 for run in runs if run.status == "COMPLETED"),
            "orchestration": "langgraph",
            "graph_run_id": graph_state["run_id"],
            "graph_status": graph_state["status"],
        },
    )
    db.commit()
    return runs


def student_dashboard(db: Session, student: StudentProfile) -> dict[str, Any]:
    student.profile_completion = profile_completion(student)
    matches = refresh_student_matches(db, student)
    lsrw = current_lsrw(db, student.id)
    recs = refresh_learning_recommendations(db, student)
    allocations = db.scalars(select(Allocation).where(Allocation.student_profile_id == student.id).order_by(Allocation.created_at.desc())).all()
    apps = db.scalars(select(Application).where(Application.student_profile_id == student.id)).all()
    db.commit()
    return {
        "profile": serialize_student(student),
        "readiness": round(sum(m.total_score for m in matches[:5]) / max(1, len(matches[:5])), 1) if matches else 0,
        "communication": serialize_lsrw(lsrw),
        "top_matches": [{**(serialize_match(m) or {}), "opportunity": serialize_opportunity(m.opportunity)} for m in matches[:5]],
        "learning": [serialize_learning(x) for x in recs[:5]],
        "applications": [serialize_application(db, a) for a in apps],
        "offers": [serialize_allocation(db, a) for a in allocations],
        "badges": [serialize_badge(x) for x in student.badges],
    }


def serialize_student(student: StudentProfile) -> dict[str, Any]:
    return {
        "id": student.id,
        "name": student.name,
        "college": student.college,
        "university": student.university,
        "degree": student.degree,
        "department": student.department,
        "current_year": student.current_year,
        "cgpa": student.cgpa,
        "city": student.city,
        "state": student.state,
        "reservation_category": student.reservation_category,
        "skills": student.skills,
        "projects": student.projects,
        "certifications": student.certifications,
        "preferences": student.preferences,
        "general_pool_opt_in": student.general_pool_opt_in,
        "profile_completion": student.profile_completion,
    }


def serialize_lsrw(item: LSRWAssessment | None) -> dict[str, Any] | None:
    if not item:
        return None
    return {"id": item.id, "listening": item.listening, "speaking": item.speaking, "reading": item.reading, "writing": item.writing, "overall": item.overall, "details": item.details}


def serialize_learning(item: LearningRecommendation) -> dict[str, Any]:
    return {"id": item.id, "skill": item.skill, "reason": item.reason, "action": item.action, "resource_url": item.resource_url, "priority": item.priority, "completed": item.completed}


def serialize_opportunity(item: Opportunity, match: MatchResult | None = None) -> dict[str, Any]:
    return {
        "id": item.id,
        "company_id": item.company_profile_id,
        "company_name": item.company.company_name if item.company else "",
        "opportunity_type": item.opportunity_type,
        "title": item.title,
        "domain": item.domain,
        "description": item.description,
        "required_skills": item.required_skills,
        "preferred_skills": item.preferred_skills,
        "seats": item.seats,
        "stipend": item.stipend,
        "location": item.location,
        "work_mode": item.work_mode,
        "min_cgpa": item.min_cgpa,
        "status": item.status,
        "duration": item.duration,
        "deadline": item.deadline,
        "reservation_policy": item.reservation_policy,
        "match": serialize_match(match) if match else None,
    }


def serialize_match(match: MatchResult | None) -> dict[str, Any] | None:
    if not match:
        return None
    return {
        "id": match.id,
        "opportunity_id": match.opportunity_id,
        "skill_score": match.skill_score,
        "required_coverage": match.required_coverage,
        "communication_score": match.communication_score,
        "project_score": match.project_score,
        "academic_score": match.academic_score,
        "location_score": match.location_score,
        "preference_score": match.preference_score,
        "portfolio_score": match.portfolio_score,
        "total_score": match.total_score,
        "explanation": match.explanation,
    }


def serialize_application(db: Session, item: Application) -> dict[str, Any]:
    opp = db.get(Opportunity, item.opportunity_id)
    return {"id": item.id, "opportunity_id": item.opportunity_id, "title": opp.title if opp else "", "company_name": opp.company.company_name if opp and opp.company else "", "status": item.status, "preference_rank": item.preference_rank}


def serialize_allocation(db: Session, item: Allocation) -> dict[str, Any]:
    opp = db.get(Opportunity, item.opportunity_id)
    student = db.get(StudentProfile, item.student_profile_id)
    return {
        "id": item.id,
        "opportunity_id": item.opportunity_id,
        "student_id": item.student_profile_id,
        "student_name": student.name if student else "",
        "title": opp.title if opp else "",
        "company_name": opp.company.company_name if opp and opp.company else "",
        "rank": item.rank,
        "round": item.round,
        "status": item.status,
        "category_slot": item.category_slot,
        "explanation": item.explanation,
    }


def serialize_badge(item: DigitalBadge) -> dict[str, Any]:
    return {"id": item.id, "title": item.title, "issuer": item.issuer, "verified": item.verified, "credential_url": item.credential_url, "verification_endpoint": f"/api/v1/sih/badges/{item.id}/verify"}


def company_dashboard(db: Session, company: CompanyProfile) -> dict[str, Any]:
    opportunities = db.scalars(select(Opportunity).where(Opportunity.company_profile_id == company.id).order_by(Opportunity.created_at.desc())).all()
    candidate_count = db.scalar(select(func.count()).select_from(Application).join(Opportunity).where(Opportunity.company_profile_id == company.id)) or 0
    active_allocations = db.scalar(select(func.count()).select_from(Allocation).join(Opportunity).where(Opportunity.company_profile_id == company.id, Allocation.status.in_(["OFFERED", "ACCEPTED"]))) or 0
    return {
        "profile": {"id": company.id, "company_name": company.company_name, "industry": company.industry, "website": company.website, "description": company.description, "recruiter_name": company.recruiter_name, "office_locations": company.office_locations, "verified": company.verified},
        "metrics": {"opportunities": len(opportunities), "applicants": candidate_count, "active_allocations": active_allocations, "learning_programs": len(company.learning_programs)},
        "opportunities": [serialize_opportunity(x) for x in opportunities],
        "learning_programs": [{"id": x.id, "title": x.title, "skills": x.skills, "provider": x.provider, "duration": x.duration, "resource_url": x.resource_url, "badge_title": x.badge_title} for x in company.learning_programs],
    }


def institution_dashboard(db: Session, institution: InstitutionProfile) -> dict[str, Any]:
    students = db.scalars(select(StudentProfile)).all()
    insights = refresh_curriculum_insights(db)
    accepted = db.scalar(select(func.count()).select_from(Allocation).where(Allocation.status == "ACCEPTED")) or 0
    total_allocations = db.scalar(select(func.count()).select_from(Allocation)) or 0
    lsrw_items = db.scalars(select(LSRWAssessment)).all()
    avg_lsrw = round(sum(x.overall for x in lsrw_items) / max(1, len(lsrw_items)), 1) if lsrw_items else 0
    ready = sum(1 for student in students if profile_completion(student) >= 70)
    skill_counts = Counter(skill for student in students for skill in clean_skills(student.skills))
    db.commit()
    return {
        "profile": {"institution_name": institution.institution_name, "city": institution.city, "state": institution.state, "departments": institution.departments},
        "metrics": {"students": len(students), "profile_ready": ready, "accepted_allocations": accepted, "placement_continuity": round(accepted / max(1, total_allocations) * 100, 1), "average_lsrw": avg_lsrw},
        "skill_supply": [{"skill": human_skill(k), "students": v} for k, v in skill_counts.most_common(12)],
        "curriculum_insights": [{"id": x.id, "department": x.department, "skill": x.skill, "gap_percent": x.gap_percent, "evidence_count": x.evidence_count, "recommendation": x.recommendation, "source": x.source} for x in sorted(insights, key=lambda x: -x.gap_percent)[:20]],
    }


def academician_dashboard(db: Session, profile: AcademicianProfile) -> dict[str, Any]:
    opportunities = db.scalars(select(AcademicianOpportunity).where(AcademicianOpportunity.status == "OPEN")).all()
    applications = db.scalars(select(AcademicianOpportunityApplication).where(AcademicianOpportunityApplication.academician_profile_id == profile.id)).all()
    applied_ids = {x.opportunity_id for x in applications}
    items = []
    for opp in opportunities:
        items.append({
            "id": opp.id, "opportunity_type": opp.opportunity_type, "title": opp.title, "host_name": opp.host_name,
            "description": opp.description, "required_expertise": opp.required_expertise, "location": opp.location,
            "mode": opp.mode, "deadline": opp.deadline, "match_score": academician_match_score(profile, opp),
            "applied": opp.id in applied_ids,
        })
    insights = db.scalars(select(CurriculumInsight).order_by(CurriculumInsight.gap_percent.desc()).limit(12)).all()
    return {
        "profile": {"id": profile.id, "name": profile.name, "institution": profile.institution, "department": profile.department, "designation": profile.designation, "expertise": profile.expertise, "interests": profile.interests},
        "opportunities": sorted(items, key=lambda x: -x["match_score"]),
        "curriculum_insights": [{"department": x.department, "skill": x.skill, "gap_percent": x.gap_percent, "recommendation": x.recommendation, "evidence_count": x.evidence_count} for x in insights],
    }
