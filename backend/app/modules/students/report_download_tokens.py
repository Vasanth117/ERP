"""Short-lived report download tokens."""

import json
import secrets

from app.core.redis import get_redis

_TOKEN_TTL = 15 * 60
_PREFIX = "student:report:download:"


async def issue_report_download_token(*, tenant_id: str, user_id: str, export_id: str) -> str:
    token = secrets.token_urlsafe(32)
    redis = get_redis()
    payload = json.dumps({"export_id": export_id, "user_id": user_id})
    await redis.setex(f"{_PREFIX}{tenant_id}:{token}", _TOKEN_TTL, payload)
    return token


async def resolve_report_download_token(*, tenant_id: str, token: str, user_id: str) -> str:
    from app.core.exceptions import AppError

    redis = get_redis()
    raw = await redis.get(f"{_PREFIX}{tenant_id}:{token}")
    if raw is None:
        raise AppError(code="FORBIDDEN", message="Download token invalid or expired", status_code=403)
    data = json.loads(raw)
    if data.get("user_id") != user_id:
        raise AppError(code="FORBIDDEN", message="Download token not authorized", status_code=403)
    export_id = data.get("export_id")
    if not export_id:
        raise AppError(code="FORBIDDEN", message="Download token invalid", status_code=403)
    await redis.delete(f"{_PREFIX}{tenant_id}:{token}")
    return export_id
