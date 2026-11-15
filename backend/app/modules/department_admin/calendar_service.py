"""Department Admin — calendar and events."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.enums import TimetableEntryStatus
from app.modules.academics.models import AcademicCalendarEvent, ClassSession, TimetableEntry
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin.calendar_conflict_detection import detect_calendar_conflicts
from app.modules.department_admin.department_scope import assert_faculty_visible_to_department
from app.modules.department_admin.integrations.department_data_reader import DepartmentDataReader
from app.modules.department_admin.models import (
    DepartmentCalendarChangeRecord,
    DepartmentCalendarEvent,
    DepartmentEventStatus,
)
from app.modules.department_admin.phase6_schemas import (
    CalendarCancelBody,
    CalendarConflictRead,
    CalendarEventCreate,
    CalendarEventRead,
    CalendarEventUpdate,
    CalendarFilters,
    CalendarOverviewRead,
    CollegeCalendarEventRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus

_reader = DepartmentDataReader()

VALID_CATEGORIES = frozenset(
    {
        "meeting",
        "faculty_meeting",
        "committee",
        "student_meeting",
        "seminar",
        "workshop",
        "project_review",
        "deadline",
        "internal_event",
        "general",
    }
)


def _event_read(doc: DepartmentCalendarEvent) -> CalendarEventRead:
    return CalendarEventRead(
        event_id=str(doc.id),
        title=doc.title,
        description=doc.description,
        category=doc.category,
        starts_at=doc.starts_at,
        ends_at=doc.ends_at,
        timezone=doc.timezone,
        venue=doc.venue,
        room=doc.room,
        laboratory=doc.laboratory,
        organizer_user_id=str(doc.organizer_user_id),
        responsible_faculty_user_id=str(doc.responsible_faculty_user_id) if doc.responsible_faculty_user_id else None,
        audience_scope=doc.audience_scope,
        programme_code=doc.programme_code,
        batch_label=doc.batch_label,
        section_code=doc.section_code,
        visibility=doc.visibility,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        related_course_code=doc.related_course_code,
        registration_required=doc.registration_required,
        status=doc.status,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _apply_filters(query: dict, filters: CalendarFilters, central_id: PydanticObjectId) -> dict:
    query["tenant_id"] = query.get("tenant_id")
    query["central_department_id"] = central_id
    if filters.status:
        query["status"] = filters.status.value
    else:
        query["status"] = {"$ne": DepartmentEventStatus.CANCELLED.value}
    if filters.category:
        query["category"] = filters.category
    if filters.programme_code:
        query["programme_code"] = filters.programme_code.upper()
    if filters.batch_label:
        query["batch_label"] = filters.batch_label
    if filters.section_code:
        query["section_code"] = filters.section_code.upper()
    if filters.audience_scope:
        query["audience_scope"] = filters.audience_scope
    if filters.academic_year_label:
        query["academic_year_label"] = filters.academic_year_label
    if filters.semester_label:
        query["semester_label"] = filters.semester_label
    if filters.date_from or filters.date_to:
        slot: dict = {}
        if filters.date_from:
            slot["$gte"] = filters.date_from
        if filters.date_to:
            slot["$lte"] = filters.date_to
        query["starts_at"] = slot
    return query


async def calendar_overview(
    scope: AccessScope,
    user: User,
    *,
    filters: CalendarFilters,
    pagination: Pagination,
) -> CalendarOverviewRead:
    authorize(scope, Permission.DEPARTMENT_CALENDAR_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    if filters.programme_code and filters.programme_code.upper() not in {c.upper() for c in institution.programme_codes}:
        raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    q = _apply_filters({"tenant_id": tenant_id}, filters, central_id)
    db_query = DepartmentCalendarEvent.find(q).sort("starts_at")
    total = await db_query.count()
    rows = await db_query.skip(pagination.offset).limit(pagination.limit).to_list()
    dept_items = [_event_read(r) for r in rows]
    from_time = filters.date_from or datetime.now(timezone.utc)
    to_time = filters.date_to or (from_time + timedelta(days=30))
    college_rows = await _reader.upcoming_department_events(tenant_id, central_id, from_time=from_time, to_time=to_time, limit=50)
    college_items = [
        CollegeCalendarEventRead(
            event_id=f"college:{row['title']}:{row['event_at']}",
            title=row["title"],
            description=None,
            event_at=datetime.fromisoformat(row["event_at"].replace("Z", "+00:00")),
            event_type=row.get("event_type", "general"),
            audience="college_or_department",
        )
        for row in college_rows
    ]
    return CalendarOverviewRead(department_events=dept_items, college_events=college_items, total_department=total)


async def list_calendar_events(
    scope: AccessScope,
    user: User,
    *,
    filters: CalendarFilters,
    pagination: Pagination,
) -> Page[CalendarEventRead]:
    authorize(scope, Permission.DEPARTMENT_CALENDAR_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    q = _apply_filters({"tenant_id": tenant_id}, filters, central_id)
    db_query = DepartmentCalendarEvent.find(q).sort("starts_at")
    total = await db_query.count()
    rows = await db_query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_event_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_calendar_event(scope: AccessScope, user: User, event_id: str) -> CalendarEventRead:
    authorize(scope, Permission.DEPARTMENT_CALENDAR_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentCalendarEvent.get(to_object_id(event_id, "event_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Event not found", status_code=404)
    return _event_read(doc)


async def create_calendar_event(scope: AccessScope, user: User, payload: CalendarEventCreate) -> CalendarEventRead:
    authorize(scope, Permission.DEPARTMENT_CALENDAR_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    if payload.category not in VALID_CATEGORIES:
        raise AppError(code="VALIDATION_ERROR", message="Unsupported event category", status_code=422)
    if payload.programme_code and payload.programme_code.upper() not in {c.upper() for c in institution.programme_codes}:
        raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    organizer = to_object_id(payload.organizer_user_id, "organizer_user_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, organizer)
    responsible = None
    if payload.responsible_faculty_user_id:
        responsible = to_object_id(payload.responsible_faculty_user_id, "responsible_faculty_user_id")
        await assert_faculty_visible_to_department(tenant_id, central_id, responsible)
    if payload.idempotency_key:
        existing = await DepartmentCalendarEvent.find_one(
            Eq(DepartmentCalendarEvent.tenant_id, tenant_id),
            Eq(DepartmentCalendarEvent.idempotency_key, payload.idempotency_key),
        )
        if existing and existing.central_department_id == central_id:
            return _event_read(existing)
    doc = DepartmentCalendarEvent(
        tenant_id=tenant_id,
        central_department_id=central_id,
        title=payload.title.strip(),
        description=payload.description,
        category=payload.category,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        timezone=payload.timezone,
        venue=payload.venue,
        room=payload.room,
        laboratory=payload.laboratory,
        organizer_user_id=organizer,
        responsible_faculty_user_id=responsible,
        audience_scope=payload.audience_scope,
        programme_code=payload.programme_code.upper() if payload.programme_code else None,
        batch_label=payload.batch_label,
        section_code=payload.section_code.upper() if payload.section_code else None,
        visibility=payload.visibility,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        related_course_code=payload.related_course_code.upper() if payload.related_course_code else None,
        registration_required=payload.registration_required,
        status=DepartmentEventStatus.DRAFT,
        idempotency_key=payload.idempotency_key,
        created_by=user.id,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.calendar_event.created",
        resource_type="department_calendar_event",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _event_read(doc)


async def update_calendar_event(
    scope: AccessScope,
    user: User,
    event_id: str,
    payload: CalendarEventUpdate,
) -> CalendarEventRead:
    authorize(scope, Permission.DEPARTMENT_CALENDAR_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentCalendarEvent.get(to_object_id(event_id, "event_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Event not found", status_code=404)
    if doc.status == DepartmentEventStatus.CANCELLED:
        raise AppError(code="FORBIDDEN", message="Cancelled events cannot be edited", status_code=403)
    before = {"starts_at": doc.starts_at.isoformat(), "ends_at": doc.ends_at.isoformat(), "room": doc.room}
    if payload.title is not None:
        doc.title = payload.title.strip()
    if payload.description is not None:
        doc.description = payload.description
    if payload.category is not None:
        if payload.category not in VALID_CATEGORIES:
            raise AppError(code="VALIDATION_ERROR", message="Unsupported event category", status_code=422)
        doc.category = payload.category
    if payload.starts_at is not None:
        doc.starts_at = payload.starts_at
    if payload.ends_at is not None:
        doc.ends_at = payload.ends_at
    if doc.ends_at <= doc.starts_at:
        raise AppError(code="VALIDATION_ERROR", message="ends_at must be after starts_at", status_code=422)
    if payload.venue is not None:
        doc.venue = payload.venue
    if payload.room is not None:
        doc.room = payload.room
    if payload.laboratory is not None:
        doc.laboratory = payload.laboratory
    if payload.responsible_faculty_user_id is not None:
        fid = to_object_id(payload.responsible_faculty_user_id, "responsible_faculty_user_id")
        await assert_faculty_visible_to_department(tenant_id, central_id, fid)
        doc.responsible_faculty_user_id = fid
    for field in ("audience_scope", "programme_code", "batch_label", "section_code", "visibility"):
        val = getattr(payload, field)
        if val is not None:
            setattr(doc, field, val.upper() if field in {"programme_code", "section_code"} and val else val)
    if payload.status is not None:
        doc.status = payload.status
    doc.updated_at = utcnow()
    doc.change_history.append(
        DepartmentCalendarChangeRecord(
            changed_by=user.id,
            change_type="update",
            reason=payload.change_reason,
            before=before,
            after={"starts_at": doc.starts_at.isoformat(), "ends_at": doc.ends_at.isoformat(), "room": doc.room},
        )
    )
    await doc.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.calendar_event.updated",
        resource_type="department_calendar_event",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _event_read(doc)


async def cancel_calendar_event(
    scope: AccessScope,
    user: User,
    event_id: str,
    body: CalendarCancelBody,
) -> CalendarEventRead:
    authorize(scope, Permission.DEPARTMENT_CALENDAR_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentCalendarEvent.get(to_object_id(event_id, "event_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Event not found", status_code=404)
    doc.status = DepartmentEventStatus.CANCELLED
    doc.change_history.append(
        DepartmentCalendarChangeRecord(
            changed_by=user.id,
            change_type="cancel",
            reason=body.reason,
            before={"status": "active"},
            after={"status": DepartmentEventStatus.CANCELLED.value},
        )
    )
    doc.updated_at = utcnow()
    await doc.save()
    key = f"dept_calendar_cancel:{doc.id}"
    if not await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)
    ):
        await DomainOutboxEvent(
            tenant_id=tenant_id,
            event_type="department.calendar.event_cancelled",
            aggregate_type="department_calendar_event",
            aggregate_id=str(doc.id),
            payload={"event_id": str(doc.id), "title": doc.title},
            idempotency_key=key,
            status=OutboxEventStatus.PENDING,
        ).insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.calendar_event.cancelled",
        resource_type="department_calendar_event",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _event_read(doc)


async def upcoming_calendar_events(
    scope: AccessScope,
    user: User,
    *,
    days: int,
    pagination: Pagination,
) -> Page[CalendarEventRead]:
    authorize(scope, Permission.DEPARTMENT_CALENDAR_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=min(max(days, 1), 90))
    q = {
        "tenant_id": tenant_id,
        "central_department_id": central_id,
        "starts_at": {"$gte": now, "$lte": end},
        "status": {"$in": [DepartmentEventStatus.PUBLISHED.value, DepartmentEventStatus.SCHEDULED.value]},
    }
    db_query = DepartmentCalendarEvent.find(q).sort("starts_at")
    total = await db_query.count()
    rows = await db_query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_event_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def calendar_conflicts(
    scope: AccessScope,
    user: User,
    *,
    event_id: str | None,
    starts_at: datetime | None,
    ends_at: datetime | None,
    room: str | None,
    laboratory: str | None,
    organizer_user_id: str | None,
) -> CalendarConflictRead:
    authorize(scope, Permission.DEPARTMENT_CALENDAR_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    if event_id:
        doc = await DepartmentCalendarEvent.get(to_object_id(event_id, "event_id"))
        if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
            raise AppError(code="NOT_FOUND", message="Event not found", status_code=404)
        starts_at = doc.starts_at
        ends_at = doc.ends_at
        room = doc.room
        laboratory = doc.laboratory
        organizer_user_id = str(doc.organizer_user_id)
    if starts_at is None or ends_at is None:
        raise AppError(code="VALIDATION_ERROR", message="starts_at and ends_at required", status_code=422)
    organizer_oid = to_object_id(organizer_user_id, "organizer_user_id") if organizer_user_id else None
    if organizer_oid:
        await assert_faculty_visible_to_department(tenant_id, central_id, organizer_oid)
    peers = await DepartmentCalendarEvent.find(
        {
            "tenant_id": tenant_id,
            "central_department_id": central_id,
            "starts_at": {"$lt": ends_at},
            "ends_at": {"$gt": starts_at},
        }
    ).to_list()
    timetable: list[TimetableEntry] = []
    sessions: list[ClassSession] = []
    if organizer_oid:
        timetable = await TimetableEntry.find(
            {
                "tenant_id": tenant_id,
                "faculty_user_id": organizer_oid,
                "status": TimetableEntryStatus.ACTIVE,
            }
        ).to_list()
        sessions = await ClassSession.find(
            {
                "tenant_id": tenant_id,
                "faculty_user_id": organizer_oid,
                "scheduled_start": {"$lt": ends_at},
                "scheduled_end": {"$gt": starts_at},
            }
        ).to_list()
    conflicts = detect_calendar_conflicts(
        event_id=event_id,
        starts_at=starts_at,
        ends_at=ends_at,
        room=room,
        laboratory=laboratory,
        organizer_faculty_id=organizer_oid,
        peer_events=peers,
        timetable_rows=timetable,
        class_sessions=sessions,
    )
    return CalendarConflictRead(conflicts=conflicts)