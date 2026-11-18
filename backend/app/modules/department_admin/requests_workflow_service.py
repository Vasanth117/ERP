"""Unified departmental requests inbox — orchestrates canonical workflows."""

from __future__ import annotations

from datetime import datetime, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin import request_categories as cat
from app.modules.department_admin.attendance_oversight_service import review_correction_request as review_attendance_correction
from app.modules.department_admin.models import (
    DepartmentCourseOfferingRequest,
    DepartmentFacultyAssignmentRequest,
    DepartmentRequestCoordinationAction,
    DepartmentRequestCoordinationLog,
    DepartmentRequestCoordinationRecord,
    DepartmentRequestForwardTarget,
    DepartmentRequestStatus,
    DepartmentResourceRequest,
    DepartmentSectionTransferRequest,
    DepartmentStudentCorrectionRequest,
    DepartmentSubstituteRequest,
    DepartmentTimetableChangeRequest,
)
from app.modules.department_admin.phase3_schemas import SectionTransferReview, StudentCorrectionReview
from app.modules.department_admin.phase4_schemas import AttendanceCorrectionReview
from app.modules.department_admin.phase7_schemas import (
    RequestDecisionBody,
    RequestDetailRead,
    RequestEscalateBody,
    RequestFilters,
    RequestForwardBody,
    RequestHistoryRead,
    RequestHistoryRecordRead,
    RequestRejectBody,
    RequestSummaryRead,
    UnifiedRequestListItem,
    UnifiedRequestStatus,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.department_admin.request_aggregator import aggregate_requests
from app.modules.department_admin.student_administration_service import review_correction_request
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


def _assert_not_self_approval(requester_id: PydanticObjectId, actor_id: PydanticObjectId) -> None:
    if requester_id == actor_id:
        raise AppError(code="FORBIDDEN", message="Separation of duties: cannot act on your own request", status_code=403)


async def _get_coord_log(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    category: str,
    source_id: str,
) -> DepartmentRequestCoordinationLog | None:
    return await DepartmentRequestCoordinationLog.find_one(
        Eq(DepartmentRequestCoordinationLog.tenant_id, tenant_id),
        Eq(DepartmentRequestCoordinationLog.central_department_id, central_id),
        Eq(DepartmentRequestCoordinationLog.request_category, category),
        Eq(DepartmentRequestCoordinationLog.source_id, source_id),
    )


async def _ensure_request_visible(
    scope: AccessScope,
    user: User,
    request_id: str,
) -> tuple[str, str, PydanticObjectId, PydanticObjectId, InstitutionDepartment]:
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    category, source_id = cat.parse_request_id(request_id)
    items = await aggregate_requests(
        tenant_id,
        central_id,
        institution.id,
        category_filter=category,
        status_filter=None,
        date_from=None,
        date_to=None,
    )
    if not any(i.request_id == request_id for i in items):
        raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
    return category, source_id, tenant_id, central_id, institution


async def _coord_log(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    category: str,
    source_id: str,
) -> DepartmentRequestCoordinationLog:
    doc = await DepartmentRequestCoordinationLog.find_one(
        Eq(DepartmentRequestCoordinationLog.tenant_id, tenant_id),
        Eq(DepartmentRequestCoordinationLog.request_category, category),
        Eq(DepartmentRequestCoordinationLog.source_id, source_id),
    )
    if doc is None:
        doc = DepartmentRequestCoordinationLog(
            tenant_id=tenant_id,
            central_department_id=central_id,
            request_category=category,
            source_id=source_id,
        )
        await doc.insert()
    return doc


def _apply_coordination_overlay(
    item: UnifiedRequestListItem,
    log: DepartmentRequestCoordinationLog | None,
) -> UnifiedRequestStatus:
    if log is None or not log.records:
        return item.status
    last = log.records[-1]
    if last.action == DepartmentRequestCoordinationAction.REQUEST_INFORMATION:
        return UnifiedRequestStatus.AWAITING_INFORMATION
    if last.action == DepartmentRequestCoordinationAction.FORWARD:
        return UnifiedRequestStatus.FORWARDED
    if last.action == DepartmentRequestCoordinationAction.ESCALATE:
        return UnifiedRequestStatus.ESCALATED
    return item.status


async def list_requests(
    scope: AccessScope,
    user: User,
    *,
    filters: RequestFilters,
    pagination: Pagination,
) -> Page[UnifiedRequestListItem]:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    rows = await aggregate_requests(
        tenant_id,
        central_id,
        institution.id,
        category_filter=filters.category,
        status_filter=filters.status,
        date_from=filters.date_from,
        date_to=filters.date_to,
    )
    if filters.requester_user_id:
        rows = [r for r in rows if r.requester_user_id == filters.requester_user_id]
    enriched: list[UnifiedRequestListItem] = []
    for row in rows:
        category, source_id = cat.parse_request_id(row.request_id)
        log = await DepartmentRequestCoordinationLog.find_one(
            Eq(DepartmentRequestCoordinationLog.tenant_id, tenant_id),
            Eq(DepartmentRequestCoordinationLog.request_category, category),
            Eq(DepartmentRequestCoordinationLog.source_id, source_id),
        )
        status = _apply_coordination_overlay(row, log)
        if filters.status and status != filters.status:
            continue
        if log and log.due_date:
            row = row.model_copy(update={"due_date": log.due_date, "status": status})
        else:
            row = row.model_copy(update={"status": status})
        enriched.append(row)
    total = len(enriched)
    page = enriched[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=page, total=total, limit=pagination.limit, offset=pagination.offset)


async def requests_summary(scope: AccessScope, user: User, *, filters: RequestFilters) -> RequestSummaryRead:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    rows = await aggregate_requests(
        tenant_id,
        central_id,
        institution.id,
        category_filter=filters.category,
        status_filter=None,
        date_from=filters.date_from,
        date_to=filters.date_to,
    )
    by_category: dict[str, int] = {}
    pending = approved = rejected = forwarded = 0
    now = utcnow()
    overdue = 0
    for row in rows:
        by_category[row.category] = by_category.get(row.category, 0) + 1
        category, source_id = cat.parse_request_id(row.request_id)
        log = await DepartmentRequestCoordinationLog.find_one(
            Eq(DepartmentRequestCoordinationLog.tenant_id, tenant_id),
            Eq(DepartmentRequestCoordinationLog.request_category, category),
            Eq(DepartmentRequestCoordinationLog.source_id, source_id),
        )
        status = _apply_coordination_overlay(row, log)
        if status in {UnifiedRequestStatus.PENDING, UnifiedRequestStatus.AWAITING_INFORMATION}:
            pending += 1
        elif status == UnifiedRequestStatus.APPROVED:
            approved += 1
        elif status == UnifiedRequestStatus.REJECTED:
            rejected += 1
        elif status in {UnifiedRequestStatus.FORWARDED, UnifiedRequestStatus.ESCALATED}:
            forwarded += 1
        if log and log.due_date and log.due_date < now and status == UnifiedRequestStatus.PENDING:
            overdue += 1
    return RequestSummaryRead(
        total=len(rows),
        pending=pending,
        awaiting_review=pending,
        approved=approved,
        rejected=rejected,
        forwarded_or_escalated=forwarded,
        overdue=overdue,
        by_category=by_category,
    )


async def _load_canonical(tenant_id: PydanticObjectId, central_id: PydanticObjectId, category: str, source_id: str) -> dict:
    from app.modules.attendance.models import AttendanceCorrectionRequest

    oid = to_object_id(source_id, "source_id")
    if category == cat.ATTENDANCE_CORRECTION:
        doc = await AttendanceCorrectionRequest.get(oid)
        if doc and doc.tenant_id == tenant_id:
            return doc.model_dump(mode="json")
    if category == cat.SECTION_TRANSFER:
        doc = await DepartmentSectionTransferRequest.get(oid)
        if doc and doc.tenant_id == tenant_id:
            return doc.model_dump(mode="json")
    if category == cat.STUDENT_CORRECTION:
        doc = await DepartmentStudentCorrectionRequest.get(oid)
        if doc and doc.central_department_id == central_id:
            return doc.model_dump(mode="json")
    if category == cat.TIMETABLE_CHANGE:
        doc = await DepartmentTimetableChangeRequest.get(oid)
        if doc and doc.tenant_id == tenant_id:
            return doc.model_dump(mode="json")
    if category == cat.SUBSTITUTE_FACULTY:
        doc = await DepartmentSubstituteRequest.get(oid)
        if doc and doc.central_department_id == central_id:
            return doc.model_dump(mode="json")
    if category == cat.FACULTY_ASSIGNMENT:
        doc = await DepartmentFacultyAssignmentRequest.get(oid)
        if doc and doc.central_department_id == central_id:
            return doc.model_dump(mode="json")
    if category == cat.COURSE_OFFERING:
        doc = await DepartmentCourseOfferingRequest.get(oid)
        if doc and doc.central_department_id == central_id:
            return doc.model_dump(mode="json")
    if category == cat.RESOURCE_REQUEST:
        doc = await DepartmentResourceRequest.get(oid)
        if doc and doc.central_department_id == central_id:
            return doc.model_dump(mode="json")
    return {}


async def get_request(scope: AccessScope, user: User, request_id: str) -> RequestDetailRead:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_READ)
    category, source_id, tenant_id, central_id, institution = await _ensure_request_visible(scope, user, request_id)
    items = await aggregate_requests(
        tenant_id, central_id, institution.id, category_filter=category, status_filter=None, date_from=None, date_to=None
    )
    match = next(i for i in items if i.request_id == request_id)
    log = await _get_coord_log(tenant_id, central_id, category, source_id)
    status = _apply_coordination_overlay(match, log)
    canonical = await _load_canonical(tenant_id, central_id, category, source_id)
    return RequestDetailRead(
        request_id=request_id,
        category=category,
        status=status,
        requester_user_id=match.requester_user_id,
        title=match.title,
        reason=match.reason,
        submitted_at=match.submitted_at,
        due_date=log.due_date if log else None,
        assigned_reviewer_user_id=str(log.assigned_reviewer_user_id) if log and log.assigned_reviewer_user_id else None,
        escalation_level=log.escalation_level if log else 0,
        subject_ref=match.subject_ref,
        canonical=canonical,
        coordination_flags={"awaiting_information": status == UnifiedRequestStatus.AWAITING_INFORMATION},
    )


async def _append_coordination(
    *,
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    category: str,
    source_id: str,
    user: User,
    action: DepartmentRequestCoordinationAction,
    comment: str | None,
    forward_target: DepartmentRequestForwardTarget | None = None,
    due_date: datetime | None = None,
    previous_state: str | None = None,
    new_state: str | None = None,
    escalation_delta: int = 0,
) -> DepartmentRequestCoordinationLog:
    log = await _coord_log(tenant_id, central_id, category, source_id)
    log.records.append(
        DepartmentRequestCoordinationRecord(
            action=action,
            actor_user_id=user.id,
            comment=comment,
            forward_target=forward_target,
            previous_state=previous_state,
            new_state=new_state,
        )
    )
    if due_date:
        log.due_date = due_date
    log.escalation_level = max(0, log.escalation_level + escalation_delta)
    log.updated_at = utcnow()
    await log.save()
    return log


async def _queue_notification(tenant_id: PydanticObjectId, key: str, event_type: str, payload: dict) -> None:
    if await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)
    ):
        return
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type="department_request",
        aggregate_id=payload.get("request_id", ""),
        payload=payload,
        idempotency_key=key,
        status=OutboxEventStatus.PENDING,
    ).insert()


async def _simple_approve_reject(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    category: str,
    source_id: str,
    user: User,
    *,
    approve: bool,
    reason: str | None,
) -> None:
    oid = to_object_id(source_id, "source_id")
    now = utcnow()
    if category == cat.TIMETABLE_CHANGE:
        from app.modules.department_admin.models import DepartmentTimetablePlan

        doc = await DepartmentTimetableChangeRequest.get(oid)
        if doc is None or doc.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
        plan = await DepartmentTimetablePlan.get(doc.plan_id)
        if plan is None or plan.tenant_id != tenant_id or plan.central_department_id != central_id:
            raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
        if doc.status != DepartmentRequestStatus.PENDING:
            raise AppError(code="CONFLICT", message="Request already decided", status_code=409)
        _assert_not_self_approval(doc.requested_by, user.id)
        doc.status = DepartmentRequestStatus.APPROVED if approve else DepartmentRequestStatus.REJECTED
        doc.decided_by = user.id
        doc.decided_at = now
        await doc.save()
        return
    if category == cat.SUBSTITUTE_FACULTY:
        doc = await DepartmentSubstituteRequest.get(oid)
        if doc is None or doc.central_department_id != central_id:
            raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
        if doc.status != DepartmentRequestStatus.PENDING:
            raise AppError(code="CONFLICT", message="Request already decided", status_code=409)
        _assert_not_self_approval(doc.requested_by, user.id)
        doc.status = DepartmentRequestStatus.APPROVED if approve else DepartmentRequestStatus.REJECTED
        doc.updated_at = now
        await doc.save()
        return
    if category == cat.FACULTY_ASSIGNMENT:
        doc = await DepartmentFacultyAssignmentRequest.get(oid)
        if doc is None or doc.central_department_id != central_id:
            raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
        if doc.status != DepartmentRequestStatus.PENDING:
            raise AppError(code="CONFLICT", message="Request already decided", status_code=409)
        _assert_not_self_approval(doc.requested_by, user.id)
        doc.status = DepartmentRequestStatus.APPROVED if approve else DepartmentRequestStatus.REJECTED
        doc.updated_at = now
        await doc.save()
        return
    if category == cat.COURSE_OFFERING:
        doc = await DepartmentCourseOfferingRequest.get(oid)
        if doc is None or doc.central_department_id != central_id:
            raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
        if doc.status != DepartmentRequestStatus.PENDING:
            raise AppError(code="CONFLICT", message="Request already decided", status_code=409)
        _assert_not_self_approval(doc.requested_by, user.id)
        doc.status = DepartmentRequestStatus.APPROVED if approve else DepartmentRequestStatus.REJECTED
        doc.updated_at = now
        await doc.save()
        return
    if category == cat.RESOURCE_REQUEST:
        doc = await DepartmentResourceRequest.get(oid)
        if doc is None or doc.central_department_id != central_id:
            raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
        if doc.status != DepartmentRequestStatus.PENDING:
            raise AppError(code="CONFLICT", message="Request already decided", status_code=409)
        _assert_not_self_approval(doc.requested_by, user.id)
        doc.status = DepartmentRequestStatus.APPROVED if approve else DepartmentRequestStatus.REJECTED
        doc.decided_by = user.id
        doc.decided_at = now
        doc.decision_reason = reason
        doc.updated_at = now
        await doc.save()
        return
    raise AppError(code="FORBIDDEN", message="Approve/reject not supported for this category", status_code=403)


async def approve_request(
    scope: AccessScope,
    user: User,
    request_id: str,
    body: RequestDecisionBody,
) -> RequestDetailRead:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_MANAGE)
    category, source_id, tenant_id, central_id, _institution = await _ensure_request_visible(scope, user, request_id)
    if category in cat.FORWARD_ONLY_APPROVE:
        raise AppError(
            code="FORBIDDEN",
            message="Profile changes require college admin; use forward",
            status_code=403,
        )
    if category == cat.SECTION_TRANSFER:
        from app.modules.department_admin.section_transfer_service import review_section_transfer

        await review_section_transfer(
            scope,
            user,
            source_id,
            SectionTransferReview(decision="approve", rejection_reason=None),
        )
    elif category == cat.STUDENT_CORRECTION:
        detail = await get_request(scope, user, request_id)
        _assert_not_self_approval(to_object_id(detail.requester_user_id, "requester"), user.id)
        await review_correction_request(
            scope,
            user,
            source_id,
            StudentCorrectionReview(decision="approve", decision_reason=body.comment),
        )
    elif category == cat.ATTENDANCE_CORRECTION:
        await review_attendance_correction(
            scope,
            user,
            source_id,
            AttendanceCorrectionReview(decision="approve", reviewer_note=body.comment),
        )
    elif category in cat.SIMPLE_APPROVE_CATEGORIES:
        await _simple_approve_reject(tenant_id, central_id, category, source_id, user, approve=True, reason=body.comment)
    else:
        raise AppError(code="NOT_FOUND", message="Request category not supported", status_code=404)
    await record_department_audit(
        actor_id=user.id,
        action="department.request.approved",
        resource_type="department_request",
        resource_id=request_id,
        tenant_id=tenant_id,
        metadata={"category": category},
        central_department_id=central_id,
    )
    key = body.idempotency_key or f"dept_req_approve:{request_id}"
    await _queue_notification(
        tenant_id,
        key,
        "department.request.approved",
        {"request_id": request_id, "category": category},
    )
    return await get_request(scope, user, request_id)


async def reject_request(
    scope: AccessScope,
    user: User,
    request_id: str,
    body: RequestRejectBody,
) -> RequestDetailRead:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_MANAGE)
    category, source_id, tenant_id, central_id, _institution = await _ensure_request_visible(scope, user, request_id)
    if category in cat.FORWARD_ONLY_APPROVE:
        raise AppError(code="FORBIDDEN", message="Use forward or cancel for profile changes", status_code=403)
    if category == cat.SECTION_TRANSFER:
        from app.modules.department_admin.section_transfer_service import review_section_transfer

        await review_section_transfer(
            scope,
            user,
            source_id,
            SectionTransferReview(decision="reject", rejection_reason=body.rejection_reason),
        )
    elif category == cat.STUDENT_CORRECTION:
        await review_correction_request(
            scope,
            user,
            source_id,
            StudentCorrectionReview(decision="reject", decision_reason=body.rejection_reason),
        )
    elif category == cat.ATTENDANCE_CORRECTION:
        await review_attendance_correction(
            scope,
            user,
            source_id,
            AttendanceCorrectionReview(decision="reject", reviewer_note=body.rejection_reason),
        )
    elif category in cat.SIMPLE_APPROVE_CATEGORIES:
        await _simple_approve_reject(
            tenant_id, central_id, category, source_id, user, approve=False, reason=body.rejection_reason
        )
    else:
        raise AppError(code="NOT_FOUND", message="Request category not supported", status_code=404)
    await record_department_audit(
        actor_id=user.id,
        action="department.request.rejected",
        resource_type="department_request",
        resource_id=request_id,
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return await get_request(scope, user, request_id)


async def request_more_information(
    scope: AccessScope,
    user: User,
    request_id: str,
    body: RequestDecisionBody,
) -> RequestDetailRead:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_MANAGE)
    category, source_id, tenant_id, central_id, _institution = await _ensure_request_visible(scope, user, request_id)
    detail = await get_request(scope, user, request_id)
    await _append_coordination(
        tenant_id=tenant_id,
        central_id=central_id,
        category=category,
        source_id=source_id,
        user=user,
        action=DepartmentRequestCoordinationAction.REQUEST_INFORMATION,
        comment=body.comment,
        previous_state=detail.status.value,
        new_state=UnifiedRequestStatus.AWAITING_INFORMATION.value,
    )
    await _queue_notification(
        tenant_id,
        body.idempotency_key or f"dept_req_info:{request_id}",
        "department.request.information_requested",
        {"request_id": request_id, "category": category},
    )
    return await get_request(scope, user, request_id)


