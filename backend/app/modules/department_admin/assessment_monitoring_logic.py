"""Pure helpers for department assessment and marks submission monitoring."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.modules.examinations.enums import AssessmentComponentType, MarksBatchStatus


COMPLETED_BATCH_STATUSES = frozenset({MarksBatchStatus.APPROVED})


def completion_state(
    *,
    faculty_enterable_component_ids: list[str],
    batch_status_by_component: dict[str, MarksBatchStatus | None],
    assessment_locked: bool,
    final_results_published: bool,
) -> str:
    if assessment_locked or final_results_published:
        return "completed"
    if not faculty_enterable_component_ids:
        return "not_applicable"
    missing = [
        cid
        for cid in faculty_enterable_component_ids
        if batch_status_by_component.get(cid) not in COMPLETED_BATCH_STATUSES
    ]
    if not missing:
        return "completed"
    any_started = any(batch_status_by_component.get(cid) is not None for cid in faculty_enterable_component_ids)
    return "in_progress" if any_started else "pending"


def deadline_from_metadata(metadata: dict[str, Any] | None) -> datetime | None:
    if not metadata:
        return None
    for key in ("submission_deadline", "due_at", "deadline"):
        raw = metadata.get(key)
        if raw is None:
            continue
        if isinstance(raw, datetime):
            return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        if isinstance(raw, str):
            try:
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def overdue_flag(
    *,
    deadline: datetime | None,
    submitted_at: datetime | None,
    batch_status: MarksBatchStatus | None,
) -> bool | None:
    if deadline is None:
        return None
    if batch_status in COMPLETED_BATCH_STATUSES:
        if submitted_at and submitted_at > deadline:
            return True
        return False
    now = datetime.now(timezone.utc)
    return now > deadline


def filter_date_range_valid(date_from: datetime | None, date_to: datetime | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from must be on or before date_to")


def batch_counts(statuses: list[MarksBatchStatus]) -> dict[str, int]:
    keys = [s.value for s in MarksBatchStatus]
    counts = {k: 0 for k in keys}
    for st in statuses:
        counts[st.value] = counts.get(st.value, 0) + 1
    return counts


def student_submission_status(mark_status: str | None, *, batch_exists: bool) -> str:
    if mark_status:
        return mark_status
    if batch_exists:
        return "not_recorded"
    return "no_batch"