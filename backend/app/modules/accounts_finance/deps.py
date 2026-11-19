"""Accounts / Finance Staff route dependencies."""

from typing import Annotated

from fastapi import Depends

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.accounts_finance.policy import authorize_finance_dashboard
from app.modules.auth.models import User


async def finance_staff_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    authorize_finance_dashboard(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    if not user.is_active:
        raise AppError(code="FORBIDDEN", message="Account is inactive", status_code=403)
    if user.role not in (
        Role.FINANCE_STAFF,
        Role.ACCOUNTS_STAFF,
        Role.COLLEGE_ADMIN,
    ):
        raise AppError(code="FORBIDDEN", message="Finance staff access required", status_code=403)
    return user