from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import Opportunity


DEMO_PASSWORD = "Demo@123"


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_demo_data

    with SessionLocal() as db:
        seed_demo_data(db)


def login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def register(client: TestClient, role: str, email: str) -> tuple[dict, dict[str, str]]:
    response = client.post(
        f"/api/v1/auth/register/{role}",
        json={"email": email, "password": "SecurePass123"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body, {"Authorization": f"Bearer {body['access_token']}"}


def test_admin_is_control_plane_and_not_publicly_registerable():
    reset_db()
    with TestClient(app) as client:
        blocked = client.post(
            "/api/v1/auth/register/ADMIN",
            json={"email": "attacker@example.com", "password": "SecurePass123"},
        )
        assert blocked.status_code == 400

        student = login(client, "student@stuskilllink.demo")
        assert client.get("/api/v1/sih/admin/dashboard", headers=student).status_code == 403

        admin = login(client, "admin@stuskilllink.demo")
        dashboard = client.get("/api/v1/sih/admin/dashboard", headers=admin)
        assert dashboard.status_code == 200
        assert dashboard.json()["metrics"]["roles"]["ADMIN"] >= 1
        assert client.get("/api/v1/sih/admin/users", headers=admin).status_code == 200
        assert client.get("/api/v1/sih/admin/allocations", headers=admin).status_code == 200


def test_unverified_organizations_are_blocked_and_verified_tenants_are_isolated():
    reset_db()
    with TestClient(app) as client:
        _, pending_company = register(client, "COMPANY", "pending-company@example.com")
        create = client.post(
            "/api/v1/sih/company/opportunities",
            headers=pending_company,
            json={
                "opportunity_type": "INTERNSHIP",
                "title": "Unsafe Publish Attempt",
                "domain": "Software",
                "required_skills": ["Python"],
                "seats": 1,
            },
        )
        assert create.status_code == 403

        _, pending_institution = register(client, "INSTITUTION", "new-college@example.com")
        assert client.get("/api/v1/sih/institution/students", headers=pending_institution).status_code == 403

        admin = login(client, "admin@stuskilllink.demo")
        institutions = client.get("/api/v1/sih/admin/institutions", headers=admin).json()
        new_institution = next(x for x in institutions if x["institution_name"] == "New Institution")
        approved = client.patch(
            f"/api/v1/sih/admin/institutions/{new_institution['id']}/verification",
            headers=admin,
            json={"status": "VERIFIED", "notes": "Test tenant approved"},
        )
        assert approved.status_code == 200

        isolated = client.get("/api/v1/sih/institution/students", headers=pending_institution)
        assert isolated.status_code == 200
        assert isolated.json() == []


def test_lsrw_validation_and_protected_student_fields():
    reset_db()
    with TestClient(app) as client:
        student = login(client, "student@stuskilllink.demo")
        invalid = client.post(
            "/api/v1/sih/student/lsrw/assess",
            headers=student,
            json={
                "listening_correct": 100,
                "listening_total": 1,
                "reading_correct": 4,
                "reading_total": 5,
                "speaking_text": "This speaking answer is long enough to satisfy input validation.",
                "writing_text": "This writing answer is long enough to satisfy input validation for the assessment.",
            },
        )
        assert invalid.status_code == 422

        profile = client.get("/api/v1/sih/student/profile", headers=student).json()
        tamper = client.put(
            "/api/v1/sih/student/profile",
            headers=student,
            json={
                "name": profile["name"],
                "college": profile["college"],
                "university": profile["university"],
                "degree": profile["degree"],
                "department": profile["department"],
                "current_year": profile["current_year"],
                "cgpa": profile["cgpa"],
                "city": profile["city"],
                "state": profile["state"],
                "skills": profile["skills"],
                "projects": profile["projects"],
                "certifications": profile["certifications"],
                "reservation_category": "SC",
            },
        )
        assert tamper.status_code == 422
        unchanged = client.get("/api/v1/sih/student/profile", headers=student).json()
        assert unchanged["reservation_category"] == profile["reservation_category"]


def test_expired_opportunities_reject_applications_and_admin_cannot_reopen_them():
    reset_db()
    with SessionLocal() as db:
        opportunity = db.scalar(select(Opportunity).where(Opportunity.title == "AI Engineer Intern"))
        assert opportunity is not None
        opportunity.deadline = datetime.now(timezone.utc) - timedelta(days=1)
        opportunity_id = opportunity.id
        db.commit()

    with TestClient(app) as client:
        student = login(client, "student@stuskilllink.demo")
        apply = client.post(f"/api/v1/sih/student/opportunities/{opportunity_id}/apply", headers=student)
        assert apply.status_code == 409

        admin = login(client, "admin@stuskilllink.demo")
        reopen = client.patch(
            f"/api/v1/sih/admin/opportunities/{opportunity_id}/moderation",
            headers=admin,
            json={
                "moderation_status": "APPROVED",
                "status": "OPEN",
                "reservation_policy": {},
                "reservation_policy_approved": True,
            },
        )
        assert reopen.status_code == 409


def test_feedback_requires_completed_engagement_and_recruiter_view_hides_sensitive_category():
    reset_db()
    with TestClient(app) as client:
        company = login(client, "industry@stuskilllink.demo")
        dashboard = client.get("/api/v1/sih/company/dashboard", headers=company).json()
        opportunity = next(x for x in dashboard["opportunities"] if x["title"] == "AI Engineer Intern")

        rankings = client.get(f"/api/v1/sih/company/opportunities/{opportunity['id']}/rankings", headers=company)
        assert rankings.status_code == 200
        assert "reservation_category" not in json.dumps(rankings.json())
        assert "reservation_status" not in json.dumps(rankings.json())

        allocation = client.get("/api/v1/sih/company/allocations", headers=company).json()[0]
        premature = client.post(
            f"/api/v1/sih/company/allocations/{allocation['id']}/feedback",
            headers=company,
            json={
                "rating": 5,
                "strengths": ["Python"],
                "improvement_skills": [],
                "comments": "Too early",
                "recommend_for_placement": True,
            },
        )
        assert premature.status_code == 409


def test_admin_owns_badge_verification():
    reset_db()
    with TestClient(app) as client:
        student = login(client, "student@stuskilllink.demo")
        learning = client.get("/api/v1/sih/student/learning", headers=student).json()
        assert learning
        complete = client.post(f"/api/v1/sih/student/learning/{learning[0]['id']}/complete", headers=student)
        assert complete.status_code == 200

        admin = login(client, "admin@stuskilllink.demo")
        pending = client.get("/api/v1/sih/admin/badges?verification_status=PENDING_VERIFICATION", headers=admin)
        assert pending.status_code == 200 and pending.json()
        badge = pending.json()[0]
        verified = client.patch(
            f"/api/v1/sih/admin/badges/{badge['id']}/verification",
            headers=admin,
            json={"status": "VERIFIED", "notes": "Evidence checked"},
        )
        assert verified.status_code == 200
        assert verified.json()["verified"] is True


def test_cookie_session_logout_and_csrf_origin_boundary():
    reset_db()
    with TestClient(app) as client:
        evil = client.post(
            "/api/v1/auth/login",
            headers={"Origin": "https://evil.example"},
            json={"email": "student@stuskilllink.demo", "password": DEMO_PASSWORD},
        )
        assert evil.status_code == 403

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "student@stuskilllink.demo", "password": DEMO_PASSWORD},
        )
        assert login_response.status_code == 200
        assert "stuskilllink_access" in client.cookies
        assert "stuskilllink_refresh" in client.cookies

        me = client.get("/api/v1/auth/me")
        assert me.status_code == 200 and me.json()["role"] == "STUDENT"

        logout = client.post("/api/v1/auth/logout")
        assert logout.status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401


def test_admin_moderation_rejects_reservation_overbooking():
    reset_db()
    with TestClient(app) as client:
        admin = login(client, "admin@stuskilllink.demo")
        opportunities = client.get("/api/v1/sih/admin/opportunities", headers=admin).json()
        opportunity = next(x for x in opportunities if x["title"] == "AI Engineer Intern")
        invalid = client.patch(
            f"/api/v1/sih/admin/opportunities/{opportunity['id']}/moderation",
            headers=admin,
            json={
                "moderation_status": "APPROVED",
                "status": "OPEN",
                "reservation_policy": {"OBC": opportunity["seats"], "SC": 1},
                "reservation_policy_approved": True,
            },
        )
        assert invalid.status_code == 422


def test_production_settings_fail_closed_and_accept_hardened_configuration():
    from pydantic import ValidationError
    from app.config import Settings

    try:
        Settings(_env_file=None, environment="production", jwt_secret_key="stuskilllink-local-development-secret-change-me")
    except ValidationError as exc:
        message = str(exc)
        assert "Production DATABASE_URL must use PostgreSQL" in message
        assert "JWT_SECRET_KEY must be a unique 32+ character secret" in message
        assert "SECURE_COOKIES must be true in production" in message
    else:
        raise AssertionError("Unsafe production defaults must be rejected")

    try:
        Settings(
            _env_file=None,
            environment="production",
            debug=False,
            database_url="postgresql+psycopg://app:secret@db.example.internal/stuskilllink",
            redis_url="rediss://cache.example.internal:6380/0",
            jwt_secret_key="REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS",
            cors_origins="https://stuskill.example.com",
            allowed_hosts="stuskill.example.com",
            auto_seed_demo=False,
            auto_create_schema=False,
            require_email_verification=True,
            secure_cookies=True,
            public_app_url="https://stuskill.example.com",
            smtp_url="smtps://mailer:secret@mail.example.com:465",
        )
    except ValidationError as exc:
        assert "template placeholder" in str(exc)
    else:
        raise AssertionError("Template JWT secrets must be rejected in production")

    hardened = Settings(
        _env_file=None,
        environment="production",
        debug=False,
        database_url="postgresql+psycopg://app:secret@db.example.internal/stuskilllink",
        redis_url="rediss://cache.example.internal:6380/0",
        jwt_secret_key="a-production-only-secret-that-is-long-and-random-12345",
        cors_origins="https://stuskill.example.com",
        allowed_hosts="stuskill.example.com",
        auto_seed_demo=False,
        auto_create_schema=False,
        require_email_verification=True,
        secure_cookies=True,
        cookie_samesite="lax",
        public_app_url="https://stuskill.example.com",
        smtp_url="smtps://mailer:secret@mail.example.com:465",
    )
    assert hardened.is_production is True
    assert hardened.cors_list == ["https://stuskill.example.com"]


