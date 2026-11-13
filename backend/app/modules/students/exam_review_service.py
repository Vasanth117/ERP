"""Revaluation, rechecking, and student marks correction requests."""

from uuid import uuid4

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.exam_review_enums import ExamReviewHistoryAction, ExamReviewRequestStatus, ExamReviewRequestType
from app.modules.students.exam_review_models import (
    StudentExamReviewPaymentReference,
    StudentExamReviewRequestHistory,
    StudentMarksCorrectionRequest,
    StudentRecheckingRequest,
    StudentRevaluationRequest,
)
from app.modules.students.exam_review_schemas import (
    ReviewEligibleSubjectRead,
    ReviewFeeDetailsRead,
    ReviewRequestHistoryRead,
    ReviewRequestRead,
    ReviewRequestSubmitInput,
    RevisedMarkRead,
)
from app.modules.students.integrations.exam_review_reader import (
    fee_verified,
    published_subject_lines,
    review_fee_payment,
    review_window,
    window_open,
    withdrawal_allowed,
)
from app.modules.students.policy import require_student_scope


async def _history(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    request_id: str,
    request_type: ExamReviewRequestType,
    action: ExamReviewHistoryAction,
    note: str | None = None,
) -> None:
    await StudentExamReviewRequestHistory(
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
        request_type=request_type,
        action=action.value,
        note=note,
    ).insert()


async def get_eligible_review_subjects(scope: AccessScope, user: User, season_id: str) -> list[ReviewEligibleSubjectRead]:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_READ)
    tenant_id = require_student_scope(scope)
    lines = await published_subject_lines(tenant_id, user.id, season_id)
    rev_window = await review_window(tenant_id, season_id, "revaluation")
    rec_window = await review_window(tenant_id, season_id, "rechecking")
    open_rev = window_open(rev_window)
    open_rec = window_open(rec_window)
    return [
        ReviewEligibleSubjectRead(
            season_id=season_id,
            course_code=line.course_code,
            eligible_for_revaluation=open_rev and (line.pass_fail or "").lower() in {"pass", "fail"},
            eligible_for_rechecking=open_rec,
            eligible_for_correction=(line.pass_fail or "").lower() == "fail",
            review_window_open=open_rev or open_rec,
        )
        for line in lines
    ]


async def get_review_fee_details(scope: AccessScope, user: User, season_id: str, review_type: str) -> ReviewFeeDetailsRead:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_READ)
    tenant_id = require_student_scope(scope)
    window = await review_window(tenant_id, season_id, review_type)
    if window is None:
        raise AppError(code="NOT_FOUND", message="Review window not configured", status_code=404)
    return ReviewFeeDetailsRead(
        review_type=review_type,
        season_id=season_id,
        fee_required=window.fee_required,
        fee_amount=window.fee_amount,
        fee_code=window.fee_code,
        fee_verified=False,
        application_close_at=window.application_close_at,
    )


async def submit_revaluation(scope: AccessScope, user: User, payload: ReviewRequestSubmitInput) -> ReviewRequestRead:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_MANAGE)
    tenant_id = require_student_scope(scope)
    window = await review_window(tenant_id, payload.season_id, "revaluation")
    if not window_open(window):
        raise AppError(code="DEADLINE_PASSED", message="Revaluation window closed", status_code=403)
    eligible = await get_eligible_review_subjects(scope, user, payload.season_id)
    match = next((e for e in eligible if e.course_code == payload.course_code), None)
    if match is None or not match.eligible_for_revaluation:
        raise AppError(code="NOT_ELIGIBLE", message="Subject not eligible for revaluation", status_code=403)
    request_id = f"rev-{uuid4().hex[:12]}"
    payment = await review_fee_payment(tenant_id, request_id)
    verified = fee_verified(payment, required=window.fee_required if window else False)
    if window and window.fee_required and not verified:
        await StudentExamReviewPaymentReference(
            tenant_id=tenant_id,
            user_id=user.id,
            request_id=request_id,
            fee_code=window.fee_code,
            payment_verified=False,
        ).insert()
    status = ExamReviewRequestStatus.PAYMENT_PENDING if window and window.fee_required and not verified else ExamReviewRequestStatus.SUBMITTED
    row = StudentRevaluationRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=request_id,
        season_id=payload.season_id,
        course_code=payload.course_code,
        component_id=payload.component_id,
        reason=payload.reason,
        status=status,
        fee_verified=verified,
    )
    await row.insert()
    await _history(tenant_id, user.id, request_id, ExamReviewRequestType.REVALUATION, ExamReviewHistoryAction.SUBMITTED)
    await record_audit(
        actor_id=scope.user_id,
        action="student.revaluation.submitted",
        resource_type="student_revaluation_request",
        resource_id=request_id,
        tenant_id=tenant_id,
    )
    return _revaluation_read(row)


def _revaluation_read(row: StudentRevaluationRequest) -> ReviewRequestRead:
    return ReviewRequestRead(
        request_id=row.request_id,
        request_type=ExamReviewRequestType.REVALUATION.value,
        season_id=row.season_id,
        course_code=row.course_code,
        component_id=row.component_id,
        status=row.status.value,
        reason=row.reason,
        fee_verified=row.fee_verified,
        revised_mark_published=row.revised_mark_published,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def submit_rechecking(scope: AccessScope, user: User, payload: ReviewRequestSubmitInput) -> ReviewRequestRead:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_MANAGE)
    tenant_id = require_student_scope(scope)
    window = await review_window(tenant_id, payload.season_id, "rechecking")
    if not window_open(window):
        raise AppError(code="DEADLINE_PASSED", message="Rechecking window closed", status_code=403)
    eligible = await get_eligible_review_subjects(scope, user, payload.season_id)
    match = next((e for e in eligible if e.course_code == payload.course_code), None)
    if match is None or not match.eligible_for_rechecking:
        raise AppError(code="NOT_ELIGIBLE", message="Subject not eligible for rechecking", status_code=403)
    request_id = f"rec-{uuid4().hex[:12]}"
    payment = await review_fee_payment(tenant_id, request_id)
    verified = fee_verified(payment, required=window.fee_required if window else False)
    status = ExamReviewRequestStatus.PAYMENT_PENDING if window and window.fee_required and not verified else ExamReviewRequestStatus.SUBMITTED
    row = StudentRecheckingRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=request_id,
        season_id=payload.season_id,
        course_code=payload.course_code,
        reason=payload.reason,
        status=status,
        fee_verified=verified,
    )
    try:
        await row.insert()
    except DuplicateKeyError as exc:
        raise AppError(code="DUPLICATE_REQUEST", message="Active rechecking request exists", status_code=409) from exc
    await _history(tenant_id, user.id, request_id, ExamReviewRequestType.RECHECKING, ExamReviewHistoryAction.SUBMITTED)
    await record_audit(
        actor_id=scope.user_id,
        action="student.rechecking.submitted",
        resource_type="student_rechecking_request",
        resource_id=request_id,
        tenant_id=tenant_id,
    )
    return ReviewRequestRead(
        request_id=row.request_id,
        request_type=ExamReviewRequestType.RECHECKING.value,
        season_id=row.season_id,
        course_code=row.course_code,
        component_id=None,
        status=row.status.value,
        reason=row.reason,
        fee_verified=row.fee_verified,
        revised_mark_published=False,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def submit_marks_correction(scope: AccessScope, user: User, payload: ReviewRequestSubmitInput) -> ReviewRequestRead:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_MANAGE)
    tenant_id = require_student_scope(scope)
    window = await review_window(tenant_id, payload.season_id, "marks_correction")
    if window is not None and not window_open(window):
        raise AppError(code="DEADLINE_PASSED", message="Correction window closed", status_code=403)
    request_id = f"corr-{uuid4().hex[:12]}"
    row = StudentMarksCorrectionRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=request_id,
        season_id=payload.season_id,
        course_code=payload.course_code,
        component_id=payload.component_id,
        reason=payload.reason,
    )
    await row.insert()
    await _history(tenant_id, user.id, request_id, ExamReviewRequestType.MARKS_CORRECTION, ExamReviewHistoryAction.SUBMITTED)
    await record_audit(
        actor_id=scope.user_id,
        action="student.marks_correction.submitted",
        resource_type="student_marks_correction_request",
        resource_id=request_id,
        tenant_id=tenant_id,
    )
    return ReviewRequestRead(
        request_id=row.request_id,
        request_type=ExamReviewRequestType.MARKS_CORRECTION.value,
        season_id=row.season_id,
        course_code=row.course_code,
        component_id=row.component_id,
        status=row.status.value,
        reason=row.reason,
        fee_verified=False,
        revised_mark_published=False,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def get_review_request_status(scope: AccessScope, user: User, request_id: str) -> ReviewRequestRead:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_READ)
    tenant_id = require_student_scope(scope)
    for model, rtype in (
        (StudentRevaluationRequest, ExamReviewRequestType.REVALUATION),
        (StudentRecheckingRequest, ExamReviewRequestType.RECHECKING),
        (StudentMarksCorrectionRequest, ExamReviewRequestType.MARKS_CORRECTION),
    ):
        row = await model.find_one({"tenant_id": tenant_id, "user_id": user.id, "request_id": request_id})
        if row is not None:
            return ReviewRequestRead(
                request_id=row.request_id,
                request_type=rtype.value,
                season_id=row.season_id,
                course_code=row.course_code,
                component_id=getattr(row, "component_id", None),
                status=row.status.value,
                reason=row.reason,
                fee_verified=getattr(row, "fee_verified", False),
                revised_mark_published=getattr(row, "revised_mark_published", False),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
    raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)


