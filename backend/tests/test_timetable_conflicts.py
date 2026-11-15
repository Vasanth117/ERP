"""Timetable conflict detection unit tests."""

from datetime import time

from types import SimpleNamespace
from beanie import PydanticObjectId

from app.modules.department_admin.timetable_conflict import detect_slot_conflicts


def _slot(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": PydanticObjectId(),
        "faculty_user_id": PydanticObjectId(),
        "section": "A",
        "course_code": "CS101",
        "day_of_week": 1,
        "start_time": time(9, 0),
        "end_time": time(10, 0),
        "room": None,
        "laboratory": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_faculty_overlap_detected() -> None:
    faculty = PydanticObjectId()
    a = _slot(faculty_user_id=faculty)
    b = _slot(faculty_user_id=faculty, course_code="CS102", section="B")
    conflicts = detect_slot_conflicts([a, b])
    assert any(c["conflict_type"] == "faculty_overlap" for c in conflicts)


def test_no_conflict_different_days() -> None:
    faculty = PydanticObjectId()
    a = _slot(faculty_user_id=faculty, day_of_week=1)
    b = _slot(faculty_user_id=faculty, day_of_week=2)
    conflicts = detect_slot_conflicts([a, b])
    assert not conflicts