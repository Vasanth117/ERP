"""Expiring audit export download tokens."""

import hashlib
import json
import secrets

from app.core.redis import get_redis

TOKEN_TTL_SECONDS = 15 * 60
_KEY_PREFIX = "college:audit_export:"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _key(tenant_id: str, token_hash: str) -> str:
    return f"{_KEY_PREFIX}{tenant_id}:{token_hash}"


async def issue_audit_export_token(
    *,
    tenant_id: str,
    user_id: str,
    export_id: str,
) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    redis = get_redis()
    payload = json.dumps({"export_id": export_id, "user_id": user_id})
    await redis.setex(_key(tenant_id, token_hash), TOKEN_TTL_SECONDS, payload)
    return token, token_hash


async def resolve_audit_export_token(
    *,
    tenant_id: str,
    token: str,
    user_id: str,
) -> str:
    token_hash = _hash_token(token)
    redis = get_redis()
    raw = await redis.get(_key(tenant_id, token_hash))
    if raw is None:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Audit export token invalid or expired", status_code=403)
    data = json.loads(raw)
    if data.get("user_id") != user_id:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Audit export token not authorized", status_code=403)
    export_id = data.get("export_id")
    if not export_id:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Audit export token invalid", status_code=403)
    return export_id