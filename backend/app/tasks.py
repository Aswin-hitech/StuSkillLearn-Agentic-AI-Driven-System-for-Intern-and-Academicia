from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import EmailActionToken, StudentProfile, User
from app.notifications import send_email, send_sms
from app.services import refresh_curriculum_insights, run_seven_agent_cycle


@celery_app.task(name="stuskilllink.run_seven_agent_cycle", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def run_seven_agent_cycle_task(student_profile_id: int | None = None, actor_user_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
        student = db.get(StudentProfile, student_profile_id) if student_profile_id else None
        actor = db.get(User, actor_user_id) if actor_user_id else None
        rows = run_seven_agent_cycle(db, student, actor)
        return {"agent_runs": [row.id for row in rows], "count": len(rows)}
    finally:
        db.close()


@celery_app.task(name="stuskilllink.refresh_curriculum", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def refresh_curriculum_task(institution_profile_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
        rows = refresh_curriculum_insights(db, institution_profile_id)
        db.commit()
        return {"generated": len(rows), "institution_profile_id": institution_profile_id}
    finally:
        db.close()


@celery_app.task(name="stuskilllink.send_email", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_email_task(to_email: str, subject: str, text: str) -> bool:
    return send_email(to_email, subject, text)


@celery_app.task(name="stuskilllink.send_sms", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_sms_task(to_number: str, body: str) -> bool:
    return send_sms(to_number, body)


@celery_app.task(name="stuskilllink.cleanup_expired_auth_tokens")
def cleanup_expired_auth_tokens_task() -> int:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        result = db.execute(delete(EmailActionToken).where(EmailActionToken.expires_at < now))
        db.commit()
        return int(result.rowcount or 0)
    finally:
        db.close()
