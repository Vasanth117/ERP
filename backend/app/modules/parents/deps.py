"""Parent route dependencies."""

from typing import Annotated

from fastapi import Depends, status

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.modules.auth.models import User
from app.modules.parents.policy import require_parent_scope


async def parent_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    require_parent_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    if not user.is_active:
        raise AppError(code="FORBIDDEN", message="Account is not active", status_code=403)
    return user


async def parent_profile_update_rate_limit(
    user: Annotated[User, Depends(parent_user)],
) -> None:
    redis = get_redis()
    key = f"rl:parent:profile:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > 10:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many profile updates; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def parent_payment_rate_limit(
    user: Annotated[User, Depends(parent_user)],
) -> None:
    redis = get_redis()
    key = f"rl:parent:payment:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)
    if count > 5:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many payment attempts; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def parent_enquiry_rate_limit(
    user: Annotated[User, Depends(parent_user)],
) -> None:
    redis = get_redis()
    key = f"rl:parent:enquiry:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 600)
    if count > 12:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many enquiries; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def parent_linking_rate_limit(
    user: Annotated[User, Depends(parent_user)],
) -> None:
    redis = get_redis()
    key = f"rl:parent:linking:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)
    if count > 8:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many linking attempts; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )