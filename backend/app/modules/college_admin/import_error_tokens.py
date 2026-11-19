"""Expiring import error report tokens."""

import hashlib
import json
import secrets

from app.core.redis import get_redis

TOKEN_TTL_SECONDS = 15 * 60
_KEY_PREFIX = "college:import_errors:"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def issue_import_error_token(*, tenant_id: str, user_id: str, job_id: str) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    redis = get_redis()
    payload = json.dumps({"job_id": job_id, "user_id": user_id})
    await redis.setex(f"{_KEY_PREFIX}{tenant_id}:{token_hash}", TOKEN_TTL_SECONDS, payload)
    return token, token_hash


async def resolve_import_error_token(*, tenant_id: str, token: str, user_id: str) -> str:
    token_hash = _hash_token(token)
    redis = get_redis()
    raw = await redis.get(f"{_KEY_PREFIX}{tenant_id}:{token_hash}")
    if raw is None:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Error report token invalid or expired", status_code=403)
    data = json.loads(raw)
    if data.get("user_id") != user_id:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Token not authorized", status_code=403)
    job_id = data.get("job_id")
    if not job_id:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Invalid token", status_code=403)
    return job_id