"""Department-scoped audit logging (canonical metadata for Phase 9 visibility)."""

from __future__ import annotations

from typing import Any

from beanie import PydanticObjectId

from app.modules.audit.service import record_audit
from app.modules.department_admin.audit_meta import department_audit_metadata


async def record_department_audit(
    *,
    actor_id: PydanticObjectId | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    tenant_id: PydanticObjectId | None,
    central_department_id: PydanticObjectId,
    metadata: dict[str, Any] | None = None,
    outcome: str = "success",
) -> None:
    await record_audit(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=tenant_id,
        metadata=department_audit_metadata(central_department_id, metadata),
        outcome=outcome,
    )