"""Parent–college meeting requests, availability, and appointments."""

from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.models import AcademicCalendarEvent
from app.modules.auth.models import User
from app.modules.parents.enums import (
    DEFAULT_PARENT_MEETING_CATEGORIES,
    ParentDataPermission,
    ParentMeetingAppointmentStatus,
    ParentMeetingRequestStatus,
)
from app.modules.parents.models import (
    ParentMeetingAppointment,
    ParentMeetingAvailabilityPolicy,
    ParentMeetingCategory,
    ParentMeetingFollowup,
    ParentMeetingHistory,
    ParentMeetingOutcome,
    ParentMeetingRequest,
)
from app.modules.parents.phase5_schemas import (
    ParentMeetingAppointmentRead,
    ParentMeetingCancelCreate,
    ParentMeetingCategoryRead,
    ParentMeetingDashboardRead,
    ParentMeetingOutcomeRead,
    ParentMeetingRepresentativeRead,
    ParentMeetingRequestCreate,
    ParentMeetingRequestRead,
    ParentMeetingRescheduleCreate,
    ParentMeetingSlotRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent
from app.modules.tenants.models import Department

_ACTIVE_APPOINTMENT = frozenset(
    {ParentMeetingAppointmentStatus.SCHEDULED.value, ParentMeetingAppointmentStatus.COMPLETED.value}
)
_OPEN_REQUEST = frozenset(
    {
        ParentMeetingRequestStatus.SUBMITTED.value,
        ParentMeetingRequestStatus.PENDING_STAFF.value,
        ParentMeetingRequestStatus.RESCHEDULE_REQUESTED.value,
    }
)


async def _ensure_categories(tenant_id: PydanticObjectId) -> list[ParentMeetingCategory]:
    existing = await ParentMeetingCategory.find({"tenant_id": tenant_id}).to_list()
    if existing:
        return [c for c in existing if c.active]
    for code, title in DEFAULT_PARENT_MEETING_CATEGORIES:
        await ParentMeetingCategory(
            tenant_id=tenant_id,
            category_code=code,
            title=title,
            requires_staff_selection=code in {"faculty", "hod", "class_advisor"},
        ).insert()
    return await ParentMeetingCategory.find({"tenant_id": tenant_id, "active": True}).to_list()


async def _policy(tenant_id: PydanticObjectId) -> ParentMeetingAvailabilityPolicy:
    row = await ParentMeetingAvailabilityPolicy.find_one({"tenant_id": tenant_id, "policy_id": "default"})
    if row is None:
        row = ParentMeetingAvailabilityPolicy(tenant_id=tenant_id)
        await row.insert()
    return row


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


async def _staff_busy(
    tenant_id: PydanticObjectId, staff_user_id: PydanticObjectId | None, start: datetime, end: datetime
) -> bool:
    if staff_user_id is None:
        return False
    overlap = await ParentMeetingAppointment.find_one(
        {
            "tenant_id": tenant_id,
            "staff_user_id": staff_user_id,
            "status": ParentMeetingAppointmentStatus.SCHEDULED.value,
            "scheduled_start": {"$lt": end},
            "scheduled_end": {"$gt": start},
        }
    )
    return overlap is not None


async def list_meeting_categories(scope: AccessScope, parent: User) -> list[ParentMeetingCategoryRead]:
    authorize(scope, Permission.PARENT_MEETING_READ)
    tenant_id = require_parent_scope(scope)
    cats = await _ensure_categories(tenant_id)
    return [
        ParentMeetingCategoryRead(
            category_code=c.category_code,
            title=c.title,
            requires_staff_selection=c.requires_staff_selection,
        )
        for c in cats
    ]


async def list_representatives(
    scope: AccessScope, parent: User, *, department_id: str | None = None
) -> list[ParentMeetingRepresentativeRead]:
    authorize(scope, Permission.PARENT_MEETING_READ)
    tenant_id = require_parent_scope(scope)
    filters: dict = {"tenant_id": tenant_id, "role": Role.FACULTY}
    if department_id:
        filters["department_id"] = PydanticObjectId(department_id)
    users = await User.find(filters).limit(100).to_list()
    dept_cache: dict[str, str] = {}
    items: list[ParentMeetingRepresentativeRead] = []
    for u in users:
        dept_name = None
        if u.department_id:
            key = str(u.department_id)
            if key not in dept_cache:
                dept = await Department.get(u.department_id)
                dept_cache[key] = dept.name if dept else ""
            dept_name = dept_cache[key]
        items.append(
            ParentMeetingRepresentativeRead(
                staff_user_id=str(u.id),
                full_name=u.full_name,
                department_id=str(u.department_id) if u.department_id else None,
                department_name=dept_name,
            )
        )
    return items


async def get_meeting_availability(
    scope: AccessScope,
    parent: User,
    *,
    on_date: date,
    staff_user_id: str | None = None,
) -> list[ParentMeetingSlotRead]:
    authorize(scope, Permission.PARENT_MEETING_READ)
    tenant_id = require_parent_scope(scope)
    policy = await _policy(tenant_id)
    if on_date.weekday() not in policy.weekdays:
        return []
    holiday = await AcademicCalendarEvent.find_one(
        {
            "tenant_id": tenant_id,
            "event_type": {"$in": ["holiday", "institution_holiday"]},
            "event_at": {
                "$gte": datetime.combine(on_date, time.min, tzinfo=timezone.utc),
                "$lt": datetime.combine(on_date + timedelta(days=1), time.min, tzinfo=timezone.utc),
            },
        }
    )
    if holiday:
        return []
    start_t = _parse_hhmm(policy.day_start)
    end_t = _parse_hhmm(policy.day_end)
    cursor = datetime.combine(on_date, start_t, tzinfo=timezone.utc)
    end_dt = datetime.combine(on_date, end_t, tzinfo=timezone.utc)
    staff_oid = PydanticObjectId(staff_user_id) if staff_user_id else None
    slots: list[ParentMeetingSlotRead] = []
    delta = timedelta(minutes=policy.slot_minutes)
    while cursor + delta <= end_dt:
        slot_end = cursor + delta
        busy = await _staff_busy(tenant_id, staff_oid, cursor, slot_end)
        slots.append(ParentMeetingSlotRead(slot_start=cursor, slot_end=slot_end, available=not busy))
        cursor = slot_end
    return slots


async def get_meeting_dashboard(
    scope: AccessScope, parent: User, *, student_user_id: str | None = None
) -> ParentMeetingDashboardRead:
    authorize(scope, Permission.PARENT_MEETING_READ)
    tenant_id = require_parent_scope(scope)
    req_filters: dict = {"tenant_id": tenant_id, "parent_user_id": parent.id}
    appt_filters: dict = {"tenant_id": tenant_id, "parent_user_id": parent.id}
    if student_user_id:
        sid = await resolve_student_for_parent(
            scope, parent, student_user_id, ParentDataPermission.REQUEST_MEETINGS
        )
        req_filters["student_user_id"] = sid
        appt_filters["student_user_id"] = sid
    requests = await ParentMeetingRequest.find(req_filters).to_list()
    appointments = await ParentMeetingAppointment.find(appt_filters).to_list()
    now = utcnow()
    upcoming = sum(
        1
        for a in appointments
        if a.status == ParentMeetingAppointmentStatus.SCHEDULED.value and a.scheduled_start > now
    )
    pending = sum(1 for r in requests if r.status in _OPEN_REQUEST)
    confirmed = sum(1 for r in requests if r.status == ParentMeetingRequestStatus.CONFIRMED.value)
    awaiting = sum(1 for r in requests if r.status == ParentMeetingRequestStatus.PENDING_STAFF.value)
    rescheduled = sum(1 for r in requests if r.status == ParentMeetingRequestStatus.RESCHEDULE_REQUESTED.value)
    cancelled = sum(1 for r in requests if r.status == ParentMeetingRequestStatus.CANCELLED.value)
    completed = sum(
        1 for a in appointments if a.status == ParentMeetingAppointmentStatus.COMPLETED.value
    )
    followups = 0
    for a in appointments:
        followups += await ParentMeetingFollowup.find(
            {"tenant_id": tenant_id, "appointment_id": a.appointment_id, "status": "open", "parent_visible": True}
        ).count()
    return ParentMeetingDashboardRead(
        upcoming=upcoming,
        pending_requests=pending,
        confirmed=confirmed,
        awaiting_staff=awaiting,
        rescheduled=rescheduled,
        cancelled=cancelled,
        completed=completed,
        followups_open=followups,
    )


async def create_meeting_request(
    scope: AccessScope, parent: User, student_user_id: str, payload: ParentMeetingRequestCreate
) -> ParentMeetingRequestRead:
    authorize(scope, Permission.PARENT_MEETING_MANAGE)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.REQUEST_MEETINGS)
    rel, _ = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.REQUEST_MEETINGS)
    cats = {c.category_code: c for c in await _ensure_categories(tenant_id)}
    if payload.category_code not in cats:
        raise AppError(code="VALIDATION_ERROR", message="Unknown meeting category", status_code=422)
    staff_oid = PydanticObjectId(payload.staff_user_id) if payload.staff_user_id else None
    if cats[payload.category_code].requires_staff_selection and staff_oid is None:
        raise AppError(code="VALIDATION_ERROR", message="Staff selection required", status_code=422)
    if await _staff_busy(tenant_id, staff_oid, payload.preferred_start, payload.preferred_end):
        raise AppError(code="CONFLICT", message="Selected slot is not available", status_code=409)
    request_id = f"mtg_{uuid4().hex[:12]}"
    dept_oid = PydanticObjectId(payload.department_id) if payload.department_id else None
    row = ParentMeetingRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        relationship_id=rel.id,
        category_code=payload.category_code,
        department_id=dept_oid,
        staff_user_id=staff_oid,
        purpose=payload.purpose.strip(),
        remarks=(payload.remarks or "").strip() or None,
        preferred_date=payload.preferred_date,
        preferred_start=payload.preferred_start,
        preferred_end=payload.preferred_end,
        alternate_preferences=payload.alternate_preferences,
        meeting_mode=payload.meeting_mode.value,
        supporting_document_refs=list(payload.supporting_document_refs),
        status=ParentMeetingRequestStatus.PENDING_STAFF.value,
    )
    await row.insert()
    await ParentMeetingHistory(
        tenant_id=tenant_id,
        request_id=request_id,
        from_status=None,
        to_status=row.status,
        note="Submitted by parent",
        changed_by=parent.id,
    ).insert()
    return _request_read(row)


