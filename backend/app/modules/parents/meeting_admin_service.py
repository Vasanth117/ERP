"""College admin parent meeting workflow."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.parents.enums import ParentMeetingAppointmentStatus, ParentMeetingRequestStatus
from app.modules.parents.meeting_portal_service import _staff_busy
from app.modules.parents.models import (
    ParentMeetingAppointment,
    ParentMeetingFollowup,
    ParentMeetingHistory,
    ParentMeetingOutcome,
    ParentMeetingRequest,
)
from app.modules.parents.phase5_schemas import ParentMeetingAdminDecision, ParentMeetingOutcomeRecord


async def list_meeting_requests_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentMeetingRequest.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "request_id": r.request_id,
            "parent_user_id": str(r.parent_user_id),
            "student_user_id": str(r.student_user_id),
            "category_code": r.category_code,
            "status": r.status,
            "preferred_start": r.preferred_start,
            "staff_user_id": str(r.staff_user_id) if r.staff_user_id else None,
        }
        for r in rows
    ]


async def decide_meeting_request(
    scope: AccessScope,
    request_id: str,
    payload: ParentMeetingAdminDecision,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    row = await ParentMeetingRequest.find_one({"tenant_id": scope.tenant_id, "request_id": request_id})
    if row is None:
        raise AppError(code="NOT_FOUND", message="Meeting request not found", status_code=404)
    prev = row.status
    decision = payload.decision.lower()
    if decision == "reject":
        row.status = ParentMeetingRequestStatus.REJECTED.value
        row.rejection_reason = payload.rejection_reason
        row.updated_at = utcnow()
        await row.save()
        await ParentMeetingHistory(
            tenant_id=row.tenant_id,
            request_id=request_id,
            from_status=prev,
            to_status=row.status,
            note=payload.rejection_reason,
            changed_by=reviewer_id,
        ).insert()
        return {"request_id": request_id, "status": row.status}

    if decision not in {"confirm", "approve"}:
        raise AppError(code="VALIDATION_ERROR", message="Invalid decision", status_code=422)
    if payload.scheduled_start is None or payload.scheduled_end is None:
        payload_start = row.preferred_start
        payload_end = row.preferred_end
    else:
        payload_start = payload.scheduled_start
        payload_end = payload.scheduled_end
    staff_oid = PydanticObjectId(payload.staff_user_id) if payload.staff_user_id else row.staff_user_id
    if await _staff_busy(row.tenant_id, staff_oid, payload_start, payload_end):
        raise AppError(code="CONFLICT", message="Staff schedule conflict", status_code=409)
    appointment_id = f"mapt_{uuid4().hex[:12]}"
    appt = ParentMeetingAppointment(
        tenant_id=row.tenant_id,
        appointment_id=appointment_id,
        request_id=request_id,
        parent_user_id=row.parent_user_id,
        student_user_id=row.student_user_id,
        staff_user_id=staff_oid,
        department_id=row.department_id,
        category_code=row.category_code,
        scheduled_start=payload_start,
        scheduled_end=payload_end,
        meeting_mode=row.meeting_mode,
        venue_or_link=payload.venue_or_link,
        parent_visible_agenda=payload.parent_visible_agenda,
        staff_preparation_notes=payload.staff_preparation_notes,
        status=ParentMeetingAppointmentStatus.SCHEDULED.value,
    )
    await appt.insert()
    row.status = ParentMeetingRequestStatus.CONFIRMED.value
    row.appointment_id = appointment_id
    row.updated_at = utcnow()
    await row.save()
    await ParentMeetingHistory(
        tenant_id=row.tenant_id,
        request_id=request_id,
        appointment_id=appointment_id,
        from_status=prev,
        to_status=row.status,
        note="Meeting confirmed",
        changed_by=reviewer_id,
    ).insert()
    return {"request_id": request_id, "status": row.status, "appointment_id": appointment_id}


async def record_meeting_outcome(
    scope: AccessScope,
    appointment_id: str,
    payload: ParentMeetingOutcomeRecord,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    appt = await ParentMeetingAppointment.find_one(
        {"tenant_id": scope.tenant_id, "appointment_id": appointment_id}
    )
    if appt is None:
        raise AppError(code="NOT_FOUND", message="Appointment not found", status_code=404)
    existing = await ParentMeetingOutcome.find_one(
        {"tenant_id": scope.tenant_id, "appointment_id": appointment_id}
    )
    if existing:
        existing.parent_visible_summary = payload.parent_visible_summary
        existing.agreed_next_steps = payload.agreed_next_steps
        existing.staff_internal_notes = payload.staff_internal_notes
        existing.recorded_by = reviewer_id
        existing.completed_at = utcnow()
        await existing.save()
    else:
        await ParentMeetingOutcome(
            tenant_id=scope.tenant_id,
            appointment_id=appointment_id,
            parent_visible_summary=payload.parent_visible_summary,
            agreed_next_steps=payload.agreed_next_steps,
            staff_internal_notes=payload.staff_internal_notes,
            recorded_by=reviewer_id,
        ).insert()
    if payload.mark_completed:
        appt.status = ParentMeetingAppointmentStatus.COMPLETED.value
        appt.updated_at = utcnow()
        await appt.save()
        req = await ParentMeetingRequest.find_one(
            {"tenant_id": scope.tenant_id, "request_id": appt.request_id}
        )
        if req:
            req.status = ParentMeetingRequestStatus.COMPLETED.value
            req.updated_at = utcnow()
            await req.save()
    return {"appointment_id": appointment_id, "status": appt.status}