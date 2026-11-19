"""Hostel leave, outpass and gate movement services."""

from __future__ import annotations

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.hostel_notify import notify_hostel_student
from app.modules.hostel.leave_outpass_models import (
    HostelGateMovement,
    HostelLeaveApprovalHistory,
    HostelLeaveOutpassStatus,
    HostelLeaveRequest,
    HostelLeaveType,
    HostelOutpassRequest,
    HostelRequestKind,
    HostelResidentMovementHistory,
)
from app.modules.hostel.leave_outpass_schemas import (
    ApprovalDecision,
    GateMovementInput,
    LeaveOutpassOverview,
    LeaveOutpassRead,
    LeaveSubmit,
    LeaveTypeUpsert,
    OutpassSubmit,
)
from app.modules.hostel.mess_schemas import BillingAdjustmentCreate
from app.modules.hostel.mess_service import add_billing_adjustment
from app.modules.hostel.policy import (
    authorize_hostel_gate_manage,
    authorize_hostel_leave_manage,
    authorize_hostel_leave_read,
    require_hostel_tenant_scope,
)
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus


async def _active_resident(tenant_id: PydanticObjectId, student_user_id: PydanticObjectId) -> HostelResident:
    doc = await HostelResident.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": student_user_id,
            "status": {"$in": [HostelResidentStatus.CHECKED_IN.value, HostelResidentStatus.TEMPORARILY_OUTSIDE.value]},
        }
    )
    if doc is None:
        raise AppError(code="VALIDATION_ERROR", message="Active hostel residency required", status_code=422)
    return doc


async def _conflicting_outpass(tenant_id: PydanticObjectId, student_user_id: PydanticObjectId, from_at, to_at, exclude_id: str | None = None) -> bool:
    q: dict = {
        "tenant_id": tenant_id,
        "student_user_id": student_user_id,
        "status": {
            "$in": [
                HostelLeaveOutpassStatus.PENDING_APPROVAL.value,
                HostelLeaveOutpassStatus.APPROVED.value,
                HostelLeaveOutpassStatus.DEPARTURE_RECORDED.value,
                HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value,
            ]
        },
        "from_at": {"$lt": to_at},
        "to_at": {"$gt": from_at},
    }
    if exclude_id:
        q["request_id"] = {"$ne": exclude_id}
    return await HostelOutpassRequest.find(q).count() > 0


async def upsert_leave_type(scope: AccessScope, payload: LeaveTypeUpsert) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_leave_manage(scope)
    code = payload.type_code.strip().upper()
    doc = await HostelLeaveType.find_one(Eq(HostelLeaveType.tenant_id, tenant_id), Eq(HostelLeaveType.type_code, code))
    if doc:
        doc.label = payload.label
        doc.requires_document = payload.requires_document
        doc.max_duration_hours = payload.max_duration_hours
        doc.policy = payload.policy
        doc.active = payload.active
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await HostelLeaveType(
            tenant_id=tenant_id,
            type_code=code,
            label=payload.label,
            requires_document=payload.requires_document,
            max_duration_hours=payload.max_duration_hours,
            policy=payload.policy,
            active=payload.active,
        ).insert()
    return {"type_code": code}


