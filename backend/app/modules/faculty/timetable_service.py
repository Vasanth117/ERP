"""Faculty timetable, sessions, and calendar."""

from datetime import date, datetime, time, timedelta, timezone

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.academics.enums import TimetableEntryStatus
from app.modules.academics.models import AcademicCalendarEvent, ClassSession
from app.modules.academics.repositories import AcademicQueryRepository
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.faculty.content_schemas import (
    CalendarEventRead,
    ClassSessionRead,
    ClassroomSummary,
    ExaminationScheduleRead,
    SessionUpdateRequestCreate,
    SessionUpdateRequestRead,
    TimetableChangeRead,
    TimetableDayRead,
    TimetableNotificationRead,
    TimetableSlotRead,
    TimetableWeekRead,
)
from app.modules.faculty.enums import FacultyActivityType, SessionUpdateRequestStatus
from app.modules.faculty.models import ClassSessionUpdateRequest, FacultyTimetableNotification
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.profile_service import ensure_faculty_profile
from app.modules.faculty.repositories import FacultyActivityRepository

_academic = AcademicQueryRepository()
_activity_repo = FacultyActivityRepository()


def _times_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and start_b < end_a


def _detect_conflicts(slots: list[TimetableSlotRead]) -> list[str]:
    conflicts: list[str] = []
    active = [s for s in slots if s.status not in {TimetableEntryStatus.CANCELLED.value}]
    for i, left in enumerate(active):
        for right in active[i + 1 :]:
            if left.day_of_week != right.day_of_week:
                continue
            if _times_overlap(left.start_time, left.end_time, right.start_time, right.end_time):
                conflicts.append(
                    f"{left.course_code}/{left.section} overlaps with {right.course_code}/{right.section} "
                    f"on day {left.day_of_week}"
                )
    return conflicts


def _map_timetable_slot(entry) -> TimetableSlotRead:
    return TimetableSlotRead(
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
        status=entry.status.value if hasattr(entry.status, "value") else str(entry.status),
    )


async def get_daily_timetable(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
) -> TimetableDayRead:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    anchor = anchor_date or date.today()
    day = anchor.weekday()
    entries = await _academic.timetable(tenant_id, user.id, day_of_week=day)
    slots = [_map_timetable_slot(e) for e in entries]
    conflicts = _detect_conflicts(slots)
    return TimetableDayRead(anchor_date=anchor, slots=slots, conflicts=conflicts)


async def get_weekly_timetable(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
) -> TimetableWeekRead:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    anchor = anchor_date or date.today()
    week_start = anchor - timedelta(days=anchor.weekday())
    all_slots: list[TimetableSlotRead] = []
    days: list[TimetableDayRead] = []
    for offset in range(7):
        current = week_start + timedelta(days=offset)
        day = current.weekday()
        entries = await _academic.timetable(tenant_id, user.id, day_of_week=day)
        slots = [_map_timetable_slot(e) for e in entries]
        all_slots.extend(slots)
        days.append(TimetableDayRead(anchor_date=current, slots=slots, conflicts=_detect_conflicts(slots)))
    return TimetableWeekRead(anchor_date=anchor, days=days, conflicts=_detect_conflicts(all_slots))