def test_admin_cli_bootstrap_is_idempotent_and_refuses_role_escalation():
    from app.cli import create_admin
    from app.models import User

    reset_db()
    first = create_admin("ops-admin@example.com", "StrongAdminPass123")
    assert first.role == "ADMIN" and first.email_verified and first.is_active
    first_id = first.id

    second = create_admin("ops-admin@example.com", "NewStrongAdmin456")
    assert second.id == first_id

    try:
        create_admin("student@stuskilllink.demo", "StrongAdminPass123")
    except RuntimeError as exc:
        assert "non-admin" in str(exc)
    else:
        raise AssertionError("CLI must never promote an existing non-admin account")


def test_login_rate_limit_counts_failures_but_success_resets_bucket():
    reset_db()
    with TestClient(app) as client:
        registered, _ = register(client, "STUDENT", "rate-limit@example.com")
        assert registered["user"]["email"] == "rate-limit@example.com"

        # Successful sign-ins must not consume the failed-login budget.
        for _ in range(10):
            ok = client.post(
                "/api/v1/auth/login",
                json={"email": "rate-limit@example.com", "password": "SecurePass123"},
            )
            assert ok.status_code == 200, ok.text

        for _ in range(8):
            bad = client.post(
                "/api/v1/auth/login",
                json={"email": "rate-limit@example.com", "password": "WrongPass999"},
            )
            assert bad.status_code == 401, bad.text

        blocked = client.post(
            "/api/v1/auth/login",
            json={"email": "rate-limit@example.com", "password": "WrongPass999"},
        )
        assert blocked.status_code == 429, blocked.text


