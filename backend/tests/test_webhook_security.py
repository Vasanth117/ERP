"""Webhook signature and replay tests."""

import pytest

from app.core.exceptions import AppError
from app.modules.integrations.webhook_security import compute_webhook_signature, verify_webhook_signature


def test_signature_roundtrip() -> None:
    body = b'{"event":"test"}'
    ts = "1700000000"
    sig = compute_webhook_signature("secret", body, ts)
    verify_webhook_signature(
        secret="secret",
        body=body,
        timestamp=ts,
        provided_signature=sig,
        max_age_seconds=999999999,
    )


def test_rejects_bad_signature() -> None:
    with pytest.raises(AppError) as exc:
        verify_webhook_signature(
            secret="secret",
            body=b"{}",
            timestamp="1700000000",
            provided_signature="bad",
            max_age_seconds=999999999,
        )
    assert exc.value.code == "WEBHOOK_INVALID"
