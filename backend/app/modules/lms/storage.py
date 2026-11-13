"""Private LMS file storage (tenant-scoped keys)."""

import hashlib
import re
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import AppError

ALLOWED_EXTENSIONS = frozenset({".pdf", ".ppt", ".pptx", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg"})
ALLOWED_MIME_PREFIXES = (
    "application/pdf",
    "application/vnd.",
    "application/msword",
    "text/plain",
    "image/",
)
MAX_BYTES = 15 * 1024 * 1024


def _base_path() -> Path:
    base = Path(get_settings().lms_storage_path)
    base.mkdir(parents=True, exist_ok=True)
    return base


def validate_upload(file_name: str, mime_type: str, size: int) -> None:
    if size <= 0 or size > MAX_BYTES:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"File size must be between 1 byte and {MAX_BYTES} bytes",
            status_code=422,
        )
    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(code="VALIDATION_ERROR", message="File type is not allowed", status_code=422)
    if not any(mime_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
        raise AppError(code="VALIDATION_ERROR", message="MIME type is not allowed", status_code=422)


def storage_key_for(tenant_id: str, category: str, file_name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", file_name)[:120]
    return f"{tenant_id}/{category}/{uuid.uuid4().hex}_{safe}"


def write_bytes(storage_key: str, data: bytes) -> tuple[str, str]:
    path = _base_path() / storage_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    resolved = path.resolve()
    base = _base_path().resolve()
    if not str(resolved).startswith(str(base)):
        raise AppError(code="FORBIDDEN", message="Invalid storage path", status_code=403)
    checksum = hashlib.sha256(data).hexdigest()
    return storage_key, checksum


def read_bytes(storage_key: str) -> bytes:
    path = _base_path() / storage_key
    if not path.is_file():
        raise AppError(code="NOT_FOUND", message="File not found", status_code=404)
    resolved = path.resolve()
    base = _base_path().resolve()
    if not str(resolved).startswith(str(base)):
        raise AppError(code="FORBIDDEN", message="Invalid file path", status_code=403)
    return path.read_bytes()
