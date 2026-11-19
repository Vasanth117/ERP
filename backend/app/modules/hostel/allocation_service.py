"""Hostel room and bed allocation services."""

from datetime import date
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import (
    HOSTEL_BED_HOLDING_ALLOCATION_STATUSES,
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBedStatus,
    HostelRoom,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.allocation_schemas import (
    AllocationCancel,
    AllocationConfirm,
    AllocationCreate,
    AllocationExtend,
    AllocationRead,
    AllocationTransferCreate,
)
from app.modules.hostel.application_models import HostelAllocationHistory, HostelRoomTransferRequest, HostelTransferStatus
from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.hostel_models import HostelApplication
from app.modules.hostel.hostel_notify import notify_hostel_student
from app.modules.hostel.infrastructure_models import InstitutionHostel
from app.modules.hostel.infrastructure_validation import norm_code
from app.modules.hostel.policy import (
    authorize_hostel_allocation_manage,
    authorize_hostel_allocation_read,
    require_hostel_tenant_scope,
)
from app.modules.students.models import StudentProfile


async def _allocation_history(
    tenant_id: PydanticObjectId,
    *,
    allocation_id: str,
    event_type: str,
    actor_id: PydanticObjectId | None,
    from_status: str | None = None,
    to_status: str | None = None,
    from_bed_id: str | None = None,
    to_bed_id: str | None = None,
    note: str | None = None,
    metadata: dict | None = None,
) -> None:
    await HostelAllocationHistory(
        tenant_id=tenant_id,
        allocation_id=allocation_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        from_bed_id=from_bed_id,
        to_bed_id=to_bed_id,
        note=note,
        metadata=metadata or {},
        actor_id=actor_id,
    ).insert()


async def _assert_student_eligible(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    application_id: str | None,
) -> tuple[User, StudentProfile | None, HostelApplication | None]:
    user = await User.find_one(Eq(User.tenant_id, tenant_id), Eq(User.id, student_user_id))
    if user is None:
        raise AppError(code="NOT_FOUND", message="Student not found", status_code=404)
    profile = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, student_user_id))
    app = None
    if application_id:
        app = await HostelApplication.find_one(
            Eq(HostelApplication.tenant_id, tenant_id),
            Eq(HostelApplication.application_id, application_id),
        )
        if app is None:
            raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
        if app.status not in (
            HostelApplicationStatus.APPROVED,
            HostelApplicationStatus.ACCEPTED,
            HostelApplicationStatus.SUBMITTED,
            HostelApplicationStatus.ALLOCATION_OFFERED,
        ):
            raise AppError(code="VALIDATION_ERROR", message="Application not eligible for allocation", status_code=422)
    holding_statuses = [HostelAllocationStatus(s) for s in HOSTEL_BED_HOLDING_ALLOCATION_STATUSES]
    holding = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.student_user_id, student_user_id),
        In(HostelAllocation.status, holding_statuses),
    )
    if holding:
        raise AppError(code="CONFLICT", message="Student already has an active allocation", status_code=409)
    return user, profile, app


