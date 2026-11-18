"""Timetable conflict detection for department plans."""

from datetime import time
from typing import Any

from beanie import PydanticObjectId

from app.modules.academics.enums import SessionType, TimetableEntryStatus
from app.modules.academics.models import TimetableEntry
from app.modules.department_admin.models import DepartmentTimetableSlot


def times_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and start_b < end_a


def _slot_dict(slot: DepartmentTimetableSlot) -> dict[str, Any]:
    return {
        "slot_id": str(slot.id),
        "faculty_user_id": str(slot.faculty_user_id),
        "section": slot.section,
        "course_code": slot.course_code,
        "day_of_week": slot.day_of_week,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "room": slot.room,
        "laboratory": slot.laboratory,
    }


def detect_slot_conflicts(slots: list[DepartmentTimetableSlot]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for i, left in enumerate(slots):
        if left.end_time <= left.start_time:
            conflicts.append(
                {
                    "conflict_type": "invalid_duration",
                    "message": f"Invalid duration for {left.course_code}/{left.section}",
                    "slot_id": str(left.id),
                }
            )
        for right in slots[i + 1 :]:
            if left.day_of_week != right.day_of_week:
                continue
            if not times_overlap(left.start_time, left.end_time, right.start_time, right.end_time):
                continue
            if left.faculty_user_id == right.faculty_user_id:
                conflicts.append(
                    {
                        "conflict_type": "faculty_overlap",
                        "message": f"Faculty overlap on day {left.day_of_week}",
                        "faculty_user_id": str(left.faculty_user_id),
                        "slots": [_slot_dict(left), _slot_dict(right)],
                    }
                )
            if left.section == right.section:
                conflicts.append(
                    {
                        "conflict_type": "section_overlap",
                        "message": f"Section {left.section} has overlapping sessions",
                        "section": left.section,
                        "slots": [_slot_dict(left), _slot_dict(right)],
                    }
                )
            if left.room and right.room and left.room == right.room:
                conflicts.append(
                    {
                        "conflict_type": "room_overlap",
                        "message": f"Room {left.room} double-booked",
                        "room": left.room,
                        "slots": [_slot_dict(left), _slot_dict(right)],
                    }
                )
            if left.laboratory and right.laboratory and left.laboratory == right.laboratory:
                conflicts.append(
                    {
                        "conflict_type": "laboratory_overlap",
                        "message": f"Laboratory {left.laboratory} double-booked",
                        "laboratory": left.laboratory,
                        "slots": [_slot_dict(left), _slot_dict(right)],
                    }
                )
            if (
                left.course_code == right.course_code
                and left.section == right.section
                and left.faculty_user_id == right.faculty_user_id
            ):
                conflicts.append(
                    {
                        "conflict_type": "duplicate_subject",
                        "message": f"Duplicate schedule for {left.course_code}/{left.section}",
                        "slots": [_slot_dict(left), _slot_dict(right)],
                    }
                )
    return conflicts


async def detect_external_conflicts(
    *,
    tenant_id: PydanticObjectId,
    faculty_user_id: PydanticObjectId,
    day_of_week: int,
    start_time: time,
    end_time: time,
    exclude_faculty_duplicate: bool = True,
) -> list[dict[str, Any]]:
    rows = await TimetableEntry.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": faculty_user_id,
            "day_of_week": day_of_week,
            "status": TimetableEntryStatus.ACTIVE,
        }
    ).to_list()
    found: list[dict[str, Any]] = []
    for entry in rows:
        if times_overlap(start_time, end_time, entry.start_time, entry.end_time):
            found.append(
                {
                    "conflict_type": "published_faculty_overlap",
                    "message": f"Overlaps published entry {entry.course_code}/{entry.section}",
                    "timetable_entry_id": str(entry.id),
                }
            )
    return found


def session_type_allowed(value: str) -> bool:
    return value in {SessionType.LECTURE.value, SessionType.LABORATORY.value, SessionType.TUTORIAL.value}