"""Barcode and status validation for physical copies."""

import re

from app.core.exceptions import AppError
from app.modules.library.library_enums import LibraryCopyStatus

_BARCODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]{3,63}$")

_NON_TRANSFERABLE_STATUSES = frozenset(
    {
        LibraryCopyStatus.ISSUED,
        LibraryCopyStatus.RESERVED,
    }
)


def normalize_barcode(raw: str) -> str:
    value = raw.strip()
    if not _BARCODE_RE.match(value):
        raise AppError(
            code="VALIDATION_ERROR",
            message="Barcode must be 4-64 alphanumeric characters (hyphens allowed)",
            status_code=422,
        )
    return value.upper()


def assert_transferable_status(status: LibraryCopyStatus) -> None:
    if status in _NON_TRANSFERABLE_STATUSES:
        raise AppError(
            code="CONFLICT",
            message=f"Copy in status '{status.value}' cannot be transferred",
            status_code=409,
        )