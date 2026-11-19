"""Hostel Admin route dependencies."""

from typing import Annotated

from fastapi import Depends

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.hostel.policy import has_hostel_portal_access, require_hostel_tenant_scope


async def hostel_admin_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    require_hostel_tenant_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    if not user.is_active:
        raise AppError(code="FORBIDDEN", message="Account is inactive", status_code=403)
    if user.role not in (Role.HOSTEL_ADMIN, Role.COLLEGE_ADMIN) and not has_hostel_portal_access(scope):
        raise AppError(code="FORBIDDEN", message="Hostel Admin access required", status_code=403)
    return user