async def submit_leave_student(scope: AccessScope, user: User, payload: LeaveSubmit) -> LeaveOutpassRead:
    tenant_id = require_hostel_tenant_scope(scope)
    if user.tenant_id != tenant_id:
        raise AppError(code="FORBIDDEN", message="Tenant mismatch", status_code=403)
    resident = await _active_resident(tenant_id, user.id)
    if payload.expected_return_at <= payload.departure_at:
        raise AppError(code="VALIDATION_ERROR", message="Invalid leave window", status_code=422)
    leave_type = await HostelLeaveType.find_one(
        Eq(HostelLeaveType.tenant_id, tenant_id), Eq(HostelLeaveType.type_code, payload.leave_type_code.upper())
    )
    if leave_type is None or not leave_type.active:
        raise AppError(code="NOT_FOUND", message="Leave type not found", status_code=404)
    if leave_type.requires_document and not payload.document_ref:
        raise AppError(code="VALIDATION_ERROR", message="Supporting document required", status_code=422)
    if leave_type.max_duration_hours:
        hours = (payload.expected_return_at - payload.departure_at).total_seconds() / 3600
        if hours > leave_type.max_duration_hours:
            raise AppError(code="VALIDATION_ERROR", message="Leave exceeds maximum duration", status_code=422)
    if await _conflicting_outpass(tenant_id, user.id, payload.departure_at, payload.expected_return_at):
        raise AppError(code="CONFLICT", message="Conflicting approved/pending movement", status_code=409)
    request_id = f"hlv_{uuid4().hex[:10]}"
    doc = await HostelLeaveRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        student_user_id=user.id,
        resident_id=resident.resident_id,
        leave_type_code=leave_type.type_code,
        reason=payload.reason,
        destination=payload.destination,
        departure_at=payload.departure_at,
        expected_return_at=payload.expected_return_at,
        emergency_contact_ref=payload.emergency_contact_ref,
        document_ref=payload.document_ref,
        status=HostelLeaveOutpassStatus.PENDING_APPROVAL,
        parent_approval_required=bool(leave_type.policy.get("parent_approval_required")),
    ).insert()
    await HostelResidentMovementHistory(
        tenant_id=tenant_id,
        student_user_id=user.id,
        resident_id=resident.resident_id,
        event_type="leave_submitted",
        request_id=request_id,
        detail={"leave_type": leave_type.type_code},
        actor_id=user.id,
    ).insert()
    return _leave_read(doc)


async def submit_outpass_student(scope: AccessScope, user: User, payload: OutpassSubmit) -> LeaveOutpassRead:
    tenant_id = require_hostel_tenant_scope(scope)
    if user.tenant_id != tenant_id:
        raise AppError(code="FORBIDDEN", message="Tenant mismatch", status_code=403)
    resident = await _active_resident(tenant_id, user.id)
    if payload.to_at <= payload.from_at:
        raise AppError(code="VALIDATION_ERROR", message="Invalid outpass window", status_code=422)
    if await _conflicting_outpass(tenant_id, user.id, payload.from_at, payload.to_at):
        raise AppError(code="CONFLICT", message="Conflicting outpass", status_code=409)
    request_id = f"hop_{uuid4().hex[:10]}"
    doc = await HostelOutpassRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        student_user_id=user.id,
        resident_id=resident.resident_id,
        outpass_type=payload.outpass_type,
        from_at=payload.from_at,
        to_at=payload.to_at,
        reason=payload.reason,
        destination=payload.destination,
        status=HostelLeaveOutpassStatus.PENDING_APPROVAL,
    ).insert()
    await HostelResidentMovementHistory(
        tenant_id=tenant_id,
        student_user_id=user.id,
        resident_id=resident.resident_id,
        event_type="outpass_submitted",
        request_id=request_id,
        actor_id=user.id,
    ).insert()
    return _outpass_read(doc)


def _leave_read(doc: HostelLeaveRequest) -> LeaveOutpassRead:
    return LeaveOutpassRead(
        request_id=doc.request_id,
        kind=HostelRequestKind.LEAVE.value,
        student_user_id=str(doc.student_user_id),
        resident_id=doc.resident_id,
        status=doc.status,
        departure_at=doc.departure_at,
        expected_return_at=doc.expected_return_at,
        reason=doc.reason,
        leave_type_code=doc.leave_type_code,
        created_at=doc.created_at,
    )


def _outpass_read(doc: HostelOutpassRequest) -> LeaveOutpassRead:
    return LeaveOutpassRead(
        request_id=doc.request_id,
        kind=HostelRequestKind.OUTPASS.value,
        student_user_id=str(doc.student_user_id),
        resident_id=doc.resident_id,
        status=doc.status,
        from_at=doc.from_at,
        to_at=doc.to_at,
        reason=doc.reason,
        outpass_type=doc.outpass_type.value,
        created_at=doc.created_at,
    )


async def review_request(scope: AccessScope, payload: ApprovalDecision) -> LeaveOutpassRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_leave_manage(scope)
    history_id = f"lah_{uuid4().hex[:10]}"
    if payload.kind == HostelRequestKind.LEAVE.value:
        doc = await HostelLeaveRequest.find_one(
            Eq(HostelLeaveRequest.tenant_id, tenant_id), Eq(HostelLeaveRequest.request_id, payload.request_id)
        )
        if doc is None:
            raise AppError(code="NOT_FOUND", message="Leave request not found", status_code=404)
        if doc.status not in (HostelLeaveOutpassStatus.PENDING_APPROVAL, HostelLeaveOutpassStatus.SUBMITTED):
            raise AppError(code="CONFLICT", message="Request not pending", status_code=409)
        if payload.return_for_correction:
            doc.status = HostelLeaveOutpassStatus.RETURNED_FOR_CORRECTION
        elif payload.approve:
            doc.status = HostelLeaveOutpassStatus.APPROVED
            doc.approver_id = scope.user_id
            await _maybe_mess_exemption(scope, tenant_id, doc)
        else:
            doc.status = HostelLeaveOutpassStatus.REJECTED
            doc.rejection_reason = payload.comment
            doc.approver_id = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
        decision = "approved" if payload.approve else ("returned" if payload.return_for_correction else "rejected")
        await HostelLeaveApprovalHistory(
            tenant_id=tenant_id,
            history_id=history_id,
            request_kind=HostelRequestKind.LEAVE,
            request_id=doc.request_id,
            decision=decision,
            actor_id=scope.user_id,
            comment=payload.comment,
        ).insert()
        await notify_hostel_student(
            tenant_id,
            student_user_id=doc.student_user_id,
            event_type="leave.decision",
            title="Leave request decision",
            body=f"Your leave request was {decision}.",
            aggregate_id=doc.request_id,
        )
        return _leave_read(doc)
    doc = await HostelOutpassRequest.find_one(
        Eq(HostelOutpassRequest.tenant_id, tenant_id), Eq(HostelOutpassRequest.request_id, payload.request_id)
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Outpass not found", status_code=404)
    if doc.status not in (
        HostelLeaveOutpassStatus.PENDING_APPROVAL,
        HostelLeaveOutpassStatus.SUBMITTED,
    ):
        raise AppError(code="CONFLICT", message="Request not pending", status_code=409)
    if payload.return_for_correction:
        doc.status = HostelLeaveOutpassStatus.RETURNED_FOR_CORRECTION
    elif payload.approve:
        doc.status = HostelLeaveOutpassStatus.APPROVED
        doc.approver_id = scope.user_id
    else:
        doc.status = HostelLeaveOutpassStatus.REJECTED
        doc.rejection_reason = payload.comment
        doc.approver_id = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    decision = "approved" if payload.approve else ("returned" if payload.return_for_correction else "rejected")
    await HostelLeaveApprovalHistory(
        tenant_id=tenant_id,
        history_id=history_id,
        request_kind=HostelRequestKind.OUTPASS,
        request_id=doc.request_id,
        decision=decision,
        actor_id=scope.user_id,
        comment=payload.comment,
    ).insert()
    await notify_hostel_student(
        tenant_id,
        student_user_id=doc.student_user_id,
        event_type="outpass.decision",
        title="Outpass decision",
        body=f"Your outpass was {decision}.",
        aggregate_id=doc.request_id,
    )
    return _outpass_read(doc)


async def _maybe_mess_exemption(scope: AccessScope, tenant_id: PydanticObjectId, leave: HostelLeaveRequest) -> None:
    """Apply mess billing adjustment when policy allows exemption on approved leave."""
    leave_type = await HostelLeaveType.find_one(
        Eq(HostelLeaveType.tenant_id, tenant_id), Eq(HostelLeaveType.type_code, leave.leave_type_code)
    )
    if not leave_type:
        return
    policy = leave_type.policy or {}
    if not policy.get("mess_exemption_enabled"):
        return
    daily_credit = float(policy.get("mess_daily_credit", 0))
    if daily_credit <= 0:
        return
    days = max(1, int((leave.expected_return_at - leave.departure_at).days) + 1)
    from app.modules.hostel.mess_models import HostelMessEnrollment, MessEnrollmentStatus

    enr = await HostelMessEnrollment.find_one(
        {"tenant_id": tenant_id, "student_user_id": leave.student_user_id, "status": MessEnrollmentStatus.ACTIVE.value}
    )
    if enr is None:
        return
    await add_billing_adjustment(
        scope,
        BillingAdjustmentCreate(
            enrollment_id=enr.enrollment_id,
            amount_delta=-round(daily_credit * days, 2),
            reason=f"Approved leave mess exemption {leave.request_id}",
            source_type="leave_exemption",
            source_ref=leave.request_id,
        ),
    )


async def record_gate_movement(scope: AccessScope, payload: GateMovementInput) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_gate_manage(scope)
    student_id: PydanticObjectId | None = None
    resident_id: str | None = None
    if payload.kind == HostelRequestKind.LEAVE.value:
        doc = await HostelLeaveRequest.find_one(
            Eq(HostelLeaveRequest.tenant_id, tenant_id), Eq(HostelLeaveRequest.request_id, payload.request_id)
        )
        if doc is None:
            raise AppError(code="NOT_FOUND", message="Leave not found", status_code=404)
        if payload.movement_type == "departure":
            if doc.status != HostelLeaveOutpassStatus.APPROVED:
                raise AppError(code="CONFLICT", message="Departure requires approved leave", status_code=409)
            doc.status = HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE
            doc.departure_recorded_at = utcnow()
            doc.gate_staff_id = scope.user_id
            if doc.resident_id:
                res = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant_id), Eq(HostelResident.resident_id, doc.resident_id))
                if res:
                    res.status = HostelResidentStatus.TEMPORARILY_OUTSIDE
                    res.updated_at = utcnow()
                    await res.save()
        elif payload.movement_type == "return":
            if doc.status not in (HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE, HostelLeaveOutpassStatus.DEPARTURE_RECORDED, HostelLeaveOutpassStatus.OVERDUE):
                raise AppError(code="CONFLICT", message="Return not allowed for current status", status_code=409)
            doc.status = HostelLeaveOutpassStatus.RETURNED
            doc.actual_return_at = utcnow()
            doc.gate_staff_id = scope.user_id
            if doc.resident_id:
                res = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant_id), Eq(HostelResident.resident_id, doc.resident_id))
                if res and res.status == HostelResidentStatus.TEMPORARILY_OUTSIDE:
                    res.status = HostelResidentStatus.CHECKED_IN
                    res.updated_at = utcnow()
                    await res.save()
        elif payload.movement_type == "cancel_departure":
            doc.status = HostelLeaveOutpassStatus.APPROVED
        doc.updated_at = utcnow()
        await doc.save()
        student_id = doc.student_user_id
        resident_id = doc.resident_id
    else:
        doc = await HostelOutpassRequest.find_one(
            Eq(HostelOutpassRequest.tenant_id, tenant_id), Eq(HostelOutpassRequest.request_id, payload.request_id)
        )
        if doc is None:
            raise AppError(code="NOT_FOUND", message="Outpass not found", status_code=404)
        if payload.movement_type == "departure":
            if doc.status != HostelLeaveOutpassStatus.APPROVED:
                raise AppError(code="CONFLICT", message="Departure requires approved outpass", status_code=409)
            doc.status = HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE
            doc.departure_recorded_at = utcnow()
            doc.gate_staff_id = scope.user_id
            if doc.resident_id:
                res = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant_id), Eq(HostelResident.resident_id, doc.resident_id))
                if res:
                    res.status = HostelResidentStatus.TEMPORARILY_OUTSIDE
                    res.updated_at = utcnow()
                    await res.save()
        elif payload.movement_type == "return":
            if doc.status not in (HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE, HostelLeaveOutpassStatus.OVERDUE):
                raise AppError(code="CONFLICT", message="Return not allowed", status_code=409)
            doc.status = HostelLeaveOutpassStatus.RETURNED if doc.actual_return_at is None else HostelLeaveOutpassStatus.CLOSED
            doc.actual_return_at = utcnow()
            doc.gate_staff_id = scope.user_id
            if doc.resident_id:
                res = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant_id), Eq(HostelResident.resident_id, doc.resident_id))
                if res and res.status == HostelResidentStatus.TEMPORARILY_OUTSIDE:
                    res.status = HostelResidentStatus.CHECKED_IN
                    res.updated_at = utcnow()
                    await res.save()
        elif payload.movement_type == "cancel_departure":
            doc.status = HostelLeaveOutpassStatus.APPROVED
        doc.updated_at = utcnow()
        await doc.save()
        student_id = doc.student_user_id
        resident_id = doc.resident_id
    movement_id = f"hgm_{uuid4().hex[:10]}"
    await HostelGateMovement(
        tenant_id=tenant_id,
        movement_id=movement_id,
        request_kind=HostelRequestKind(payload.kind),
        request_id=payload.request_id,
        student_user_id=student_id,
        movement_type=payload.movement_type,
        gate_staff_id=scope.user_id,
        note=payload.note,
    ).insert()
    if student_id:
        await HostelResidentMovementHistory(
            tenant_id=tenant_id,
            student_user_id=student_id,
            resident_id=resident_id,
            event_type=payload.movement_type,
            request_id=payload.request_id,
            detail={"kind": payload.kind},
            actor_id=scope.user_id,
        ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.gate.movement",
        module="hostel_leave",
        resource_type=payload.kind,
        resource_id=payload.request_id,
    )
    return {"movement_id": movement_id, "request_id": payload.request_id}


async def mark_overdue_returns(tenant_id: PydanticObjectId) -> int:
    now = utcnow()
    count = 0
    leave_rows = await HostelLeaveRequest.find(
        {
            "tenant_id": tenant_id,
            "status": {"$in": [HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value, HostelLeaveOutpassStatus.DEPARTURE_RECORDED.value]},
            "expected_return_at": {"$lt": now},
        }
    ).to_list()
    for doc in leave_rows:
        doc.status = HostelLeaveOutpassStatus.OVERDUE
        doc.updated_at = utcnow()
        await doc.save()
        count += 1
    out_rows = await HostelOutpassRequest.find(
        {
            "tenant_id": tenant_id,
            "status": HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value,
            "to_at": {"$lt": now},
        }
    ).to_list()
    for doc in out_rows:
        doc.status = HostelLeaveOutpassStatus.OVERDUE
        doc.updated_at = utcnow()
        await doc.save()
        count += 1
    return count


async def leave_outpass_overview(scope: AccessScope) -> LeaveOutpassOverview:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_leave_read(scope)
    await mark_overdue_returns(tenant_id)
    pending_leave = await HostelLeaveRequest.find(
        {"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.PENDING_APPROVAL.value}
    ).count()
    pending_outpass = await HostelOutpassRequest.find(
        {"tenant_id": tenant_id, "status": {"$in": [HostelLeaveOutpassStatus.PENDING_APPROVAL.value, "pending"]}}
    ).count()
    approved_leave = await HostelLeaveRequest.find(
        {"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.APPROVED.value}
    ).count()
    approved_outpass = await HostelOutpassRequest.find(
        {"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.APPROVED.value}
    ).count()
    outside = (
        await HostelLeaveRequest.find(
            {"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value}
        ).count()
        + await HostelOutpassRequest.find(
            {"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value}
        ).count()
    )
    overdue = (
        await HostelLeaveRequest.find({"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.OVERDUE.value}).count()
        + await HostelOutpassRequest.find({"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.OVERDUE.value}).count()
    )
    cancelled = (
        await HostelLeaveRequest.find({"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.CANCELLED.value}).count()
        + await HostelOutpassRequest.find({"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.CANCELLED.value}).count()
    )
    return LeaveOutpassOverview(
        pending_leave=pending_leave,
        pending_outpass=pending_outpass,
        approved_leave=approved_leave,
        approved_outpass=approved_outpass,
        currently_outside=outside,
        overdue_returns=overdue,
        cancelled=cancelled,
    )


async def list_leave_requests(scope: AccessScope, pagination: Pagination, *, status: HostelLeaveOutpassStatus | None = None) -> Page[LeaveOutpassRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_leave_read(scope)
    q: dict = {"tenant_id": tenant_id}
    if status:
        q["status"] = status.value
    total = await HostelLeaveRequest.find(q).count()
    skip = (pagination.page - 1) * pagination.page_size
    rows = await HostelLeaveRequest.find(q).sort("-created_at").skip(skip).limit(pagination.page_size).to_list()
    return Page(items=[_leave_read(r) for r in rows], total=total, page=pagination.page, page_size=pagination.page_size)


async def list_outpass_requests(scope: AccessScope, pagination: Pagination, *, status: HostelLeaveOutpassStatus | None = None) -> Page[LeaveOutpassRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_leave_read(scope)
    q: dict = {"tenant_id": tenant_id}
    if status:
        q["status"] = status.value
    total = await HostelOutpassRequest.find(q).count()
    skip = (pagination.page - 1) * pagination.page_size
    rows = await HostelOutpassRequest.find(q).sort("-created_at").skip(skip).limit(pagination.page_size).to_list()
    return Page(items=[_outpass_read(r) for r in rows], total=total, page=pagination.page, page_size=pagination.page_size)

