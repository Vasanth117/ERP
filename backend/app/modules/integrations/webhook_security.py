"""Webhook signature verification and replay prevention."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from app.common.time import utcnow
from app.core.exceptions import AppError


def compute_webhook_signature(secret: str, body: bytes, timestamp: str) -> str:
    payload = f"{timestamp}.".encode() + body
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify_webhook_signature(
    *,
    secret: str,
    body: bytes,
    timestamp: str,
    provided_signature: str,
    max_age_seconds: int = 300,
) -> None:
    try:
        ts = int(timestamp)
    except ValueError as exc:
        raise AppError(code="WEBHOOK_INVALID", message="Invalid timestamp", status_code=400) from exc
    if utcnow().timestamp() - ts > max_age_seconds:
        raise AppError(code="WEBHOOK_REPLAY", message="Webhook timestamp expired", status_code=409)
    expected = compute_webhook_signature(secret, body, timestamp)
    if not secrets.compare_digest(expected, provided_signature):
        raise AppError(code="WEBHOOK_INVALID", message="Invalid webhook signature", status_code=401)


def new_idempotency_key() -> str:
    return secrets.token_urlsafe(24)
