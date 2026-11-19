"""Hostel audit bridge to institution audit (append-only)."""

from beanie import PydanticObjectId

from app.modules.college_admin.security_admin_service import append_institution_audit


async def record_hostel_audit(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId | None,
    action: str,
    module: str,
    resource_type: str,
    resource_id: str | None = None,
    hostel_code: str | None = None,
    from_status: str | None = None,
    to_status: str | None = None,
    reason: str | None = None,
    metadata: dict | None = None,
) -> None:
    meta = dict(metadata or {})
    if hostel_code:
        meta["hostel_code"] = hostel_code
    if from_status:
        meta["from_status"] = from_status
    if to_status:
        meta["to_status"] = to_status
    if reason:
        meta["reason"] = reason
    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action=action,
        module=module,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=meta,
    )