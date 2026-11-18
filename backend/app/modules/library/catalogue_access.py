"""Catalogue RBAC helpers."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.modules.library.policy import require_library_tenant_scope


def authorize_catalogue_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_CATALOGUE_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_CATALOGUE_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_CATALOGUE_READ)


def authorize_catalogue_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_CATALOGUE_MANAGE)


def require_catalogue_tenant(scope: AccessScope) -> PydanticObjectId:
    authorize_catalogue_read(scope)
    return require_library_tenant_scope(scope)