"""College admin route dependencies."""

from typing import Annotated

from fastapi import Depends, status

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.modules.auth.models import User
from app.modules.college_admin.policy import require_college_tenant_scope


async def college_admin_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    require_college_tenant_scope(scope)
    if user.role not in (Role.COLLEGE_ADMIN, Role.SUPER_ADMIN):
        raise AppError(code="FORBIDDEN", message="College administrator access required", status_code=403)
    if user.tenant_id is not None and str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    return user


async def institution_settings_rate_limit(
    user: Annotated[User, Depends(college_admin_user)],
) -> None:
    redis = get_redis()
    key = f"rl:college_admin:settings:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > 15:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many settings updates; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
