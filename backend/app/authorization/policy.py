"""Permission checks for API and services."""

from app.common.access import AccessScope
from app.authorization.permissions import Permission
from app.core.exceptions import AppError


def authorize(scope: AccessScope, permission: Permission) -> None:
    allowed = scope.effective_permissions
    if permission not in allowed:
        raise AppError(
            code="FORBIDDEN",
            message="You do not have permission for this action",
            status_code=403,
        )


def authorize_support_scope(scope: AccessScope, required_scope: str) -> None:
    if scope.support_session_id is None:
        raise AppError(
            code="SUPPORT_SESSION_REQUIRED",
            message="Controlled support session is required",
            status_code=403,
        )
    if required_scope not in scope.support_scopes:
        raise AppError(
            code="SUPPORT_SCOPE_DENIED",
            message="This support session does not include the required scope",
            status_code=403,
        )
