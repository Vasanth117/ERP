"""Circulation RBAC and branch scope."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.library.facility_access import require_facility_manage, require_facility_read
from app.modules.library.policy import require_library_tenant_scope


def authorize_circulation_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_CIRCULATION_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_CIRCULATION_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_CIRCULATION_READ)


def authorize_circulation_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_CIRCULATION_MANAGE)


async def require_circulation_read(scope: AccessScope, *, branch_code: str | None = None) -> PydanticObjectId:
    authorize_circulation_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    if branch_code and Permission.LIBRARY_ADMIN_READ not in scope.effective_permissions:
        from app.modules.college_admin.library_admin_models import LibraryBranch

        branch = await LibraryBranch.find_one({"tenant_id": tenant_id, "branch_code": branch_code.upper()})
        library_code = branch.library_code if branch else None
        if library_code:
            await require_facility_read(scope, library_code=library_code, branch_code=branch_code)
    return tenant_id


async def require_circulation_manage(scope: AccessScope, *, branch_code: str | None) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return tenant_id
    authorize_circulation_manage(scope)
    if branch_code:
        from app.modules.college_admin.library_admin_models import LibraryBranch

        branch = await LibraryBranch.find_one({"tenant_id": tenant_id, "branch_code": branch_code.upper()})
        library_code = branch.library_code if branch else None
        if library_code:
            await require_facility_manage(scope, library_code=library_code, branch_code=branch_code)
        else:
            raise AppError(code="VALIDATION_ERROR", message="Unknown branch for circulation", status_code=422)
    return tenant_id