async def _claim_bed(tenant_id: PydanticObjectId, bed_id: str, *, allocation_id: str) -> HostelBed:
    coll = HostelBed.get_motor_collection()
    now = utcnow()
    doc = await coll.find_one_and_update(
        {
            "tenant_id": tenant_id,
            "bed_id": bed_id,
            "status": HostelBedStatus.AVAILABLE.value,
        },
        {
            "$set": {
                "status": HostelBedStatus.ALLOCATED.value,
                "held_allocation_id": allocation_id,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, bed_id))
        if bed is None:
            raise AppError(code="NOT_FOUND", message="Bed not found", status_code=404)
        if bed.status in (HostelBedStatus.MAINTENANCE, HostelBedStatus.BLOCKED):
            raise AppError(code="CONFLICT", message="Bed is not available for allocation", status_code=409)
        raise AppError(code="CONFLICT", message="Bed is no longer available", status_code=409)
    return HostelBed.model_validate(doc)


async def _release_bed(tenant_id: PydanticObjectId, bed_id: str) -> None:
    coll = HostelBed.get_motor_collection()
    await coll.update_one(
        {"tenant_id": tenant_id, "bed_id": bed_id},
        {"$set": {"status": HostelBedStatus.AVAILABLE.value, "held_allocation_id": None, "updated_at": utcnow()}},
    )


def _allocation_read(doc: HostelAllocation) -> AllocationRead:
    return AllocationRead(
        allocation_id=doc.allocation_id,
        student_user_id=str(doc.student_user_id),
        application_id=doc.application_id,
        hostel_code=doc.hostel_code,
        bed_id=doc.bed_id,
        building_code=doc.building_code,
        block_code=doc.block_code,
        room_code=doc.room_code,
        bed_label=doc.bed_label,
        status=doc.status,
        start_date=doc.start_date,
        expected_end_date=doc.expected_end_date,
        allocation_reason=doc.allocation_reason,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def create_allocation_record(
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId | None,
    payload: AllocationCreate,
) -> AllocationRead:
    hostel_code = norm_code(payload.hostel_code)
    hostel = await InstitutionHostel.find_one(Eq(InstitutionHostel.tenant_id, tenant_id), Eq(InstitutionHostel.hostel_code, hostel_code))
    if hostel is None or not hostel.is_active:
        raise AppError(code="VALIDATION_ERROR", message="Hostel not active", status_code=422)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    student, _, app = await _assert_student_eligible(tenant_id, student_id, payload.application_id)
    if payload.start_date and payload.expected_end_date and payload.expected_end_date < payload.start_date:
        raise AppError(code="VALIDATION_ERROR", message="Invalid allocation date range", status_code=422)
    allocation_id = f"hal_{uuid4().hex[:12]}"
    bed = await _claim_bed(tenant_id, payload.bed_id.strip(), allocation_id=allocation_id)
    if bed.hostel_code and bed.hostel_code != hostel_code:
        await _release_bed(tenant_id, bed.bed_id)
        raise AppError(code="VALIDATION_ERROR", message="Bed does not belong to selected hostel", status_code=422)
    room = await HostelRoom.find_one(
        Eq(HostelRoom.tenant_id, tenant_id),
        Eq(HostelRoom.building_code, bed.building_code),
        Eq(HostelRoom.block_code, bed.block_code),
        Eq(HostelRoom.room_code, bed.room_code),
    )
    if room and room.operational_status != "active":
        await _release_bed(tenant_id, bed.bed_id)
        raise AppError(code="CONFLICT", message="Room is not active", status_code=409)
    status = HostelAllocationStatus.PENDING_APPROVAL if payload.require_approval else HostelAllocationStatus.CONFIRMED
    doc = HostelAllocation(
        tenant_id=tenant_id,
        allocation_id=allocation_id,
        student_user_id=student_id,
        application_id=payload.application_id,
        hostel_code=hostel_code,
        bed_id=bed.bed_id,
        building_code=bed.building_code,
        block_code=bed.block_code,
        room_code=bed.room_code,
        floor_id=room.floor_id if room else None,
        bed_label=bed.bed_label,
        status=status,
        allocation_reason=payload.allocation_reason,
        start_date=payload.start_date,
        expected_end_date=payload.expected_end_date,
        actor_id=actor_id,
    )
    try:
        await doc.insert()
    except DuplicateKeyError:
        await _release_bed(tenant_id, bed.bed_id)
        raise AppError(code="CONFLICT", message="Concurrent allocation conflict", status_code=409)
    if app:
        app.status = HostelApplicationStatus.COMPLETED
        app.allocation_id = allocation_id
        app.updated_at = utcnow()
        await app.save()
    await _allocation_history(
        tenant_id,
        allocation_id=allocation_id,
        event_type="created",
        actor_id=actor_id,
        to_status=status.value,
        to_bed_id=bed.bed_id,
        metadata={"student_user_id": str(student_id)},
    )
    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action="hostel.allocation.create",
        module="hostel",
        resource_type="hostel_allocation",
        resource_id=allocation_id,
    )
    await notify_hostel_student(
        tenant_id,
        student_user_id=student_id,
        event_type="allocation_created",
        title="Hostel allocation",
        body=f"Your hostel bed allocation {allocation_id} has been recorded.",
        aggregate_id=allocation_id,
    )
    from app.modules.hostel.resident_service import ensure_resident_from_allocation

    await ensure_resident_from_allocation(doc)
    _ = student
    return _allocation_read(doc)


async def create_allocation(scope: AccessScope, payload: AllocationCreate) -> AllocationRead:
    authorize_hostel_allocation_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    return await create_allocation_record(tenant_id, scope.user_id, payload)


async def confirm_allocation(scope: AccessScope, payload: AllocationConfirm) -> AllocationRead:
    authorize_hostel_allocation_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.allocation_id, payload.allocation_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Allocation not found", status_code=404)
    if doc.status not in (HostelAllocationStatus.PENDING_APPROVAL, HostelAllocationStatus.APPROVED, HostelAllocationStatus.CONFIRMED):
        raise AppError(code="CONFLICT", message="Allocation cannot be confirmed", status_code=409)
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, doc.bed_id))
    if bed is None or bed.status != HostelBedStatus.ALLOCATED:
        raise AppError(code="CONFLICT", message="Bed availability changed; revalidate", status_code=409)
    prev = doc.status.value
    doc.status = HostelAllocationStatus.ACTIVE
    doc.approver_id = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _allocation_history(
        tenant_id,
        allocation_id=doc.allocation_id,
        event_type="confirmed",
        actor_id=scope.user_id,
        from_status=prev,
        to_status=doc.status.value,
        note=payload.note,
    )
    return _allocation_read(doc)