def test_reserved_capacity_does_not_silently_convert_when_policy_disallows_it():
    from app.models import CompanyProfile, PlatformPolicy, StudentProfile
    from app.services import allocate_opportunity, ensure_application, refresh_student_matches

    reset_db()
    with SessionLocal() as db:
        company = db.scalar(select(CompanyProfile).where(CompanyProfile.company_name == "TechNova Labs"))
        assert company is not None
        policy = db.get(PlatformPolicy, 1)
        assert policy is not None
        policy.allow_reserved_seat_conversion = False

        opportunity = Opportunity(
            company_profile_id=company.id,
            opportunity_type="INTERNSHIP",
            title="No Silent Conversion Role",
            domain="Software",
            description="Policy integrity test",
            required_skills=["Python"],
            preferred_skills=[],
            seats=2,
            stipend=0,
            location="Remote",
            work_mode="REMOTE",
            min_cgpa=0,
            status="OPEN",
            moderation_status="APPROVED",
            duration="4 weeks",
            deadline=datetime.now(timezone.utc) + timedelta(days=30),
            reservation_policy={"EWS": 1},  # Seed data has no verified EWS candidate.
            reservation_policy_approved=True,
            published_at=datetime.now(timezone.utc),
        )
        db.add(opportunity)
        db.flush()
        students = db.scalars(select(StudentProfile)).all()
        for index, student in enumerate(students, start=1):
            ensure_application(db, student, opportunity, preference_rank=index)
            refresh_student_matches(db, student)
        db.commit()

        allocations = allocate_opportunity(db, opportunity)
        active = [row for row in allocations if row.status in {"OFFERED", "ACCEPTED", "IN_PROGRESS", "COMPLETED"}]
        assert len(active) == 1
        assert active[0].category_slot == "OPEN"


def test_reserved_rejection_stays_vacant_without_same_category_replacement_when_conversion_disabled():
    from app.models import Allocation, CompanyProfile, PlatformPolicy, StudentProfile, User
    from app.services import allocate_opportunity, ensure_application, refresh_student_matches, respond_to_allocation

    reset_db()
    with SessionLocal() as db:
        company = db.scalar(select(CompanyProfile).where(CompanyProfile.company_name == "TechNova Labs"))
        assert company is not None
        policy = db.get(PlatformPolicy, 1)
        assert policy is not None
        policy.allow_reserved_seat_conversion = False

        opportunity = Opportunity(
            company_profile_id=company.id,
            opportunity_type="INTERNSHIP",
            title="Reserved Reallocation Integrity Role",
            domain="Artificial Intelligence",
            description="Reallocation policy integrity test",
            required_skills=["Python"],
            preferred_skills=[],
            seats=2,
            stipend=0,
            location="Chennai",
            work_mode="HYBRID",
            min_cgpa=0,
            status="OPEN",
            moderation_status="APPROVED",
            duration="4 weeks",
            deadline=datetime.now(timezone.utc) + timedelta(days=30),
            reservation_policy={"OBC": 1},
            reservation_policy_approved=True,
            published_at=datetime.now(timezone.utc),
        )
        db.add(opportunity)
        db.flush()
        students = db.scalars(select(StudentProfile)).all()
        for index, student in enumerate(students, start=1):
            ensure_application(db, student, opportunity, preference_rank=index)
            refresh_student_matches(db, student)
        db.commit()

        allocations = allocate_opportunity(db, opportunity)
        reserved = next(row for row in allocations if row.category_slot == "OBC")
        reserved_student = db.get(StudentProfile, reserved.student_profile_id)
        assert reserved_student is not None and reserved_student.reservation_category == "OBC"
        actor = db.get(User, reserved_student.user_id)
        assert actor is not None

        respond_to_allocation(db, reserved, "REJECTED", actor)
        all_rows = db.scalars(select(Allocation).where(Allocation.opportunity_id == opportunity.id)).all()
        assert sum(1 for row in all_rows if row.category_slot == "OBC" and row.status != "REJECTED") == 0
        assert len(all_rows) == 2  # Rejection does not create a mislabeled replacement.


