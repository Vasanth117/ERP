"""Library notification RBAC."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role


def authorize_notification_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_NOTIFICATION_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_NOTIFICATION_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_NOTIFICATION_READ)


def authorize_notification_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_NOTIFICATION_MANAGE)


def authorize_notification_publish(scope: AccessScope) -> None:
    if Permission.LIBRARY_NOTIFICATION_PUBLISH in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_NOTIFICATION_PUBLISH)


def authorize_notification_run(scope: AccessScope) -> None:
    if Permission.LIBRARY_NOTIFICATION_RUN in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_NOTIFICATION_RUN)