"""Student route dependencies."""

from typing import Annotated

from fastapi import Depends, status

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.modules.auth.models import User
from app.modules.students.policy import require_student_scope


async def student_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    require_student_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    return user


async def profile_update_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:profile:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > 10:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many profile updates; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def exam_review_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:exam_review:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)
    if count > 10:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many examination review requests; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def academic_document_request_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:academic_document:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 600)
    if count > 5:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many document requests; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def exam_registration_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:exam_registration:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)
    if count > 8:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many examination registration attempts; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def enrollment_request_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:enrollment_request:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)
    if count > 5:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many enrollment requests; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def lms_assignment_submit_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:lms_submit:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)
    if count > 20:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many assignment submissions; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def finance_payment_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:finance_payment:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)
    if count > 15:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many payment initiation attempts; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def student_portal_request_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:portal_request:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)
    if count > 25:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many portal requests; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def finance_scholarship_rate_limit(
    user: Annotated[User, Depends(student_user)],
) -> None:
    redis = get_redis()
    key = f"rl:student:finance_scholarship:{user.id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 600)
    if count > 5:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many scholarship applications; try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
