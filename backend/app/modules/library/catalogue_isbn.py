"""ISBN-10 and ISBN-13 validation and normalization."""

import re

from app.core.exceptions import AppError

_ISBN10_RE = re.compile(r"^[0-9]{9}[0-9Xx]$")
_ISBN13_RE = re.compile(r"^97[89][0-9]{10}$")


def _check_isbn10_checksum(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(digits[:9]):
        total += int(ch) * (10 - i)
    check = digits[9].upper()
    check_val = 10 if check == "X" else int(check)
    return (total + check_val) % 11 == 0


def _check_isbn13_checksum(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(digits[:12]):
        weight = 1 if i % 2 == 0 else 3
        total += int(ch) * weight
    check = (10 - (total % 10)) % 10
    return check == int(digits[12])


def normalize_isbn10(raw: str | None) -> str | None:
    if raw is None or not str(raw).strip():
        return None
    cleaned = re.sub(r"[^0-9Xx]", "", raw.strip())
    if len(cleaned) != 10:
        raise AppError(code="VALIDATION_ERROR", message="ISBN-10 must be 10 characters", status_code=422)
    if not _ISBN10_RE.match(cleaned.upper()):
        raise AppError(code="VALIDATION_ERROR", message="Invalid ISBN-10 format", status_code=422)
    if not _check_isbn10_checksum(cleaned):
        raise AppError(code="VALIDATION_ERROR", message="Invalid ISBN-10 checksum", status_code=422)
    return cleaned.upper()


def normalize_isbn13(raw: str | None) -> str | None:
    if raw is None or not str(raw).strip():
        return None
    cleaned = re.sub(r"[^0-9]", "", raw.strip())
    if len(cleaned) != 13:
        raise AppError(code="VALIDATION_ERROR", message="ISBN-13 must be 13 digits", status_code=422)
    if not _ISBN13_RE.match(cleaned):
        raise AppError(code="VALIDATION_ERROR", message="ISBN-13 must start with 978 or 979", status_code=422)
    if not _check_isbn13_checksum(cleaned):
        raise AppError(code="VALIDATION_ERROR", message="Invalid ISBN-13 checksum", status_code=422)
    return cleaned


def validate_cover_reference(*, cover_url: str | None, cover_storage_key: str | None) -> None:
    if cover_url:
        url = cover_url.strip()
        if not (url.startswith("https://") or url.startswith("http://")):
            raise AppError(code="VALIDATION_ERROR", message="cover_url must be an http(s) URL", status_code=422)
        if len(url) > 2048:
            raise AppError(code="VALIDATION_ERROR", message="cover_url too long", status_code=422)
    if cover_storage_key:
        key = cover_storage_key.strip()
        if ".." in key or key.startswith("/"):
            raise AppError(code="VALIDATION_ERROR", message="Invalid cover_storage_key", status_code=422)