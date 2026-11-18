"""Department Admin route dependencies."""

from typing import Annotated

from fastapi import Depends

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.modules.auth.models import User
from app.modules.department_admin.policy import require_department_admin_scope
from fastapi import status


async def department_admin_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    await require_department_admin_scope(scope, user)
    return user


async def profile_update_rate_limit(
    user: Annotated[User, Depends(department_admin_user)],
) -> None:
    redis = get_redis()
    key = f"rl:department:profile:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > 10:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many profile updates; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )