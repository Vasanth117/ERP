"""Faculty route dependencies."""

from typing import Annotated

from fastapi import Depends

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.core.redis import get_redis
from app.core.exceptions import AppError
from app.modules.auth.models import User
from fastapi import status


async def faculty_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    from app.modules.faculty.policy import require_faculty_scope

    require_faculty_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    return user


async def profile_update_rate_limit(
    user: Annotated[User, Depends(faculty_user)],
) -> None:
    redis = get_redis()
    key = f"rl:faculty:profile:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > 10:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many profile updates; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def announcement_rate_limit(user: Annotated[User, Depends(faculty_user)]) -> None:
    redis = get_redis()
    key = f"rl:faculty:announcement:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > 5:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many announcements; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
