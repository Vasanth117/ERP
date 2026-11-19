"""Exam timetable conflict detection."""

from datetime import datetime
from typing import Any

from beanie import PydanticObjectId

from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableEntryStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetableEntry


def _normalize_instant(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def datetime_ranges_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    start_a = _normalize_instant(start_a)
    end_a = _normalize_instant(end_a)
    start_b = _normalize_instant(start_b)
    end_b = _normalize_instant(end_b)
    return start_a < end_b and start_b < end_a


def _entry_dict(entry: ExamTimetableEntry) -> dict[str, Any]:
    return {
        "entry_code": entry.entry_code,
        "course_code": entry.course_code,
        "student_group_label": entry.student_group_label,
        "scheduled_start": entry.scheduled_start.isoformat(),
        "scheduled_end": entry.scheduled_end.isoformat(),
        "centre_code": entry.centre_code,
        "room_label": entry.room_label,
        "facility_id": entry.facility_id,
    }


def detect_entry_conflicts(entries: list[ExamTimetableEntry]) -> list[dict[str, Any]]:
    active = [e for e in entries if e.status == ExamTimetableEntryStatus.ACTIVE]
    conflicts: list[dict[str, Any]] = []
    for i, left in enumerate(active):
        if left.scheduled_end <= left.scheduled_start:
            conflicts.append(
                {
                    "conflict_type": "invalid_duration",
                    "message": f"Invalid duration for entry {left.entry_code}",
                    "entry_code": left.entry_code,
                }
            )
        for right in active[i + 1 :]:
            if not datetime_ranges_overlap(
                left.scheduled_start,
                left.scheduled_end,
                right.scheduled_start,
                right.scheduled_end,
            ):
                continue
            if left.student_group_label == right.student_group_label:
                conflicts.append(
                    {
                        "conflict_type": "student_group_clash",
                        "message": f"Student group {left.student_group_label} has overlapping examinations",
                        "student_group_label": left.student_group_label,
                        "entries": [_entry_dict(left), _entry_dict(right)],
                    }
                )
            if (
                left.course_code == right.course_code
                and left.section == right.section
                and left.batch_label == right.batch_label
                and left.programme_code == right.programme_code
            ):
                conflicts.append(
                    {
                        "conflict_type": "subject_group_overlap",
                        "message": f"Overlapping examinations for {left.course_code}/{left.section or '—'}",
                        "entries": [_entry_dict(left), _entry_dict(right)],
                    }
                )
            room_left = (left.centre_code, left.room_label)
            room_right = (right.centre_code, right.room_label)
            if room_left[0] and room_left[1] and room_left == room_right:
                conflicts.append(
                    {
                        "conflict_type": "room_clash",
                        "message": f"Room {left.centre_code}/{left.room_label} is double-booked",
                        "entries": [_entry_dict(left), _entry_dict(right)],
                    }
                )
            if left.facility_id and right.facility_id and left.facility_id == right.facility_id:
                conflicts.append(
                    {
                        "conflict_type": "venue_clash",
                        "message": f"Facility {left.facility_id} is double-booked",
                        "entries": [_entry_dict(left), _entry_dict(right)],
                    }
                )
            if (
                left.course_code == right.course_code
                and left.paper_code
                and left.paper_code == right.paper_code
                and left.section == right.section
            ):
                conflicts.append(
                    {
                        "conflict_type": "duplicate_examination",
                        "message": f"Duplicate paper schedule for {left.course_code}/{left.paper_code}",
                        "entries": [_entry_dict(left), _entry_dict(right)],
                    }
                )
    return conflicts


async def load_timetable_entries(tenant_id: PydanticObjectId, timetable_id: PydanticObjectId) -> list[ExamTimetableEntry]:
    return await ExamTimetableEntry.find(
        {"tenant_id": tenant_id, "timetable_id": timetable_id},
    ).to_list()