async def list_class_sessions(
    scope: AccessScope,
    user: User,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[ClassSessionRead]:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    from_dt = datetime.combine(from_date or date.today(), time.min, tzinfo=timezone.utc)
    to_dt = datetime.combine(to_date or (from_date or date.today()) + timedelta(days=7), time.max, tzinfo=timezone.utc)
    sessions = await _academic.class_sessions(tenant_id, user.id, from_time=from_dt, to_time=to_dt)
    return [_map_session(s) for s in sessions]


def _map_session(session: ClassSession) -> ClassSessionRead:
    return ClassSessionRead(
        id=str(session.id),
        course_code=session.course_code,
        section=session.section,
        session_type=session.session_type,
        scheduled_start=session.scheduled_start,
        scheduled_end=session.scheduled_end,
        room=session.room,
        laboratory=session.laboratory,
        status=session.status,
        topic=session.topic,
    )


async def list_classrooms(scope: AccessScope, user: User) -> list[ClassroomSummary]:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    entries = await _academic.timetable(tenant_id, user.id)
    counts: dict[tuple[str | None, str | None], int] = {}
    for entry in entries:
        key = (entry.room, entry.laboratory)
        counts[key] = counts.get(key, 0) + 1
    return [
        ClassroomSummary(room=room, laboratory=lab, session_count=count)
        for (room, lab), count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]


async def get_academic_calendar(scope: AccessScope, user: User, *, limit: int = 30) -> list[CalendarEventRead]:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    profile = await ensure_faculty_profile(scope, user)
    filters: dict = {
        "tenant_id": tenant_id,
        "event_at": {"$gte": datetime.now(timezone.utc)},
        "audience": {"$in": ["faculty", "all"]},
    }
    if profile.department_id:
        filters["$or"] = [{"department_id": profile.department_id}, {"department_id": None}]
    events = await AcademicCalendarEvent.find(filters).sort("event_at").limit(limit).to_list()
    return [
        CalendarEventRead(
            id=str(e.id),
            title=e.title,
            description=e.description,
            event_at=e.event_at,
            event_type=e.event_type,
        )
        for e in events
    ]


async def get_examination_schedules(scope: AccessScope, user: User) -> list[ExaminationScheduleRead]:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await _academic.examinations(tenant_id, user.id)
    return [
        ExaminationScheduleRead(
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


async def get_timetable_changes(scope: AccessScope, user: User) -> list[TimetableChangeRead]:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    changes = await _academic.timetable_changes(tenant_id, user.id)
    return [
        TimetableChangeRead(
            id=str(c.id),
            change_type=c.change_type,
            summary=c.summary,
            effective_at=c.effective_at,
            related_session_id=str(c.related_session_id) if c.related_session_id else None,
        )
        for c in changes
    ]


async def get_timetable_notifications(scope: AccessScope, user: User) -> list[TimetableNotificationRead]:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    docs = (
        await FacultyTimetableNotification.find({"tenant_id": tenant_id, "user_id": user.id})
        .sort("-created_at")
        .limit(30)
        .to_list()
    )
    return [
        TimetableNotificationRead(
            id=str(d.id),
            title=d.title,
            body=d.body,
            created_at=d.created_at,
            read_at=d.read_at,
        )
        for d in docs
    ]


async def list_cancelled_rescheduled_sessions(scope: AccessScope, user: User) -> list[ClassSessionRead]:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    sessions = await ClassSession.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "status": {"$in": ["cancelled", "rescheduled"]},
        }
    ).sort("-scheduled_start").limit(50).to_list()
    return [_map_session(s) for s in sessions]


async def get_session_history(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[ClassSessionRead]:
    authorize(scope, Permission.FACULTY_TIMETABLE_READ)
    tenant_id = require_faculty_scope(scope)
    query = ClassSession.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "status": "completed",
        }
    ).sort("-scheduled_start")
    total = await query.count()
    sessions = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_map_session(s) for s in sessions],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def submit_session_update_request(
    scope: AccessScope,
    user: User,
    session_id: PydanticObjectId,
    payload: SessionUpdateRequestCreate,
) -> SessionUpdateRequestRead:
    authorize(scope, Permission.FACULTY_SESSION_REQUEST)
    tenant_id = require_faculty_scope(scope)
    session = await ClassSession.get(session_id)
    if session is None or str(session.tenant_id) != str(tenant_id) or str(session.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Class session not found", status_code=404)
    body: dict = {}
    if payload.topic is not None:
        body["topic"] = payload.topic
    if payload.proposed_start is not None:
        body["proposed_start"] = payload.proposed_start.isoformat()
    if payload.proposed_end is not None:
        body["proposed_end"] = payload.proposed_end.isoformat()
    request = ClassSessionUpdateRequest(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        class_session_id=session_id,
        request_type=payload.request_type,
        status=SessionUpdateRequestStatus.PENDING,
        payload=body,
        reason=payload.reason,
    )
    await request.insert()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.SESSION_UPDATE_REQUESTED,
        title="Session update requested",
        metadata={"session_id": str(session_id), "request_type": payload.request_type.value},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.session_update.requested",
        resource_type="class_session_update_request",
        resource_id=str(request.id),
        tenant_id=tenant_id,
        metadata={"class_session_id": str(session_id)},
    )
    return SessionUpdateRequestRead(
        id=str(request.id),
        class_session_id=str(session_id),
        request_type=request.request_type,
        status=request.status.value,
        payload=request.payload,
        reason=request.reason,
        created_at=request.created_at,
    )
