"""Unified departmental request category identifiers."""

from __future__ import annotations

from app.core.exceptions import AppError

SECTION_TRANSFER = "section_transfer"
STUDENT_CORRECTION = "student_correction"
ATTENDANCE_CORRECTION = "attendance_correction"
TIMETABLE_CHANGE = "timetable_change"
SUBSTITUTE_FACULTY = "substitute_faculty"
FACULTY_ASSIGNMENT = "faculty_assignment"
COURSE_OFFERING = "course_offering"
PROFILE_CHANGE = "profile_change"
RESOURCE_REQUEST = "resource_request"

ALL_CATEGORIES = frozenset(
    {
        SECTION_TRANSFER,
        STUDENT_CORRECTION,
        ATTENDANCE_CORRECTION,
        TIMETABLE_CHANGE,
        SUBSTITUTE_FACULTY,
        FACULTY_ASSIGNMENT,
        COURSE_OFFERING,
        PROFILE_CHANGE,
        RESOURCE_REQUEST,
    }
)

DELEGATED_APPROVE_CATEGORIES = frozenset(
    {
        SECTION_TRANSFER,
        STUDENT_CORRECTION,
        ATTENDANCE_CORRECTION,
    }
)

SIMPLE_APPROVE_CATEGORIES = frozenset(
    {
        TIMETABLE_CHANGE,
        SUBSTITUTE_FACULTY,
        FACULTY_ASSIGNMENT,
        COURSE_OFFERING,
        RESOURCE_REQUEST,
    }
)

FORWARD_ONLY_APPROVE = frozenset({PROFILE_CHANGE})


def compose_request_id(category: str, source_oid: str) -> str:
    return f"{category}:{source_oid}"


def parse_request_id(request_id: str) -> tuple[str, str]:
    if ":" not in request_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid request_id format", status_code=422)
    category, source_id = request_id.split(":", 1)
    if category not in ALL_CATEGORIES:
        raise AppError(code="VALIDATION_ERROR", message="Unknown request category", status_code=422)
    return category, source_id