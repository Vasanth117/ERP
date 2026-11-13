"""Student timetable reads from central academics collections."""

from datetime import date, datetime, time, timedelta, timezone

from beanie import PydanticObjectId

from app.modules.academics.enums import SessionType, TimetableEntryStatus
from app.modules.academics.models import (
    AcademicCalendarEvent,
    ClassSession,
    ExaminationSchedule,
    TimetableChangeLog,
    TimetableEntry,
)
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment
from app.modules.students.integrations.data_reader import StudentDataReader

_reader = StudentDataReader()


def _slot_key(course_code: str, section: str) -> tuple[str, str]:
    return course_code, section


async def student_section_keys(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[tuple[str, str, str]]:
    """Returns list of (course_id, course_code, section_code)."""
    roster = await _reader.roster_entries(
        tenant_id, student_user_id, academic_year_label=year, semester_label=semester
    )
    return [(r.course_id, r.course_code, r.section_code) for r in roster]


async def timetable_entries_for_student(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    day_of_week: int | None = None,
    course_code: str | None = None,
    session_type: SessionType | None = None,
    include_cancelled: bool = True,
) -> list[TimetableEntry]:
    sections = await student_section_keys(tenant_id, student_user_id, year=year, semester=semester)
    if not sections:
        return []
    or_clauses = [{"course_code": code, "section": sec} for _, code, sec in sections]
    filters: dict = {
        "tenant_id": tenant_id,
        "academic_year_label": year,
        "semester_label": semester,
        "$or": or_clauses,
    }
    if day_of_week is not None:
        filters["day_of_week"] = day_of_week
    if course_code is not None:
        filters["course_code"] = course_code
    if session_type is not None:
        filters["session_type"] = session_type
    if not include_cancelled:
        filters["status"] = TimetableEntryStatus.ACTIVE
    return await TimetableEntry.find(filters).sort([("day_of_week", 1), ("start_time", 1)]).to_list()


async def faculty_for_course_section(
    tenant_id: PydanticObjectId,
    *,
    course_code: str,
    section: str,
    year: str,
    semester: str,
) -> list[FacultyAssignment]:
    return await FacultyAssignment.find(
        {
            "tenant_id": tenant_id,
            "course_code": course_code,
            "section": section,
            "academic_year_label": year,
            "semester_label": semester,
            "status": AssignmentStatus.ACTIVE,
        }
    ).to_list()


async def class_sessions_for_student(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    from_date: date | None = None,
    to_date: date | None = None,
    statuses: list[str] | None = None,
) -> list[ClassSession]:
    sections = await student_section_keys(tenant_id, student_user_id, year=year, semester=semester)
    if not sections:
        return []
    course_codes = {code for _, code, _ in sections}
    from_dt = datetime.combine(from_date or date.today(), time.min, tzinfo=timezone.utc)
    to_dt = datetime.combine(to_date or (from_date or date.today()) + timedelta(days=1), time.max, tzinfo=timezone.utc)
    filters: dict = {
        "tenant_id": tenant_id,
        "course_code": {"$in": list(course_codes)},
        "academic_year_label": year,
        "semester_label": semester,
        "scheduled_start": {"$gte": from_dt, "$lte": to_dt},
    }
    if statuses:
        filters["status"] = {"$in": statuses}
    sessions = await ClassSession.find(filters).sort("scheduled_start").to_list()
    section_map = _slot_key
    allowed = {section_map(code, sec) for _, code, sec in sections}
    return [s for s in sessions if section_map(s.course_code, s.section) in allowed]


async def examination_schedules_for_student(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[ExaminationSchedule]:
    return await _reader.examination_schedule(
        tenant_id, student_user_id, academic_year_label=year, semester_label=semester, limit=50
    )


async def calendar_events_for_student(
    tenant_id: PydanticObjectId,
    *,
    year: str,
    from_time: datetime | None = None,
    limit: int = 50,
    department_id: PydanticObjectId | None = None,
) -> list[AcademicCalendarEvent]:
    filters: dict = {
        "tenant_id": tenant_id,
        "audience": {"$in": ["students", "all", "student"]},
    }
    if from_time is not None:
        filters["event_at"] = {"$gte": from_time}
    if department_id is not None:
        filters["$or"] = [{"department_id": department_id}, {"department_id": None}]
    return await AcademicCalendarEvent.find(filters).sort("event_at").limit(limit).to_list()


async def timetable_changes_for_student(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    limit: int = 30,
) -> list[TimetableChangeLog]:
    entries = await timetable_entries_for_student(
        tenant_id, student_user_id, year=year, semester=semester, include_cancelled=True
    )
    faculty_ids = {e.faculty_user_id for e in entries}
    if not faculty_ids:
        return []
    course_codes = {e.course_code for e in entries}
    rows = await TimetableChangeLog.find(
        {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
    ).sort("-effective_at").limit(limit * 3).to_list()
    filtered: list[TimetableChangeLog] = []
    for row in rows:
        summary = row.summary.lower()
        if any(code.lower() in summary for code in course_codes):
            filtered.append(row)
        if len(filtered) >= limit:
            break
    return filtered
