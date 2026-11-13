"""Private local export artifact storage."""

import hashlib
import json
from pathlib import Path

from app.core.config import get_settings


def _base_path() -> Path:
    base = Path(get_settings().export_storage_path)
    base.mkdir(parents=True, exist_ok=True)
    return base


def storage_key_for(tenant_id: str, job_id: str, fmt: str) -> str:
    return f"{tenant_id}/{job_id}/export.{fmt}"


def write_json_export(storage_key: str, payload: dict) -> tuple[int, str]:
    path = _base_path() / storage_key
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, default=str).encode("utf-8")
    path.write_bytes(data)
    checksum = hashlib.sha256(data).hexdigest()
    return len(data), checksum


def read_artifact_bytes(storage_key: str) -> bytes:
    path = _base_path() / storage_key
    if not path.is_file():
        from app.core.exceptions import AppError

        raise AppError(code="NOT_FOUND", message="Export artifact not found", status_code=404)
    resolved = path.resolve()
    base = _base_path().resolve()
    if not str(resolved).startswith(str(base)):
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Invalid artifact path", status_code=403)
    return path.read_bytes()
