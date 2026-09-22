from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AcademicianOpportunity,
    AcademicianProfile,
    CompanyProfile,
    DigitalBadge,
    IndustryLearningProgram,
    InstitutionProfile,
    LSRWAssessment,
    Opportunity,
    PlatformPolicy,
    StudentProfile,
    User,
)
from app.security import hash_password

DEMO_PASSWORD = "Demo@123"


def make_user(db: Session, email: str, role: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(
        email=email.lower(),
        password_hash=hash_password(DEMO_PASSWORD),
        role=role,
        email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _deadline(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc)


def seed_demo_data(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)):
        return

    # Control-plane account is seeded only when AUTO_SEED_DEMO is explicitly enabled.
    make_user(db, "admin@stuskilllink.demo", "ADMIN")

    institution_user = make_user(db, "institution@stuskilllink.demo", "INSTITUTION")
    institution = InstitutionProfile(
        user_id=institution_user.id,
        institution_name="Knowledge Institute of Technology",
        institution_code="KIT-DEMO-2026",
        city="Coimbatore",
        state="Tamil Nadu",
        departments=["Artificial Intelligence and Machine Learning", "Computer Science", "Information Technology"],
        verified=True,
        verification_status="VERIFIED",
        verified_at=datetime.now(timezone.utc),
    )
    db.add(institution)
    db.flush()

    db.add(
        PlatformPolicy(
            id=1,
            policy_version="policy-v2-demo",
            reservation_policy={"OBC": 1, "SC": 1},
            allow_reserved_seat_conversion=True,
            minimum_profile_completion=55,
            minimum_required_skill_coverage=40.0,
        )
    )

    student_user = make_user(db, "student@stuskilllink.demo", "STUDENT")
    student = StudentProfile(
        user_id=student_user.id,
        institution_profile_id=institution.id,
        name="Arjun Kumar",
        college=institution.institution_name,
        university="Anna University",
        degree="B.Tech",
        department="Artificial Intelligence and Machine Learning",
        current_year=4,
        cgpa=8.4,
        city="Coimbatore",
        state="Tamil Nadu",
        reservation_category="GENERAL",
        reservation_status="VERIFIED",
        reservation_source="Demo institution verification",
        reservation_verified_at=datetime.now(timezone.utc),
        skills=["python", "machine learning", "sql", "pandas", "scikit-learn", "git", "rest apis", "fastapi"],
        projects=[
            {"title": "Campus Skill Mapper", "description": "ML-driven skill mapping and role recommendation portal", "technologies": ["Python", "Machine Learning", "FastAPI"]},
            {"title": "Vision Attendance", "description": "Computer vision attendance prototype", "technologies": ["Python", "OpenCV"]},
        ],
        certifications=[{"name": "Python for Data Science", "provider": "NPTEL", "verified": True}],
        preferences={
            "preferred_domains": ["Artificial Intelligence", "Data Science", "Backend"],
            "preferred_locations": ["Coimbatore", "Chennai", "Bengaluru"],
            "work_modes": ["HYBRID", "REMOTE"],
            "ranked_opportunity_ids": [],
            "ranked_company_ids": [],
        },
        general_pool_opt_in=True,
        profile_completion=92,
        resume_text="Python machine learning SQL pandas scikit-learn FastAPI REST APIs OpenCV project experience communication",
    )
    db.add(student)
    db.flush()
    db.add(LSRWAssessment(student_profile_id=student.id, listening=82, speaking=74, reading=88, writing=80, overall=81, details={"method": "demo baseline"}))
    db.add_all([
        DigitalBadge(
            student_profile_id=student.id,
            title="Industry API Foundations",
            issuer="TechNova Labs",
            verified=True,
            verification_status="VERIFIED",
            credential_url="https://example.com/badge/api",
            credential_id="DEMO-API-001",
            standards={"type": "OpenBadges3-compatible", "demo": True},
        ),
        DigitalBadge(
            student_profile_id=student.id,
            title="Python Data Practice",
            issuer="NPTEL",
            verified=True,
            verification_status="VERIFIED",
            credential_url="https://nptel.ac.in/",
            credential_id="DEMO-NPTEL-001",
            standards={"type": "OpenBadges3-compatible", "demo": True},
        ),
    ])

    extra_students = [
        ("meera@stuskilllink.demo", "Meera Nair", 8.8, "OBC", ["python", "machine learning", "pytorch", "docker", "fastapi", "sql"], 84),
        ("rahul@stuskilllink.demo", "Rahul S", 8.1, "SC", ["python", "machine learning", "tensorflow", "sql", "communication"], 76),
        ("priya@stuskilllink.demo", "Priya K", 7.9, "GENERAL", ["python", "sql", "fastapi", "docker", "postgresql", "react"], 79),
    ]
    extras: list[StudentProfile] = []
    for email, name, cgpa, category, skills, lsrw in extra_students:
        user = make_user(db, email, "STUDENT")
        profile = StudentProfile(
            user_id=user.id,
            institution_profile_id=institution.id,
            name=name,
            college=institution.institution_name,
            university="Anna University",
            degree="B.Tech",
            department="Artificial Intelligence and Machine Learning",
            current_year=4,
            cgpa=cgpa,
            city="Chennai",
            state="Tamil Nadu",
            reservation_category=category,
            reservation_status="VERIFIED",
            reservation_source="Demo institution verification",
            reservation_verified_at=datetime.now(timezone.utc),
            skills=skills,
            projects=[{"title": f"{name.split()[0]} Capstone", "description": "Industry aligned capstone", "technologies": skills[:3]}],
            certifications=[],
            preferences={"preferred_domains": ["Artificial Intelligence"], "preferred_locations": ["Chennai", "Bengaluru"], "work_modes": ["HYBRID", "REMOTE"]},
            general_pool_opt_in=True,
            profile_completion=88,
        )
        db.add(profile)
        db.flush()
        db.add(LSRWAssessment(student_profile_id=profile.id, listening=lsrw, speaking=lsrw, reading=min(100, lsrw + 2), writing=max(0, lsrw - 2), overall=lsrw, details={"method": "demo baseline"}))
        extras.append(profile)

    company_user = make_user(db, "industry@stuskilllink.demo", "COMPANY")
    company = CompanyProfile(
        user_id=company_user.id,
        company_name="TechNova Labs",
        industry="AI & Product Engineering",
        website="https://example.com/technova",
        description="Industry partner offering structured internships, placements and industry-led learning.",
        recruiter_name="Vishnu Priya",
        office_locations=["Chennai", "Bengaluru"],
        verified=True,
        verification_status="VERIFIED",
        verified_at=datetime.now(timezone.utc),
    )
    db.add(company)
    db.flush()

    second_company_user = make_user(db, "dataworks@stuskilllink.demo", "COMPANY")
    second_company = CompanyProfile(
        user_id=second_company_user.id,
        company_name="DataWorks Systems",
        industry="Data Platforms",
        website="https://example.com/dataworks",
        description="Data engineering and analytics product company.",
        recruiter_name="Talent Team",
        office_locations=["Coimbatore", "Remote"],
        verified=True,
        verification_status="VERIFIED",
        verified_at=datetime.now(timezone.utc),
    )
    db.add(second_company)
    db.flush()

    opportunities = [
        Opportunity(
            company_profile_id=company.id,
            opportunity_type="INTERNSHIP",
            title="AI Engineer Intern",
            domain="Artificial Intelligence",
            description="Build applied ML services and production APIs with mentors.",
            required_skills=["Python", "Machine Learning", "FastAPI", "Docker"],
            preferred_skills=["PyTorch", "SQL", "REST APIs"],
            seats=2,
            stipend=18000,
            location="Chennai",
            work_mode="HYBRID",
            min_cgpa=7.0,
            status="OPEN",
            moderation_status="APPROVED",
            duration="12 weeks",
            deadline=_deadline(2026, 10, 15),
            reservation_policy={"OBC": 1},
            reservation_policy_approved=True,
            published_at=datetime.now(timezone.utc),
        ),
        Opportunity(
            company_profile_id=company.id,
            opportunity_type="PLACEMENT",
            title="Graduate Product Engineer",
            domain="Software Engineering",
            description="Graduate role for students who demonstrate strong product engineering readiness.",
            required_skills=["Python", "REST APIs", "SQL", "Git"],
            preferred_skills=["Docker", "React", "PostgreSQL"],
            seats=3,
            stipend=0,
            location="Bengaluru",
            work_mode="HYBRID",
            min_cgpa=7.5,
            status="OPEN",
            moderation_status="APPROVED",
            duration="Full-time",
            deadline=_deadline(2026, 11, 1),
            reservation_policy={},
            reservation_policy_approved=True,
            published_at=datetime.now(timezone.utc),
        ),
        Opportunity(
            company_profile_id=second_company.id,
            opportunity_type="INTERNSHIP",
            title="Data Platform Intern",
            domain="Data Science",
            description="Work on analytics pipelines and data quality automation.",
            required_skills=["Python", "SQL", "PostgreSQL"],
            preferred_skills=["Pandas", "Docker", "Power BI"],
            seats=2,
            stipend=15000,
            location="Coimbatore",
            work_mode="REMOTE",
            min_cgpa=6.5,
            status="OPEN",
            moderation_status="APPROVED",
            duration="8 weeks",
            deadline=_deadline(2026, 10, 20),
            reservation_policy={"SC": 1},
            reservation_policy_approved=True,
            published_at=datetime.now(timezone.utc),
        ),
    ]
    db.add_all(opportunities)
    db.flush()

    student.preferences = {
        **student.preferences,
        "ranked_opportunity_ids": [opportunities[0].id, opportunities[2].id, opportunities[1].id],
        "ranked_company_ids": [company.id, second_company.id],
    }
    for profile in extras:
        profile.preferences = {
            **(profile.preferences or {}),
            "ranked_opportunity_ids": [opportunities[0].id, opportunities[2].id],
            "ranked_company_ids": [company.id, second_company.id],
        }

    db.add_all([
        IndustryLearningProgram(company_profile_id=company.id, title="Production API Sprint", skills=["FastAPI", "REST APIs", "Docker"], provider="TechNova Academy", duration="2 weeks", resource_url="https://example.com/learn/api", badge_title="Industry API Foundations"),
        IndustryLearningProgram(company_profile_id=company.id, title="Applied PyTorch Lab", skills=["PyTorch", "Deep Learning"], provider="TechNova Academy", duration="3 weeks", resource_url="https://example.com/learn/pytorch", badge_title="Applied PyTorch"),
        IndustryLearningProgram(company_profile_id=second_company.id, title="PostgreSQL for Analytics", skills=["PostgreSQL", "SQL"], provider="DataWorks Learning", duration="10 hours", resource_url="https://example.com/learn/postgres", badge_title="Data SQL Ready"),
    ])

    academician_user = make_user(db, "academician@stuskilllink.demo", "ACADEMICIAN")
    academician = AcademicianProfile(
        user_id=academician_user.id,
        institution_profile_id=institution.id,
        name="Dr. Ananya Rao",
        institution=institution.institution_name,
        department="Artificial Intelligence and Machine Learning",
        designation="Associate Professor",
        expertise=["Machine Learning", "Python", "Data Science", "NLP"],
        interests=["FDP", "Research", "Industry Mentorship"],
    )
    db.add(academician)

    db.add_all([
        AcademicianOpportunity(institution_profile_id=institution.id, opportunity_type="FDP", title="Applied GenAI Faculty Development Program", host_name="TechNova Labs", description="Five-day industry-led FDP on production GenAI systems.", required_expertise=["Machine Learning", "NLP"], location="Chennai", mode="HYBRID", deadline=_deadline(2026, 10, 5)),
        AcademicianOpportunity(institution_profile_id=institution.id, opportunity_type="RESEARCH", title="Responsible AI Joint Research Call", host_name="DataWorks Systems", description="Joint industry-academia research on explainable ranking and model governance.", required_expertise=["Machine Learning", "Data Science"], location="Remote", mode="REMOTE", deadline=_deadline(2026, 10, 18)),
        AcademicianOpportunity(institution_profile_id=institution.id, opportunity_type="CONSULTANCY", title="Curriculum-to-Industry Skill Mapping Consultancy", host_name="TechNova Labs", description="Short consultancy to align course outcomes with live role requirements.", required_expertise=["Data Science", "Python"], location="Bengaluru", mode="HYBRID", deadline=_deadline(2026, 10, 25)),
    ])

    db.commit()

    # Complete the demo ranking/allocation state only after all IDs and tenant links exist.
    from app.services import (
        allocate_opportunity,
        ensure_application,
        refresh_curriculum_insights,
        refresh_learning_recommendations,
        refresh_student_matches,
    )

    all_students = [student] + extras
    for profile in all_students:
        for rank, opp in enumerate(opportunities, start=1):
            ensure_application(db, profile, opp, preference_rank=rank)
        refresh_student_matches(db, profile)
        refresh_learning_recommendations(db, profile)
    db.commit()
    allocate_opportunity(db, opportunities[0], actor=None)
    allocate_opportunity(db, opportunities[2], actor=None)
    refresh_curriculum_insights(db, institution.id)
    db.commit()
