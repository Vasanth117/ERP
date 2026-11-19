"""Hostel resident management and check-in/out."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import (
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBedStatus,
    HostelBuilding,
    HostelResidentHistory,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.hostel_models import HostelRoomAllocation
from app.modules.hostel.hostel_notify import notify_hostel_student
from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassRequest
from app.modules.hostel.mess_models import HostelMessEnrollment, MessEnrollmentStatus
from app.modules.hostel.mess_service import end_enrollment_on_checkout
from app.modules.hostel.policy import authorize_hostel_resident_manage, authorize_hostel_resident_read, require_hostel_tenant_scope
from app.modules.hostel.resident_models import (
    HostelResident,
    HostelResidentCheckinRecord,
    HostelResidentCheckoutRecord,
    HostelResidentStatus,
    HostelResidentStatusHistory,
    HostelResidentTransferHistory,
)
from app.modules.hostel.resident_schemas import (
    ResidentCheckinInput,
    ResidentCheckoutInput,
    ResidentNoShowInput,
    ResidentOperationalView,
)
from app.modules.students.models import StudentProfile

_CHECKIN_ELIGIBLE_ALLOCATION = frozenset(
    {
        HostelAllocationStatus.CONFIRMED,
        HostelAllocationStatus.APPROVED,
        HostelAllocationStatus.PENDING,
        HostelAllocationStatus.PENDING_APPROVAL,
    }
)


async def _status_history(tenant_id: PydanticObjectId, resident_id: str, *, from_s: str | None, to_s: str, actor_id, note=None):
    await HostelResidentStatusHistory(
        tenant_id=tenant_id,
        resident_id=resident_id,
        from_status=from_s,
        to_status=to_s,
        actor_id=actor_id,
        note=note,
    ).insert()


async def ensure_resident_from_allocation(alloc: HostelAllocation) -> HostelResident:
    existing = await HostelResident.find_one(Eq(HostelResident.tenant_id, alloc.tenant_id), Eq(HostelResident.allocation_id, alloc.allocation_id))
    if existing:
        return existing
    resident_id = f"hr_{uuid4().hex[:10]}"
    doc = HostelResident(
        tenant_id=alloc.tenant_id,
        resident_id=resident_id,
        student_user_id=alloc.student_user_id,
        allocation_id=alloc.allocation_id,
        hostel_code=alloc.hostel_code,
        building_code=alloc.building_code,
        block_code=alloc.block_code,
        floor_id=alloc.floor_id,
        room_code=alloc.room_code,
        bed_id=alloc.bed_id,
        bed_label=alloc.bed_label,
        status=HostelResidentStatus.AWAITING_CHECKIN,
        accommodation_start=alloc.start_date,
        expected_checkout=alloc.expected_end_date,
    )
    await doc.insert()
    await _status_history(alloc.tenant_id, resident_id, from_s=None, to_s=doc.status.value, actor_id=alloc.actor_id, note="created_from_allocation")
    return doc


async def _student_display(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> dict:
    user = await User.find_one(Eq(User.id, user_id), Eq(User.tenant_id, tenant_id))
    profile = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, user_id))
    return {
        "student_name": user.full_name if user else None,
        "roll_number": profile.roll_number if profile else None,
        "student_id": profile.student_id if profile else None,
        "contact_phone": profile.contact_phone if profile else None,
        "photo_ref": profile.profile_photo_ref if profile else None,
        "emergency_contacts": [c.model_dump() for c in profile.emergency_contacts] if profile else [],
    }


async def _resident_view(tenant_id: PydanticObjectId, doc: HostelResident) -> ResidentOperationalView:
    display = await _student_display(tenant_id, doc.student_user_id)
    now = utcnow()
    outpass = await HostelOutpassRequest.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": doc.student_user_id,
            "status": HostelLeaveOutpassStatus.APPROVED.value,
            "from_at": {"$lte": now},
            "to_at": {"$gte": now},
        }
    )
    mess_enr = await HostelMessEnrollment.find_one(
        {
            "tenant_id": tenant_id,
            "resident_id": doc.resident_id,
            "status": {"$in": [MessEnrollmentStatus.ACTIVE.value, MessEnrollmentStatus.PENDING_APPROVAL.value, MessEnrollmentStatus.PAUSED.value]},
        }
    )
    return ResidentOperationalView(
        resident_id=doc.resident_id,
        student_user_id=str(doc.student_user_id),
        allocation_id=doc.allocation_id,
        hostel_code=doc.hostel_code,
        building_code=doc.building_code,
        block_code=doc.block_code,
        floor_id=doc.floor_id,
        room_code=doc.room_code,
        bed_id=doc.bed_id,
        bed_label=doc.bed_label,
        status=doc.status,
        accommodation_start=doc.accommodation_start,
        expected_checkout=doc.expected_checkout,
        checked_in_at=doc.checked_in_at,
        checked_out_at=doc.checked_out_at,
        mess_enrollment_status=mess_enr.status.value if mess_enr else None,
        active_outpass=outpass is not None,
        **display,
    )


async def list_residents(
    scope: AccessScope,
    pagination: Pagination,
    *,
    hostel_code: str | None = None,
    status: HostelResidentStatus | None = None,
    search: str | None = None,
) -> Page[ResidentOperationalView]:
    authorize_hostel_resident_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    query = HostelResident.find(Eq(HostelResident.tenant_id, tenant_id))
    if hostel_code:
        query = query.find(Eq(HostelResident.hostel_code, hostel_code.strip().upper()))
    if status:
        query = query.find(Eq(HostelResident.status, status))
    rows = await query.sort("-updated_at").to_list()
    if search:
        needle = search.lower().strip()
        filtered = []
        for r in rows:
            view = await _resident_view(tenant_id, r)
            if needle in (view.student_name or "").lower() or needle in (view.roll_number or "").lower() or needle in view.room_code.lower():
                filtered.append(r)
        rows = filtered
    total = len(rows)
    page_rows = rows[pagination.offset : pagination.offset + pagination.limit]
    items = [await _resident_view(tenant_id, r) for r in page_rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def list_awaiting_checkin(scope: AccessScope, pagination: Pagination) -> Page[ResidentOperationalView]:
    return await list_residents(scope, pagination, status=HostelResidentStatus.AWAITING_CHECKIN)


async def get_resident(scope: AccessScope, resident_id: str) -> ResidentOperationalView:
    authorize_hostel_resident_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant_id), Eq(HostelResident.resident_id, resident_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Resident not found", status_code=404)
    return await _resident_view(tenant_id, doc)


async def check_in_resident(scope: AccessScope, payload: ResidentCheckinInput) -> ResidentOperationalView:
    authorize_hostel_resident_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    alloc = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.allocation_id, payload.allocation_id),
    )
    if alloc is None:
        raise AppError(code="NOT_FOUND", message="Allocation not found", status_code=404)
    if alloc.status not in _CHECKIN_ELIGIBLE_ALLOCATION:
        raise AppError(code="CONFLICT", message="Allocation not eligible for check-in", status_code=409)
    if payload.verify_student_user_id and str(alloc.student_user_id) != payload.verify_student_user_id:
        raise AppError(code="VALIDATION_ERROR", message="Student identity mismatch", status_code=422)
    resident = await ensure_resident_from_allocation(alloc)
    if resident.status == HostelResidentStatus.CHECKED_IN:
        raise AppError(code="CONFLICT", message="Resident already checked in", status_code=409)
    prev = resident.status.value
    now = utcnow()
    resident.status = HostelResidentStatus.CHECKED_IN
    resident.checked_in_at = now
    resident.keys_issued = payload.keys_issued
    resident.room_condition_ack = payload.room_condition_ack
    resident.checkin_note = payload.exception_reason
    resident.updated_at = now
    await resident.save()
    alloc.status = HostelAllocationStatus.ACTIVE
    alloc.checked_in_at = now
    alloc.updated_at = now
    await alloc.save()
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, alloc.bed_id))
    if bed and bed.status != HostelBedStatus.ALLOCATED:
        bed.status = HostelBedStatus.ALLOCATED
        bed.updated_at = now
        await bed.save()
    if not alloc.authoritative_allocation_id:
        auth_id = f"hra_{uuid4().hex[:12]}"
        building = await HostelBuilding.find_one(Eq(HostelBuilding.tenant_id, tenant_id), Eq(HostelBuilding.building_code, alloc.building_code))
        hostel_name = building.name if building else (alloc.hostel_code or alloc.building_code)
        await HostelRoomAllocation(
            tenant_id=tenant_id,
            student_user_id=alloc.student_user_id,
            allocation_id=auth_id,
            hostel_name=hostel_name,
            block=alloc.block_code,
            room_number=alloc.room_code,
            bed_label=alloc.bed_label,
            published=True,
            effective_from=now.date(),
        ).insert()
        alloc.authoritative_allocation_id = auth_id
        await alloc.save()
    await HostelResidentCheckinRecord(
        tenant_id=tenant_id,
        record_id=f"hci_{uuid4().hex[:8]}",
        resident_id=resident.resident_id,
        allocation_id=alloc.allocation_id,
        keys_issued=payload.keys_issued,
        room_condition_ack=payload.room_condition_ack,
        belongings_notes=payload.belongings_notes,
        exception_reason=payload.exception_reason,
        actor_id=scope.user_id,
    ).insert()
    await _status_history(tenant_id, resident.resident_id, from_s=prev, to_s=resident.status.value, actor_id=scope.user_id)
    await HostelResidentHistory(
        tenant_id=tenant_id,
        student_user_id=alloc.student_user_id,
        allocation_id=alloc.allocation_id,
        event_type="check_in",
        actor_id=scope.user_id,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.resident.check_in",
        module="hostel",
        resource_type="hostel_resident",
        resource_id=resident.resident_id,
    )
    await notify_hostel_student(
        tenant_id,
        student_user_id=alloc.student_user_id,
        event_type="check_in_confirmed",
        title="Hostel check-in",
        body=f"You are checked in to {alloc.room_code} / {alloc.bed_label}.",
        aggregate_id=resident.resident_id,
    )
    return await _resident_view(tenant_id, resident)


async def check_out_resident(scope: AccessScope, payload: ResidentCheckoutInput) -> ResidentOperationalView:
    authorize_hostel_resident_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    alloc = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.allocation_id, payload.allocation_id),
    )
    if alloc is None or alloc.status not in (HostelAllocationStatus.ACTIVE, HostelAllocationStatus.CONFIRMED):
        raise AppError(code="NOT_FOUND", message="Active resident allocation not found", status_code=404)
    resident = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant_id), Eq(HostelResident.allocation_id, alloc.allocation_id))
    if resident is None:
        resident = await ensure_resident_from_allocation(alloc)
    if resident.status == HostelResidentStatus.CHECKED_OUT:
        raise AppError(code="CONFLICT", message="Resident already checked out", status_code=409)
    prev = resident.status.value
    now = utcnow()
    resident.status = HostelResidentStatus.CHECKED_OUT
    resident.checked_out_at = now
    resident.checkout_note = payload.exception_reason
    resident.clearance_status = payload.clearance_status
    resident.updated_at = now
    await resident.save()
    alloc.status = HostelAllocationStatus.CHECKED_OUT
    alloc.checked_out_at = now
    alloc.updated_at = now
    await alloc.save()
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, alloc.bed_id))
    if bed:
        bed.status = HostelBedStatus.AVAILABLE
        bed.updated_at = now
        await bed.save()
    if alloc.authoritative_allocation_id:
        auth = await HostelRoomAllocation.find_one(
            Eq(HostelRoomAllocation.tenant_id, tenant_id),
            Eq(HostelRoomAllocation.allocation_id, alloc.authoritative_allocation_id),
        )
        if auth:
            auth.published = False
            await auth.save()
    await HostelResidentCheckoutRecord(
        tenant_id=tenant_id,
        record_id=f"hco_{uuid4().hex[:8]}",
        resident_id=resident.resident_id,
        allocation_id=alloc.allocation_id,
        checkout_type=payload.checkout_type,
        keys_returned=payload.keys_returned,
        room_condition_notes=payload.room_condition_notes,
        clearance_status=payload.clearance_status,
        exception_reason=payload.exception_reason,
        actor_id=scope.user_id,
    ).insert()
    await _status_history(tenant_id, resident.resident_id, from_s=prev, to_s=resident.status.value, actor_id=scope.user_id)
    await HostelResidentHistory(
        tenant_id=tenant_id,
        student_user_id=alloc.student_user_id,
        allocation_id=alloc.allocation_id,
        event_type="check_out",
        actor_id=scope.user_id,
    ).insert()
    await end_enrollment_on_checkout(tenant_id, resident.resident_id)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.resident.check_out",
        module="hostel",
        resource_type="hostel_resident",
        resource_id=resident.resident_id,
    )
    return await _resident_view(tenant_id, resident)


async def mark_no_show(scope: AccessScope, payload: ResidentNoShowInput) -> dict:
    authorize_hostel_resident_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    resident = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant_id), Eq(HostelResident.allocation_id, payload.allocation_id))
    if resident is None:
        raise AppError(code="NOT_FOUND", message="Resident not found", status_code=404)
    prev = resident.status.value
    resident.status = HostelResidentStatus.CANCELLED
    resident.updated_at = utcnow()
    await resident.save()
    await _status_history(tenant_id, resident.resident_id, from_s=prev, to_s=resident.status.value, actor_id=scope.user_id, note=payload.note)
    return {"resident_id": resident.resident_id, "status": resident.status.value}


async def record_transfer_history(
    tenant_id: PydanticObjectId,
    *,
    resident_id: str,
    from_allocation_id: str,
    to_allocation_id: str | None,
    reason: str | None,
    actor_id: PydanticObjectId | None,
) -> None:
    await HostelResidentTransferHistory(
        tenant_id=tenant_id,
        resident_id=resident_id,
        from_allocation_id=from_allocation_id,
        to_allocation_id=to_allocation_id,
        reason=reason,
        actor_id=actor_id,
    ).insert()