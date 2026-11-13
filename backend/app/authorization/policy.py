"""Permission checks for API and services."""

from app.common.access import AccessScope
from app.authorization.permissions import Permission, permissions_for_role
from app.core.exceptions import AppError


def authorize(scope: AccessScope, permission: Permission) -> None:
  allowed = permissions_for_role(scope.role)
  if permission not in allowed:
    raise AppError(
      code="FORBIDDEN",
      message="You do not have permission for this action",
      status_code=403,
    )
