"""Examination cell — result review and approval."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_grading_enums import (
    ExamResultApprovalStage,
    ExamResultReviewAction,
    ExamResultReviewStatus,
    ExamSubjectResultOutcome,
    ExamSubjectResultStatus,
)
from app.modules.examinations.exam_cell_grading_models import ExamSemesterResult, ExamStudentSubjectResult
from app.modules.examinations.exam_cell_marks_models import ExamMarksSubmission
from app.modules.examinations.exam_cell_marks_enums import ExamMarksSubmissionStatus
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_result_approve,
    authorize_examination_cell_result_review,
    require_examination_cell_tenant,
    resolve_department_code_filter,
)
from app.modules.examinations.exam_cell_result_models import (
    ExamResultApprovalWorkflow,
    ExamResultReviewHistory,
    ExamResultReviewRecord,
)
from app.modules.examinations.exam_cell_result_schemas import (
    ExamResultReviewComment,
    ExamResultReviewDecision,
    ExamResultReviewHistoryRead,
    ExamResultReviewRecordRead,
    ExamResultReviewStart,
    ExamResultSessionSummary,
    ExamResultWorkflowRead,
)


def _review_id() -> str:
    return f"err_{uuid4().hex[:10]}"


def _workflow_id() -> str:
    return f"erw_{uuid4().hex[:10]}"


def _history_id() -> str:
    return f"erh_{uuid4().hex[:10]}"


async def _history(
    tenant_id: PydanticObjectId,
    *,
    exam_session_id: PydanticObjectId,
    action: ExamResultReviewAction,
    actor_id: PydanticObjectId | None,
    workflow_id: str | None = None,
    review_id: str | None = None,
    comment: str | None = None,
    metadata: dict | None = None,
) -> None:
    await ExamResultReviewHistory(
        tenant_id=tenant_id,
        history_id=_history_id(),
        exam_session_id=exam_session_id,
        workflow_id=workflow_id,
        review_id=review_id,
        action=action,
        actor_id=actor_id,
        comment=comment,
        metadata=dict(metadata or {}),
    ).insert()


async def start_result_review(scope: AccessScope, actor: User, payload: ExamResultReviewStart) -> ExamResultWorkflowRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_result_review(scope)
    session_oid = to_object_id(payload.exam_session_id, "exam_session_id")

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.exam_session_id, session_oid),
    )
    if workflow is None:
        workflow = ExamResultApprovalWorkflow(
            tenant_id=tenant_id,
            workflow_id=_workflow_id(),
            exam_session_id=session_oid,
            department_code=payload.department_code,
            created_by=actor.id,
        )
        await workflow.insert()

    issues = await _validate_session_results(tenant_id, session_oid)
    review = ExamResultReviewRecord(
        tenant_id=tenant_id,
        review_id=_review_id(),
        exam_session_id=session_oid,
        department_code=payload.department_code,
        status=ExamResultReviewStatus.IN_REVIEW,
        reviewer_comment=payload.comment,
        issues=issues,
        created_by=actor.id,
    )
    await review.insert()

    workflow.current_stage = ExamResultApprovalStage.DEPARTMENT_REVIEW
    workflow.status = ExamResultReviewStatus.IN_REVIEW
    workflow.submitted_at = utcnow()
    workflow.updated_at = utcnow()
    await workflow.save()

    await _history(
        tenant_id,
        exam_session_id=session_oid,
        action=ExamResultReviewAction.DEPARTMENT_REVIEW_STARTED,
        actor_id=actor.id,
        workflow_id=workflow.workflow_id,
        review_id=review.review_id,
        comment=payload.comment,
    )
    return ExamResultWorkflowRead.from_doc(workflow)


async def _validate_session_results(tenant_id: PydanticObjectId, session_oid: PydanticObjectId) -> list[str]:
    issues: list[str] = []
    submissions = await ExamMarksSubmission.find(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.exam_session_id, session_oid),
    ).to_list()
    approved = [s for s in submissions if s.status == ExamMarksSubmissionStatus.APPROVED]
    if not approved:
        issues.append("No approved marks submissions")

    subject_results = await ExamStudentSubjectResult.find(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, session_oid),
    ).to_list()
    if not subject_results:
        issues.append("Provisional subject results missing — run calculation first")

    for row in subject_results:
        if row.outcome == ExamSubjectResultOutcome.INCOMPLETE:
            issues.append(f"Missing/invalid marks for {row.course_code} student {row.student_user_id}")
        if row.grade_point is not None and row.credit_units > 0 and row.credits_earned > row.credit_units:
            issues.append(f"Invalid credits earned for {row.course_code}")

    return issues


async def department_review_comment(
    scope: AccessScope,
    actor: User,
    workflow_id: str,
    payload: ExamResultReviewComment,
) -> ExamResultReviewRecordRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_result_review(scope)
    dept_filter = await resolve_department_code_filter(scope)

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.workflow_id, workflow_id),
    )
    if workflow is None:
        raise AppError(code="NOT_FOUND", message="Workflow not found", status_code=404)
    if dept_filter and workflow.department_code and workflow.department_code.upper() != dept_filter:
        raise AppError(code="FORBIDDEN", message="Department scope mismatch", status_code=403)

    review = await ExamResultReviewRecord.find_one(
        Eq(ExamResultReviewRecord.tenant_id, tenant_id),
        Eq(ExamResultReviewRecord.exam_session_id, workflow.exam_session_id),
    )
    if review is None:
        raise AppError(code="NOT_FOUND", message="Review record not found", status_code=404)

    review.reviewer_comment = payload.comment
    review.status = ExamResultReviewStatus.DEPARTMENT_VERIFIED
    review.updated_at = utcnow()
    await review.save()

    workflow.status = ExamResultReviewStatus.DEPARTMENT_VERIFIED
    workflow.updated_at = utcnow()
    await workflow.save()

    await _history(
        tenant_id,
        exam_session_id=workflow.exam_session_id,
        action=ExamResultReviewAction.DEPARTMENT_COMMENT,
        actor_id=actor.id,
        workflow_id=workflow.workflow_id,
        review_id=review.review_id,
        comment=payload.comment,
    )
    return ExamResultReviewRecordRead.from_doc(review)


async def exam_cell_verify(scope: AccessScope, actor: User, workflow_id: str) -> ExamResultWorkflowRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_result_approve(scope)

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.workflow_id, workflow_id),
    )
    if workflow is None:
        raise AppError(code="NOT_FOUND", message="Workflow not found", status_code=404)
    if workflow.status not in {ExamResultReviewStatus.DEPARTMENT_VERIFIED, ExamResultReviewStatus.IN_REVIEW}:
        raise AppError(code="INVALID_STATE", message="Department review required before exam cell verification", status_code=409)

    issues = await _validate_session_results(tenant_id, workflow.exam_session_id)
    if issues:
        raise AppError(code="VALIDATION_ERROR", message="; ".join(issues[:5]), status_code=422)

    workflow.current_stage = ExamResultApprovalStage.EXAM_CELL_VERIFICATION
    workflow.status = ExamResultReviewStatus.EXAM_CELL_VERIFIED
    workflow.updated_at = utcnow()
    await workflow.save()

    await _history(
        tenant_id,
        exam_session_id=workflow.exam_session_id,
        action=ExamResultReviewAction.EXAM_CELL_VERIFIED,
        actor_id=actor.id,
        workflow_id=workflow.workflow_id,
    )
    return ExamResultWorkflowRead.from_doc(workflow)


async def approve_results(scope: AccessScope, actor: User, workflow_id: str, payload: ExamResultReviewDecision) -> ExamResultWorkflowRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_result_approve(scope)

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.workflow_id, workflow_id),
    )
    if workflow is None:
        raise AppError(code="NOT_FOUND", message="Workflow not found", status_code=404)

    if not payload.approve:
        workflow.current_stage = ExamResultApprovalStage.REJECTED
        workflow.status = ExamResultReviewStatus.REJECTED
        workflow.rejected_at = utcnow()
        workflow.updated_at = utcnow()
        await workflow.save()
        await _history(
            tenant_id,
            exam_session_id=workflow.exam_session_id,
            action=ExamResultReviewAction.REJECTED,
            actor_id=actor.id,
            workflow_id=workflow.workflow_id,
            comment=payload.comment,
        )
        return ExamResultWorkflowRead.from_doc(workflow)

    if workflow.status != ExamResultReviewStatus.EXAM_CELL_VERIFIED:
        raise AppError(code="INVALID_STATE", message="Exam cell verification required before approval", status_code=409)

    now = utcnow()
    await ExamStudentSubjectResult.find(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, workflow.exam_session_id),
    ).update({"$set": {"status": ExamSubjectResultStatus.APPROVED.value, "updated_at": now}})

    await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, workflow.exam_session_id),
    ).update({"$set": {"status": ExamSubjectResultStatus.APPROVED.value, "updated_at": now}})

    workflow.current_stage = ExamResultApprovalStage.APPROVED
    workflow.status = ExamResultReviewStatus.APPROVED
    workflow.approved_at = now
    workflow.updated_at = now
    await workflow.save()

    await _history(
        tenant_id,
        exam_session_id=workflow.exam_session_id,
        action=ExamResultReviewAction.APPROVED,
        actor_id=actor.id,
        workflow_id=workflow.workflow_id,
        comment=payload.comment,
    )
    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_results_approved",
        summary="Session results approved (provisional lock)",
        exam_session_id=workflow.exam_session_id,
        metadata={"workflow_id": workflow.workflow_id},
    )
    return ExamResultWorkflowRead.from_doc(workflow)


async def resubmit_after_rejection(scope: AccessScope, actor: User, workflow_id: str) -> ExamResultWorkflowRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_result_review(scope)

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.workflow_id, workflow_id),
    )
    if workflow is None:
        raise AppError(code="NOT_FOUND", message="Workflow not found", status_code=404)
    if workflow.status != ExamResultReviewStatus.REJECTED:
        raise AppError(code="INVALID_STATE", message="Only rejected workflows can be resubmitted", status_code=409)

    workflow.current_stage = ExamResultApprovalStage.PROVISIONAL
    workflow.status = ExamResultReviewStatus.PENDING
    workflow.rejected_at = None
    workflow.updated_at = utcnow()
    await workflow.save()

    await _history(
        tenant_id,
        exam_session_id=workflow.exam_session_id,
        action=ExamResultReviewAction.RESUBMITTED,
        actor_id=actor.id,
        workflow_id=workflow.workflow_id,
    )
    return ExamResultWorkflowRead.from_doc(workflow)


async def get_session_summary(scope: AccessScope, exam_session_id: str) -> ExamResultSessionSummary:
    tenant_id = require_examination_cell_tenant(scope)
    session_oid = to_object_id(exam_session_id, "exam_session_id")

    subjects = await ExamStudentSubjectResult.find(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, session_oid),
    ).to_list()
    semesters = await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, session_oid),
    ).count()

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.exam_session_id, session_oid),
    )

    missing = sum(1 for s in subjects if s.outcome == ExamSubjectResultOutcome.INCOMPLETE)
    pass_count = sum(1 for s in subjects if s.outcome == ExamSubjectResultOutcome.PASS)
    fail_count = sum(1 for s in subjects if s.outcome == ExamSubjectResultOutcome.FAIL)
    absent_count = sum(1 for s in subjects if s.outcome == ExamSubjectResultOutcome.ABSENT)
    withheld_count = sum(1 for s in subjects if s.outcome == ExamSubjectResultOutcome.WITHHELD)
    malpractice_count = sum(1 for s in subjects if s.outcome == ExamSubjectResultOutcome.MALPRACTICE)

    return ExamResultSessionSummary(
        exam_session_id=exam_session_id,
        subject_results=len(subjects),
        semester_results=semesters,
        pass_count=pass_count,
        fail_count=fail_count,
        absent_count=absent_count,
        withheld_count=withheld_count,
        malpractice_count=malpractice_count,
        missing_marks=missing,
        workflow_stage=workflow.current_stage if workflow else None,
    )


async def review_history(scope: AccessScope, exam_session_id: str) -> list[ExamResultReviewHistoryRead]:
    tenant_id = require_examination_cell_tenant(scope)
    session_oid = to_object_id(exam_session_id, "exam_session_id")
    rows = await ExamResultReviewHistory.find(
        Eq(ExamResultReviewHistory.tenant_id, tenant_id),
        Eq(ExamResultReviewHistory.exam_session_id, session_oid),
    ).sort("-created_at").to_list()
    return [ExamResultReviewHistoryRead.from_doc(r) for r in rows]