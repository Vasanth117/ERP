"""HR route dependencies."""

from typing import Annotated

from fastapi import Depends

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.hr.policy import authorize_employee_self_service, require_employee_tenant_scope, require_hr_tenant_scope


async def hr_staff_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    require_hr_tenant_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    if not user.is_active:
        raise AppError(code="FORBIDDEN", message="Account is inactive", status_code=403)
    return user


async def employee_self_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    authorize_employee_self_service(scope)
    tenant_id = require_employee_tenant_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    if not user.is_active:
        raise AppError(code="FORBIDDEN", message="Account is inactive", status_code=403)
    return user