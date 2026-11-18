"""Unit tests for examination readiness helpers."""

from app.modules.department_admin.examination_monitoring_logic import (
    ADVISORY_DISCLAIMER,
    READINESS_TYPE,
    all_required_met,
    pending_task_key,
    readiness_indicator,
)


def test_readiness_indicator_shape() -> None:
    row = readiness_indicator("semester_session_scheduled", True, "semester_examination_sessions")
    assert row["met"] is True
    assert row["code"] == "semester_session_scheduled"


def test_all_required_met() -> None:
    indicators = [
        readiness_indicator("a", True, "x"),
        readiness_indicator("b", False, "y"),
    ]
    assert all_required_met(indicators, {"a"}) is True
    assert all_required_met(indicators, {"a", "b"}) is False


def test_pending_task_key_dedup() -> None:
    assert pending_task_key("pending_marks_batch", "id1") != pending_task_key("open_coordination_issue", "id1")


def test_advisory_constants() -> None:
    assert READINESS_TYPE == "advisory"
    assert ADVISORY_DISCLAIMER