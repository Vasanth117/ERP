"""Hostel maintenance and complaint services."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus, HostelRoom
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.hostel_notify import notify_hostel_student
from app.modules.hostel.maintenance_models import (
    HostelComplaint,
    HostelComplaintAssignment,
    HostelComplaintCategory,
    HostelComplaintFeedback,
    HostelComplaintHistory,
    HostelComplaintPriority,
    HostelComplaintStatus,
    HostelFacilityUnavailabilityHistory,
    HostelMaintenanceRequest,
    HostelMaintenanceSchedule,
    HostelMaintenanceTask,
    HostelMaintenanceTaskStatus,
)
from app.modules.hostel.maintenance_schemas import (
    ComplaintAssign,
    ComplaintClarification,
    ComplaintFeedbackInput,
    ComplaintRead,
    ComplaintStatusUpdate,
    ComplaintSubmit,
    FacilityUnavailabilityInput,
    MaintenanceDashboard,
    MaintenanceScheduleUpsert,
)
from app.modules.hostel.policy import authorize_hostel_maintenance_manage, authorize_hostel_maintenance_read, require_hostel_tenant_scope
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus


OPEN_STATUSES = frozenset(
    {
        HostelComplaintStatus.SUBMITTED.value,
        HostelComplaintStatus.ACKNOWLEDGED.value,
        HostelComplaintStatus.ASSIGNED.value,
        HostelComplaintStatus.IN_PROGRESS.value,
        HostelComplaintStatus.ON_HOLD.value,
        HostelComplaintStatus.AWAITING_PARTS.value,
        HostelComplaintStatus.REOPENED.value,
    }
)


async def _history(
    tenant_id: PydanticObjectId,
    complaint_id: str,
    action: str,
    *,
    actor_id: PydanticObjectId | None,
    from_status: str | None = None,
    to_status: str | None = None,
    detail: dict | None = None,
) -> None:
    await HostelComplaintHistory(
        tenant_id=tenant_id,
        complaint_id=complaint_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        detail=detail or {},
        actor_id=actor_id,
    ).insert()


def _complaint_read(doc: HostelComplaint) -> ComplaintRead:
    return ComplaintRead(
        complaint_id=doc.complaint_id,
        student_user_id=str(doc.student_user_id) if doc.student_user_id else None,
        hostel_code=doc.hostel_code,
        building_code=doc.building_code,
        room_code=doc.room_code,
        category_code=doc.category_code,
        subject=doc.subject,
        description=doc.description,
        priority=doc.priority,
        status=doc.status,
        assigned_to_user_id=str(doc.assigned_to_user_id) if doc.assigned_to_user_id else None,
        expected_completion=doc.expected_completion,
        created_at=doc.created_at,
    )


async def upsert_complaint_category(scope: AccessScope, category_code: str, label: str, default_priority: HostelComplaintPriority) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_maintenance_manage(scope)
    code = category_code.strip().upper()
    doc = await HostelComplaintCategory.find_one(Eq(HostelComplaintCategory.tenant_id, tenant_id), Eq(HostelComplaintCategory.category_code, code))
    if doc:
        doc.label = label
        doc.default_priority = default_priority
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await HostelComplaintCategory(
            tenant_id=tenant_id, category_code=code, label=label, default_priority=default_priority
        ).insert()
    return {"category_code": code}


async def _resolve_resident_location(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> HostelResident | None:
    return await HostelResident.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "status": {"$in": [HostelResidentStatus.CHECKED_IN.value, HostelResidentStatus.TEMPORARILY_OUTSIDE.value]},
        }
    )


async def submit_complaint(
    scope: AccessScope,
    payload: ComplaintSubmit,
    *,
    student_user: User | None = None,
) -> ComplaintRead:
    tenant_id = require_hostel_tenant_scope(scope)
    student_id: PydanticObjectId | None = None
    resident_id: str | None = None
    if student_user:
        if student_user.tenant_id != tenant_id:
            raise AppError(code="FORBIDDEN", message="Tenant mismatch", status_code=403)
        student_id = student_user.id
        resident = await _resolve_resident_location(tenant_id, student_user.id)
        if resident is None:
            raise AppError(code="VALIDATION_ERROR", message="Active residency required to raise complaints", status_code=422)
        resident_id = resident.resident_id
        if not payload.hostel_code:
            payload = payload.model_copy(update={"hostel_code": resident.hostel_code})
    else:
        authorize_hostel_maintenance_manage(scope)
    category = await HostelComplaintCategory.find_one(
        Eq(HostelComplaintCategory.tenant_id, tenant_id), Eq(HostelComplaintCategory.category_code, payload.category_code.upper())
    )
    priority = payload.priority or (category.default_priority if category else HostelComplaintPriority.MEDIUM)
    complaint_id = f"cmp_{uuid4().hex[:10]}"
    doc = await HostelComplaint(
        tenant_id=tenant_id,
        complaint_id=complaint_id,
        student_user_id=student_id,
        resident_id=resident_id,
        hostel_code=payload.hostel_code.upper() if payload.hostel_code else None,
        building_code=payload.building_code.upper(),
        block_code=payload.block_code.upper() if payload.block_code else None,
        floor_id=payload.floor_id,
        room_code=payload.room_code.upper(),
        bed_id=payload.bed_id,
        category_code=payload.category_code.upper(),
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        priority=priority,
        status=HostelComplaintStatus.SUBMITTED,
        attachment_refs=payload.attachment_refs,
        reporter_id=scope.user_id,
    ).insert()
    req_id = f"mnt_{uuid4().hex[:10]}"
    await HostelMaintenanceRequest(
        tenant_id=tenant_id,
        request_id=req_id,
        building_code=doc.building_code,
        room_code=doc.room_code,
        description=doc.description[:500],
        status="open",
        actor_id=scope.user_id,
        complaint_id=complaint_id,
    ).insert()
    await _history(tenant_id, complaint_id, "submitted", actor_id=scope.user_id, to_status=doc.status.value)
    if student_id:
        await notify_hostel_student(
            tenant_id,
            student_user_id=student_id,
            event_type="complaint.submitted",
            title="Complaint registered",
            body=f"Your complaint {complaint_id} has been submitted.",
            aggregate_id=complaint_id,
        )
    return _complaint_read(doc)


async def assign_complaint(scope: AccessScope, payload: ComplaintAssign) -> ComplaintRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_maintenance_manage(scope)
    doc = await HostelComplaint.find_one(
        Eq(HostelComplaint.tenant_id, tenant_id), Eq(HostelComplaint.complaint_id, payload.complaint_id)
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Complaint not found", status_code=404)
    prev = doc.status.value
    doc.assigned_to_user_id = to_object_id(payload.assignee_user_id, "assignee_user_id") if payload.assignee_user_id else None
    doc.assigned_department = payload.department
    doc.supervisor_user_id = to_object_id(payload.supervisor_user_id, "supervisor_user_id") if payload.supervisor_user_id else None
    doc.expected_completion = payload.expected_completion
    doc.status = HostelComplaintStatus.ASSIGNED
    doc.updated_at = utcnow()
    await doc.save()
    await HostelComplaintAssignment(
        tenant_id=tenant_id,
        assignment_id=f"asg_{uuid4().hex[:10]}",
        complaint_id=doc.complaint_id,
        assignee_user_id=doc.assigned_to_user_id,
        department=payload.department,
        supervisor_user_id=doc.supervisor_user_id,
        work_instructions=payload.work_instructions,
        materials_required=payload.materials_required,
        expected_completion=payload.expected_completion,
        actor_id=scope.user_id,
    ).insert()
    await _history(tenant_id, doc.complaint_id, "assigned", actor_id=scope.user_id, from_status=prev, to_status=doc.status.value)
    return _complaint_read(doc)


async def update_complaint_status(scope: AccessScope, payload: ComplaintStatusUpdate) -> ComplaintRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_maintenance_manage(scope)
    doc = await HostelComplaint.find_one(
        Eq(HostelComplaint.tenant_id, tenant_id), Eq(HostelComplaint.complaint_id, payload.complaint_id)
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Complaint not found", status_code=404)
    prev = doc.status.value
    doc.status = payload.status
    if payload.status in (HostelComplaintStatus.RESOLVED, HostelComplaintStatus.CLOSED):
        doc.resolved_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    if payload.repair_evidence_refs:
        await HostelMaintenanceTask(
            tenant_id=tenant_id,
            task_id=f"tsk_{uuid4().hex[:10]}",
            complaint_id=doc.complaint_id,
            task_type="corrective",
            title=f"Repair for {doc.complaint_id}",
            status=HostelMaintenanceTaskStatus.COMPLETED if payload.status == HostelComplaintStatus.RESOLVED else HostelMaintenanceTaskStatus.IN_PROGRESS,
            repair_evidence_refs=payload.repair_evidence_refs,
            completed_at=utcnow() if payload.status == HostelComplaintStatus.RESOLVED else None,
        ).insert()
    legacy = await HostelMaintenanceRequest.find_one(
        Eq(HostelMaintenanceRequest.tenant_id, tenant_id), Eq(HostelMaintenanceRequest.complaint_id, doc.complaint_id)
    )
    if legacy:
        legacy.status = "resolved" if payload.status in (HostelComplaintStatus.RESOLVED, HostelComplaintStatus.CLOSED) else "in_progress"
        await legacy.save()
    await _history(
        tenant_id,
        doc.complaint_id,
        "status_change",
        actor_id=scope.user_id,
        from_status=prev,
        to_status=doc.status.value,
        detail={"note": payload.note},
    )
    if doc.student_user_id:
        await notify_hostel_student(
            tenant_id,
            student_user_id=doc.student_user_id,
            event_type="complaint.status",
            title="Complaint updated",
            body=f"Complaint {doc.complaint_id} is now {doc.status.value}.",
            aggregate_id=doc.complaint_id,
        )
    return _complaint_read(doc)


async def list_complaints(
    scope: AccessScope,
    pagination: Pagination,
    *,
    status: HostelComplaintStatus | None = None,
    priority: HostelComplaintPriority | None = None,
    hostel_code: str | None = None,
) -> Page[ComplaintRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_maintenance_read(scope)
    q: dict = {"tenant_id": tenant_id}
    if status:
        q["status"] = status.value
    if priority:
        q["priority"] = priority.value
    if hostel_code:
        q["hostel_code"] = hostel_code.upper()
    total = await HostelComplaint.find(q).count()
    skip = (pagination.page - 1) * pagination.page_size
    rows = await HostelComplaint.find(q).sort("-created_at").skip(skip).limit(pagination.page_size).to_list()
    return Page(items=[_complaint_read(r) for r in rows], total=total, page=pagination.page, page_size=pagination.page_size)


async def student_list_complaints(scope: AccessScope, user: User, pagination: Pagination) -> Page[ComplaintRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    q = {"tenant_id": tenant_id, "student_user_id": user.id}
    total = await HostelComplaint.find(q).count()
    skip = (pagination.page - 1) * pagination.page_size
    rows = await HostelComplaint.find(q).sort("-created_at").skip(skip).limit(pagination.page_size).to_list()
    return Page(items=[_complaint_read(r) for r in rows], total=total, page=pagination.page, page_size=pagination.page_size)


async def add_complaint_clarification(scope: AccessScope, user: User, payload: ComplaintClarification) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelComplaint.find_one(
        Eq(HostelComplaint.tenant_id, tenant_id),
        Eq(HostelComplaint.complaint_id, payload.complaint_id),
        Eq(HostelComplaint.student_user_id, user.id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Complaint not found", status_code=404)
    await _history(tenant_id, doc.complaint_id, "clarification", actor_id=user.id, detail={"note": payload.note})
    return {"complaint_id": doc.complaint_id, "recorded": True}


async def submit_complaint_feedback(scope: AccessScope, user: User, payload: ComplaintFeedbackInput) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelComplaint.find_one(
        Eq(HostelComplaint.tenant_id, tenant_id),
        Eq(HostelComplaint.complaint_id, payload.complaint_id),
        Eq(HostelComplaint.student_user_id, user.id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Complaint not found", status_code=404)
    if doc.status not in (HostelComplaintStatus.RESOLVED, HostelComplaintStatus.CLOSED) and not payload.reopen_requested:
        raise AppError(code="CONFLICT", message="Feedback allowed after resolution", status_code=409)
    await HostelComplaintFeedback(
        tenant_id=tenant_id,
        feedback_id=f"cfb_{uuid4().hex[:10]}",
        complaint_id=doc.complaint_id,
        student_user_id=user.id,
        rating=payload.rating,
        comment=payload.comment,
        reopen_requested=payload.reopen_requested,
    ).insert()
    if payload.reopen_requested and doc.status in (HostelComplaintStatus.RESOLVED, HostelComplaintStatus.CLOSED):
        prev = doc.status.value
        doc.status = HostelComplaintStatus.REOPENED
        doc.updated_at = utcnow()
        await doc.save()
        await _history(tenant_id, doc.complaint_id, "reopened", actor_id=user.id, from_status=prev, to_status=doc.status.value)
    return {"complaint_id": doc.complaint_id}


async def upsert_maintenance_schedule(scope: AccessScope, payload: MaintenanceScheduleUpsert) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_maintenance_manage(scope)
    schedule_id = payload.schedule_id or f"msc_{uuid4().hex[:10]}"
    doc = await HostelMaintenanceSchedule.find_one(
        Eq(HostelMaintenanceSchedule.tenant_id, tenant_id), Eq(HostelMaintenanceSchedule.schedule_id, schedule_id)
    )
    if doc:
        doc.title = payload.title
        doc.scheduled_date = payload.scheduled_date
        doc.assignee_user_id = to_object_id(payload.assignee_user_id, "assignee_user_id") if payload.assignee_user_id else None
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await HostelMaintenanceSchedule(
            tenant_id=tenant_id,
            schedule_id=schedule_id,
            schedule_type=payload.schedule_type,
            hostel_code=payload.hostel_code.upper() if payload.hostel_code else None,
            building_code=payload.building_code.upper() if payload.building_code else None,
            title=payload.title,
            scheduled_date=payload.scheduled_date,
            assignee_user_id=to_object_id(payload.assignee_user_id, "assignee_user_id") if payload.assignee_user_id else None,
        ).insert()
    return {"schedule_id": schedule_id}


async def set_facility_unavailability(scope: AccessScope, payload: FacilityUnavailabilityInput) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_maintenance_manage(scope)
    history_id = f"fu_{uuid4().hex[:10]}"
    if payload.facility_type == "bed":
        if not payload.bed_id:
            raise AppError(code="VALIDATION_ERROR", message="bed_id required", status_code=422)
        bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, payload.bed_id))
        if bed is None:
            raise AppError(code="NOT_FOUND", message="Bed not found", status_code=404)
        if payload.unavailable:
            bed.status = HostelBedStatus.MAINTENANCE
        elif bed.status == HostelBedStatus.MAINTENANCE:
            bed.status = HostelBedStatus.AVAILABLE
        bed.updated_at = utcnow()
        await bed.save()
    else:
        room = await HostelRoom.find_one(
            {
                "tenant_id": tenant_id,
                "building_code": payload.building_code.upper(),
                "block_code": payload.block_code.upper() if payload.block_code else None,
                "room_code": payload.room_code.upper(),
            }
        )
        if room is None:
            raise AppError(code="NOT_FOUND", message="Room not found", status_code=404)
        room.maintenance_status = "unavailable" if payload.unavailable else "available"
        room.updated_at = utcnow()
        await room.save()
    await HostelFacilityUnavailabilityHistory(
        tenant_id=tenant_id,
        history_id=history_id,
        complaint_id=payload.complaint_id,
        facility_type=payload.facility_type,
        hostel_code=payload.hostel_code.upper() if payload.hostel_code else None,
        building_code=payload.building_code.upper(),
        block_code=payload.block_code.upper() if payload.block_code else None,
        room_code=payload.room_code.upper(),
        bed_id=payload.bed_id,
        unavailable=payload.unavailable,
        reason=payload.reason,
        actor_id=scope.user_id,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.facility.unavailability",
        module="hostel_maintenance",
        resource_type=payload.facility_type,
        resource_id=payload.bed_id or payload.room_code,
    )
    return {"history_id": history_id}


async def maintenance_dashboard(scope: AccessScope) -> MaintenanceDashboard:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_maintenance_read(scope)
    now = utcnow()
    total = await HostelComplaint.find({"tenant_id": tenant_id}).count()
    new_c = await HostelComplaint.find({"tenant_id": tenant_id, "status": HostelComplaintStatus.NEW.value}).count()
    open_c = await HostelComplaint.find({"tenant_id": tenant_id, "status": {"$in": list(OPEN_STATUSES)}}).count()
    in_prog = await HostelComplaint.find({"tenant_id": tenant_id, "status": HostelComplaintStatus.IN_PROGRESS.value}).count()
    high = await HostelComplaint.find(
        {"tenant_id": tenant_id, "priority": HostelComplaintPriority.HIGH.value, "status": {"$in": list(OPEN_STATUSES)}}
    ).count()
    high += await HostelComplaint.find(
        {"tenant_id": tenant_id, "priority": HostelComplaintPriority.CRITICAL.value, "status": {"$in": list(OPEN_STATUSES)}}
    ).count()
    overdue = await HostelComplaint.find(
        {
            "tenant_id": tenant_id,
            "resolution_target": {"$lt": now},
            "status": {"$in": list(OPEN_STATUSES)},
        }
    ).count()
    pending_assign = await HostelComplaint.find(
        {"tenant_id": tenant_id, "status": HostelComplaintStatus.SUBMITTED.value}
    ).count()
    resolved = await HostelComplaint.find(
        {"tenant_id": tenant_id, "status": {"$in": [HostelComplaintStatus.RESOLVED.value, HostelComplaintStatus.CLOSED.value]}}
    ).count()
    rooms_unavail = await HostelRoom.find({"tenant_id": tenant_id, "maintenance_status": "unavailable"}).count()
    return MaintenanceDashboard(
        total_complaints=total,
        new_complaints=new_c,
        open_complaints=open_c,
        in_progress=in_prog,
        high_priority=high,
        overdue=overdue,
        pending_assignments=pending_assign,
        resolved=resolved,
        rooms_unavailable=rooms_unavail,
    )


async def escalate_overdue_complaints(tenant_id: PydanticObjectId) -> int:
    now = utcnow()
    rows = await HostelComplaint.find(
        {
            "tenant_id": tenant_id,
            "status": {"$in": list(OPEN_STATUSES)},
            "expected_completion": {"$lt": now.date()},
            "escalated": False,
        }
    ).to_list()
    for doc in rows:
        doc.escalated = True
        doc.escalation_level += 1
        doc.updated_at = utcnow()
        await doc.save()
        await _history(tenant_id, doc.complaint_id, "escalated", actor_id=None, detail={"level": doc.escalation_level})
    return len(rows)