async def forward_request(
    scope: AccessScope,
    user: User,
    request_id: str,
    body: RequestForwardBody,
) -> RequestDetailRead:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_MANAGE)
    category, source_id, tenant_id, central_id, _institution = await _ensure_request_visible(scope, user, request_id)
    try:
        target = DepartmentRequestForwardTarget(body.forward_target)
    except ValueError as exc:
        raise AppError(code="VALIDATION_ERROR", message="Invalid forward_target", status_code=422) from exc
    detail = await get_request(scope, user, request_id)
    await _append_coordination(
        tenant_id=tenant_id,
        central_id=central_id,
        category=category,
        source_id=source_id,
        user=user,
        action=DepartmentRequestCoordinationAction.FORWARD,
        comment=body.comment,
        forward_target=target,
        due_date=body.due_date,
        previous_state=detail.status.value,
        new_state=UnifiedRequestStatus.FORWARDED.value,
    )
    await _queue_notification(
        tenant_id,
        body.idempotency_key or f"dept_req_fwd:{request_id}:{target.value}",
        "department.request.forwarded",
        {"request_id": request_id, "forward_target": target.value},
    )
    return await get_request(scope, user, request_id)


async def escalate_request(
    scope: AccessScope,
    user: User,
    request_id: str,
    body: RequestEscalateBody,
) -> RequestDetailRead:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_MANAGE)
    category, source_id, tenant_id, central_id, _institution = await _ensure_request_visible(scope, user, request_id)
    detail = await get_request(scope, user, request_id)
    await _append_coordination(
        tenant_id=tenant_id,
        central_id=central_id,
        category=category,
        source_id=source_id,
        user=user,
        action=DepartmentRequestCoordinationAction.ESCALATE,
        comment=body.comment,
        due_date=body.due_date,
        previous_state=detail.status.value,
        new_state=UnifiedRequestStatus.ESCALATED.value,
        escalation_delta=1,
    )
    await _queue_notification(
        tenant_id,
        body.idempotency_key or f"dept_req_esc:{request_id}",
        "department.request.escalated",
        {"request_id": request_id},
    )
    return await get_request(scope, user, request_id)


