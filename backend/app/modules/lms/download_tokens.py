"""Short-lived LMS download tokens (Redis)."""

import json
import secrets

from app.core.redis import get_redis

TOKEN_TTL_SECONDS = 15 * 60
_KEY_PREFIX = "lms:download:"


def _key(tenant_id: str, token: str) -> str:
    return f"{_KEY_PREFIX}{tenant_id}:{token}"


async def issue_material_download_token(
    *,
    tenant_id: str,
    user_id: str,
    material_id: str,
) -> str:
    token = secrets.token_urlsafe(32)
    redis = get_redis()
    payload = json.dumps({"material_id": material_id, "user_id": user_id})
    await redis.setex(_key(tenant_id, token), TOKEN_TTL_SECONDS, payload)
    return token


async def resolve_material_download_token(
    *,
    tenant_id: str,
    token: str,
    user_id: str,
) -> str:
    redis = get_redis()
    raw = await redis.get(_key(tenant_id, token))
    if raw is None:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Download token invalid or expired", status_code=403)
    data = json.loads(raw)
    if data.get("user_id") != user_id:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Download token not authorized", status_code=403)
    material_id = data.get("material_id")
    if not material_id:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Download token invalid", status_code=403)
    await redis.delete(_key(tenant_id, token))
    return material_id
