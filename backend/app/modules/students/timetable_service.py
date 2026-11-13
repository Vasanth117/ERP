"""Student timetable and academic calendar."""

from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.modules.academics.enums import SessionType, TimetableEntryStatus
from app.modules.auth.models import User
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.timetable_reader import (
    calendar_events_for_student,
    class_sessions_for_student,
    examination_schedules_for_student,
    faculty_for_course_section,
    timetable_changes_for_student,
    timetable_entries_for_student,
)
from app.modules.students.student_schedule_models import (
    AcademicCalendarReference,
    AttendanceNotificationRecord,
    StudentTimetableView,
)
from app.modules.students.student_schedule_schemas import (
    CalendarEventStudentRead,
    ClassSessionStudentRead,
    ExaminationScheduleStudentRead,
    FacultySlotInfo,
    StudentTimetableDayRead,
    StudentTimetableSemesterRead,
    StudentTimetableSlotRead,
    StudentTimetableWeekRead,
    TimetableChangeStudentRead,
    TimetableNotificationStudentRead,
)
from app.modules.students.policy import require_student_scope
from app.modules.students.profile_service import ensure_student_profile

_reader = StudentDataReader()


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        from app.core.exceptions import AppError

        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _timetable_prefs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> StudentTimetableView:
    row = await StudentTimetableView.find_one({"tenant_id": tenant_id, "user_id": user_id})
    if row is not None:
        return row
    row = StudentTimetableView(tenant_id=tenant_id, user_id=user_id)
    await row.insert()
    return row


async def _map_slot(
    tenant_id: PydanticObjectId,
    entry,
    *,
    year: str,
    semester: str,
    faculty_names: dict[str, str],
) -> StudentTimetableSlotRead:
    assignments = await faculty_for_course_section(
        tenant_id, course_code=entry.course_code, section=entry.section, year=year, semester=semester
    )
    faculty = [
        FacultySlotInfo(
            faculty_user_id=str(a.user_id),
            display_name=faculty_names.get(str(a.user_id), "Faculty"),
            role=a.assignment_role.value if hasattr(a.assignment_role, "value") else str(a.assignment_role),
        )
        for a in assignments
    ]
    status = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
    return StudentTimetableSlotRead(
        id=str(entry.id),
        day_of_week=entry.day_of_week,
        start_time=entry.start_time,
        end_time=entry.end_time,
        course_code=entry.course_code,
        course_name=entry.course_name,
        section=entry.section,
        session_type=entry.session_type,
        room=entry.room,
        laboratory=entry.laboratory,
        status=status,
        faculty=faculty,
    )


async def _slots_for_student(
    scope: AccessScope,
    user: User,
    *,
    day_of_week: int | None = None,
    course_code: str | None = None,
    session_type: SessionType | None = None,
) -> list[StudentTimetableSlotRead]:
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    prefs = await _timetable_prefs(tenant_id, user.id)
    entries = await timetable_entries_for_student(
        tenant_id,
        user.id,
        year=year,
        semester=semester,
        day_of_week=day_of_week,
        course_code=course_code or prefs.default_course_filter,
        session_type=SessionType.LABORATORY if prefs.show_laboratory_only else session_type,
        include_cancelled=not prefs.hide_cancelled,
    )
    faculty_ids: set[PydanticObjectId] = {e.faculty_user_id for e in entries}
    faculty_names: dict[str, str] = {}
    if faculty_ids:
        from app.modules.auth.models import User as AuthUser

        users = await AuthUser.find({"_id": {"$in": list(faculty_ids)}}).to_list()
        faculty_names = {str(u.id): u.full_name for u in users}
    return [await _map_slot(tenant_id, e, year=year, semester=semester, faculty_names=faculty_names) for e in entries]


async def get_daily_timetable(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
    course_code: str | None = None,
) -> StudentTimetableDayRead:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    anchor = anchor_date or date.today()
    slots = await _slots_for_student(scope, user, day_of_week=anchor.weekday(), course_code=course_code)
    return StudentTimetableDayRead(anchor_date=anchor, slots=slots)


async def get_weekly_timetable(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
    course_code: str | None = None,
) -> StudentTimetableWeekRead:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    anchor = anchor_date or date.today()
    week_start = anchor - timedelta(days=anchor.weekday())
    days: list[StudentTimetableDayRead] = []
    for offset in range(7):
        current = week_start + timedelta(days=offset)
        slots = await _slots_for_student(scope, user, day_of_week=current.weekday(), course_code=course_code)
        days.append(StudentTimetableDayRead(anchor_date=current, slots=slots))
    return StudentTimetableWeekRead(anchor_date=anchor, days=days)


