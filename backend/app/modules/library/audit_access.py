"""Library audit and inventory-control authorization."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.modules.library.policy import require_library_tenant_scope


def require_audit_read(scope: AccessScope) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if Permission.LIBRARY_AUDIT_READ in scope.effective_permissions:
        return tenant_id
    if Permission.LIBRARY_AUDIT_EXPORT in scope.effective_permissions:
        return tenant_id
    if Permission.TENANT_AUDIT_READ in scope.effective_permissions:
        return tenant_id
    authorize(scope, Permission.LIBRARY_AUDIT_READ)
    return tenant_id


def require_audit_export(scope: AccessScope) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if Permission.LIBRARY_AUDIT_EXPORT in scope.effective_permissions:
        return tenant_id
    if Permission.TENANT_AUDIT_READ in scope.effective_permissions:
        return tenant_id
    authorize(scope, Permission.LIBRARY_AUDIT_EXPORT)
    return tenant_id


def require_discrepancy_manage(scope: AccessScope) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if Permission.LIBRARY_INVENTORY_MANAGE in scope.effective_permissions:
        return tenant_id
    authorize(scope, Permission.LIBRARY_INVENTORY_DISCREPANCY_MANAGE)
    return tenant_id


def require_stock_adjust_approve(scope: AccessScope) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if Permission.LIBRARY_INVENTORY_APPROVE in scope.effective_permissions:
        return tenant_id
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return tenant_id
    authorize(scope, Permission.LIBRARY_INVENTORY_APPROVE)
    return tenant_id


def assert_no_audit_mutation() -> None:
    raise AppError(
        code="FORBIDDEN",
        message="Library audit records are immutable",
        status_code=403,
    )