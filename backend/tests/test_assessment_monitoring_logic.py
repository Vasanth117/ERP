"""Unit tests for department assessment monitoring helpers."""

from datetime import datetime, timezone

import pytest

from app.modules.department_admin.assessment_monitoring_logic import (
    completion_state,
    deadline_from_metadata,
    overdue_flag,
    student_submission_status,
)
from app.modules.examinations.enums import MarksBatchStatus


def test_completion_state_when_all_approved() -> None:
    state = completion_state(
        faculty_enterable_component_ids=["c1", "c2"],
        batch_status_by_component={"c1": MarksBatchStatus.APPROVED, "c2": MarksBatchStatus.APPROVED},
        assessment_locked=False,
        final_results_published=False,
    )
    assert state == "completed"


def test_completion_state_pending() -> None:
    state = completion_state(
        faculty_enterable_component_ids=["c1"],
        batch_status_by_component={"c1": None},
        assessment_locked=False,
        final_results_published=False,
    )
    assert state == "pending"


def test_completion_state_locked_assessment() -> None:
    state = completion_state(
        faculty_enterable_component_ids=["c1"],
        batch_status_by_component={"c1": None},
        assessment_locked=True,
        final_results_published=False,
    )
    assert state == "completed"


def test_deadline_from_metadata_iso_string() -> None:
    raw = deadline_from_metadata({"submission_deadline": "2025-12-01T10:00:00+00:00"})
    assert raw is not None
    assert raw.year == 2025


def test_overdue_unknown_without_deadline() -> None:
    assert overdue_flag(deadline=None, submitted_at=None, batch_status=MarksBatchStatus.DRAFT) is None


def test_overdue_after_deadline_for_draft() -> None:
    deadline = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert overdue_flag(deadline=deadline, submitted_at=None, batch_status=MarksBatchStatus.DRAFT) is True


def test_student_submission_status_without_marks() -> None:
    assert student_submission_status(None, batch_exists=True) == "not_recorded"
    assert student_submission_status("draft", batch_exists=True) == "draft"


def test_phase5_filters_date_range() -> None:
    from app.modules.department_admin.phase5_schemas import AssessmentMonitoringFilters

    with pytest.raises(ValueError):
        AssessmentMonitoringFilters(
            date_from=datetime(2025, 2, 1, tzinfo=timezone.utc),
            date_to=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )