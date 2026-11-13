"""SSRF URL validation."""

import pytest

from app.core.url_safety import validate_outbound_url


def test_blocks_localhost() -> None:
    with pytest.raises(ValueError):
        validate_outbound_url("http://localhost/health")


def test_allows_public_https() -> None:
    validate_outbound_url("https://api.sendgrid.com/v3")