async def cancel_allocation(scope: AccessScope, payload: AllocationCancel) -> AllocationRead:
    authorize_hostel_allocation_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.allocation_id, payload.allocation_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Allocation not found", status_code=404)
    if doc.status in (HostelAllocationStatus.CANCELLED, HostelAllocationStatus.COMPLETED, HostelAllocationStatus.CHECKED_OUT):
        raise AppError(code="CONFLICT", message="Allocation already closed", status_code=409)
    prev = doc.status.value
    doc.status = HostelAllocationStatus.CANCELLED
    doc.updated_at = utcnow()
    await doc.save()
    await _release_bed(tenant_id, doc.bed_id)
    await _allocation_history(
        tenant_id,
        allocation_id=doc.allocation_id,
        event_type="cancelled",
        actor_id=scope.user_id,
        from_status=prev,
        to_status=doc.status.value,
        note=payload.reason,
    )
    return _allocation_read(doc)


async def extend_allocation(scope: AccessScope, payload: AllocationExtend) -> AllocationRead:
    authorize_hostel_allocation_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.allocation_id, payload.allocation_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Allocation not found", status_code=404)
    if doc.start_date and payload.expected_end_date < doc.start_date:
        raise AppError(code="VALIDATION_ERROR", message="End date before start", status_code=422)
    doc.expected_end_date = payload.expected_end_date
    doc.updated_at = utcnow()
    await doc.save()
    await _allocation_history(
        tenant_id,
        allocation_id=doc.allocation_id,
        event_type="extended",
        actor_id=scope.user_id,
        metadata={"expected_end_date": payload.expected_end_date.isoformat()},
    )
    return _allocation_read(doc)


async def create_transfer(scope: AccessScope, payload: AllocationTransferCreate) -> dict:
    authorize_hostel_allocation_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    current = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.allocation_id, payload.allocation_id),
    )
    if current is None or current.status not in (HostelAllocationStatus.ACTIVE, HostelAllocationStatus.CONFIRMED):
        raise AppError(code="NOT_FOUND", message="Active allocation not found", status_code=404)
    target = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, payload.target_bed_id))
    if target is None or target.status != HostelBedStatus.AVAILABLE:
        raise AppError(code="CONFLICT", message="Target bed unavailable", status_code=409)
    transfer_id = f"hxf_{uuid4().hex[:10]}"
    await HostelRoomTransferRequest(
        tenant_id=tenant_id,
        transfer_id=transfer_id,
        allocation_id=current.allocation_id,
        student_user_id=current.student_user_id,
        transfer_type=payload.transfer_type,
        target_bed_id=payload.target_bed_id,
        reason=payload.reason,
        status=HostelTransferStatus.PENDING_APPROVAL,
        actor_id=scope.user_id,
    ).insert()
    return {"transfer_id": transfer_id, "status": HostelTransferStatus.PENDING_APPROVAL.value}


async def complete_transfer(scope: AccessScope, transfer_id: str) -> AllocationRead:
    authorize_hostel_allocation_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    xfer = await HostelRoomTransferRequest.find_one(
        Eq(HostelRoomTransferRequest.tenant_id, tenant_id),
        Eq(HostelRoomTransferRequest.transfer_id, transfer_id),
    )
    if xfer is None or xfer.status != HostelTransferStatus.PENDING_APPROVAL:
        raise AppError(code="NOT_FOUND", message="Transfer not found or not approvable", status_code=404)
    current = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.allocation_id, xfer.allocation_id),
    )
    if current is None:
        raise AppError(code="NOT_FOUND", message="Allocation missing", status_code=404)
    new_alloc_id = f"hal_{uuid4().hex[:12]}"
    new_bed = await _claim_bed(tenant_id, xfer.target_bed_id, allocation_id=new_alloc_id)
    prev_bed = current.bed_id
    prev_status = current.status.value
    current.status = HostelAllocationStatus.TRANSFERRED
    current.checked_out_at = utcnow()
    current.updated_at = utcnow()
    await current.save()
    await _release_bed(tenant_id, prev_bed)
    new_doc = HostelAllocation(
        tenant_id=tenant_id,
        allocation_id=new_alloc_id,
        student_user_id=current.student_user_id,
        application_id=current.application_id,
        hostel_code=new_bed.hostel_code or current.hostel_code,
        bed_id=new_bed.bed_id,
        building_code=new_bed.building_code,
        block_code=new_bed.block_code,
        room_code=new_bed.room_code,
        bed_label=new_bed.bed_label,
        status=HostelAllocationStatus.ACTIVE,
        allocation_reason=f"Transfer from {current.allocation_id}",
        start_date=current.start_date,
        expected_end_date=current.expected_end_date,
        previous_allocation_id=current.allocation_id,
        actor_id=scope.user_id,
        approver_id=scope.user_id,
    )
    try:
        await new_doc.insert()
    except DuplicateKeyError:
        await _release_bed(tenant_id, new_bed.bed_id)
        await _claim_bed(tenant_id, prev_bed, allocation_id=current.allocation_id)
        current.status = HostelAllocationStatus.ACTIVE
        await current.save()
        raise AppError(code="CONFLICT", message="Transfer failed due to concurrent allocation", status_code=409)
    xfer.status = HostelTransferStatus.COMPLETED
    xfer.new_allocation_id = new_alloc_id
    xfer.approver_id = scope.user_id
    xfer.updated_at = utcnow()
    await xfer.save()
    await _allocation_history(
        tenant_id,
        allocation_id=current.allocation_id,
        event_type="transferred_out",
        actor_id=scope.user_id,
        from_status=prev_status,
        to_status=current.status.value,
        from_bed_id=prev_bed,
        to_bed_id=new_bed.bed_id,
    )
    await _allocation_history(
        tenant_id,
        allocation_id=new_alloc_id,
        event_type="transferred_in",
        actor_id=scope.user_id,
        to_status=new_doc.status.value,
        to_bed_id=new_bed.bed_id,
        metadata={"previous_allocation_id": current.allocation_id},
    )
    from app.modules.hostel.resident_service import ensure_resident_from_allocation, record_transfer_history

    old_resident = await ensure_resident_from_allocation(current)
    await record_transfer_history(
        tenant_id,
        resident_id=old_resident.resident_id,
        from_allocation_id=current.allocation_id,
        to_allocation_id=new_alloc_id,
        reason=xfer.reason,
        actor_id=scope.user_id,
    )
    await ensure_resident_from_allocation(new_doc)
    return _allocation_read(new_doc)


async def get_allocation(scope: AccessScope, allocation_id: str) -> AllocationRead:
    authorize_hostel_allocation_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelAllocation.find_one(Eq(HostelAllocation.tenant_id, tenant_id), Eq(HostelAllocation.allocation_id, allocation_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Allocation not found", status_code=404)
    return _allocation_read(doc)


async def list_allocations(
    scope: AccessScope,
    pagination,
    *,
    hostel_code: str | None = None,
    status: HostelAllocationStatus | None = None,
) -> Page[AllocationRead]:
    authorize_hostel_allocation_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    query = HostelAllocation.find(Eq(HostelAllocation.tenant_id, tenant_id))
    if hostel_code:
        query = query.find(Eq(HostelAllocation.hostel_code, norm_code(hostel_code)))
    if status:
        query = query.find(Eq(HostelAllocation.status, status))
    total = await query.count()
    rows = await query.sort("-updated_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_allocation_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)