async def list_meeting_requests(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentMeetingRequestRead]:
    authorize(scope, Permission.PARENT_MEETING_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.REQUEST_MEETINGS)
    rows = await ParentMeetingRequest.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-created_at").to_list()
    return [_request_read(r) for r in rows]


async def list_appointments(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentMeetingAppointmentRead]:
    authorize(scope, Permission.PARENT_MEETING_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.REQUEST_MEETINGS)
    rows = await ParentMeetingAppointment.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-scheduled_start").to_list()
    result: list[ParentMeetingAppointmentRead] = []
    for row in rows:
        outcome = await ParentMeetingOutcome.find_one(
            {"tenant_id": tenant_id, "appointment_id": row.appointment_id}
        )
        result.append(
            ParentMeetingAppointmentRead(
                appointment_id=row.appointment_id,
                request_id=row.request_id,
                category_code=row.category_code,
                scheduled_start=row.scheduled_start,
                scheduled_end=row.scheduled_end,
                meeting_mode=row.meeting_mode,
                venue_or_link=row.venue_or_link,
                parent_visible_agenda=row.parent_visible_agenda,
                status=row.status,
                outcome_summary=outcome.parent_visible_summary if outcome else None,
            )
        )
    return result


async def request_reschedule(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    request_id: str,
    payload: ParentMeetingRescheduleCreate,
) -> ParentMeetingRequestRead:
    authorize(scope, Permission.PARENT_MEETING_MANAGE)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.REQUEST_MEETINGS)
    row = await ParentMeetingRequest.find_one(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid, "request_id": request_id}
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Meeting request not found", status_code=404)
    if await _staff_busy(tenant_id, row.staff_user_id, payload.preferred_start, payload.preferred_end):
        raise AppError(code="CONFLICT", message="Slot not available", status_code=409)
    prev = row.status
    row.status = ParentMeetingRequestStatus.RESCHEDULE_REQUESTED.value
    row.preferred_start = payload.preferred_start
    row.preferred_end = payload.preferred_end
    row.updated_at = utcnow()
    await row.save()
    await ParentMeetingHistory(
        tenant_id=tenant_id,
        request_id=request_id,
        from_status=prev,
        to_status=row.status,
        note=payload.reason,
        changed_by=parent.id,
    ).insert()
    return _request_read(row)


