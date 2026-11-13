"""Write and read audit history."""

from typing import Any

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.policy import authorize
from app.authorization.permissions import Permission
from app.common.context import get_request_id
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
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
  outcome: str = "success",
) -> None:
  entry = AuditLog(
    actor_id=actor_id,
    action=action,
    resource_type=resource_type,
    resource_id=resource_id,
    tenant_id=tenant_id,
    outcome=outcome,
    request_id=get_request_id(),
    metadata=metadata or {},
  )
  await entry.insert()


async def list_audit_logs(scope: AccessScope, pagination: Pagination) -> Page[AuditLogRead]:
  authorize(scope, Permission.TENANT_AUDIT_READ)
  if scope.tenant_id is None and not scope.is_super_admin:
    raise AppError(
      code="TENANT_REQUIRED",
      message="College context is required",
      status_code=403,
    )

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
