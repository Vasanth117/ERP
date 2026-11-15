"""Determine whether attendance submission is expected for a scheduled class."""

from datetime import date, datetime, time

from beanie import PydanticObjectId

from app.modules.academics.enums import TimetableEntryStatus
from app.modules.academics.models import ClassSession, TimetableEntry
from app.modules.attendance.enums import AttendanceSessionStatus
from app.modules.attendance.models import AttendanceSession

# Matches faculty `list_cancelled_rescheduled_sessions` query.
EXCLUDED_CLASS_SESSION_STATUSES = frozenset({"cancelled", "rescheduled"})

# Timetable entries that do not require attendance capture for the recurring slot.
EXCLUDED_TIMETABLE_STATUSES = frozenset(
    {TimetableEntryStatus.CANCELLED, TimetableEntryStatus.RESCHEDULED}
)


def _day_bounds(session_date: date) -> tuple[datetime, datetime]:
    return datetime.combine(session_date, time.min), datetime.combine(session_date, time.max)


async def is_attendance_submission_expected(
    tenant_id: PydanticObjectId,
    *,
    faculty_user_id: PydanticObjectId,
    course_code: str,
    section: str,
    session_date: date,
) -> tuple[bool, str]:
    """Return (expected, reason_code). When expected is False, missing attendance is not applicable."""

    submitted = await AttendanceSession.find_one(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": faculty_user_id,
            "course_code": course_code.upper(),
            "section": section.upper(),
            "session_date": session_date,
            "status": AttendanceSessionStatus.SUBMITTED,
        }
    )
    if submitted is not None:
        return False, "already_submitted"

    start, end = _day_bounds(session_date)
    class_sessions = await ClassSession.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": faculty_user_id,
            "course_code": course_code.upper(),
            "section": section.upper(),
            "scheduled_start": {"$gte": start, "$lte": end},
        }
    ).to_list()
    for row in class_sessions:
        if row.status in EXCLUDED_CLASS_SESSION_STATUSES:
            return False, f"class_session_{row.status}"

    cancelled_slots = await TimetableEntry.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": faculty_user_id,
            "course_code": course_code.upper(),
            "section": section.upper(),
            "day_of_week": session_date.weekday(),
            "status": {"$in": [s.value for s in EXCLUDED_TIMETABLE_STATUSES]},
        }
    ).count()
    if cancelled_slots > 0:
        return False, "timetable_slot_excluded"

    return True, "expected"


async def filter_pending_requiring_submission(
    tenant_id: PydanticObjectId,
    rows: list,
) -> list:
    """Filter PendingAttendanceSubmission rows that still require faculty submission."""
    kept: list = []
    for row in rows:
        course_code = getattr(row, "class_label", None) or getattr(row, "course_code", "")
        expected, _ = await is_attendance_submission_expected(
            tenant_id,
            faculty_user_id=row.faculty_user_id,
            course_code=course_code,
            section=row.section,
            session_date=row.session_date,
        )
        if expected:
            kept.append(row)
    return kept