async def cancel_meeting_request(
    scope: AccessScope, parent: User, student_user_id: str, request_id: str, payload: ParentMeetingCancelCreate
) -> ParentMeetingRequestRead:
    authorize(scope, Permission.PARENT_MEETING_MANAGE)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.REQUEST_MEETINGS)
    row = await ParentMeetingRequest.find_one(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid, "request_id": request_id}
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Meeting request not found", status_code=404)
    prev = row.status
    row.status = ParentMeetingRequestStatus.CANCELLED.value
    row.updated_at = utcnow()
    await row.save()
    if row.appointment_id:
        appt = await ParentMeetingAppointment.find_one(
            {"tenant_id": tenant_id, "appointment_id": row.appointment_id}
        )
        if appt and appt.status == ParentMeetingAppointmentStatus.SCHEDULED.value:
            appt.status = ParentMeetingAppointmentStatus.CANCELLED.value
            appt.cancellation_reason = payload.reason
            appt.cancelled_by = parent.id
            appt.updated_at = utcnow()
            await appt.save()
    await ParentMeetingHistory(
        tenant_id=tenant_id,
        request_id=request_id,
        appointment_id=row.appointment_id,
        from_status=prev,
        to_status=row.status,
        note=payload.reason,
        changed_by=parent.id,
    ).insert()
    return _request_read(row)


