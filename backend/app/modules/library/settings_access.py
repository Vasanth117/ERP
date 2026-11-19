"""Library settings / policy RBAC."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role


def authorize_settings_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_SETTINGS_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_SETTINGS_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_SETTINGS_READ)


def authorize_settings_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_SETTINGS_MANAGE)


def authorize_settings_activate(scope: AccessScope) -> None:
    if Permission.LIBRARY_SETTINGS_APPROVE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_SETTINGS_APPROVE)