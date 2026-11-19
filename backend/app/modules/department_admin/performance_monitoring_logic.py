"""Pure helpers for department academic performance aggregates."""

from __future__ import annotations

FAIL_TOKENS = frozenset({"fail", "failed", "f"})
PASS_TOKENS = frozenset({"pass", "passed", "p", "o", "a"})


def normalize_pass_fail(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    token = str(value).strip().lower()
    if token in FAIL_TOKENS:
        return "fail"
    if token in PASS_TOKENS:
        return "pass"
    return "unknown"


def pass_percentage(passed: int, failed: int) -> float | None:
    denom = passed + failed
    if denom <= 0:
        return None
    return round((passed / denom) * 100.0, 2)


def period_label(*, academic_year_label: str | None, semester_label: str | None, season_id: str | None) -> str:
    if season_id:
        return season_id
    parts = [p for p in (academic_year_label, semester_label) if p]
    return "/".join(parts) if parts else "unspecified"


DEFAULT_SUPPORT_INDICATORS: frozenset[str] = frozenset(
    {
        "attendance_shortage",
        "published_subject_failure",
        "active_arrear",
        "academic_standing",
    }
)

PERFORMANCE_FOLLOW_UP_CATEGORIES: frozenset[str] = frozenset(
    {
        "attendance_shortage",
        "academic_failure",
        "arrear",
        "progression_review",
        "performance_support",
    }
)