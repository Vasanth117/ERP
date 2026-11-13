"""Expiring signed export download tokens (private, non-public URLs)."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError


def _secret() -> bytes:
    return get_settings().jwt_secret.encode("utf-8")


def hash_download_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def issue_raw_download_token() -> str:
    return secrets.token_urlsafe(32)


def build_download_authorization(
    *,
    artifact_id: str,
    tenant_id: str,
    user_id: str,
    expires_at: datetime,
    raw_token: str,
) -> str:
    payload = f"{artifact_id}:{tenant_id}:{user_id}:{int(expires_at.timestamp())}:{raw_token}"
    return hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_download_authorization(
    *,
    artifact_id: str,
    tenant_id: str,
    user_id: str,
    expires_at: datetime,
    raw_token: str,
    signature: str,
) -> None:
    if utcnow() > expires_at:
        raise AppError(code="DOWNLOAD_EXPIRED", message="Download link has expired", status_code=410)
    expected = build_download_authorization(
        artifact_id=artifact_id,
        tenant_id=tenant_id,
        user_id=user_id,
        expires_at=expires_at,
        raw_token=raw_token,
    )
    if not hmac.compare_digest(expected, signature):
        raise AppError(code="DOWNLOAD_UNAUTHORIZED", message="Invalid download authorization", status_code=403)


def default_download_expiry() -> datetime:
    hours = get_settings().export_download_expire_hours
    return utcnow() + timedelta(hours=hours)
