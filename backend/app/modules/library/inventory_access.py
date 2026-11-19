"""Inventory RBAC (reuses library / branch scope)."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from beanie import PydanticObjectId

from app.core.exceptions import AppError
from app.modules.library.facility_access import require_facility_manage, require_facility_read
from app.modules.library.policy import require_library_tenant_scope


def authorize_inventory_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_INVENTORY_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_INVENTORY_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_INVENTORY_READ)


def authorize_inventory_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_INVENTORY_MANAGE)


async def require_inventory_read(scope: AccessScope, *, branch_code: str | None = None, library_code: str | None = None) -> PydanticObjectId:
    authorize_inventory_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    if branch_code and library_code:
        await require_facility_read(scope, library_code=library_code, branch_code=branch_code)
    return tenant_id


async def require_inventory_manage(scope: AccessScope, *, branch_code: str | None, library_code: str | None = None) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return tenant_id
    authorize_inventory_manage(scope)
    if not library_code and branch_code:
        from app.modules.college_admin.library_admin_models import LibraryBranch

        branch = await LibraryBranch.find_one({"tenant_id": tenant_id, "branch_code": branch_code.upper()})
        library_code = branch.library_code if branch else None
    if library_code:
        await require_facility_manage(scope, library_code=library_code, branch_code=branch_code)
    elif branch_code:
        raise AppError(code="VALIDATION_ERROR", message="library_code required for branch-scoped inventory manage", status_code=422)
    return tenant_id