"""Hostel application lifecycle services."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.application_models import HostelApplicationReview, HostelApplicationStatusHistory
from app.modules.hostel.application_schemas import (
    HostelApplicationRead,
    HostelApplicationReviewInput,
    HostelApplicationStaffSubmit,
    HostelApplicationSubmit,
)
from app.modules.hostel.eligibility_service import evaluate_hostel_eligibility
from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.hostel_models import HostelApplication
from app.modules.hostel.hostel_notify import notify_hostel_student
from app.modules.hostel.infrastructure_validation import norm_code
from app.modules.hostel.policy import authorize_hostel_application_manage, authorize_hostel_application_read, require_hostel_tenant_scope
from app.modules.hostel.waiting_list_service import add_application_to_waiting_list, ensure_default_waiting_list
from app.modules.students.models import StudentProfile
from app.modules.students.policy import require_student_scope


async def _status_history(
    tenant_id: PydanticObjectId,
    *,
    application_id: str,
    from_status: str | None,
    to_status: str,
    actor_id: PydanticObjectId | None,
    note: str | None = None,
) -> None:
    await HostelApplicationStatusHistory(
        tenant_id=tenant_id,
        application_id=application_id,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        note=note,
    ).insert()


def _app_read(doc: HostelApplication) -> HostelApplicationRead:
    return HostelApplicationRead(
        application_id=doc.application_id,
        student_user_id=str(doc.student_user_id),
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        preferred_hostel_code=doc.preferred_hostel_code,
        preferred_room_type=doc.preferred_room_type,
        status=doc.status,
        reason=doc.reason,
        eligibility_result=doc.eligibility_result,
        internal_remarks=doc.internal_remarks,
        active_offer_id=doc.active_offer_id,
        allocation_id=doc.allocation_id,
        submitted_at=doc.submitted_at,
        updated_at=doc.updated_at,
    )


async def _transition_application(
    tenant_id: PydanticObjectId,
    doc: HostelApplication,
    new_status: HostelApplicationStatus,
    *,
    actor_id: PydanticObjectId | None,
    note: str | None = None,
) -> None:
    prev = doc.status.value
    doc.status = new_status
    doc.updated_at = utcnow()
    await doc.save()
    await _status_history(tenant_id, application_id=doc.application_id, from_status=prev, to_status=new_status.value, actor_id=actor_id, note=note)


async def submit_application(scope: AccessScope, user: User, payload: HostelApplicationSubmit) -> HostelApplicationRead:
    authorize(scope, Permission.STUDENT_RESIDENCE_MANAGE)
    tenant_id = require_student_scope(scope)
    if user.tenant_id != tenant_id:
        raise AppError(code="FORBIDDEN", message="Tenant mismatch", status_code=403)
    open_statuses = [
        HostelApplicationStatus.DRAFT,
        HostelApplicationStatus.SUBMITTED,
        HostelApplicationStatus.UNDER_REVIEW,
        HostelApplicationStatus.ADDITIONAL_INFO_REQUIRED,
        HostelApplicationStatus.APPROVED,
        HostelApplicationStatus.WAITLISTED,
        HostelApplicationStatus.ALLOCATION_OFFERED,
        HostelApplicationStatus.ACCEPTED,
    ]
    open_app = await HostelApplication.find_one(
        Eq(HostelApplication.tenant_id, tenant_id),
        Eq(HostelApplication.student_user_id, user.id),
        Eq(HostelApplication.academic_year_label, payload.academic_year_label),
        In(HostelApplication.status, open_statuses),
    )
    if open_app:
        raise AppError(code="CONFLICT", message="An open application already exists for this academic year", status_code=409)
    profile = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, user.id))
    eligibility = await evaluate_hostel_eligibility(
        tenant_id,
        student_user=user,
        profile=profile,
        academic_year_label=payload.academic_year_label,
        preferred_hostel_code=payload.preferred_hostel_code,
        eligibility_payload=payload.eligibility_payload,
    )
    application_id = f"happ_{uuid4().hex[:12]}"
    doc = HostelApplication(
        tenant_id=tenant_id,
        student_user_id=user.id,
        application_id=application_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        requested_hostel_category=payload.requested_hostel_category,
        preferred_hostel_code=norm_code(payload.preferred_hostel_code) if payload.preferred_hostel_code else None,
        preferred_room_type=payload.preferred_room_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
        reason=payload.reason,
        eligibility_payload=payload.eligibility_payload,
        document_refs=payload.document_refs,
        eligibility_result=eligibility,
        status=HostelApplicationStatus.SUBMITTED,
    )
    await doc.insert()
    await _status_history(tenant_id, application_id=application_id, from_status=None, to_status=doc.status.value, actor_id=user.id)
    await notify_hostel_student(
        tenant_id,
        student_user_id=user.id,
        event_type="application_received",
        title="Hostel application received",
        body=f"Your hostel application {application_id} has been submitted.",
        aggregate_id=application_id,
    )
    return _app_read(doc)


async def staff_submit_application(scope: AccessScope, payload: HostelApplicationStaffSubmit) -> HostelApplicationRead:
    authorize_hostel_application_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    user = await User.find_one(Eq(User.tenant_id, tenant_id), Eq(User.id, student_id))
    if user is None:
        raise AppError(code="NOT_FOUND", message="Student not found", status_code=404)
    submit_payload = HostelApplicationSubmit(**payload.model_dump(exclude={"student_user_id"}))
    student_scope = AccessScope(
        role=user.role,
        user_id=user.id,
        tenant_id=tenant_id,
        department_id=user.department_id,
        effective_permissions=scope.effective_permissions,
    )
    return await submit_application(student_scope, user, submit_payload)


async def list_applications(
    scope: AccessScope,
    pagination: Pagination,
    *,
    status: HostelApplicationStatus | None = None,
    academic_year_label: str | None = None,
    preferred_hostel_code: str | None = None,
    student_user_id: str | None = None,
) -> Page[HostelApplicationRead]:
    authorize_hostel_application_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    query = HostelApplication.find(Eq(HostelApplication.tenant_id, tenant_id))
    if status:
        query = query.find(Eq(HostelApplication.status, status))
    if academic_year_label:
        query = query.find(Eq(HostelApplication.academic_year_label, academic_year_label))
    if preferred_hostel_code:
        query = query.find(Eq(HostelApplication.preferred_hostel_code, norm_code(preferred_hostel_code)))
    if student_user_id:
        query = query.find(Eq(HostelApplication.student_user_id, to_object_id(student_user_id, "student_user_id")))
    total = await query.count()
    rows = await query.sort("-submitted_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_app_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_application(scope: AccessScope, application_id: str, *, student_user: User | None = None) -> HostelApplicationRead:
    if student_user is not None:
        authorize(scope, Permission.STUDENT_RESIDENCE_READ)
        tenant_id = require_student_scope(scope)
    else:
        authorize_hostel_application_read(scope)
        tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelApplication.find_one(Eq(HostelApplication.tenant_id, tenant_id), Eq(HostelApplication.application_id, application_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    if student_user is not None and doc.student_user_id != student_user.id:
        raise AppError(code="FORBIDDEN", message="Not your application", status_code=403)
    return _app_read(doc)


async def review_application(scope: AccessScope, payload: HostelApplicationReviewInput) -> HostelApplicationRead:
    authorize_hostel_application_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelApplication.find_one(
        Eq(HostelApplication.tenant_id, tenant_id),
        Eq(HostelApplication.application_id, payload.application_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    if payload.internal_remarks:
        doc.internal_remarks = payload.internal_remarks
    review_id = f"hrev_{uuid4().hex[:10]}"
    await HostelApplicationReview(
        tenant_id=tenant_id,
        review_id=review_id,
        application_id=doc.application_id,
        decision=payload.decision.value,
        remarks=payload.remarks,
        reviewer_id=scope.user_id,
    ).insert()
    decision = payload.decision
    if decision == HostelApplicationStatus.WAITLISTED:
        list_id = await ensure_default_waiting_list(tenant_id, doc.academic_year_label, doc.preferred_hostel_code)
        await add_application_to_waiting_list(
            tenant_id,
            application=doc,
            list_id=list_id,
            hostel_code=doc.preferred_hostel_code,
            room_type=doc.preferred_room_type,
        )
    await _transition_application(tenant_id, doc, decision, actor_id=scope.user_id, note=payload.remarks)
    event = {
        HostelApplicationStatus.APPROVED: "application_approved",
        HostelApplicationStatus.REJECTED: "application_rejected",
        HostelApplicationStatus.ADDITIONAL_INFO_REQUIRED: "application_info_required",
        HostelApplicationStatus.WAITLISTED: "application_waitlisted",
    }.get(decision, "application_updated")
    await notify_hostel_student(
        tenant_id,
        student_user_id=doc.student_user_id,
        event_type=event,
        title="Hostel application update",
        body=f"Your application {doc.application_id} is now {decision.value}.",
        aggregate_id=doc.application_id,
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.application.review",
        module="hostel",
        resource_type="hostel_application",
        resource_id=doc.application_id,
        metadata={"decision": decision.value},
    )
    return _app_read(doc)