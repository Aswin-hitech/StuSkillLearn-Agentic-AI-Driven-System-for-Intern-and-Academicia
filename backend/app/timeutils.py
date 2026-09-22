from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | None) -> datetime | None:
    """Normalize database/application datetimes to aware UTC.

    SQLite may deserialize timezone-aware SQLAlchemy DateTime columns as naive
    datetimes. Treat such values as UTC because StuSkillLink persists timestamps
    in UTC. PostgreSQL values with offsets are converted to UTC.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_expired(value: datetime | None, *, now: datetime | None = None) -> bool:
    normalized = ensure_utc(value)
    if normalized is None:
        return False
    return normalized <= ensure_utc(now) if now is not None else normalized <= utc_now()


def not_expired(value: datetime | None, *, now: datetime | None = None) -> bool:
    return not is_expired(value, now=now)
