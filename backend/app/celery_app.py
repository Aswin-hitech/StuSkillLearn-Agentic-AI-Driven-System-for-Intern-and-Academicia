from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "stuskilllink",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
    task_soft_time_limit=240,
    task_time_limit=300,
    beat_schedule={
        "cleanup-expired-auth-tokens-hourly": {
            "task": "stuskilllink.cleanup_expired_auth_tokens",
            "schedule": 3600.0,
        },
    },
)
