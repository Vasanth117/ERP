"""Export download token expiry and signature."""

from datetime import timedelta

import pytest

from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.data_governance.download_tokens import (
    build_download_authorization,
    issue_raw_download_token,
    verify_download_authorization,
)


def test_download_signature_valid() -> None:
    expires = utcnow() + timedelta(hours=1)
    token = issue_raw_download_token()
    sig = build_download_authorization(
        artifact_id="a1",
        tenant_id="t1",
        user_id="u1",
        expires_at=expires,
        raw_token=token,
    )
    verify_download_authorization(
        artifact_id="a1",
        tenant_id="t1",
        user_id="u1",
        expires_at=expires,
        raw_token=token,
        signature=sig,
    )


def test_download_rejects_expired() -> None:
    expires = utcnow() - timedelta(minutes=1)
    token = issue_raw_download_token()
    sig = build_download_authorization(
        artifact_id="a1",
        tenant_id="t1",
        user_id="u1",
        expires_at=expires,
        raw_token=token,
    )
    with pytest.raises(AppError) as exc:
        verify_download_authorization(
            artifact_id="a1",
            tenant_id="t1",
            user_id="u1",
            expires_at=expires,
            raw_token=token,
            signature=sig,
        )
    assert exc.value.code == "DOWNLOAD_EXPIRED"
