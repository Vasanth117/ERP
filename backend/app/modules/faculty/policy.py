"""Faculty authorization helpers."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.roles import Role
from app.core.exceptions import AppError


def require_faculty_scope(scope: AccessScope) -> PydanticObjectId:
    """Resolve the faculty user id from auth context — never trust client-supplied ids."""
    authorize(scope, Permission.FACULTY_SELF_ACCESS)
    if scope.tenant_id is None:
        raise AppError(
            code="TENANT_REQUIRED",
            message="College context is required",
            status_code=403,
        )
    if scope.role != Role.FACULTY:
        raise AppError(
            code="FORBIDDEN",
            message="This endpoint is available to faculty accounts only",
            status_code=403,
        )
    return scope.user_id
