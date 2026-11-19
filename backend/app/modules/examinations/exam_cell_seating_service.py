"""Examination cell — seating logistics and invigilation."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In
from pymongo.errors import DuplicateKeyError

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.repositories import InstitutionCampusRepository
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_seating_manage,
    authorize_examination_cell_seating_publish,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamRegistration, ExamRegistrationSubject
from app.modules.examinations.exam_cell_seating_enums import (
    ExamDutyHistoryAction,
    ExamDutyHistoryKind,
    ExamSeatingAllocationStatus,
    ExamSeatingPlanStatus,
    ExamSeatingPolicy,
)
from app.modules.examinations.exam_cell_seating_models import (
    ExamDutyHistory,
    ExamInvigilatorAssignment,
    ExamRoom,
    ExamSeatingAllocation,
    ExamSeatingPlan,
    ExamVenue,
)
from app.modules.examinations.exam_cell_seating_schemas import (
    ExamInvigilatorAssignRequest,
    ExamInvigilatorAssignmentRead,
    ExamRoomAttendanceRow,
    ExamRoomAttendanceSheet,
    ExamRoomCreate,
    ExamRoomRead,
    ExamSeatingAllocateRequest,
    ExamSeatingAllocationRead,
    ExamSeatingChangeRequest,
    ExamSeatingPlanCreate,
    ExamSeatingPlanRead,
    ExamSeatingPlanSummary,
    ExamVenueCreate,
    ExamVenueRead,
)
from app.modules.examinations.exam_cell_timetable_validation import assert_venue_assignment
from app.modules.examinations.semester_examination_models import ExaminationCentre
from app.modules.students.models import StudentProfile


_campus_repo = InstitutionCampusRepository()


def _venue_id() -> str:
    return f"exv_{uuid4().hex[:10]}"


def _room_id() -> str:
    return f"exr_{uuid4().hex[:10]}"


def _plan_id() -> str:
    return f"esp_{uuid4().hex[:10]}"


def _allocation_id() -> str:
    return f"esa_{uuid4().hex[:10]}"


def _assignment_id() -> str:
    return f"eiv_{uuid4().hex[:10]}"


async def _duty_history(
    tenant_id: PydanticObjectId,
    *,
    kind: ExamDutyHistoryKind,
    action: ExamDutyHistoryAction,
    plan_id: str | None,
    exam_session_id: PydanticObjectId | None,
    resource_id: str | None,
    actor_id: PydanticObjectId | None,
    note: str | None = None,
    metadata: dict | None = None,
) -> None:
    await ExamDutyHistory(
        tenant_id=tenant_id,
        history_id=f"edh_{uuid4().hex[:10]}",
        kind=kind,
        action=action,
        plan_id=plan_id,
        exam_session_id=exam_session_id,
        resource_id=resource_id,
        actor_id=actor_id,
        note=note,
        metadata=dict(metadata or {}),
    ).insert()


async def _session(tenant_id: PydanticObjectId, session_oid: PydanticObjectId) -> ExamSession:
    row = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, session_oid))
    if row is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    return row


async def create_exam_venue(scope: AccessScope, actor: User, payload: ExamVenueCreate) -> ExamVenueRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_seating_manage(scope)
    session_oid = to_object_id(payload.exam_session_id, "exam_session_id")
    await _session(tenant_id, session_oid)

    campus_oid: PydanticObjectId | None = None
    if payload.campus_id:
        campus_oid = to_object_id(payload.campus_id, "campus_id")
        if await _campus_repo.get_by_id(tenant_id, campus_oid) is None:
            raise AppError(code="VALIDATION_ERROR", message="Unknown campus", status_code=422)

    if payload.centre_code:
        centre = await ExaminationCentre.find_one(
            Eq(ExaminationCentre.tenant_id, tenant_id),
            Eq(ExaminationCentre.centre_code, payload.centre_code),
        )
        if centre is None or not centre.is_active:
            raise AppError(code="VALIDATION_ERROR", message="Unknown examination centre", status_code=422)

    doc = ExamVenue(
        tenant_id=tenant_id,
        venue_id=_venue_id(),
        exam_session_id=session_oid,
        name=payload.name.strip(),
        campus_id=campus_oid,
        centre_code=payload.centre_code,
        facility_id=payload.facility_id,
    )
    await doc.insert()
    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_venue_created",
        summary=f"Venue {doc.name} added",
        exam_session_id=session_oid,
    )
    return ExamVenueRead.from_doc(doc)


async def create_exam_room(scope: AccessScope, actor: User, payload: ExamRoomCreate) -> ExamRoomRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_seating_manage(scope)

    venue = await ExamVenue.find_one(Eq(ExamVenue.tenant_id, tenant_id), Eq(ExamVenue.venue_id, payload.venue_id))
    if venue is None or not venue.active:
        raise AppError(code="NOT_FOUND", message="Exam venue not found", status_code=404)

    if payload.usable_seating_capacity > payload.total_capacity:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Usable seating capacity cannot exceed total capacity",
            status_code=422,
        )

    campus_oid = await assert_venue_assignment(
        tenant_id,
        centre_code=venue.centre_code,
        room_label=payload.room_label,
        facility_id=payload.facility_id or venue.facility_id,
        campus_id=str(venue.campus_id) if venue.campus_id else payload.campus_id,
    )

    doc = ExamRoom(
        tenant_id=tenant_id,
        room_id=_room_id(),
        venue_id=venue.venue_id,
        exam_session_id=venue.exam_session_id,
        room_label=payload.room_label,
        campus_id=campus_oid or venue.campus_id,
        facility_id=payload.facility_id or venue.facility_id,
        department_code=payload.department_code,
        programme_code=payload.programme_code,
        total_capacity=payload.total_capacity,
        usable_seating_capacity=payload.usable_seating_capacity,
    )
    try:
        await doc.insert()
    except DuplicateKeyError as exc:
        raise AppError(code="CONFLICT", message="Room label already exists for this session", status_code=409) from exc

    await _duty_history(
        tenant_id,
        kind=ExamDutyHistoryKind.SEATING,
        action=ExamDutyHistoryAction.CREATED,
        plan_id=None,
        exam_session_id=venue.exam_session_id,
        resource_id=doc.room_id,
        actor_id=actor.id,
        note="Exam room configured",
    )
    return ExamRoomRead.from_doc(doc)


async def create_seating_plan(scope: AccessScope, actor: User, payload: ExamSeatingPlanCreate) -> ExamSeatingPlanRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_seating_manage(scope)
    session_oid = to_object_id(payload.exam_session_id, "exam_session_id")
    await _session(tenant_id, session_oid)

    doc = ExamSeatingPlan(
        tenant_id=tenant_id,
        plan_id=_plan_id(),
        exam_session_id=session_oid,
        title=payload.title.strip(),
        course_code=payload.course_code,
        timetable_entry_id=to_object_id(payload.timetable_entry_id, "timetable_entry_id") if payload.timetable_entry_id else None,
        seating_policy=payload.seating_policy,
        created_by=actor.id,
    )
    await doc.insert()
    await _duty_history(
        tenant_id,
        kind=ExamDutyHistoryKind.SEATING,
        action=ExamDutyHistoryAction.CREATED,
        plan_id=doc.plan_id,
        exam_session_id=session_oid,
        resource_id=doc.plan_id,
        actor_id=actor.id,
    )
    return ExamSeatingPlanRead.from_doc(doc)


async def _load_registrations(
    tenant_id: PydanticObjectId,
    session_oid: PydanticObjectId,
    course_code: str | None,
) -> list[tuple[PydanticObjectId, str]]:
    regs = await ExamRegistration.find(
        Eq(ExamRegistration.tenant_id, tenant_id),
        Eq(ExamRegistration.exam_session_id, session_oid),
        In(ExamRegistration.status, [ExamRegistrationStatus.CONFIRMED, ExamRegistrationStatus.SUBMITTED]),
    ).to_list()
    if not regs:
        return []

    reg_ids = [r.registration_id for r in regs]
    subject_filters = [
        Eq(ExamRegistrationSubject.tenant_id, tenant_id),
        Eq(ExamRegistrationSubject.exam_session_id, session_oid),
        In(ExamRegistrationSubject.registration_id, reg_ids),
    ]
    subjects = await ExamRegistrationSubject.find(*subject_filters).to_list()
    pairs: list[tuple[PydanticObjectId, str]] = []
    seen: set[tuple[str, str]] = set()
    for subj in subjects:
        if course_code and subj.course_code.upper() != course_code:
            continue
        key = (str(subj.student_user_id), subj.course_code.upper())
        if key in seen:
            continue
        seen.add(key)
        pairs.append((subj.student_user_id, subj.course_code.upper()))
    return pairs


async def allocate_seating(scope: AccessScope, actor: User, payload: ExamSeatingAllocateRequest) -> list[ExamSeatingAllocationRead]:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_seating_manage(scope)

    plan = await ExamSeatingPlan.find_one(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.plan_id, payload.plan_id))
    if plan is None:
        raise AppError(code="NOT_FOUND", message="Seating plan not found", status_code=404)
    if plan.status == ExamSeatingPlanStatus.PUBLISHED:
        raise AppError(code="PLAN_LOCKED", message="Published plans cannot be auto-allocated", status_code=409)

    rooms = await ExamRoom.find(
        Eq(ExamRoom.tenant_id, tenant_id),
        Eq(ExamRoom.exam_session_id, plan.exam_session_id),
        Eq(ExamRoom.active, True),
    ).sort("+room_label").to_list()
    if not rooms:
        raise AppError(code="VALIDATION_ERROR", message="No exam rooms configured for this session", status_code=422)

    candidates = await _load_registrations(tenant_id, plan.exam_session_id, payload.course_code or plan.course_code)
    if not candidates:
        raise AppError(code="VALIDATION_ERROR", message="No registered candidates to allocate", status_code=422)

    student_ids = [c[0] for c in candidates]
    profiles = {
        str(p.user_id): p
        for p in await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id), In(StudentProfile.user_id, student_ids)).to_list()
    }
    from app.modules.auth.models import User

    users = {
        str(u.id): u.full_name
        for u in await User.find(Eq(User.tenant_id, tenant_id), In(User.id, student_ids)).to_list()
    }

    if plan.seating_policy == ExamSeatingPolicy.PROGRAMME:
        candidates.sort(key=lambda row: (profiles.get(str(row[0])).programme_code if profiles.get(str(row[0])) else "", str(row[0])))
    elif plan.seating_policy == ExamSeatingPolicy.DEPARTMENT:
        candidates.sort(key=lambda row: (profiles.get(str(row[0])).programme_code if profiles.get(str(row[0])) else "", str(row[0])))
    else:
        candidates.sort(key=lambda row: str(row[0]))

    total_capacity = sum(room.usable_seating_capacity for room in rooms)
    if len(candidates) > total_capacity:
        raise AppError(
            code="CAPACITY_EXCEEDED",
            message=f"Need {len(candidates)} seats but only {total_capacity} usable capacity available",
            status_code=422,
        )

    await ExamSeatingAllocation.find(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.plan_id, plan.plan_id),
        Eq(ExamSeatingAllocation.status, ExamSeatingAllocationStatus.ALLOCATED),
    ).delete()

    results: list[ExamSeatingAllocationRead] = []
    candidate_index = 0
    for room in rooms:
        seat = 1
        while seat <= room.usable_seating_capacity and candidate_index < len(candidates):
            student_id, course = candidates[candidate_index]
            profile = profiles.get(str(student_id))
            doc = ExamSeatingAllocation(
                tenant_id=tenant_id,
                allocation_id=_allocation_id(),
                plan_id=plan.plan_id,
                exam_session_id=plan.exam_session_id,
                room_id=room.room_id,
                student_user_id=student_id,
                course_code=course,
                seat_number=seat,
                roll_number=profile.roll_number if profile else None,
                display_name=users.get(str(student_id)),
                programme_code=profile.programme_code if profile else None,
            )
            try:
                await doc.insert()
            except DuplicateKeyError as exc:
                raise AppError(code="CONFLICT", message="Seat allocation conflict detected", status_code=409) from exc
            results.append(ExamSeatingAllocationRead.from_doc(doc))
            candidate_index += 1
            seat += 1

    await _duty_history(
        tenant_id,
        kind=ExamDutyHistoryKind.SEATING,
        action=ExamDutyHistoryAction.ALLOCATED,
        plan_id=plan.plan_id,
        exam_session_id=plan.exam_session_id,
        resource_id=plan.plan_id,
        actor_id=actor.id,
        metadata={"allocated": len(results)},
    )
    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_seating_allocated",
        summary=f"Allocated {len(results)} seats for plan {plan.plan_id}",
        exam_session_id=plan.exam_session_id,
        metadata={"plan_id": plan.plan_id},
    )
    return results


async def change_seat_allocation(
    scope: AccessScope,
    actor: User,
    allocation_id: str,
    payload: ExamSeatingChangeRequest,
) -> ExamSeatingAllocationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_seating_manage(scope)

    doc = await ExamSeatingAllocation.find_one(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.allocation_id, allocation_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Allocation not found", status_code=404)

    plan = await ExamSeatingPlan.find_one(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.plan_id, doc.plan_id))
    if plan and plan.status == ExamSeatingPlanStatus.PUBLISHED:
        authorize_examination_cell_seating_publish(scope)

    room = await ExamRoom.find_one(Eq(ExamRoom.tenant_id, tenant_id), Eq(ExamRoom.room_id, payload.room_id))
    if room is None:
        raise AppError(code="NOT_FOUND", message="Target room not found", status_code=404)
    if payload.seat_number > room.usable_seating_capacity:
        raise AppError(code="VALIDATION_ERROR", message="Seat number exceeds room usable capacity", status_code=422)

    taken = await ExamSeatingAllocation.find_one(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.plan_id, doc.plan_id),
        Eq(ExamSeatingAllocation.room_id, payload.room_id),
        Eq(ExamSeatingAllocation.seat_number, payload.seat_number),
        Eq(ExamSeatingAllocation.status, ExamSeatingAllocationStatus.ALLOCATED),
    )
    if taken is not None and taken.allocation_id != allocation_id:
        raise AppError(code="CONFLICT", message="Seat already allocated", status_code=409)

    doc.room_id = payload.room_id
    doc.seat_number = payload.seat_number
    doc.status = ExamSeatingAllocationStatus.CHANGED
    doc.updated_at = utcnow()
    await doc.save()

    await _duty_history(
        tenant_id,
        kind=ExamDutyHistoryKind.SEATING,
        action=ExamDutyHistoryAction.CHANGED,
        plan_id=doc.plan_id,
        exam_session_id=doc.exam_session_id,
        resource_id=doc.allocation_id,
        actor_id=actor.id,
        note=payload.note,
    )
    return ExamSeatingAllocationRead.from_doc(doc)


async def submit_seating_plan(scope: AccessScope, actor: User, plan_id: str) -> ExamSeatingPlanRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_seating_manage(scope)
    plan = await ExamSeatingPlan.find_one(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.plan_id, plan_id))
    if plan is None:
        raise AppError(code="NOT_FOUND", message="Seating plan not found", status_code=404)
    if plan.status != ExamSeatingPlanStatus.DRAFT:
        raise AppError(code="INVALID_STATE", message="Only draft plans can be submitted", status_code=409)
    plan.status = ExamSeatingPlanStatus.PENDING_APPROVAL
    plan.updated_at = utcnow()
    await plan.save()
    await _duty_history(
        tenant_id,
        kind=ExamDutyHistoryKind.SEATING,
        action=ExamDutyHistoryAction.APPROVED,
        plan_id=plan.plan_id,
        exam_session_id=plan.exam_session_id,
        resource_id=plan.plan_id,
        actor_id=actor.id,
        note="Submitted for approval",
    )
    return ExamSeatingPlanRead.from_doc(plan)


async def publish_seating_plan(scope: AccessScope, actor: User, plan_id: str) -> ExamSeatingPlanRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_seating_publish(scope)
    plan = await ExamSeatingPlan.find_one(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.plan_id, plan_id))
    if plan is None:
        raise AppError(code="NOT_FOUND", message="Seating plan not found", status_code=404)
    if plan.status not in {ExamSeatingPlanStatus.DRAFT, ExamSeatingPlanStatus.PENDING_APPROVAL}:
        raise AppError(code="INVALID_STATE", message="Plan cannot be published from current status", status_code=409)

    count = await ExamSeatingAllocation.find(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.plan_id, plan.plan_id),
        In(ExamSeatingAllocation.status, [ExamSeatingAllocationStatus.ALLOCATED, ExamSeatingAllocationStatus.CHANGED]),
    ).count()
    if count == 0:
        raise AppError(code="VALIDATION_ERROR", message="Cannot publish plan without allocations", status_code=422)

    plan.status = ExamSeatingPlanStatus.PUBLISHED
    plan.published_at = utcnow()
    plan.approved_by = actor.id
    plan.updated_at = utcnow()
    await plan.save()
    await _duty_history(
        tenant_id,
        kind=ExamDutyHistoryKind.SEATING,
        action=ExamDutyHistoryAction.PUBLISHED,
        plan_id=plan.plan_id,
        exam_session_id=plan.exam_session_id,
        resource_id=plan.plan_id,
        actor_id=actor.id,
    )
    return ExamSeatingPlanRead.from_doc(plan)


async def assign_invigilator(scope: AccessScope, actor: User, payload: ExamInvigilatorAssignRequest) -> ExamInvigilatorAssignmentRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_seating_manage(scope)

    plan = await ExamSeatingPlan.find_one(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.plan_id, payload.plan_id))
    if plan is None:
        raise AppError(code="NOT_FOUND", message="Seating plan not found", status_code=404)

    room = await ExamRoom.find_one(Eq(ExamRoom.tenant_id, tenant_id), Eq(ExamRoom.room_id, payload.room_id))
    if room is None:
        raise AppError(code="NOT_FOUND", message="Room not found", status_code=404)

    faculty_id = to_object_id(payload.faculty_user_id, "faculty_user_id")
    doc = ExamInvigilatorAssignment(
        tenant_id=tenant_id,
        assignment_id=_assignment_id(),
        plan_id=payload.plan_id,
        exam_session_id=plan.exam_session_id,
        room_id=payload.room_id,
        faculty_user_id=faculty_id,
        duty_role=payload.duty_role,
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
    )
    try:
        await doc.insert()
    except DuplicateKeyError as exc:
        raise AppError(code="CONFLICT", message="Invigilator already assigned to this room", status_code=409) from exc

    await _duty_history(
        tenant_id,
        kind=ExamDutyHistoryKind.INVIGILATION,
        action=ExamDutyHistoryAction.ALLOCATED,
        plan_id=payload.plan_id,
        exam_session_id=plan.exam_session_id,
        resource_id=doc.assignment_id,
        actor_id=actor.id,
    )
    return ExamInvigilatorAssignmentRead.from_doc(doc)


async def room_attendance_sheet(scope: AccessScope, plan_id: str, room_id: str) -> ExamRoomAttendanceSheet:
    tenant_id = require_examination_cell_tenant(scope)

    room = await ExamRoom.find_one(Eq(ExamRoom.tenant_id, tenant_id), Eq(ExamRoom.room_id, room_id))
    if room is None:
        raise AppError(code="NOT_FOUND", message="Room not found", status_code=404)

    rows_db = await ExamSeatingAllocation.find(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.plan_id, plan_id),
        Eq(ExamSeatingAllocation.room_id, room_id),
        In(ExamSeatingAllocation.status, [ExamSeatingAllocationStatus.ALLOCATED, ExamSeatingAllocationStatus.CHANGED]),
    ).sort("+seat_number").to_list()

    rows = [
        ExamRoomAttendanceRow(
            seat_number=row.seat_number,
            student_user_id=str(row.student_user_id),
            roll_number=row.roll_number,
            display_name=row.display_name,
            course_code=row.course_code,
        )
        for row in rows_db
    ]
    return ExamRoomAttendanceSheet(plan_id=plan_id, room_id=room_id, room_label=room.room_label, rows=rows)


async def seating_plan_summary(scope: AccessScope, plan_id: str) -> ExamSeatingPlanSummary:
    tenant_id = require_examination_cell_tenant(scope)
    plan = await ExamSeatingPlan.find_one(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.plan_id, plan_id))
    if plan is None:
        raise AppError(code="NOT_FOUND", message="Seating plan not found", status_code=404)

    allocated = await ExamSeatingAllocation.find(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.plan_id, plan_id),
        In(ExamSeatingAllocation.status, [ExamSeatingAllocationStatus.ALLOCATED, ExamSeatingAllocationStatus.CHANGED]),
    ).count()
    rooms = await ExamRoom.find(
        Eq(ExamRoom.tenant_id, tenant_id),
        Eq(ExamRoom.exam_session_id, plan.exam_session_id),
        Eq(ExamRoom.active, True),
    ).to_list()
    capacity = sum(r.usable_seating_capacity for r in rooms)
    used_rooms = len({r.room_id for r in rooms if r.room_id})

    allocations = await ExamSeatingAllocation.find(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.plan_id, plan_id),
    ).to_list()
    used_rooms = len({a.room_id for a in allocations})
    return ExamSeatingPlanSummary(
        plan_id=plan_id,
        allocated_students=allocated,
        total_usable_capacity=capacity,
        rooms_used=used_rooms,
    )


async def list_plan_allocations(scope: AccessScope, plan_id: str) -> list[ExamSeatingAllocationRead]:
    tenant_id = require_examination_cell_tenant(scope)
    rows = await ExamSeatingAllocation.find(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.plan_id, plan_id),
    ).sort("+room_id", "+seat_number").to_list()
    return [ExamSeatingAllocationRead.from_doc(r) for r in rows]