async def withdraw_review_request(scope: AccessScope, user: User, request_id: str) -> ReviewRequestRead:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_MANAGE)
    tenant_id = require_student_scope(scope)
    row = await StudentRevaluationRequest.find_one({"tenant_id": tenant_id, "user_id": user.id, "request_id": request_id})
    rtype = ExamReviewRequestType.REVALUATION
    if row is None:
        row = await StudentRecheckingRequest.find_one({"tenant_id": tenant_id, "user_id": user.id, "request_id": request_id})
        rtype = ExamReviewRequestType.RECHECKING
    if row is None:
        raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
    window = await review_window(tenant_id, row.season_id, rtype.value)
    if not withdrawal_allowed(window):
        raise AppError(code="WITHDRAWAL_CLOSED", message="Withdrawal deadline passed", status_code=403)
    if row.status in {ExamReviewRequestStatus.COMPLETED, ExamReviewRequestStatus.WITHDRAWN}:
        raise AppError(code="INVALID_STATE", message="Cannot withdraw", status_code=409)
    row.status = ExamReviewRequestStatus.WITHDRAWN
    row.updated_at = utcnow()
    await row.save()
    await _history(tenant_id, user.id, request_id, rtype, ExamReviewHistoryAction.WITHDRAWN)
    await record_audit(
        actor_id=scope.user_id,
        action="student.exam_review.withdrawn",
        resource_type="exam_review_request",
        resource_id=request_id,
        tenant_id=tenant_id,
    )
    return await get_review_request_status(scope, user, request_id)


async def review_request_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[ReviewRequestHistoryRead]:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_READ)
    tenant_id = require_student_scope(scope)
    query = StudentExamReviewRequestHistory.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            ReviewRequestHistoryRead(
                request_id=r.request_id,
                request_type=r.request_type.value,
                action=r.action,
                note=r.note,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_revised_published_marks(scope: AccessScope, user: User, season_id: str) -> list[RevisedMarkRead]:
    authorize(scope, Permission.STUDENT_EXAM_REVIEW_READ)
    tenant_id = require_student_scope(scope)
    completed = await StudentRevaluationRequest.find(
        {
            "tenant_id": tenant_id,
            "user_id": user.id,
            "season_id": season_id,
            "status": ExamReviewRequestStatus.COMPLETED,
            "revised_mark_published": True,
        }
    ).to_list()
    if not completed:
        return []
    lines = await published_subject_lines(tenant_id, user.id, season_id)
    by_course = {line.course_code: line for line in lines}
    result: list[RevisedMarkRead] = []
    for req in completed:
        line = by_course.get(req.course_code)
        if line is None or not line.published:
            continue
        result.append(
            RevisedMarkRead(
                season_id=season_id,
                course_code=req.course_code,
                component_id=req.component_id,
                marks_obtained=line.total_obtained,
                max_marks=line.total_max,
                published_at=line.published_at,
            )
        )
    return result
