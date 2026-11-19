"""Examination cell — marks entry and moderation."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from pymongo.errors import DuplicateKeyError

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_marks_enums import (
    ExamMarksCandidateStatus,
    ExamMarksComponentStatus,
    ExamMarksCorrectionStatus,
    ExamMarksHistoryAction,
    ExamMarksSubmissionStatus,
)
from app.modules.examinations.exam_cell_marks_models import (
    ExamMarksComponent,
    ExamMarksCorrection,
    ExamMarksEntry,
    ExamMarksHistory,
    ExamMarksSubmission,
)
from app.modules.examinations.exam_cell_marks_schemas import (
    ExamMarksAccessGrant,
    ExamMarksBulkUpsert,
    ExamMarksCorrectionRead,
    ExamMarksCorrectionRequest,
    ExamMarksEntryRead,
    ExamMarksEntryUpsert,
    ExamMarksHistoryRead,
    ExamMarksImportError,
    ExamMarksImportRequest,
    ExamMarksImportResult,
    ExamMarksComponentInput,
    ExamMarksSubjectSummary,
    ExamMarksSubmissionRead,
    ExamMarksSubmitRequest,
)
from app.modules.examinations.exam_cell_marks_validation import (
    load_assessment_components,
    resolve_assessment_config,
    validate_component_marks,
)
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_marks_enter,
    authorize_examination_cell_marks_manage,
    authorize_examination_cell_marks_moderate,
    authorize_examination_cell_read,
    require_examination_cell_tenant,
)
from app.modules.students.models import StudentProfile


def _submission_id() -> str:
    return f"ems_{uuid4().hex[:10]}"


def _entry_id() -> str:
    return f"eme_{uuid4().hex[:10]}"


def _correction_id() -> str:
    return f"emc_{uuid4().hex[:10]}"


async def _history(
    tenant_id: PydanticObjectId,
    submission_id: str,
    *,
    action: ExamMarksHistoryAction,
    actor_id: PydanticObjectId | None,
    entry_id: str | None = None,
    note: str | None = None,
    metadata: dict | None = None,
) -> None:
    await ExamMarksHistory(
        tenant_id=tenant_id,
        submission_id=submission_id,
        entry_id=entry_id,
        action=action,
        actor_id=actor_id,
        note=note,
        metadata=dict(metadata or {}),
    ).insert()


async def _session(tenant_id: PydanticObjectId, session_oid: PydanticObjectId) -> ExamSession:
    row = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, session_oid))
    if row is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    return row


def _require_tenant(scope: AccessScope) -> PydanticObjectId:
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    return scope.tenant_id


def _is_assigned_examiner(submission: ExamMarksSubmission, actor: User) -> bool:
    allowed = {submission.primary_examiner_user_id, *submission.authorized_examiner_user_ids}
    return actor.id in allowed


def _can_enter_marks(scope: AccessScope, submission: ExamMarksSubmission, actor: User) -> None:
    if Permission.EXAMINATION_CELL_MARKS_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_MARKS in scope.effective_permissions:
        return
    if _is_assigned_examiner(submission, actor):
        return
    authorize_examination_cell_marks_enter(scope)
    raise AppError(code="FORBIDDEN", message="Marks entry not authorized for this submission", status_code=403)


def _can_read_marks(scope: AccessScope, submission: ExamMarksSubmission, actor: User) -> None:
    try:
        authorize_examination_cell_read(scope)
        return
    except AppError:
        pass
    if _has_marks_staff(scope) or _is_assigned_examiner(submission, actor):
        return
    raise AppError(code="FORBIDDEN", message="Marks data is not accessible", status_code=403)


def _has_marks_staff(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_MARKS_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_CELL_MARKS_MODERATE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_MARKS in scope.effective_permissions
    )


def _assert_submission_editable(submission: ExamMarksSubmission) -> None:
    if submission.status in {ExamMarksSubmissionStatus.APPROVED, ExamMarksSubmissionStatus.LOCKED}:
        raise AppError(code="MARKS_LOCKED", message="Submission is locked for changes", status_code=409)


async def grant_marks_access(scope: AccessScope, actor: User, payload: ExamMarksAccessGrant) -> ExamMarksSubmissionRead:
    tenant_id = _require_tenant(scope)
    authorize_examination_cell_marks_manage(scope)

    session_oid = to_object_id(payload.exam_session_id, "exam_session_id")
    session = await _session(tenant_id, session_oid)
    examiner = to_object_id(payload.primary_examiner_user_id, "primary_examiner_user_id")
    others = [to_object_id(x, "authorized_examiner_user_id") for x in payload.authorized_examiner_user_ids]

    existing = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.exam_session_id, session_oid),
        Eq(ExamMarksSubmission.course_code, payload.course_code),
        Eq(ExamMarksSubmission.primary_examiner_user_id, examiner),
    )
    if existing is not None:
        existing.assessment_config_id = payload.assessment_config_id
        existing.authorized_examiner_user_ids = others
        existing.updated_at = utcnow()
        await existing.save()
        await _history(tenant_id, existing.submission_id, action=ExamMarksHistoryAction.ACCESS_GRANTED, actor_id=actor.id)
        return ExamMarksSubmissionRead.from_doc(existing)

    doc = ExamMarksSubmission(
        tenant_id=tenant_id,
        submission_id=_submission_id(),
        exam_session_id=session_oid,
        course_code=payload.course_code,
        assessment_config_id=payload.assessment_config_id,
        primary_examiner_user_id=examiner,
        authorized_examiner_user_ids=others,
    )
    await doc.insert()
    await _history(tenant_id, doc.submission_id, action=ExamMarksHistoryAction.ACCESS_GRANTED, actor_id=actor.id)
    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_marks_access_granted",
        summary=f"Marks entry access for {payload.course_code}",
        exam_session_id=session_oid,
        metadata={"submission_id": doc.submission_id, "examiner": str(examiner), "term": session.semester_label},
    )
    return ExamMarksSubmissionRead.from_doc(doc)


async def get_submission(scope: AccessScope, submission_id: str, *, actor: User | None = None) -> ExamMarksSubmissionRead:
    tenant_id = _require_tenant(scope)
    doc = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, submission_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Marks submission not found", status_code=404)
    if actor is not None:
        _can_read_marks(scope, doc, actor)
    return ExamMarksSubmissionRead.from_doc(doc)


async def _upsert_single_entry(
    tenant_id: PydanticObjectId,
    submission: ExamMarksSubmission,
    session: ExamSession,
    item: ExamMarksEntryUpsert,
    *,
    configured_components: dict,
) -> ExamMarksEntry:
    student_id = to_object_id(item.student_user_id, "student_user_id")
    entry = await ExamMarksEntry.find_one(
        Eq(ExamMarksEntry.tenant_id, tenant_id),
        Eq(ExamMarksEntry.submission_id, submission.submission_id),
        Eq(ExamMarksEntry.student_user_id, student_id),
    )
    if entry is None:
        entry = ExamMarksEntry(
            tenant_id=tenant_id,
            entry_id=_entry_id(),
            submission_id=submission.submission_id,
            exam_session_id=submission.exam_session_id,
            student_user_id=student_id,
            course_code=submission.course_code,
        )

    if entry.locked:
        raise AppError(code="MARKS_LOCKED", message="Student marks entry is locked", status_code=409)

    entry.candidate_status = item.candidate_status
    if entry.id is None:
        await entry.insert()

    total = 0.0
    max_total = 0.0
    for comp in item.components:
        configured = configured_components.get(comp.component_code)
        validate_component_marks(comp, candidate_status=item.candidate_status, configured=configured)
        max_val = configured.max_marks if configured is not None else comp.max_marks
        max_total += max_val
        if item.candidate_status == ExamMarksCandidateStatus.PRESENT and comp.marks_obtained is not None:
            total += comp.marks_obtained

        row = await ExamMarksComponent.find_one(
            Eq(ExamMarksComponent.tenant_id, tenant_id),
            Eq(ExamMarksComponent.entry_id, entry.entry_id),
            Eq(ExamMarksComponent.component_code, comp.component_code),
        )
        if row is None:
            row = ExamMarksComponent(
                tenant_id=tenant_id,
                submission_id=submission.submission_id,
                entry_id=entry.entry_id,
                component_code=comp.component_code,
                component_type=comp.component_type,
                max_marks=max_val,
                min_marks=comp.min_marks,
            )
        row.marks_obtained = comp.marks_obtained
        row.status = ExamMarksComponentStatus.DRAFT
        row.updated_at = utcnow()
        if row.id is None:
            await row.insert()
        else:
            await row.save()

    entry.total_marks = total if item.candidate_status == ExamMarksCandidateStatus.PRESENT else None
    entry.max_marks = max_total if max_total > 0 else None
    entry.updated_at = utcnow()
    await entry.save()
    return entry


async def save_marks_draft(
    scope: AccessScope,
    actor: User,
    submission_id: str,
    payload: ExamMarksEntryUpsert,
) -> ExamMarksEntryRead:
    tenant_id = _require_tenant(scope)
    submission = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, submission_id),
    )
    if submission is None:
        raise AppError(code="NOT_FOUND", message="Marks submission not found", status_code=404)
    _can_enter_marks(scope, submission, actor)
    _assert_submission_editable(submission)

    session = await _session(tenant_id, submission.exam_session_id)
    config = await resolve_assessment_config(
        tenant_id,
        course_code=submission.course_code,
        academic_year_label=session.academic_year_label,
        semester_label=session.semester_label,
        programme_code=None,
        explicit_config_id=submission.assessment_config_id,
    )
    configured: dict = {}
    if config is not None:
        configured = await load_assessment_components(tenant_id, config.config_id)

    entry = await _upsert_single_entry(tenant_id, submission, session, payload, configured_components=configured)
    components = await ExamMarksComponent.find(
        Eq(ExamMarksComponent.tenant_id, tenant_id),
        Eq(ExamMarksComponent.entry_id, entry.entry_id),
    ).to_list()
    comp_reads = [
        ExamMarksComponentInput(
            component_code=c.component_code,
            component_type=c.component_type,
            marks_obtained=c.marks_obtained,
            max_marks=c.max_marks,
            min_marks=c.min_marks,
        )
        for c in components
    ]
    await _history(
        tenant_id,
        submission_id,
        action=ExamMarksHistoryAction.DRAFT_SAVED,
        actor_id=actor.id,
        entry_id=entry.entry_id,
    )
    return ExamMarksEntryRead.from_parts(entry, comp_reads)


async def bulk_save_marks(
    scope: AccessScope,
    actor: User,
    submission_id: str,
    payload: ExamMarksBulkUpsert,
) -> list[ExamMarksEntryRead]:
    results: list[ExamMarksEntryRead] = []
    for item in payload.entries:
        results.append(await save_marks_draft(scope, actor, submission_id, item))
    tenant_id = _require_tenant(scope)
    await _history(
        tenant_id,
        submission_id,
        action=ExamMarksHistoryAction.BULK_SAVED,
        actor_id=actor.id,
        metadata={"count": len(results)},
    )
    return results


async def submit_marks(
    scope: AccessScope,
    actor: User,
    submission_id: str,
    payload: ExamMarksSubmitRequest,
) -> ExamMarksSubmissionRead:
    tenant_id = _require_tenant(scope)
    submission = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, submission_id),
    )
    if submission is None:
        raise AppError(code="NOT_FOUND", message="Marks submission not found", status_code=404)
    _can_enter_marks(scope, submission, actor)
    _assert_submission_editable(submission)

    entries = await ExamMarksEntry.find(
        Eq(ExamMarksEntry.tenant_id, tenant_id),
        Eq(ExamMarksEntry.submission_id, submission_id),
    ).count()
    if entries == 0:
        raise AppError(code="VALIDATION_ERROR", message="Cannot submit without marks entries", status_code=422)

    submission.status = ExamMarksSubmissionStatus.SUBMITTED
    submission.submitted_at = utcnow()
    submission.updated_at = utcnow()
    await submission.save()

    await ExamMarksComponent.find(
        Eq(ExamMarksComponent.tenant_id, tenant_id),
        Eq(ExamMarksComponent.submission_id, submission_id),
    ).update({"$set": {"status": ExamMarksComponentStatus.SUBMITTED.value, "updated_at": utcnow()}})

    await _history(
        tenant_id,
        submission_id,
        action=ExamMarksHistoryAction.SUBMITTED,
        actor_id=actor.id,
        note=payload.note,
    )
    return ExamMarksSubmissionRead.from_doc(submission)


async def moderate_marks(scope: AccessScope, actor: User, submission_id: str) -> ExamMarksSubmissionRead:
    tenant_id = _require_tenant(scope)
    authorize_examination_cell_marks_moderate(scope)
    submission = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, submission_id),
    )
    if submission is None:
        raise AppError(code="NOT_FOUND", message="Marks submission not found", status_code=404)
    if submission.status != ExamMarksSubmissionStatus.SUBMITTED:
        raise AppError(code="INVALID_STATE", message="Only submitted batches can be moderated", status_code=409)

    submission.status = ExamMarksSubmissionStatus.UNDER_MODERATION
    submission.updated_at = utcnow()
    await submission.save()
    await _history(tenant_id, submission_id, action=ExamMarksHistoryAction.MODERATED, actor_id=actor.id)
    return ExamMarksSubmissionRead.from_doc(submission)


async def approve_marks(scope: AccessScope, actor: User, submission_id: str) -> ExamMarksSubmissionRead:
    tenant_id = _require_tenant(scope)
    authorize_examination_cell_marks_moderate(scope)
    submission = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, submission_id),
    )
    if submission is None:
        raise AppError(code="NOT_FOUND", message="Marks submission not found", status_code=404)
    if submission.status not in {ExamMarksSubmissionStatus.SUBMITTED, ExamMarksSubmissionStatus.UNDER_MODERATION}:
        raise AppError(code="INVALID_STATE", message="Submission not ready for approval", status_code=409)

    from app.common.context import get_request_id
    from app.modules.examinations.exam_cell_sod import assert_marks_approval_separation

    await assert_marks_approval_separation(tenant_id, actor, submission, request_id=get_request_id())

    submission.status = ExamMarksSubmissionStatus.APPROVED
    submission.approved_at = utcnow()
    submission.updated_at = utcnow()
    await submission.save()
    await ExamMarksEntry.find(
        Eq(ExamMarksEntry.tenant_id, tenant_id),
        Eq(ExamMarksEntry.submission_id, submission_id),
    ).update({"$set": {"locked": True, "updated_at": utcnow()}})
    await _history(tenant_id, submission_id, action=ExamMarksHistoryAction.LOCKED, actor_id=actor.id)
    return ExamMarksSubmissionRead.from_doc(submission)


async def request_marks_correction(
    scope: AccessScope,
    actor: User,
    submission_id: str,
    payload: ExamMarksCorrectionRequest,
) -> ExamMarksCorrectionRead:
    tenant_id = _require_tenant(scope)
    submission = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, submission_id),
    )
    if submission is None:
        raise AppError(code="NOT_FOUND", message="Marks submission not found", status_code=404)
    _can_enter_marks(scope, submission, actor)

    doc = ExamMarksCorrection(
        tenant_id=tenant_id,
        correction_id=_correction_id(),
        submission_id=submission_id,
        entry_id=payload.entry_id,
        component_code=payload.component_code.upper() if payload.component_code else None,
        requested_marks=payload.requested_marks,
        reason=payload.reason,
        requested_by=actor.id,
    )
    await doc.insert()
    await _history(
        tenant_id,
        submission_id,
        action=ExamMarksHistoryAction.CORRECTION_REQUESTED,
        actor_id=actor.id,
        entry_id=payload.entry_id,
    )
    return ExamMarksCorrectionRead.from_doc(doc)


async def apply_marks_correction(scope: AccessScope, actor: User, correction_id: str, *, approve: bool) -> ExamMarksCorrectionRead:
    tenant_id = _require_tenant(scope)
    authorize_examination_cell_marks_moderate(scope)
    doc = await ExamMarksCorrection.find_one(
        Eq(ExamMarksCorrection.tenant_id, tenant_id),
        Eq(ExamMarksCorrection.correction_id, correction_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    if doc.status != ExamMarksCorrectionStatus.PENDING:
        raise AppError(code="INVALID_STATE", message="Correction already resolved", status_code=409)

    if not approve:
        doc.status = ExamMarksCorrectionStatus.REJECTED
        doc.resolved_by = actor.id
        doc.resolved_at = utcnow()
        await doc.save()
        return ExamMarksCorrectionRead.from_doc(doc)

    entry = await ExamMarksEntry.find_one(
        Eq(ExamMarksEntry.tenant_id, tenant_id),
        Eq(ExamMarksEntry.entry_id, doc.entry_id),
    )
    if entry is None:
        raise AppError(code="NOT_FOUND", message="Marks entry not found", status_code=404)

    submission = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, doc.submission_id),
    )
    if submission is None:
        raise AppError(code="NOT_FOUND", message="Submission not found", status_code=404)

    session = await _session(tenant_id, submission.exam_session_id)
    config = await resolve_assessment_config(
        tenant_id,
        course_code=submission.course_code,
        academic_year_label=session.academic_year_label,
        semester_label=session.semester_label,
        programme_code=None,
        explicit_config_id=submission.assessment_config_id,
    )
    configured = await load_assessment_components(tenant_id, config.config_id) if config else {}

    if doc.component_code:
        component = await ExamMarksComponent.find_one(
            Eq(ExamMarksComponent.tenant_id, tenant_id),
            Eq(ExamMarksComponent.entry_id, doc.entry_id),
            Eq(ExamMarksComponent.component_code, doc.component_code),
        )
        if component is None:
            raise AppError(code="NOT_FOUND", message="Component marks not found", status_code=404)
        payload = ExamMarksComponentInput(
            component_code=component.component_code,
            component_type=component.component_type,
            marks_obtained=doc.requested_marks,
            max_marks=component.max_marks,
            min_marks=component.min_marks,
        )
        validate_component_marks(
            payload,
            candidate_status=entry.candidate_status,
            configured=configured.get(component.component_code),
        )
        component.marks_obtained = doc.requested_marks
        component.updated_at = utcnow()
        await component.save()

    components = await ExamMarksComponent.find(
        Eq(ExamMarksComponent.tenant_id, tenant_id),
        Eq(ExamMarksComponent.entry_id, entry.entry_id),
    ).to_list()
    if entry.candidate_status == ExamMarksCandidateStatus.PRESENT:
        entry.total_marks = sum(c.marks_obtained or 0 for c in components)
    entry.updated_at = utcnow()
    await entry.save()

    doc.status = ExamMarksCorrectionStatus.APPROVED
    doc.resolved_by = actor.id
    doc.resolved_at = utcnow()
    await doc.save()
    await _history(
        tenant_id,
        doc.submission_id,
        action=ExamMarksHistoryAction.CORRECTION_APPLIED,
        actor_id=actor.id,
        entry_id=doc.entry_id,
    )
    return ExamMarksCorrectionRead.from_doc(doc)


async def import_marks(
    scope: AccessScope,
    actor: User,
    submission_id: str,
    payload: ExamMarksImportRequest,
) -> ExamMarksImportResult:
    tenant_id = _require_tenant(scope)
    submission = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, submission_id),
    )
    if submission is None:
        raise AppError(code="NOT_FOUND", message="Marks submission not found", status_code=404)
    _can_enter_marks(scope, submission, actor)
    _assert_submission_editable(submission)

    errors: list[ExamMarksImportError] = []
    accepted = 0
    for idx, row in enumerate(payload.rows):
        student_id: PydanticObjectId | None = None
        try:
            if row.student_user_id:
                student_id = to_object_id(row.student_user_id, "student_user_id")
            elif row.roll_number:
                profile = await StudentProfile.find_one(
                    Eq(StudentProfile.tenant_id, tenant_id),
                    Eq(StudentProfile.roll_number, row.roll_number.strip()),
                )
                if profile is None:
                    raise AppError(code="NOT_FOUND", message="Unknown roll number", status_code=404)
                student_id = profile.user_id
            else:
                raise AppError(code="VALIDATION_ERROR", message="student_user_id or roll_number required", status_code=422)

            item = ExamMarksEntryUpsert(
                student_user_id=str(student_id),
                candidate_status=row.candidate_status,
                components=[
                    ExamMarksComponentInput(
                        component_code=row.component_code,
                        marks_obtained=row.marks_obtained,
                        max_marks=row.max_marks,
                    )
                ],
            )
            await save_marks_draft(scope, actor, submission_id, item)
            accepted += 1
        except AppError as exc:
            errors.append(ExamMarksImportError(row_index=idx, message=exc.message))
        except DuplicateKeyError:
            errors.append(ExamMarksImportError(row_index=idx, message="Duplicate marks entry"))

    if accepted:
        await _history(
            tenant_id,
            submission_id,
            action=ExamMarksHistoryAction.IMPORTED,
            actor_id=actor.id,
            metadata={"accepted": accepted, "rejected": len(errors)},
        )
    return ExamMarksImportResult(accepted=accepted, rejected=len(errors), errors=errors)


async def marks_subject_summary(scope: AccessScope, submission_id: str) -> ExamMarksSubjectSummary:
    tenant_id = _require_tenant(scope)
    submission = await ExamMarksSubmission.find_one(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.submission_id, submission_id),
    )
    if submission is None:
        raise AppError(code="NOT_FOUND", message="Marks submission not found", status_code=404)

    total = await ExamMarksEntry.find(
        Eq(ExamMarksEntry.tenant_id, tenant_id),
        Eq(ExamMarksEntry.submission_id, submission_id),
    ).count()
    entry_rows = await ExamMarksEntry.find(
        Eq(ExamMarksEntry.tenant_id, tenant_id),
        Eq(ExamMarksEntry.submission_id, submission_id),
    ).to_list()
    with_marks = sum(1 for row in entry_rows if row.total_marks is not None)
    return ExamMarksSubjectSummary(
        course_code=submission.course_code,
        entries_total=total,
        entries_with_marks=with_marks,
        submitted=submission.status != ExamMarksSubmissionStatus.DRAFT,
        status=submission.status,
    )


async def marks_history(scope: AccessScope, submission_id: str) -> list[ExamMarksHistoryRead]:
    tenant_id = _require_tenant(scope)
    rows = await ExamMarksHistory.find(
        Eq(ExamMarksHistory.tenant_id, tenant_id),
        Eq(ExamMarksHistory.submission_id, submission_id),
    ).sort("-created_at").to_list()
    return [
        ExamMarksHistoryRead(
            submission_id=row.submission_id,
            action=row.action,
            actor_id=str(row.actor_id) if row.actor_id else None,
            note=row.note,
            created_at=row.created_at,
        )
        for row in rows
    ]