async def request_history(scope: AccessScope, user: User, request_id: str) -> RequestHistoryRead:
    authorize(scope, Permission.DEPARTMENT_REQUESTS_READ)
    category, source_id, tenant_id, central_id, _institution = await _ensure_request_visible(scope, user, request_id)
    detail = await get_request(scope, user, request_id)
    if detail.request_id != request_id:
        raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
    log = await DepartmentRequestCoordinationLog.find_one(
        Eq(DepartmentRequestCoordinationLog.tenant_id, tenant_id),
        Eq(DepartmentRequestCoordinationLog.request_category, category),
        Eq(DepartmentRequestCoordinationLog.source_id, source_id),
    )
    coordination: list[RequestHistoryRecordRead] = []
    if log:
        coordination = [
            RequestHistoryRecordRead(
                action=r.action.value,
                actor_user_id=str(r.actor_user_id),
                comment=r.comment,
                forward_target=r.forward_target.value if r.forward_target else None,
                previous_state=r.previous_state,
                new_state=r.new_state,
                created_at=r.created_at,
            )
            for r in log.records
        ]
    canonical_history: list[dict] = []
    if category == cat.SECTION_TRANSFER:
        doc = await DepartmentSectionTransferRequest.get(to_object_id(source_id, "source_id"))
        if doc and doc.tenant_id == tenant_id and (
            doc.central_department_id == central_id or doc.destination_central_department_id == central_id
        ):
            canonical_history = [s.model_dump(mode="json") for s in doc.approval_steps]
    return RequestHistoryRead(
        request_id=request_id,
        canonical_history=canonical_history,
        coordination_history=coordination,
    )