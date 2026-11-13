"""Expiring download tokens for faculty report/document exports."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_token() -> str:
    return secrets.token_urlsafe(32)


def sign_download(*, export_id: str, tenant_id: str, user_id: str, expires_at: datetime, raw: str) -> str:
    payload = f"{export_id}:{tenant_id}:{user_id}:{int(expires_at.timestamp())}:{raw}"
    return hmac.new(get_settings().jwt_secret.encode("utf-8"), payload.encode(), hashlib.sha256).hexdigest()


def verify_download(*, export_id: str, tenant_id: str, user_id: str, expires_at: datetime, raw: str, sig: str) -> None:
    if utcnow() > expires_at:
        raise AppError(code="DOWNLOAD_EXPIRED", message="Download link has expired", status_code=410)
    expected = sign_download(export_id=export_id, tenant_id=tenant_id, user_id=user_id, expires_at=expires_at, raw=raw)
    if not hmac.compare_digest(expected, sig):
        raise AppError(code="DOWNLOAD_UNAUTHORIZED", message="Invalid download authorization", status_code=403)


def default_expiry() -> datetime:
    return utcnow() + timedelta(hours=get_settings().export_download_expire_hours)
