"""Write and read audit history."""

from typing import Any

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.api.deps import AccessScope
from app.common.schemas import Page, Pagination
from app.modules.audit.models import AuditLog
from app.modules.audit.schemas import AuditLogRead


async def record_audit(
    *,
    actor_id: PydanticObjectId | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    tenant_id: PydanticObjectId | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=tenant_id,
        metadata=metadata or {},
    )
    await entry.insert()


async def list_audit_logs(scope: AccessScope, pagination: Pagination) -> Page[AuditLogRead]:
    if scope.tenant_id is None and not scope.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="College context is required")

    filters: dict[str, Any] = {}
    if scope.tenant_id is not None:
        filters["tenant_id"] = scope.tenant_id

    total = await AuditLog.find(filters).count()
    documents = (
        await AuditLog.find(filters)
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    return Page(
        items=[AuditLogRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
