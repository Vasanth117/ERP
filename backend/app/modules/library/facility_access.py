"""Branch- and library-scoped access for librarian facility operations."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.library.facility_enums import LibraryStaffAssignmentStatus
from app.modules.library.facility_models import LibraryStaffAssignment
from app.modules.library.policy import require_library_tenant_scope


def has_institution_library_manage(scope: AccessScope) -> bool:
    return Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN


def authorize_facility_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_FACILITY_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_FACILITY_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_FACILITY_READ)


def authorize_facility_manage(scope: AccessScope) -> None:
    if has_institution_library_manage(scope):
        return
    authorize(scope, Permission.LIBRARY_FACILITY_MANAGE)


async def _active_assignments(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[LibraryStaffAssignment]:
    return await LibraryStaffAssignment.find(
        Eq(LibraryStaffAssignment.tenant_id, tenant_id),
        Eq(LibraryStaffAssignment.employee_user_id, user_id),
        Eq(LibraryStaffAssignment.status, LibraryStaffAssignmentStatus.ACTIVE),
    ).to_list()


def _assignment_covers(
    assignments: list[LibraryStaffAssignment],
    *,
    library_code: str,
    branch_code: str | None,
) -> bool:
    normalized_lib = library_code.upper()
    normalized_branch = branch_code.upper() if branch_code else None
    for row in assignments:
        if row.library_code.upper() != normalized_lib:
            continue
        if row.branch_code is None:
            return True
        if normalized_branch and row.branch_code.upper() == normalized_branch:
            return True
    return False


async def require_facility_read(
    scope: AccessScope,
    *,
    library_code: str | None = None,
    branch_code: str | None = None,
) -> PydanticObjectId:
    authorize_facility_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    if has_institution_library_manage(scope) or Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return tenant_id
    if library_code is None and branch_code is None:
        return tenant_id
    if library_code is None:
        raise AppError(code="VALIDATION_ERROR", message="library_code is required for branch-scoped access", status_code=422)
    assignments = await _active_assignments(tenant_id, scope.user_id)
    if not _assignment_covers(assignments, library_code=library_code, branch_code=branch_code):
        raise AppError(code="FORBIDDEN", message="Not assigned to this library or branch", status_code=403)
    return tenant_id


async def require_facility_manage(
    scope: AccessScope,
    *,
    library_code: str | None = None,
    branch_code: str | None = None,
    institution_level: bool = False,
) -> PydanticObjectId:
    tenant_id = require_library_tenant_scope(scope)
    if has_institution_library_manage(scope):
        return tenant_id
    authorize_facility_manage(scope)
    if institution_level:
        raise AppError(
            code="FORBIDDEN",
            message="Institution-level library configuration requires college library manage permission",
            status_code=403,
        )
    if library_code is None:
        raise AppError(code="VALIDATION_ERROR", message="library_code is required", status_code=422)
    assignments = await _active_assignments(tenant_id, scope.user_id)
    if not _assignment_covers(assignments, library_code=library_code, branch_code=branch_code):
        raise AppError(code="FORBIDDEN", message="Not assigned to manage this library or branch", status_code=403)
    return tenant_id