"""Examination cell route dependencies."""

from typing import Annotated

from fastapi import Depends, status

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_policy import require_examination_cell_tenant


async def examination_cell_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    require_examination_cell_tenant(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    if not user.is_active:
        raise AppError(code="FORBIDDEN", message="Account is inactive", status_code=403)
    return user


async def exam_cell_sensitive_rate_limit(
    user: Annotated[User, Depends(examination_cell_user)],
) -> None:
    redis = get_redis()
    key = f"rl:exam_cell:sensitive:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > 20:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many sensitive examination operations; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )