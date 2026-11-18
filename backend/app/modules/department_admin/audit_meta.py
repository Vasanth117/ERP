"""Department audit metadata helpers (no app imports — safe for unit tests)."""

from __future__ import annotations

from typing import Any

from beanie import PydanticObjectId


def department_audit_metadata(
    central_department_id: PydanticObjectId,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {"central_department_id": str(central_department_id)}
    if extra:
        meta.update(extra)
    return meta