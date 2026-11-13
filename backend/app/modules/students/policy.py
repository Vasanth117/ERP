"""Student authorization helpers."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.roles import Role
from app.core.exceptions import AppError


def require_student_scope(scope: AccessScope) -> PydanticObjectId:
    """Resolve tenant from auth context — never trust client-supplied student ids."""
    authorize(scope, Permission.STUDENT_SELF_ACCESS)
    if scope.tenant_id is None:
        raise AppError(
            code="TENANT_REQUIRED",
            message="College context is required",
            status_code=403,
        )
    if scope.role != Role.STUDENT:
        raise AppError(
            code="FORBIDDEN",
            message="This endpoint is available to student accounts only",
            status_code=403,
        )
    return scope.tenant_id