async def get_meeting_outcome(
    scope: AccessScope, parent: User, student_user_id: str, appointment_id: str
) -> ParentMeetingOutcomeRead:
    authorize(scope, Permission.PARENT_MEETING_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.REQUEST_MEETINGS)
    appt = await ParentMeetingAppointment.find_one(
        {
            "tenant_id": tenant_id,
            "parent_user_id": parent.id,
            "student_user_id": sid,
            "appointment_id": appointment_id,
        }
    )
    if appt is None:
        raise AppError(code="NOT_FOUND", message="Appointment not found", status_code=404)
    outcome = await ParentMeetingOutcome.find_one({"tenant_id": tenant_id, "appointment_id": appointment_id})
    if outcome is None:
        raise AppError(code="NOT_FOUND", message="Outcome not yet published", status_code=404)
    followups = await ParentMeetingFollowup.find(
        {"tenant_id": tenant_id, "appointment_id": appointment_id, "parent_visible": True}
    ).to_list()
    return ParentMeetingOutcomeRead(
        appointment_id=appointment_id,
        parent_visible_summary=outcome.parent_visible_summary,
        agreed_next_steps=outcome.agreed_next_steps,
        completed_at=outcome.completed_at,
        followups=[
            {
                "followup_id": f.followup_id,
                "description": f.description,
                "status": f.status,
                "target_date": f.target_date.isoformat() if f.target_date else None,
            }
            for f in followups
        ],
    )


def _request_read(row: ParentMeetingRequest) -> ParentMeetingRequestRead:
    return ParentMeetingRequestRead(
        request_id=row.request_id,
        category_code=row.category_code,
        status=row.status,
        purpose=row.purpose,
        meeting_mode=row.meeting_mode,
        preferred_start=row.preferred_start,
        preferred_end=row.preferred_end,
        appointment_id=row.appointment_id,
        rejection_reason=row.rejection_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )