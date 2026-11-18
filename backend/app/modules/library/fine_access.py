"""Library fine RBAC (manage vs approve separation)."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.modules.library.circulation_access import require_circulation_manage, require_circulation_read
from app.modules.library.policy import require_library_tenant_scope


def authorize_fine_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_FINE_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_FINE_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_FINE_READ)


def authorize_fine_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_FINE_MANAGE)


def authorize_fine_approve(scope: AccessScope) -> None:
    if Permission.LIBRARY_FINE_APPROVE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_FINE_APPROVE)


async def require_fine_read(scope: AccessScope, *, branch_code: str | None = None) -> PydanticObjectId:
    authorize_fine_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    if branch_code:
        await require_circulation_read(scope, branch_code=branch_code)
    return tenant_id


async def require_fine_manage(scope: AccessScope, *, branch_code: str | None) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return tenant_id
    authorize_fine_manage(scope)
    if branch_code:
        await require_circulation_manage(scope, branch_code=branch_code)
    return tenant_id