def test_operational_metadata_requires_auth_and_model_inventory_is_admin_only():
    reset_db()
    with TestClient(app) as client:
        assert client.get("/api/v1/sih/system/provider").status_code == 401
        assert client.get("/api/v1/sih/system/integrations").status_code == 401
        assert client.get("/api/v1/sih/system/provider/models").status_code == 401

        student = login(client, "student@stuskilllink.demo")
        assert client.get("/api/v1/sih/system/provider", headers=student).status_code == 200
        assert client.get("/api/v1/sih/system/integrations", headers=student).status_code == 200
        assert client.get("/api/v1/sih/system/provider/models", headers=student).status_code == 403

        admin = login(client, "admin@stuskilllink.demo")
        models = client.get("/api/v1/sih/system/provider/models", headers=admin)
        assert models.status_code == 200


def test_badge_review_notes_are_admin_only_and_public_verification_exposes_safe_metadata():
    reset_db()
    with TestClient(app) as client:
        student = login(client, "student@stuskilllink.demo")
        learning = client.get("/api/v1/sih/student/learning", headers=student).json()
        assert learning
        complete = client.post(f"/api/v1/sih/student/learning/{learning[0]['id']}/complete", headers=student)
        assert complete.status_code == 200

        admin = login(client, "admin@stuskilllink.demo")
        pending = client.get("/api/v1/sih/admin/badges?verification_status=PENDING_VERIFICATION", headers=admin).json()
        badge = pending[0]
        internal_note = "Evidence hash and issuer record checked by governance team"
        verified = client.patch(
            f"/api/v1/sih/admin/badges/{badge['id']}/verification",
            headers=admin,
            json={"status": "VERIFIED", "notes": internal_note},
        )
        assert verified.status_code == 200

        admin_view = client.get("/api/v1/sih/admin/badges", headers=admin).json()
        reviewed = next(x for x in admin_view if x["id"] == badge["id"])
        assert reviewed["verification_notes"] == internal_note
        assert reviewed["reviewed_at"] is not None

        public = client.get(f"/api/v1/sih/badges/{badge['id']}/verify")
        assert public.status_code == 200
        assert public.json()["verified"] is True
        assert "verification_notes" not in public.json()

        portfolio = client.get("/api/v1/sih/student/portfolio", headers=student)
        assert portfolio.status_code == 200
        own_badge = next(x for x in portfolio.json()["badges"] if x["id"] == badge["id"])
        assert "verification_notes" not in own_badge


def test_company_trust_revocation_pauses_roles_and_admin_cannot_open_roles_for_untrusted_company():
    reset_db()
    with TestClient(app) as client:
        admin = login(client, "admin@stuskilllink.demo")
        companies = client.get("/api/v1/sih/admin/companies", headers=admin).json()
        company = next(x for x in companies if x["company_name"] == "TechNova Labs")
        opportunities = client.get("/api/v1/sih/admin/opportunities", headers=admin).json()
        role = next(x for x in opportunities if x["company_id"] == company["id"] and x["status"] == "OPEN")

        suspended = client.patch(
            f"/api/v1/sih/admin/companies/{company['id']}/verification",
            headers=admin,
            json={"status": "SUSPENDED", "notes": "Compliance review"},
        )
        assert suspended.status_code == 200
        assert suspended.json()["affected_open_opportunities"] >= 1

        after = client.get("/api/v1/sih/admin/opportunities", headers=admin).json()
        paused = next(x for x in after if x["id"] == role["id"])
        assert paused["status"] == "PAUSED"

        reopen = client.patch(
            f"/api/v1/sih/admin/opportunities/{role['id']}/moderation",
            headers=admin,
            json={
                "moderation_status": "APPROVED",
                "status": "OPEN",
                "reservation_policy": role.get("reservation_policy", {}),
                "reservation_policy_approved": bool(role.get("reservation_policy")),
            },
        )
        assert reopen.status_code == 409


def test_opportunity_policy_cannot_be_marked_approved_when_opportunity_is_not_approved():
    reset_db()
    with TestClient(app) as client:
        admin = login(client, "admin@stuskilllink.demo")
        opportunities = client.get("/api/v1/sih/admin/opportunities", headers=admin).json()
        opportunity = opportunities[0]
        invalid = client.patch(
            f"/api/v1/sih/admin/opportunities/{opportunity['id']}/moderation",
            headers=admin,
            json={
                "moderation_status": "PENDING",
                "status": "DRAFT",
                "reservation_policy": {"OBC": 1},
                "reservation_policy_approved": True,
            },
        )
        assert invalid.status_code == 422
