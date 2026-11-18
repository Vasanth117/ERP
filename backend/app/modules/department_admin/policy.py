"""Department Admin access and department boundary enforcement."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionDepartment


async def require_department_admin_scope(scope: AccessScope, user: User) -> PydanticObjectId:
    """Return tenant id after validating department admin role and college context."""
    authorize(scope, Permission.DEPARTMENT_SELF_ACCESS)
    if scope.tenant_id is None or user.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    if str(scope.tenant_id) != str(user.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    if scope.role != Role.DEPARTMENT_ADMIN:
        raise AppError(
            code="FORBIDDEN",
            message="This endpoint is available to department administrator accounts only",
            status_code=403,
        )
    if user.department_id is None:
        raise AppError(
            code="DEPARTMENT_REQUIRED",
            message="Your account is not assigned to a department",
            status_code=403,
        )
    return scope.tenant_id


async def resolve_authorized_department(scope: AccessScope, user: User) -> tuple[PydanticObjectId, InstitutionDepartment]:
    """Resolve institution department from trusted user assignment (central department id)."""
    await require_department_admin_scope(scope, user)
    central_id = user.department_id
    assert central_id is not None
    institution = await InstitutionDepartment.find_one(
        Eq(InstitutionDepartment.tenant_id, scope.tenant_id),
        Eq(InstitutionDepartment.central_department_id, central_id),
    )
    if institution is None:
        institution = await InstitutionDepartment.get(central_id)
    if institution is None or institution.tenant_id != scope.tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found for this account", status_code=404)
    if scope.department_id is not None and str(scope.department_id) != str(central_id):
        raise AppError(code="FORBIDDEN", message="Department context mismatch", status_code=403)
    return central_id, institution


def assert_filter_department(central_department_id: PydanticObjectId, requested: str | None, *, field: str) -> None:
    if requested is None:
        return
    if str(requested) not in {str(central_department_id)}:
        raise AppError(
            code="FORBIDDEN",
            message=f"{field} is outside your authorized department",
            status_code=403,
        )