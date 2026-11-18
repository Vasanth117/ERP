"""Section transfer requests, multi-step approval, transactional completion."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from motor.motor_asyncio import AsyncIOMotorClientSession

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.mongo_transactions import run_in_transaction
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.department_admin.department_scope import department_programme_codes
from app.modules.department_admin.models import (
    DepartmentRequestStatus,
    DepartmentSection,
    DepartmentSectionStatus,
    DepartmentSectionTransferHistory,
    DepartmentSectionTransferRequest,
    SectionTransferApprovalRole,
    SectionTransferInitiator,
    SectionTransferScenario,
)
from app.modules.department_admin.phase3_schemas import (
    SectionTransferCreate,
    SectionTransferRead,
    SectionTransferReview,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.department_admin.section_transfer_workflow import (
    all_steps_approved,
    assert_reviewer_may_act,
    build_approval_chain,
    classify_scenario,
    next_pending_step,
)
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus
from app.modules.students.models import StudentEnrollment, StudentProfile

from app.modules.department_admin.class_management_helpers import (
    assert_programme_in_department,
    resolve_section_def,
    section_enrolled_count,
)


def _batch_labels(payload: SectionTransferCreate) -> tuple[str, str]:
    from_batch = payload.batch_label.strip()
    to_batch = (payload.to_batch_label or payload.batch_label).strip()
    return from_batch, to_batch


def _transfer_read(doc: DepartmentSectionTransferRequest) -> SectionTransferRead:
    from_batch = doc.from_batch_label or (doc.batch_label or "")
    to_batch = doc.to_batch_label or from_batch
    return SectionTransferRead(
        request_id=str(doc.id),
        student_user_id=str(doc.student_user_id),
        from_section_code=doc.from_section_code,
        to_section_code=doc.to_section_code,
        from_batch_label=from_batch,
        to_batch_label=to_batch,
        batch_label=from_batch,
        programme_code=doc.programme_code,
        transfer_scenario=doc.transfer_scenario,
        status=doc.status,
        approval_steps=doc.approval_steps,
        effective_date=doc.effective_date,
        reason=doc.reason,
        created_at=doc.created_at,
    )


async def submit_section_transfer(
    scope: AccessScope,
    user: User,
    payload: SectionTransferCreate,
    *,
    initiator: SectionTransferInitiator = SectionTransferInitiator.DEPARTMENT_ADMIN,
) -> SectionTransferRead:
    if initiator == SectionTransferInitiator.STUDENT:
        authorize(scope, Permission.STUDENT_SECTION_TRANSFER_REQUEST)
        if scope.role != Role.STUDENT or user.id != scope.user_id:
            raise AppError(code="FORBIDDEN", message="Student context required", status_code=403)
    else:
        authorize(scope, Permission.DEPARTMENT_CLASS_MANAGE)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    central_id: PydanticObjectId | None
    institution = None
    if initiator == SectionTransferInitiator.DEPARTMENT_ADMIN:
        central_id, institution = await resolve_authorized_department(scope, user)
        assert institution is not None
        await assert_programme_in_department(institution, payload.programme_code)
    else:
        record_probe = await StudentRecord.find_one(
            Eq(StudentRecord.tenant_id, tenant_id),
            Eq(StudentRecord.user_id, user.id),
        )
        if record_probe is None or record_probe.department_id is None:
            raise AppError(code="FORBIDDEN", message="Student record not found", status_code=403)
        central_id = record_probe.department_id
        from app.modules.college_admin.identity_models import InstitutionDepartment

        institution = await InstitutionDepartment.find_one(
            Eq(InstitutionDepartment.tenant_id, tenant_id),
            Eq(InstitutionDepartment.central_department_id, central_id),
        )
        if institution is None:
            raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)

    from_batch, to_batch = _batch_labels(payload)
    dest_dept = to_object_id(payload.destination_department_id, "destination_department_id") if payload.destination_department_id else None
    scenario = classify_scenario(
        source_department_id=central_id,
        destination_department_id=dest_dept,
        from_batch_label=from_batch,
        to_batch_label=to_batch,
        tenant_match=True,
    )
    if scenario == SectionTransferScenario.CROSS_COLLEGE:
        raise AppError(code="FORBIDDEN", message="Use college administration for cross-college transfers", status_code=403)

    student_id = to_object_id(payload.student_user_id, "student_user_id")
    if initiator == SectionTransferInitiator.STUDENT and student_id != user.id:
        raise AppError(code="FORBIDDEN", message="Students may only request transfers for themselves", status_code=403)

    record = await StudentRecord.find_one(Eq(StudentRecord.tenant_id, tenant_id), Eq(StudentRecord.user_id, student_id))
    if record is None:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    if initiator == SectionTransferInitiator.DEPARTMENT_ADMIN and record.department_id != central_id:
        raise AppError(code="FORBIDDEN", message="Student outside department", status_code=403)

    target_dept = dest_dept or central_id
    if scenario == SectionTransferScenario.CROSS_DEPARTMENT:
        if dest_dept is None:
            raise AppError(code="VALIDATION_ERROR", message="destination_department_id required", status_code=422)

    if payload.idempotency_key:
        existing = await DepartmentSectionTransferRequest.find_one(
            Eq(DepartmentSectionTransferRequest.tenant_id, tenant_id),
            Eq(DepartmentSectionTransferRequest.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return _transfer_read(existing)

    programme_codes = await department_programme_codes(institution)
    code = payload.programme_code.upper()
    if code not in programme_codes:
        raise AppError(code="FORBIDDEN", message="Programme is outside department", status_code=403)

    if scenario != SectionTransferScenario.CROSS_DEPARTMENT:
        await resolve_section_def(tenant_id, central_id, code, from_batch, payload.from_section_code)

    dest_section = await resolve_section_def(
        tenant_id, target_dept, code, to_batch, payload.to_section_code
    )
    if dest_section.status != DepartmentSectionStatus.ACTIVE:
        raise AppError(code="VALIDATION_ERROR", message="Destination section is not active", status_code=422)

    approval_steps = await build_approval_chain(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        scenario=scenario,
    )

    doc = DepartmentSectionTransferRequest(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        central_department_id=central_id,
        destination_central_department_id=dest_dept,
        student_user_id=student_id,
        from_section_code=payload.from_section_code.upper(),
        to_section_code=payload.to_section_code.upper(),
        from_batch_label=from_batch,
        to_batch_label=to_batch,
        batch_label=from_batch,
        programme_code=code,
        to_programme_code=(payload.to_programme_code or payload.programme_code).upper() if payload.to_programme_code else code,
        transfer_scenario=scenario,
        initiator=initiator,
        effective_date=payload.effective_date,
        reason=payload.reason,
        requested_by=user.id,
        idempotency_key=payload.idempotency_key,
        approval_steps=approval_steps,
        student_record_updated_at=record.updated_at,
        destination_section_revision=dest_section.revision,
    )
    await doc.insert()
    await AuditLog(
        actor_id=user.id,
        action="department.section_transfer.request",
        resource_type="department_section_transfer",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        outcome="success",
        metadata={"scenario": scenario.value, "initiator": initiator.value},
    ).insert()
    return _transfer_read(doc)


async def list_section_transfers(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[SectionTransferRead]:
    authorize(scope, Permission.DEPARTMENT_CLASS_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query = DepartmentSectionTransferRequest.find(
        Eq(DepartmentSectionTransferRequest.tenant_id, tenant_id),
        Eq(DepartmentSectionTransferRequest.institution_department_id, institution.id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_transfer_read(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_section_transfer(scope: AccessScope, user: User, request_id: str) -> SectionTransferRead:
    authorize(scope, Permission.DEPARTMENT_CLASS_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentSectionTransferRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.institution_department_id != institution.id:
        raise AppError(code="NOT_FOUND", message="Transfer request not found", status_code=404)
    return _transfer_read(doc)


async def _enqueue_transfer_completed_notification(
    session: AsyncIOMotorClientSession,
    *,
    tenant_id: PydanticObjectId,
    transfer_id: str,
    student_user_id: str,
    payload: dict,
) -> None:
    key = f"section_transfer_completed:{transfer_id}"
    existing = await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id),
        Eq(DomainOutboxEvent.idempotency_key, key),
        session=session,
    )
    if existing:
        return
    event = DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="section_transfer.completed",
        aggregate_type="department_section_transfer",
        aggregate_id=transfer_id,
        payload=payload,
        idempotency_key=key,
        status=OutboxEventStatus.PENDING,
    )
    await event.insert(session=session)


async def _execute_transfer_in_transaction(
    session: AsyncIOMotorClientSession,
    *,
    doc: DepartmentSectionTransferRequest,
    actor_id: PydanticObjectId,
) -> None:
    tenant_id = doc.tenant_id
    target_dept = doc.destination_central_department_id or doc.central_department_id
    record = await StudentRecord.find_one(
        Eq(StudentRecord.tenant_id, tenant_id),
        Eq(StudentRecord.user_id, doc.student_user_id),
        session=session,
    )
    if record is None:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    if doc.student_record_updated_at and record.updated_at != doc.student_record_updated_at:
        raise AppError(
            code="CONFLICT",
            message="Student allocation changed since request; recreate or refresh request",
            status_code=409,
        )

    dest_section = await resolve_section_def(
        tenant_id,
        target_dept,
        doc.programme_code,
        doc.to_batch_label,
        doc.to_section_code,
        session=session,
    )
    if dest_section.status != DepartmentSectionStatus.ACTIVE:
        raise AppError(code="VALIDATION_ERROR", message="Destination section is not active", status_code=422)
    if doc.destination_section_revision is not None and dest_section.revision != doc.destination_section_revision:
        raise AppError(code="CONFLICT", message="Destination section changed; re-validate capacity", status_code=409)

    enrolled = await StudentProfile.find(
        {
            "tenant_id": tenant_id,
            "department_id": target_dept,
            "programme_code": doc.programme_code,
            "batch_label": doc.to_batch_label,
            "section_code": doc.to_section_code,
        },
        session=session,
    ).count()
    if enrolled >= dest_section.capacity:
        raise AppError(code="CONFLICT", message="Destination section at capacity", status_code=409)

    previous_section = record.section_code
    previous_batch = record.batch_label
    record.section_code = doc.to_section_code
    record.batch_label = doc.to_batch_label
    if doc.to_programme_code:
        record.programme_code = doc.to_programme_code
    if doc.destination_central_department_id:
        record.department_id = doc.destination_central_department_id
    record.updated_at = utcnow()
    record.updated_by = actor_id
    await record.save(session=session)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, doc.student_user_id),
        session=session,
    )
    if profile:
        profile.section_code = record.section_code
        profile.batch_label = record.batch_label
        profile.programme_code = record.programme_code
        profile.department_id = record.department_id
        profile.updated_at = utcnow()
        await profile.save(session=session)

    enrollments = await StudentEnrollment.find(
        Eq(StudentEnrollment.tenant_id, tenant_id),
        Eq(StudentEnrollment.user_id, doc.student_user_id),
        session=session,
    ).to_list()
    for line in enrollments:
        if line.section_code == doc.from_section_code:
            line.section_code = doc.to_section_code
            await line.save(session=session)

    history = DepartmentSectionTransferHistory(
        tenant_id=tenant_id,
        transfer_request_id=doc.id,
        student_user_id=doc.student_user_id,
        central_department_id=doc.central_department_id,
        from_section_code=doc.from_section_code,
        to_section_code=doc.to_section_code,
        from_batch_label=doc.from_batch_label,
        to_batch_label=doc.to_batch_label,
        programme_code=doc.programme_code,
        transfer_scenario=doc.transfer_scenario,
        effective_date=doc.effective_date,
        completed_by=actor_id,
    )
    await history.insert(session=session)

    doc.status = DepartmentRequestStatus.COMPLETED
    doc.execution_key = str(doc.id)
    doc.decided_by = actor_id
    doc.decided_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save(session=session)

    await AuditLog(
        actor_id=actor_id,
        action="department.section_transfer.complete",
        resource_type="department_section_transfer",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        outcome="success",
        metadata={
            "previous_section": previous_section,
            "previous_batch": previous_batch,
            "new_section": doc.to_section_code,
        },
    ).insert(session=session)

    await _enqueue_transfer_completed_notification(
        session,
        tenant_id=tenant_id,
        transfer_id=str(doc.id),
        student_user_id=str(doc.student_user_id),
        payload={
            "student_user_id": str(doc.student_user_id),
            "from_section_code": doc.from_section_code,
            "to_section_code": doc.to_section_code,
            "from_batch_label": doc.from_batch_label,
            "to_batch_label": doc.to_batch_label,
        },
    )


async def review_section_transfer(
    scope: AccessScope,
    user: User,
    request_id: str,
    payload: SectionTransferReview,
) -> SectionTransferRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentSectionTransferRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Transfer request not found", status_code=404)
    if scope.role == Role.DEPARTMENT_ADMIN:
        _, institution = await resolve_authorized_department(scope, user)
        if doc.institution_department_id != institution.id and doc.destination_central_department_id != user.department_id:
            raise AppError(code="NOT_FOUND", message="Transfer request not found", status_code=404)
    if doc.status in {DepartmentRequestStatus.COMPLETED, DepartmentRequestStatus.REJECTED, DepartmentRequestStatus.CANCELLED}:
        return _transfer_read(doc)
    if doc.execution_key:
        return _transfer_read(doc)

    pending = next_pending_step(doc.approval_steps)
    if pending is None:
        if all_steps_approved(doc.approval_steps) and doc.status != DepartmentRequestStatus.COMPLETED:
            await run_in_transaction(lambda session: _execute_transfer_in_transaction(session, doc=doc, actor_id=user.id))
            refreshed = await DepartmentSectionTransferRequest.get(doc.id)
            assert refreshed is not None
            return _transfer_read(refreshed)
        return _transfer_read(doc)

    if pending.role == SectionTransferApprovalRole.COLLEGE_ADMIN:
        authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    else:
        authorize(scope, Permission.DEPARTMENT_STUDENT_MANAGE)
    assert_reviewer_may_act(
        scope=scope,
        user_id=user.id,
        requested_by=doc.requested_by,
        initiator=doc.initiator,
        step_role=pending.role,
        source_central_id=doc.central_department_id,
        destination_central_id=doc.destination_central_department_id,
        user_department_id=user.department_id,
        user_role=scope.role,
    )

    if payload.decision == "reject":
        pending.status = DepartmentRequestStatus.REJECTED
        pending.decided_by = user.id
        pending.decided_at = utcnow()
        pending.comment = payload.rejection_reason
        doc.status = DepartmentRequestStatus.REJECTED
        doc.rejection_reason = payload.rejection_reason
        doc.decided_by = user.id
        doc.decided_at = utcnow()
        doc.updated_at = utcnow()
        await doc.save()
        return _transfer_read(doc)

    pending.status = DepartmentRequestStatus.APPROVED
    pending.decided_by = user.id
    pending.decided_at = utcnow()
    doc.updated_at = utcnow()
    if all_steps_approved(doc.approval_steps):
        doc.status = DepartmentRequestStatus.APPROVED
        await doc.save()
        async def _run(session: AsyncIOMotorClientSession) -> None:
            await _execute_transfer_in_transaction(session, doc=doc, actor_id=user.id)

        await run_in_transaction(_run)
        refreshed = await DepartmentSectionTransferRequest.get(doc.id)
        assert refreshed is not None
        return _transfer_read(refreshed)
    doc.status = DepartmentRequestStatus.PENDING
    await doc.save()
    return _transfer_read(doc)


# Backward-compatible aliases used by class_management_service
create_section_transfer = submit_section_transfer