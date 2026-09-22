"""Production integration status and audit-mirroring boundaries."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings


@dataclass(frozen=True)
class LearningProvider:
    name: str
    catalog_url: str


LEARNING_PROVIDERS = (
    LearningProvider("NPTEL", "https://nptel.ac.in/courses"),
    LearningProvider("SWAYAM", "https://swayam.gov.in/explorer"),
    LearningProvider("Coursera", "https://www.coursera.org/search"),
)


def learning_provider_status() -> list[dict[str, Any]]:
    return [{"name": item.name, "catalog_url": item.catalog_url, "mode": "catalog-link"} for item in LEARNING_PROVIDERS]


def notification_status() -> dict[str, Any]:
    return {
        "email": "configured" if settings.smtp_url else "not-configured",
        "sms": "configured" if (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from_number) else "not-configured",
        "delivery": "SMTP and Twilio adapters are implemented; background delivery uses Celery when configured.",
    }


def mongodb_status() -> dict[str, Any]:
    return {
        "configured": bool(settings.mongodb_uri),
        "purpose": "Optional append-only event/document mirror; PostgreSQL remains the transactional source of truth.",
    }


def mirror_audit_event(document: dict[str, Any]) -> bool:
    """Best-effort MongoDB event mirror when pymongo + MONGODB_URI are configured."""
    if not settings.mongodb_uri:
        return False
    try:
        from pymongo import MongoClient

        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1500)
        client.get_database("stuskilllink").get_collection("audit_events").insert_one(document)
        client.close()
        return True
    except Exception:
        return False
