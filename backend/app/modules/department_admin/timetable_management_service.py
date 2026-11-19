"""Department Admin timetable plans, validation, and publication."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.mongo_transactions import run_in_transaction
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.enums import SessionType, TimetableEntryStatus
from app.modules.academics.models import AcademicYearContext, TimetableEntry, TimetableChangeLog
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin.department_scope import (
    assert_course_in_department,
    assert_faculty_visible_to_department,
    department_course_codes,
    faculty_user_ids_in_department,
)
from app.modules.department_admin.models import (
    DepartmentRequestStatus,
    DepartmentTimetableChangeRequest,
    DepartmentTimetablePlan,
    DepartmentTimetablePublishSnapshot,
    DepartmentTimetableSlot,
    DepartmentTimetableStatus,
)
from app.modules.department_admin.phase4_schemas import (
    TimetableChangeCreate,
    TimetableChangeRead,
    TimetableConflictRead,
    TimetablePlanCreate,
    TimetablePlanRead,
    TimetablePlanUpdate,
    TimetablePublishBody,
    TimetableSlotCreate,
    TimetableSlotRead,
    TimetableSlotUpdate,
    TimetableValidationResult,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.department_admin.timetable_conflict import (
    detect_external_conflicts,
    detect_slot_conflicts,
    session_type_allowed,
)
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.models import LeaveRequest


def _plan_read(plan: DepartmentTimetablePlan, *, slot_count: int = 0) -> TimetablePlanRead:
    return TimetablePlanRead(
        timetable_id=str(plan.id),
        academic_year_label=plan.academic_year_label,
        semester_label=plan.semester_label,
        programme_code=plan.programme_code,
        batch_label=plan.batch_label,
        title=plan.title,
        status=plan.status,
        revision=plan.revision,
        published_version=plan.published_version,
        slot_count=slot_count,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def _slot_read(slot: DepartmentTimetableSlot) -> TimetableSlotRead:
    return TimetableSlotRead(
        slot_id=str(slot.id),
        plan_id=str(slot.plan_id),
        faculty_user_id=str(slot.faculty_user_id),
        section=slot.section,
        course_code=slot.course_code,
        course_name=slot.course_name,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time,
        session_type=slot.session_type,
        room=slot.room,
        laboratory=slot.laboratory,
        revision=slot.revision,
    )


async def _get_plan_for_dept(scope: AccessScope, user: User, plan_id: str) -> tuple[DepartmentTimetablePlan, PydanticObjectId]:
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    plan = await DepartmentTimetablePlan.get(to_object_id(plan_id, "timetable_id"))
    if plan is None or plan.tenant_id != tenant_id or plan.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Timetable plan not found", status_code=404)
    return plan, central_id


async def list_timetables(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[TimetablePlanRead]:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query = DepartmentTimetablePlan.find(
        Eq(DepartmentTimetablePlan.tenant_id, tenant_id),
        Eq(DepartmentTimetablePlan.central_department_id, central_id),
    )
    total = await query.count()
    rows = await query.sort("-updated_at").skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[TimetablePlanRead] = []
    for row in rows:
        slots = await DepartmentTimetableSlot.find(Eq(DepartmentTimetableSlot.plan_id, row.id)).count()
        items.append(_plan_read(row, slot_count=slots))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def create_timetable(scope: AccessScope, user: User, payload: TimetablePlanCreate) -> TimetablePlanRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = DepartmentTimetablePlan(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        central_department_id=central_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        programme_code=payload.programme_code.upper() if payload.programme_code else None,
        batch_label=payload.batch_label,
        title=payload.title,
        created_by=user.id,
        updated_by=user.id,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.timetable.create",
        resource_type="department_timetable_plan",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _plan_read(doc)


async def get_timetable(scope: AccessScope, user: User, plan_id: str) -> TimetablePlanRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_READ)
    plan, _ = await _get_plan_for_dept(scope, user, plan_id)
    slots = await DepartmentTimetableSlot.find(Eq(DepartmentTimetableSlot.plan_id, plan.id)).count()
    return _plan_read(plan, slot_count=slots)


async def update_timetable(scope: AccessScope, user: User, plan_id: str, payload: TimetablePlanUpdate) -> TimetablePlanRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_MANAGE)
    plan, _ = await _get_plan_for_dept(scope, user, plan_id)
    if plan.status not in {DepartmentTimetableStatus.DRAFT, DepartmentTimetableStatus.SUBMITTED}:
        raise AppError(code="FORBIDDEN", message="Only draft or submitted plans can be edited", status_code=403)
    if payload.title is not None:
        plan.title = payload.title
    if payload.programme_code is not None:
        plan.programme_code = payload.programme_code.upper()
    if payload.batch_label is not None:
        plan.batch_label = payload.batch_label
    plan.revision += 1
    plan.updated_by = user.id
    plan.updated_at = utcnow()
    await plan.save()
    slots = await DepartmentTimetableSlot.find(Eq(DepartmentTimetableSlot.plan_id, plan.id)).count()
    return _plan_read(plan, slot_count=slots)


async def list_plan_slots(scope: AccessScope, user: User, plan_id: str) -> list[TimetableSlotRead]:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_READ)
    plan, _ = await _get_plan_for_dept(scope, user, plan_id)
    rows = await DepartmentTimetableSlot.find(Eq(DepartmentTimetableSlot.plan_id, plan.id)).sort("+day_of_week", "+start_time").to_list()
    return [_slot_read(r) for r in rows]


async def add_slot(scope: AccessScope, user: User, plan_id: str, payload: TimetableSlotCreate) -> TimetableSlotRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_MANAGE)
    plan, central_id = await _get_plan_for_dept(scope, user, plan_id)
    if plan.status not in {DepartmentTimetableStatus.DRAFT, DepartmentTimetableStatus.SUBMITTED}:
        raise AppError(code="FORBIDDEN", message="Cannot modify slots on this plan status", status_code=403)
    tenant_id = plan.tenant_id
    if not session_type_allowed(payload.session_type):
        raise AppError(code="VALIDATION_ERROR", message="Invalid session_type", status_code=422)
    faculty_id = to_object_id(payload.faculty_user_id, "faculty_user_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, faculty_id)
    await assert_course_in_department(tenant_id, central_id, payload.course_code)
    slot = DepartmentTimetableSlot(
        plan_id=plan.id,
        tenant_id=tenant_id,
        central_department_id=central_id,
        faculty_user_id=faculty_id,
        programme_code=(payload.programme_code or plan.programme_code or "").upper() or None,
        batch_label=payload.batch_label or plan.batch_label,
        section=payload.section.upper(),
        course_code=payload.course_code.upper(),
        course_name=payload.course_name,
        course_id=payload.course_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        session_type=payload.session_type,
        room=payload.room,
        room_id=payload.room_id,
        laboratory=payload.laboratory,
    )
    await slot.insert()
    plan.updated_at = utcnow()
    await plan.save()
    return _slot_read(slot)


async def update_slot(scope: AccessScope, user: User, slot_id: str, payload: TimetableSlotUpdate) -> TimetableSlotRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_MANAGE)
    slot = await DepartmentTimetableSlot.get(to_object_id(slot_id, "slot_id"))
    if slot is None:
        raise AppError(code="NOT_FOUND", message="Slot not found", status_code=404)
    plan = await DepartmentTimetablePlan.get(slot.plan_id)
    if plan is None:
        raise AppError(code="NOT_FOUND", message="Plan not found", status_code=404)
    _, central_id = await _get_plan_for_dept(scope, user, str(plan.id))
    if plan.status not in {DepartmentTimetableStatus.DRAFT, DepartmentTimetableStatus.SUBMITTED}:
        raise AppError(code="FORBIDDEN", message="Cannot modify slots on this plan status", status_code=403)
    if payload.revision is not None and payload.revision != slot.revision:
        raise AppError(code="CONFLICT", message="Slot was modified by another user", status_code=409)
    tenant_id = slot.tenant_id
    for field in ("section", "course_code", "course_name", "day_of_week", "start_time", "end_time", "session_type", "room", "laboratory"):
        value = getattr(payload, field)
        if value is not None:
            setattr(slot, field, value.upper() if field == "section" else value)
    if payload.faculty_user_id is not None:
        faculty_id = to_object_id(payload.faculty_user_id, "faculty_user_id")
        await assert_faculty_visible_to_department(tenant_id, central_id, faculty_id)
        slot.faculty_user_id = faculty_id
    if payload.course_code is not None:
        await assert_course_in_department(tenant_id, central_id, payload.course_code)
        slot.course_code = payload.course_code.upper()
    if payload.session_type is not None and not session_type_allowed(payload.session_type):
        raise AppError(code="VALIDATION_ERROR", message="Invalid session_type", status_code=422)
    slot.revision += 1
    slot.updated_at = utcnow()
    await slot.save()
    return _slot_read(slot)


async def validate_timetable(scope: AccessScope, user: User, plan_id: str) -> TimetableValidationResult:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_READ)
    plan, central_id = await _get_plan_for_dept(scope, user, plan_id)
    tenant_id = plan.tenant_id
    slots = await DepartmentTimetableSlot.find(Eq(DepartmentTimetableSlot.plan_id, plan.id)).to_list()
    raw_conflicts = detect_slot_conflicts(slots)
    for slot in slots:
        raw_conflicts.extend(
            await detect_external_conflicts(
                tenant_id=tenant_id,
                faculty_user_id=slot.faculty_user_id,
                day_of_week=slot.day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
            )
        )
        on_leave = await LeaveRequest.find_one(
            {
                "tenant_id": tenant_id,
                "employee_user_id": slot.faculty_user_id,
                "status": LeaveRequestStatus.APPROVED.value,
            }
        )
        if on_leave:
            raw_conflicts.append(
                {
                    "conflict_type": "faculty_on_leave",
                    "message": "Faculty has approved leave overlapping timetable week (dept should verify dates)",
                    "faculty_user_id": str(slot.faculty_user_id),
                    "slot_id": str(slot.id),
                }
            )
    conflicts = [TimetableConflictRead(conflict_type=c["conflict_type"], message=c["message"], details=c) for c in raw_conflicts]
    return TimetableValidationResult(valid=not conflicts, conflicts=conflicts)


async def submit_timetable(scope: AccessScope, user: User, plan_id: str) -> TimetablePlanRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_MANAGE)
    validation = await validate_timetable(scope, user, plan_id)
    if not validation.valid:
        raise AppError(code="VALIDATION_ERROR", message="Timetable has conflicts", status_code=422)
    plan, _ = await _get_plan_for_dept(scope, user, plan_id)
    if plan.status != DepartmentTimetableStatus.DRAFT:
        raise AppError(code="CONFLICT", message="Only draft timetables can be submitted", status_code=409)
    plan.status = DepartmentTimetableStatus.SUBMITTED
    plan.updated_by = user.id
    plan.updated_at = utcnow()
    await plan.save()
    slots = await DepartmentTimetableSlot.find(Eq(DepartmentTimetableSlot.plan_id, plan.id)).count()
    return _plan_read(plan, slot_count=slots)


async def approve_timetable(scope: AccessScope, user: User, plan_id: str) -> TimetablePlanRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_MANAGE)
    plan, _ = await _get_plan_for_dept(scope, user, plan_id)
    if plan.status != DepartmentTimetableStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Timetable is not submitted", status_code=409)
    plan.status = DepartmentTimetableStatus.APPROVED
    plan.updated_by = user.id
    plan.updated_at = utcnow()
    await plan.save()
    slots = await DepartmentTimetableSlot.find(Eq(DepartmentTimetableSlot.plan_id, plan.id)).count()
    return _plan_read(plan, slot_count=slots)


async def _publish_entries(session, *, plan: DepartmentTimetablePlan, slots: list[DepartmentTimetableSlot], actor_id: PydanticObjectId) -> None:
    for slot in slots:
        entry = TimetableEntry(
            tenant_id=plan.tenant_id,
            faculty_user_id=slot.faculty_user_id,
            academic_year_label=plan.academic_year_label,
            semester_label=plan.semester_label,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            course_code=slot.course_code,
            course_name=slot.course_name,
            course_id=slot.course_id,
            section=slot.section,
            session_type=SessionType(slot.session_type) if slot.session_type in SessionType._value2member_map_ else SessionType.LECTURE,
            room=slot.room,
            room_id=slot.room_id,
            laboratory=slot.laboratory,
            status=TimetableEntryStatus.ACTIVE,
        )
        await entry.insert(session=session)
        await TimetableChangeLog(
            tenant_id=plan.tenant_id,
            faculty_user_id=slot.faculty_user_id,
            change_type="department_publish",
            summary=f"Published {slot.course_code}/{slot.section} via plan {plan.id}",
            effective_at=utcnow(),
            new_values={"timetable_entry_id": str(entry.id), "plan_id": str(plan.id)},
        ).insert(session=session)


async def publish_timetable(scope: AccessScope, user: User, plan_id: str, body: TimetablePublishBody) -> TimetablePlanRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_MANAGE)
    plan, _ = await _get_plan_for_dept(scope, user, plan_id)
    tenant_id = plan.tenant_id
    if plan.status != DepartmentTimetableStatus.APPROVED:
        raise AppError(code="CONFLICT", message="Timetable must be approved before publish", status_code=409)
    if body.idempotency_key:
        existing = await DepartmentTimetablePlan.find_one(
            Eq(DepartmentTimetablePlan.tenant_id, tenant_id),
            Eq(DepartmentTimetablePlan.publish_idempotency_key, body.idempotency_key),
        )
        if existing and existing.id != plan.id and existing.status == DepartmentTimetableStatus.PUBLISHED:
            return await get_timetable(scope, user, str(existing.id))
        if plan.publish_idempotency_key == body.idempotency_key and plan.status == DepartmentTimetableStatus.PUBLISHED:
            return await get_timetable(scope, user, plan_id)
    validation = await validate_timetable(scope, user, plan_id)
    if not validation.valid:
        raise AppError(code="VALIDATION_ERROR", message="Timetable has conflicts", status_code=422)
    slots = await DepartmentTimetableSlot.find(Eq(DepartmentTimetableSlot.plan_id, plan.id)).to_list()
    if not slots:
        raise AppError(code="VALIDATION_ERROR", message="Cannot publish empty timetable", status_code=422)

    previous_published = await DepartmentTimetablePlan.find(
        Eq(DepartmentTimetablePlan.tenant_id, tenant_id),
        Eq(DepartmentTimetablePlan.central_department_id, plan.central_department_id),
        Eq(DepartmentTimetablePlan.academic_year_label, plan.academic_year_label),
        Eq(DepartmentTimetablePlan.semester_label, plan.semester_label),
        Eq(DepartmentTimetablePlan.status, DepartmentTimetableStatus.PUBLISHED),
    ).to_list()

    async def _txn(mongo_session) -> None:
        for prev in previous_published:
            if prev.id != plan.id:
                prev.status = DepartmentTimetableStatus.SUPERSEDED
                prev.updated_at = utcnow()
                await prev.save(session=mongo_session)
        await _publish_entries(mongo_session, plan=plan, slots=slots, actor_id=user.id)
        plan.status = DepartmentTimetableStatus.PUBLISHED
        plan.published_version += 1
        plan.publish_idempotency_key = body.idempotency_key
        plan.updated_by = user.id
        plan.updated_at = utcnow()
        await plan.save(session=mongo_session)
        await DepartmentTimetablePublishSnapshot(
            tenant_id=tenant_id,
            plan_id=plan.id,
            version=plan.published_version,
            slot_payloads=[_slot_read(s).model_dump(mode="json") for s in slots],
            published_by=user.id,
        ).insert(session=mongo_session)

    try:
        from app.common.mongo_transactions import run_in_transaction

        await run_in_transaction(_txn)
    except AppError as exc:
        if exc.code == "TRANSACTIONS_UNAVAILABLE":
            raise AppError(
                code="TRANSACTIONS_UNAVAILABLE",
                message="MongoDB replica set required to publish timetables",
                status_code=503,
            ) from exc
        raise

    await record_department_audit(
        actor_id=user.id,
        action="department.timetable.publish",
        resource_type="department_timetable_plan",
        resource_id=str(plan.id),
        tenant_id=tenant_id,
        metadata={"version": plan.published_version, "slots": len(slots)},
        central_department_id=central_id,
    )
    return await get_timetable(scope, user, plan_id)


async def list_timetable_conflicts(scope: AccessScope, user: User, plan_id: str) -> list[TimetableConflictRead]:
    result = await validate_timetable(scope, user, plan_id)
    return result.conflicts


async def timetable_view_by_section(scope: AccessScope, user: User, section_code: str) -> list[TimetableSlotRead]:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    code = section_code.upper()
    slots = await DepartmentTimetableSlot.find(
        Eq(DepartmentTimetableSlot.tenant_id, tenant_id),
        Eq(DepartmentTimetableSlot.central_department_id, central_id),
        Eq(DepartmentTimetableSlot.section, code),
    ).to_list()
    if not slots:
        ctx = await AcademicYearContext.find_one(Eq(AcademicYearContext.tenant_id, tenant_id), Eq(AcademicYearContext.is_current, True))
        if ctx:
            entries = await TimetableEntry.find(
                {"tenant_id": tenant_id, "section": code, "academic_year_label": ctx.academic_year_label, "semester_label": ctx.semester_label}
            ).to_list()
            faculty_ids = await faculty_user_ids_in_department(tenant_id, central_id)
            return [
                TimetableSlotRead(
                    slot_id=str(e.id),
                    plan_id="published",
                    faculty_user_id=str(e.faculty_user_id),
                    section=e.section,
                    course_code=e.course_code,
                    course_name=e.course_name,
                    day_of_week=e.day_of_week,
                    start_time=e.start_time,
                    end_time=e.end_time,
                    session_type=e.session_type.value,
                    room=e.room,
                    laboratory=e.laboratory,
                    revision=1,
                )
                for e in entries
                if e.faculty_user_id in faculty_ids
            ]
    return [_slot_read(s) for s in slots]


async def timetable_view_by_faculty(scope: AccessScope, user: User, faculty_id: str) -> list[TimetableSlotRead]:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_oid = to_object_id(faculty_id, "faculty_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, faculty_oid)
    slots = await DepartmentTimetableSlot.find(
        Eq(DepartmentTimetableSlot.tenant_id, tenant_id),
        Eq(DepartmentTimetableSlot.faculty_user_id, faculty_oid),
    ).to_list()
    if slots:
        return [_slot_read(s) for s in slots]
    entries = await TimetableEntry.find(Eq(TimetableEntry.tenant_id, tenant_id), Eq(TimetableEntry.faculty_user_id, faculty_oid)).to_list()
    return [
        TimetableSlotRead(
            slot_id=str(e.id),
            plan_id="published",
            faculty_user_id=str(e.faculty_user_id),
            section=e.section,
            course_code=e.course_code,
            course_name=e.course_name,
            day_of_week=e.day_of_week,
            start_time=e.start_time,
            end_time=e.end_time,
            session_type=e.session_type.value,
            room=e.room,
            laboratory=e.laboratory,
            revision=1,
        )
        for e in entries
    ]


async def timetable_view_by_room(scope: AccessScope, user: User, room_id: str) -> list[TimetableSlotRead]:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_ids = list(await faculty_user_ids_in_department(tenant_id, central_id))
    slots = await DepartmentTimetableSlot.find(
        {
            "tenant_id": tenant_id,
            "central_department_id": central_id,
            "$or": [{"room": room_id}, {"room_id": room_id}, {"laboratory": room_id}],
        }
    ).to_list()
    if slots:
        return [_slot_read(s) for s in slots]
    entries = await TimetableEntry.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": {"$in": faculty_ids},
            "$or": [{"room": room_id}, {"room_id": room_id}, {"laboratory": room_id}],
        }
    ).to_list()
    return [
        TimetableSlotRead(
            slot_id=str(e.id),
            plan_id="published",
            faculty_user_id=str(e.faculty_user_id),
            section=e.section,
            course_code=e.course_code,
            course_name=e.course_name,
            day_of_week=e.day_of_week,
            start_time=e.start_time,
            end_time=e.end_time,
            session_type=e.session_type.value,
            room=e.room,
            laboratory=e.laboratory,
            revision=1,
        )
        for e in entries
    ]


async def create_timetable_change(scope: AccessScope, user: User, plan_id: str, payload: TimetableChangeCreate) -> TimetableChangeRead:
    authorize(scope, Permission.DEPARTMENT_TIMETABLE_MANAGE)
    plan, _ = await _get_plan_for_dept(scope, user, plan_id)
    slot_id = to_object_id(payload.slot_id, "slot_id") if payload.slot_id else None
    doc = DepartmentTimetableChangeRequest(
        tenant_id=plan.tenant_id,
        plan_id=plan.id,
        slot_id=slot_id,
        change_type=payload.change_type,
        reason=payload.reason,
        new_values=payload.new_values,
        requested_by=user.id,
    )
    await doc.insert()
    return TimetableChangeRead(
        request_id=str(doc.id),
        plan_id=str(plan.id),
        change_type=doc.change_type,
        status=doc.status,
        reason=doc.reason,
        created_at=doc.created_at,
    )