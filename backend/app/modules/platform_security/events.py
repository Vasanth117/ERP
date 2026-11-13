"""Security event helpers."""

from typing import Any

from beanie import PydanticObjectId

from app.modules.platform_security.models import SecurityEvent


async def emit_security_event(
    *,
    code: str,
    category: str,
    title: str,
    description: str,
    severity: str = "medium",
    actor_id: PydanticObjectId | None = None,
    tenant_id: PydanticObjectId | None = None,
    metadata: dict[str, Any] | None = None,
) -> SecurityEvent:
    event = SecurityEvent(
        code=code,
        category=category,
        title=title,
        description=description,
        severity=severity,
        actor_id=actor_id,
        tenant_id=tenant_id,
        metadata=metadata or {},
    )
    await event.insert()
    return event