async def get_semester_timetable(
    scope: AccessScope,
    user: User,
    *,
    course_code: str | None = None,
) -> StudentTimetableSemesterRead:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    all_slots = await _slots_for_student(scope, user, course_code=course_code)
    cancelled = [s for s in all_slots if s.status == TimetableEntryStatus.CANCELLED.value]
    rescheduled = [s for s in all_slots if s.status == TimetableEntryStatus.RESCHEDULED.value]
    active = [s for s in all_slots if s.status not in {TimetableEntryStatus.CANCELLED.value, TimetableEntryStatus.RESCHEDULED.value}]
    return StudentTimetableSemesterRead(
        academic_year_label=year,
        semester_label=semester,
        slots=active,
        cancelled_slots=cancelled,
        rescheduled_slots=rescheduled,
    )


async def get_academic_calendar(scope: AccessScope, user: User, *, limit: int = 50) -> list[CalendarEventStudentRead]:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, _ = await _term(tenant_id)
    profile = await ensure_student_profile(scope, user)
    from_time = datetime.now(timezone.utc)
    central = await calendar_events_for_student(
        tenant_id, year=year, from_time=from_time, limit=limit, department_id=profile.department_id
    )
    refs = await AcademicCalendarReference.find(
        {
            "tenant_id": tenant_id,
            "academic_year_label": year,
            "event_at": {"$gte": from_time},
            "audience": {"$in": ["students", "all", "student"]},
        }
    ).sort("event_at").limit(limit).to_list()
    if profile.programme_code:
        refs = [r for r in refs if r.programme_code is None or r.programme_code == profile.programme_code]
    items = [
        CalendarEventStudentRead(
            id=str(e.id),
            title=e.title,
            description=e.description,
            event_at=e.event_at,
            event_type=e.event_type,
            source="academic",
        )
        for e in central
    ]
    items.extend(
        CalendarEventStudentRead(
            id=str(r.id),
            title=r.title,
            description=r.description,
            event_at=r.event_at,
            event_type=r.event_type,
            source="reference",
        )
        for r in refs
    )
    items.sort(key=lambda x: x.event_at)
    return items[:limit]


async def get_examination_schedule(scope: AccessScope, user: User) -> list[ExaminationScheduleStudentRead]:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    rows = await examination_schedules_for_student(tenant_id, user.id, year=year, semester=semester)
    return [
        ExaminationScheduleStudentRead(
            id=str(r.id),
            title=r.title,
            course_code=r.course_code,
            section=r.section,
            exam_type=r.exam_type,
            scheduled_at=r.scheduled_at,
            room=r.room,
        )
        for r in rows
    ]


async def get_timetable_changes(scope: AccessScope, user: User) -> list[TimetableChangeStudentRead]:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    changes = await timetable_changes_for_student(tenant_id, user.id, year=year, semester=semester)
    return [
        TimetableChangeStudentRead(
            id=str(c.id),
            change_type=c.change_type,
            summary=c.summary,
            effective_at=c.effective_at,
            related_session_id=str(c.related_session_id) if c.related_session_id else None,
        )
        for c in changes
    ]


async def get_timetable_notifications(scope: AccessScope, user: User) -> list[TimetableNotificationStudentRead]:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    from app.modules.students.student_schedule_enums import AttendanceNotificationType

    docs = (
        await AttendanceNotificationRecord.find(
            {
                "tenant_id": tenant_id,
                "user_id": user.id,
                "notification_type": AttendanceNotificationType.TIMETABLE_CHANGE,
            }
        )
        .sort("-created_at")
        .limit(30)
        .to_list()
    )
    return [
        TimetableNotificationStudentRead(
            id=str(d.id),
            title=d.title,
            body=d.body,
            notification_type=d.notification_type.value,
            created_at=d.created_at,
            read_at=d.read_at,
        )
        for d in docs
    ]


async def list_cancelled_rescheduled_sessions(scope: AccessScope, user: User) -> list[ClassSessionStudentRead]:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    sessions = await class_sessions_for_student(
        tenant_id,
        user.id,
        year=year,
        semester=semester,
        from_date=date.today() - timedelta(days=30),
        to_date=date.today() + timedelta(days=60),
        statuses=["cancelled", "rescheduled"],
    )
    return [
        ClassSessionStudentRead(
            id=str(s.id),
            course_code=s.course_code,
            section=s.section,
            session_type=s.session_type,
            scheduled_start=s.scheduled_start,
            scheduled_end=s.scheduled_end,
            room=s.room,
            laboratory=s.laboratory,
            status=s.status,
            topic=s.topic,
        )
        for s in sessions
    ]


async def calendar_deadlines(scope: AccessScope, user: User, pagination: Pagination) -> Page[CalendarEventStudentRead]:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    items = await get_academic_calendar(scope, user, limit=200)
    deadline_types = {"deadline", "registration", "exam_period"}
    filtered = [i for i in items if i.event_type in deadline_types]
    chunk = filtered[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=chunk, total=len(filtered), limit=pagination.limit, offset=pagination.offset)
