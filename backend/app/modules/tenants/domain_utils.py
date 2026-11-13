"""Domain and tenant-code normalization for uniqueness checks."""

import re

_DOMAIN_LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_tenant_code(code: str) -> str:
    return code.strip().lower()


def normalize_domain(domain: str) -> str:
    """Normalize host / subdomain for registry storage (lowercase, no trailing dot)."""
    value = domain.strip().lower().rstrip(".")
    if value.startswith("http://"):
        value = value[7:]
    elif value.startswith("https://"):
        value = value[8:]
    if "/" in value:
        value = value.split("/", 1)[0]
    if value.startswith("*."):
        value = value[2:]
    return value


def validate_domain_format(domain: str) -> bool:
    normalized = normalize_domain(domain)
    if not normalized or len(normalized) > 253:
        return False
    if ".." in normalized:
        return False
    labels = normalized.split(".")
    if len(labels) < 1:
        return False
    for label in labels:
        if not _DOMAIN_LABEL.match(label):
            return False
    return True
