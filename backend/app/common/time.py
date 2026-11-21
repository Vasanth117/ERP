"""UTC timestamps for stored documents."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc_aware(value: datetime) -> datetime:
    """Coerce stored instants to UTC-aware for safe comparison with :func:`utcnow`."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def utc_is_past(instant: datetime, *, now: datetime | None = None) -> bool:
    """Return True when ``instant`` is at or before ``now`` (both normalized to UTC)."""
    reference = as_utc_aware(now) if now is not None else utcnow()
    return as_utc_aware(instant) <= reference
