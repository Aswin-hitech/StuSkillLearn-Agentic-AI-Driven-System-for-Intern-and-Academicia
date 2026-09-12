"""External integration boundaries used by the SIH prototype.

The product works without external credentials. These adapters expose the exact places
where production deployments can attach NPTEL/SWAYAM/Coursera catalog APIs, messaging,
and a MongoDB audit mirror without coupling core ranking/allocation logic to vendors.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


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
        "email": "configured" if os.getenv("SMTP_URL") else "optional",
        "sms": "configured" if os.getenv("TWILIO_ACCOUNT_SID") else "optional",
        "note": "Core offer/reallocation workflow is in-app and remains fully functional without messaging credentials.",
    }


def mongodb_status() -> dict[str, Any]:
    return {
        "configured": bool(os.getenv("MONGODB_URI")),
        "purpose": "Optional event/document mirror; PostgreSQL/SQLite remains the transactional source of truth.",
    }


def mirror_audit_event(document: dict[str, Any]) -> bool:
    """Best-effort MongoDB event mirror when pymongo + MONGODB_URI are configured."""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return False
    try:
        from pymongo import MongoClient  # type: ignore
        client = MongoClient(uri, serverSelectionTimeoutMS=1500)
        client.get_database("stuskilllink").get_collection("audit_events").insert_one(document)
        client.close()
        return True
    except Exception:
        return False
