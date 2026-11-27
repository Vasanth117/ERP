"""Student timetable and academic calendar."""

import calendar as calendar_mod
from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.common.ids import to_object_id
from app.common.mongo_time import _parse_time_value
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.academics.enums import SessionType, TimetableEntryStatus
from app.modules.academics.models import TimetableEntry
from app.modules.auth.models import User
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.timetable_reader import (
    calendar_events_for_student,
    class_sessions_for_student,
    examination_schedules_for_student,
    faculty_for_course_section,
    student_section_keys,
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
    TimetableOverviewHighlightRead,
    TimetableOverviewKpisRead,
    TimetableOverviewPageRead,
    TimetableOverviewTodayRowRead,
    TimetableCourseFilterOptionRead,
    TimetableDailyPageRead,
    TimetableDailySessionRowRead,
    TimetableLaboratoryPageRead,
    TimetableMonthlyDayCellRead,
    TimetableMonthlyPageRead,
    TimetableSessionDetailFieldRead,
    TimetableSessionDetailRead,
    TimetableWeeklyDayColumnRead,
    TimetableWeeklyPageRead,
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
        start_time=_parse_time_value(entry.start_time),
        end_time=_parse_time_value(entry.end_time),
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
        session_type=(
            session_type
            if session_type is not None
            else (SessionType.LABORATORY if prefs.show_laboratory_only else None)
        ),
        include_cancelled=not prefs.hide_cancelled,
    )
    faculty_ids: set[PydanticObjectId] = {e.faculty_user_id for e in entries}
    faculty_names: dict[str, str] = {}
    if faculty_ids:
        from app.modules.auth.models import User as AuthUser

        users = await AuthUser.find({"_id": {"$in": list(faculty_ids)}}).to_list()
        faculty_names = {str(u.id): u.full_name for u in users}
    return [await _map_slot(tenant_id, e, year=year, semester=semester, faculty_names=faculty_names) for e in entries]


def _session_type_label(session_type: SessionType | str) -> str:
    raw = session_type.value if hasattr(session_type, "value") else str(session_type)
    return raw.replace("_", " ").title()


def _faculty_display(faculty: list[FacultySlotInfo]) -> str:
    if not faculty:
        return "—"
    return faculty[0].display_name


async def get_timetable_overview(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
) -> TimetableOverviewPageRead:
    """ST 05.01 overview — aggregates institutional timetable data (same TimetableEntry / calendar as Department Admin)."""
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    anchor = anchor_date or date.today()
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)

    daily = await get_daily_timetable(scope, user, anchor_date=anchor)
    weekly = await get_weekly_timetable(scope, user, anchor_date=anchor)
    exams = await get_examination_schedule(scope, user)
    changes = await get_timetable_changes(scope, user)
    calendar = await get_academic_calendar(scope, user, limit=40)

    classes_today = len(daily.slots)
    classes_this_week = sum(len(day.slots) for day in weekly.days)

    now = datetime.now(timezone.utc)
    upcoming_exams = sorted((e for e in exams if e.scheduled_at >= now), key=lambda e: e.scheduled_at)
    next_exam = upcoming_exams[0] if upcoming_exams else None
    next_exam_label = next_exam.scheduled_at.strftime("%d %b") if next_exam else None
    next_exam_hint = (next_exam.exam_type or next_exam.title) if next_exam else None

    week_start = anchor - timedelta(days=anchor.weekday())
    changes_new = [c for c in changes if c.effective_at.date() >= week_start]
    changes_hint = "New" if changes_new else None

    today_rows: list[TimetableOverviewTodayRowRead] = []
    for slot in sorted(daily.slots, key=lambda s: s.start_time):
        room = slot.room or slot.laboratory or "—"
        today_rows.append(
            TimetableOverviewTodayRowRead(
                id=slot.id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                subject_label=slot.course_name or slot.course_code,
                session_type_label=_session_type_label(slot.session_type),
                room_label=room,
                faculty_label=_faculty_display(slot.faculty),
            )
        )

    highlights: list[TimetableOverviewHighlightRead] = []
    for change in changes[:4]:
        effective_day = change.effective_at.date()
        if effective_day == anchor:
            subtitle = "Updated today"
        else:
            subtitle = change.effective_at.strftime("Effective %d %b %Y")
        highlights.append(
            TimetableOverviewHighlightRead(
                id=change.id,
                kind="change",
                title=change.summary,
                subtitle=subtitle,
                badge_label="Changed",
                badge_tone="warning",
            )
        )

    holiday_types = {"holiday", "break", "vacation", "closure"}
    for event in calendar:
        if event.event_type.lower() not in holiday_types:
            continue
        highlights.append(
            TimetableOverviewHighlightRead(
                id=event.id,
                kind="holiday",
                title=event.title,
                subtitle=event.description,
                badge_label="Holiday",
                badge_tone="info",
            )
        )
        if len(highlights) >= 8:
            break

    sessions_word = "session" if classes_today == 1 else "sessions"
    footer = f"{classes_today} {sessions_word}"

    return TimetableOverviewPageRead(
        anchor_date=anchor,
        iso_week_number=anchor.isocalendar().week,
        academic_year_label=year,
        semester_label=semester,
        kpis=TimetableOverviewKpisRead(
            classes_today=classes_today,
            classes_this_week=classes_this_week,
            next_exam_label=next_exam_label,
            next_exam_hint=next_exam_hint,
            changes_count=len(changes),
            changes_new_count=len(changes_new),
            changes_hint=changes_hint,
        ),
        today_rows=today_rows,
        today_sessions_footer=footer,
        highlights=highlights,
    )


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


def _format_timetable_page_date(anchor: date) -> str:
    return anchor.strftime("%A, %d %b %Y")


def _slot_status_tone(status: str) -> str:
    if status == TimetableEntryStatus.CANCELLED.value:
        return "danger"
    if status == TimetableEntryStatus.RESCHEDULED.value:
        return "warning"
    return "muted"


def _slot_to_timeline_row(slot: StudentTimetableSlotRead) -> TimetableDailySessionRowRead:
    room = slot.room or slot.laboratory or "—"
    return TimetableDailySessionRowRead(
        slot_id=slot.id,
        start_time=slot.start_time,
        end_time=slot.end_time,
        course_code=slot.course_code,
        subject_label=slot.course_name or slot.course_code,
        session_type_label=_session_type_label(slot.session_type),
        room_label=room,
        faculty_label=_faculty_display(slot.faculty),
        status_label=slot.status.replace("_", " ").title(),
        status_tone=_slot_status_tone(slot.status),
    )


async def _course_filter_options(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    year: str,
    semester: str,
) -> list[TimetableCourseFilterOptionRead]:
    sections = await student_section_keys(tenant_id, user_id, year=year, semester=semester)
    codes = sorted({code for _, code, _ in sections})
    options = [TimetableCourseFilterOptionRead(value="", label="All courses")]
    options.extend(TimetableCourseFilterOptionRead(value=code, label=code) for code in codes)
    return options


async def _assert_slot_visible_to_student(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    entry: TimetableEntry,
    *,
    year: str,
    semester: str,
) -> None:
    sections = await student_section_keys(tenant_id, user_id, year=year, semester=semester)
    allowed = {(code, sec) for _, code, sec in sections}
    if (entry.course_code, entry.section) not in allowed:
        raise AppError(code="FORBIDDEN", message="Timetable slot not available for your enrollment", status_code=403)


async def get_timetable_session_detail(
    scope: AccessScope,
    user: User,
    slot_id: str,
    *,
    anchor_date: date | None = None,
) -> TimetableSessionDetailRead:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    anchor = anchor_date or date.today()
    entry = await TimetableEntry.get(to_object_id(slot_id, "slot id"))
    if entry is None or str(entry.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Timetable slot not found", status_code=404)
    await _assert_slot_visible_to_student(tenant_id, user.id, entry, year=year, semester=semester)

    faculty_names: dict[str, str] = {}
    from app.modules.auth.models import User as AuthUser

    users = await AuthUser.find({"_id": entry.faculty_user_id}).to_list()
    faculty_names = {str(u.id): u.full_name for u in users}
    slot = await _map_slot(tenant_id, entry, year=year, semester=semester, faculty_names=faculty_names)
    room = slot.room or slot.laboratory or "—"
    start_label = slot.start_time.strftime("%H:%M")
    end_label = slot.end_time.strftime("%H:%M")

    fields: list[TimetableSessionDetailFieldRead] = [
        TimetableSessionDetailFieldRead(label="Course", value=slot.course_code),
        TimetableSessionDetailFieldRead(label="Subject", value=slot.course_name or slot.course_code),
        TimetableSessionDetailFieldRead(label="Section", value=slot.section),
        TimetableSessionDetailFieldRead(label="Session type", value=_session_type_label(slot.session_type)),
        TimetableSessionDetailFieldRead(label="Date", value=anchor.strftime("%d %b %Y")),
        TimetableSessionDetailFieldRead(label="Time", value=f"{start_label} – {end_label}"),
        TimetableSessionDetailFieldRead(label="Room / Lab", value=room),
        TimetableSessionDetailFieldRead(label="Faculty", value=_faculty_display(slot.faculty)),
        TimetableSessionDetailFieldRead(label="Status", value=slot.status.replace("_", " ").title()),
    ]

    sessions = await class_sessions_for_student(
        tenant_id,
        user.id,
        year=year,
        semester=semester,
        from_date=anchor,
        to_date=anchor,
    )
    match = next(
        (
            s
            for s in sessions
            if s.course_code == entry.course_code
            and s.section == entry.section
            and anchor.weekday() == entry.day_of_week
        ),
        None,
    )
    if match and match.topic:
        fields.append(TimetableSessionDetailFieldRead(label="Topic", value=match.topic))

    headline = f"{slot.course_code} · {slot.course_name or slot.course_code}"
    sub = f"{start_label} – {end_label} · {room}"
    return TimetableSessionDetailRead(
        slot_id=slot.id,
        headline=headline,
        subheadline=sub,
        fields=fields,
    )


async def _session_detail_optional(
    scope: AccessScope,
    user: User,
    slot_id: str | None,
    anchor: date,
) -> TimetableSessionDetailRead | None:
    if not slot_id:
        return None
    try:
        return await get_timetable_session_detail(scope, user, slot_id, anchor_date=anchor)
    except AppError as exc:
        if exc.code == "NOT_FOUND":
            return None
        raise


async def get_timetable_daily_page(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
    course_code: str | None = None,
    slot_id: str | None = None,
) -> TimetableDailyPageRead:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    anchor = anchor_date or date.today()
    code_filter = course_code if course_code else None
    slots = await _slots_for_student(
        scope, user, day_of_week=anchor.weekday(), course_code=code_filter
    )
    rows = [_slot_to_timeline_row(s) for s in sorted(slots, key=lambda s: (s.start_time, s.course_code))]
    pick = slot_id or (rows[0].slot_id if rows else None)
    detail = await _session_detail_optional(scope, user, pick, anchor)
    count = len(rows)
    footer = f"{count} session{'s' if count != 1 else ''}"
    return TimetableDailyPageRead(
        page_subtitle=_format_timetable_page_date(anchor),
        anchor_date=anchor,
        prev_date=anchor - timedelta(days=1),
        next_date=anchor + timedelta(days=1),
        academic_year_label=year,
        semester_label=semester,
        course_filter_options=await _course_filter_options(tenant_id, user.id, year, semester),
        selected_course_code=course_code or None,
        timeline_rows=rows,
        timeline_footer=footer,
        session_detail=detail,
    )


async def get_timetable_weekly_page(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
    course_code: str | None = None,
) -> TimetableWeeklyPageRead:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    anchor = anchor_date or date.today()
    week_start = anchor - timedelta(days=anchor.weekday())
    week_end = week_start + timedelta(days=6)
    code_filter = course_code if course_code else None
    columns: list[TimetableWeeklyDayColumnRead] = []
    week_total = 0
    for offset in range(7):
        current = week_start + timedelta(days=offset)
        slots = await _slots_for_student(
            scope, user, day_of_week=current.weekday(), course_code=code_filter
        )
        rows = [_slot_to_timeline_row(s) for s in sorted(slots, key=lambda s: s.start_time)]
        week_total += len(rows)
        columns.append(
            TimetableWeeklyDayColumnRead(
                anchor_date=current,
                day_label=current.strftime("%A"),
                short_label=current.strftime("%d %b"),
                session_count=len(rows),
                slots=rows,
            )
        )
    subtitle = f"{week_start.strftime('%d %b')} – {week_end.strftime('%d %b %Y')}"
    return TimetableWeeklyPageRead(
        page_subtitle=subtitle,
        anchor_date=anchor,
        academic_year_label=year,
        semester_label=semester,
        course_filter_options=await _course_filter_options(tenant_id, user.id, year, semester),
        selected_course_code=course_code or None,
        days=columns,
        week_footer=f"{week_total} sessions this week",
    )


async def get_timetable_monthly_page(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
) -> TimetableMonthlyPageRead:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    anchor = anchor_date or date.today()
    month_start = anchor.replace(day=1)
    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today = date.today()
    weeks: list[list[TimetableMonthlyDayCellRead]] = []
    month_total = 0
    for week in calendar_mod.Calendar(firstweekday=0).monthdatescalendar(anchor.year, anchor.month):
        row: list[TimetableMonthlyDayCellRead] = []
        for day in week:
            in_month = day.month == anchor.month
            count = 0
            if in_month:
                slots = await _slots_for_student(scope, user, day_of_week=day.weekday())
                count = len(slots)
                month_total += count
            row.append(
                TimetableMonthlyDayCellRead(
                    anchor_date=day,
                    in_month=in_month,
                    day_number=day.day if in_month else None,
                    session_count=count if in_month else 0,
                    is_today=day == today,
                )
            )
        weeks.append(row)
    return TimetableMonthlyPageRead(
        page_subtitle=anchor.strftime("%B %Y"),
        anchor_date=month_start,
        academic_year_label=year,
        semester_label=semester,
        weekday_labels=weekday_labels,
        weeks=weeks,
        month_footer=f"{month_total} sessions in {anchor.strftime('%B')}",
    )


async def get_timetable_laboratory_page(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
    course_code: str | None = None,
    slot_id: str | None = None,
) -> TimetableLaboratoryPageRead:
    authorize(scope, Permission.STUDENT_TIMETABLE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    anchor = anchor_date or date.today()
    code_filter = course_code if course_code else None
    slots = await _slots_for_student(
        scope,
        user,
        day_of_week=anchor.weekday(),
        course_code=code_filter,
        session_type=SessionType.LABORATORY,
    )
    rows = [_slot_to_timeline_row(s) for s in sorted(slots, key=lambda s: s.start_time)]
    pick = slot_id or (rows[0].slot_id if rows else None)
    detail = await _session_detail_optional(scope, user, pick, anchor)
    count = len(rows)
    footer = f"{count} lab session{'s' if count != 1 else ''}"
    return TimetableLaboratoryPageRead(
        page_subtitle=f"{_format_timetable_page_date(anchor)} · Laboratory",
        anchor_date=anchor,
        prev_date=anchor - timedelta(days=1),
        next_date=anchor + timedelta(days=1),
        academic_year_label=year,
        semester_label=semester,
        course_filter_options=await _course_filter_options(tenant_id, user.id, year, semester),
        selected_course_code=course_code or None,
        timeline_rows=rows,
        timeline_footer=footer,
        session_detail=detail,
    )
