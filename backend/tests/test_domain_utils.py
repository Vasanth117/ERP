"""Domain and tenant-code normalization tests."""

from app.modules.tenants.domain_utils import normalize_domain, normalize_tenant_code, validate_domain_format


def test_normalize_tenant_code() -> None:
    assert normalize_tenant_code(" COLLEGE-01 ") == "college-01"


def test_normalize_domain_strips_scheme() -> None:
    assert normalize_domain("https://Eng.Example.edu/") == "eng.example.edu"


def test_validate_domain_format_rejects_invalid() -> None:
    assert validate_domain_format("not a domain") is False
    assert validate_domain_format("college.example.com") is True
