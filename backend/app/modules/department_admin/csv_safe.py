"""CSV parsing and formula-injection safe export."""

from __future__ import annotations

import base64
import csv
import io
import re
from typing import Any

from app.core.exceptions import AppError

FORMULA_PREFIX = re.compile(r"^[\s]*[=+\-@]")


def sanitize_csv_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if FORMULA_PREFIX.match(text):
        return "'" + text
    return text


def rows_to_csv(rows: list[dict[str, Any]], fieldnames: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: sanitize_csv_cell(row.get(k)) for k in fieldnames})
    return buf.getvalue()


def parse_csv_base64(content_base64: str, *, max_rows: int = 5000, max_bytes: int = 2_000_000) -> list[dict[str, str]]:
    try:
        raw = base64.b64decode(content_base64, validate=True)
    except Exception as exc:
        raise AppError(code="VALIDATION_ERROR", message="Invalid base64 file content", status_code=422) from exc
    if len(raw) > max_bytes:
        raise AppError(code="VALIDATION_ERROR", message="File exceeds size limit", status_code=422)
    text = raw.decode("utf-8-sig")
    if "\x00" in text:
        raise AppError(code="VALIDATION_ERROR", message="Malformed file content", status_code=422)
    buf = io.StringIO(text)
    reader = csv.DictReader(buf)
    if not reader.fieldnames:
        raise AppError(code="VALIDATION_ERROR", message="CSV missing header row", status_code=422)
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(reader, start=2):
        if idx - 1 > max_rows:
            raise AppError(code="VALIDATION_ERROR", message=f"Row limit {max_rows} exceeded", status_code=422)
        rows.append({k.strip(): (v or "").strip() for k, v in row.items() if k})
    return rows


def encode_csv_base64(csv_text: str) -> str:
    return base64.b64encode(csv_text.encode("utf-8")).decode("ascii")