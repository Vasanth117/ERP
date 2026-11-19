"""Acquisition RBAC."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.modules.library.policy import require_library_tenant_scope


def authorize_acquisition_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_ACQUISITION_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ACQUISITION_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_ACQUISITION_READ)


def authorize_acquisition_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_ACQUISITION_MANAGE)


def authorize_acquisition_approve(scope: AccessScope) -> None:
    if Permission.LIBRARY_ACQUISITION_APPROVE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_ACQUISITION_APPROVE)


def authorize_acquisition_procurement(scope: AccessScope) -> None:
    if Permission.LIBRARY_ACQUISITION_PROCURE in scope.effective_permissions:
        return
    if Permission.FINANCE_EXT_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_ACQUISITION_PROCURE)


async def require_acquisition_manage(scope: AccessScope, *, branch_code: str | None = None) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return tenant_id
    authorize_acquisition_manage(scope)
    _ = branch_code
    return tenant_id