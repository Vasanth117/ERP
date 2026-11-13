"""Private student report artifact storage."""

import json
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import AppError


def _base_path() -> Path:
    base = Path(get_settings().student_report_storage_path)
    base.mkdir(parents=True, exist_ok=True)
    return base


def write_report_json(tenant_id: str, export_id: str, payload: dict) -> str:
    storage_key = f"{tenant_id}/reports/{export_id}_{uuid.uuid4().hex[:8]}.json"
    path = _base_path() / storage_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, default=str), encoding="utf-8")
    resolved = path.resolve()
    base = _base_path().resolve()
    if not str(resolved).startswith(str(base)):
        raise AppError(code="FORBIDDEN", message="Invalid storage path", status_code=403)
    return storage_key


def read_report_json(storage_key: str) -> dict:
    path = _base_path() / storage_key
    if not path.is_file():
        raise AppError(code="NOT_FOUND", message="Report file not found", status_code=404)
    return json.loads(path.read_text(encoding="utf-8"))
