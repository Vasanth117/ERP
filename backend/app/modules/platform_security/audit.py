"""Append-only platform audit writer."""

from typing import Any

from beanie import PydanticObjectId

from app.common.context import get_request_id
from app.modules.platform_security.models import PlatformAuditLog


async def record_platform_audit(
    *,
    actor_id: PydanticObjectId | None,
    action: str,
    module: str,
    resource_type: str,
    resource_id: str | None,
    tenant_id: PydanticObjectId | None = None,
    outcome: str = "success",
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    entry = PlatformAuditLog(
        actor_id=actor_id,
        action=action,
        module=module,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=tenant_id,
        outcome=outcome,
        request_id=get_request_id(),
        before_state=before_state,
        after_state=after_state,
        metadata=metadata or {},
    )
    await entry.insert()
