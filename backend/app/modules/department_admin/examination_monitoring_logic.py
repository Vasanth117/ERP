"""Pure helpers for examination readiness (advisory)."""

from __future__ import annotations

from typing import Any

ADVISORY_DISCLAIMER = "college_examination_administration"
READINESS_TYPE = "advisory"


def readiness_indicator(code: str, met: bool, source: str, detail: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"code": code, "met": met, "source": source}
    if detail:
        row["detail"] = detail
    return row


def all_required_met(indicators: list[dict[str, Any]], required_codes: set[str]) -> bool:
    by_code = {i["code"]: i["met"] for i in indicators}
    return all(by_code.get(code) is True for code in required_codes)


def pending_task_key(task_type: str, reference_id: str) -> str:
    return f"{task_type}:{reference_id}"