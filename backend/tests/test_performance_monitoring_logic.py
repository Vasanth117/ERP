"""Unit tests for performance monitoring helpers."""

from app.modules.department_admin.performance_monitoring_logic import (
    normalize_pass_fail,
    pass_percentage,
    period_label,
)


def test_normalize_pass_fail() -> None:
    assert normalize_pass_fail("FAIL") == "fail"
    assert normalize_pass_fail("pass") == "pass"
    assert normalize_pass_fail(None) is None


def test_pass_percentage_zero_denominator() -> None:
    assert pass_percentage(0, 0) is None
    assert pass_percentage(3, 1) == 75.0


def test_period_label_season() -> None:
    assert period_label(academic_year_label="2025", semester_label="odd", season_id="2025-ODD") == "2025-ODD"