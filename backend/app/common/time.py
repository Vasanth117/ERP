"""UTC timestamps for stored documents."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc_aware(value: datetime) -> datetime:
    """Coerce stored instants to UTC-aware for safe comparison with :func:`utcnow`."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
