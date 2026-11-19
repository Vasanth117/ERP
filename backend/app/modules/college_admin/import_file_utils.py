"""Safe CSV import parsing for college admin."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import re
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import AppError

FORMULA_PREFIX = re.compile(r"^[\s]*[=+\-@]")
IMPORT_EXTENSIONS = frozenset({".csv", ".xlsx"})
IMPORT_MIMES = frozenset(
    {
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)
MAX_IMPORT_BYTES = 5 * 1024 * 1024
MAX_IMPORT_ROWS = 10_000


def import_storage_base() -> Path:
    base = Path(get_settings().export_storage_path) / "institution_imports"
    base.mkdir(parents=True, exist_ok=True)
    return base


def validate_import_file(file_name: str, mime_type: str, size: int) -> None:
    if size <= 0 or size > MAX_IMPORT_BYTES:
        raise AppError(code="VALIDATION_ERROR", message="Import file size exceeds limit", status_code=422)
    ext = Path(file_name).suffix.lower()
    if ext not in IMPORT_EXTENSIONS:
        raise AppError(code="VALIDATION_ERROR", message="Only CSV and Excel extensions allowed", status_code=422)
    if mime_type not in IMPORT_MIMES and not mime_type.startswith("text/"):
        raise AppError(code="VALIDATION_ERROR", message="Unsupported import MIME type", status_code=422)


def parse_csv_bytes(raw: bytes, *, max_rows: int = MAX_IMPORT_ROWS) -> list[dict[str, str]]:
    if b"\x00" in raw[:4096]:
        raise AppError(code="VALIDATION_ERROR", message="Malformed file content", status_code=422)
    text = raw.decode("utf-8-sig")
    buf = io.StringIO(text)
    reader = csv.DictReader(buf)
    if not reader.fieldnames:
        raise AppError(code="VALIDATION_ERROR", message="CSV missing header row", status_code=422)
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(reader, start=2):
        if idx - 1 > max_rows:
            raise AppError(code="VALIDATION_ERROR", message="Row limit exceeded", status_code=422)
        clean = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
        rows.append(clean)
    return rows


def parse_import_content(content_base64: str, file_name: str) -> tuple[bytes, list[dict[str, str]]]:
    try:
        raw = base64.b64decode(content_base64, validate=True)
    except Exception as exc:
        raise AppError(code="VALIDATION_ERROR", message="Invalid base64 file content", status_code=422) from exc
    validate_import_file(file_name, "text/csv", len(raw))
    ext = Path(file_name).suffix.lower()
    if ext == ".xlsx":
        raise AppError(
            code="VALIDATION_ERROR",
            message="Excel imports require server-side conversion; upload CSV for this release",
            status_code=422,
        )
    return raw, parse_csv_bytes(raw)


def file_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_import_file(storage_key: str, data: bytes) -> None:
    path = import_storage_base() / storage_key
    path.parent.mkdir(parents=True, exist_ok=True)
    resolved = path.resolve()
    if not str(resolved).startswith(str(import_storage_base().resolve())):
        raise AppError(code="FORBIDDEN", message="Invalid storage path", status_code=403)
    path.write_bytes(data)