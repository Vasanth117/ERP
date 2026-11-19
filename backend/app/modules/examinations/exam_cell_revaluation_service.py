"""Revaluation, rechecking and supplementary examination services."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultStatus
from app.modules.examinations.exam_cell_grading_models import ExamSemesterResult, ExamStudentSubjectResult
from app.modules.examinations.exam_cell_grading_service import recalculate_for_student_course
from app.modules.examinations.exam_cell_grading_calc import percentage_from_marks
from app.modules.examinations.exam_cell_publication_enums import ExamPublicationStatus
from app.modules.examinations.exam_cell_publication_models import ExamResultPublication
from app.modules.examinations.exam_cell_publication_schemas import ExamPublicationReviseRequest
from app.modules.examinations.exam_cell_publication_service import publish_results, revise_publication
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_revaluation_manage,
    authorize_examination_cell_supplementary_manage,
    require_college_tenant,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus, ExamRegistrationSubjectType
from app.modules.examinations.exam_cell_registration_models import ExamRegistration, ExamRegistrationSubject
from app.modules.examinations.exam_cell_registration_service import register_student
from app.modules.examinations.exam_cell_registration_schemas import ExamRegistrationCreate, ExamRegistrationSubjectInput
from app.modules.examinations.exam_cell_revaluation_enums import (
    ExamRevaluationApplicationStatus,
    ExamRevaluationHistoryAction,
    ExamSupplementaryRegistrationStatus,
)
from app.modules.examinations.exam_cell_revaluation_models import (
    ExamRevaluationApplication,
    ExamRevaluationApproval,
    ExamRevaluationEvaluation,
    ExamRevaluationHistory,
    ExamSupplementaryAttempt,
    ExamSupplementaryRegistration,
)
from app.modules.examinations.exam_cell_revaluation_schemas import (
    ExamRevaluationApplicationRead,
    ExamRevaluationApply,
    ExamRevaluationApprovalDecision,
    ExamRevaluationAssignEvaluator,
    ExamRevaluationRecordEvaluation,
    ExamSupplementaryEligibilityRead,
    ExamSupplementaryRegister,
    ExamSupplementaryRegistrationRead,
)
from app.modules.examinations.exam_review_models import ExaminationReviewFeePayment, ExaminationReviewWindow
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.students.arrear_backlog_enums import BacklogStatus
from app.modules.students.arrear_backlog_models import StudentArrearReference


def _app_id() -> str:
    return f"era_{uuid4().hex[:10]}"


def _eval_id() -> str:
    return f"ere_{uuid4().hex[:10]}"


def _approval_id() -> str:
    return f"erp_{uuid4().hex[:10]}"


def _history_id() -> str:
    return f"erh_{uuid4().hex[:10]}"


def _supp_reg_id() -> str:
    return f"esr_{uuid4().hex[:10]}"


def _attempt_id() -> str:
    return f"esa_{uuid4().hex[:10]}"


async def _reval_history(
    tenant_id: PydanticObjectId,
    *,
    application_id: str,
    action: ExamRevaluationHistoryAction,
    actor_id: PydanticObjectId | None,
    before: dict | None = None,
    after: dict | None = None,
    note: str | None = None,
) -> None:
    await ExamRevaluationHistory(
        tenant_id=tenant_id,
        history_id=_history_id(),
        application_id=application_id,
        action=action,
        actor_id=actor_id,
        before_snapshot=dict(before or {}),
        after_snapshot=dict(after or {}),
        note=note,
    ).insert()


async def _verify_review_fee(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    payment_request_id: str | None,
    fee_code: str | None,
) -> bool:
    if not payment_request_id:
        return False
    pay = await ExaminationReviewFeePayment.find_one(
        Eq(ExaminationReviewFeePayment.tenant_id, tenant_id),
        Eq(ExaminationReviewFeePayment.request_id, payment_request_id),
        Eq(ExaminationReviewFeePayment.student_user_id, student_user_id),
    )
    if pay and pay.status == ExaminationFeePaymentStatus.PAID:
        if fee_code and pay.fee_code != fee_code:
            return False
        return True
    return False


async def _active_review_window(tenant_id: PydanticObjectId, season_id: str | None, review_type: str) -> ExaminationReviewWindow | None:
    if not season_id:
        return None
    return await ExaminationReviewWindow.find_one(
        Eq(ExaminationReviewWindow.tenant_id, tenant_id),
        Eq(ExaminationReviewWindow.season_id, season_id),
        Eq(ExaminationReviewWindow.review_type, review_type),
    )


async def apply_revaluation(scope: AccessScope, actor: User, payload: ExamRevaluationApply) -> ExamRevaluationApplicationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_revaluation_manage(scope)

    student_oid = to_object_id(payload.student_user_id, "student_user_id")
    session_oid = to_object_id(payload.exam_session_id, "exam_session_id")
    course = payload.course_code

    result = await ExamStudentSubjectResult.find_one(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, session_oid),
        Eq(ExamStudentSubjectResult.student_user_id, student_oid),
        Eq(ExamStudentSubjectResult.course_code, course),
        Eq(ExamStudentSubjectResult.status, ExamSubjectResultStatus.APPROVED),
    )
    if result is None:
        raise AppError(code="NOT_FOUND", message="Published approved subject result required", status_code=404)

    publication = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.exam_session_id, session_oid),
        Eq(ExamResultPublication.status, ExamPublicationStatus.PUBLISHED),
    )

    window = await _active_review_window(tenant_id, payload.season_id, payload.application_type.value)
    if window:
        now = utcnow()
        if not (as_utc_aware(window.application_open_at) <= now <= as_utc_aware(window.application_close_at)):
            raise AppError(code="DEADLINE_PASSED", message="Application window closed", status_code=422)
        fee_code = window.fee_code
        fee_amount = window.fee_amount if window.fee_required else 0
    else:
        fee_code = None
        fee_amount = 0

    fee_verified = True if window is None else (not window.fee_required)
    if window and window.fee_required:
        fee_verified = await _verify_review_fee(
            tenant_id,
            student_user_id=student_oid,
            payment_request_id=payload.payment_request_id,
            fee_code=fee_code,
        )
    elif payload.payment_request_id:
        fee_verified = await _verify_review_fee(
            tenant_id,
            student_user_id=student_oid,
            payment_request_id=payload.payment_request_id,
            fee_code=fee_code,
        )

    status = ExamRevaluationApplicationStatus.FEE_VERIFIED if fee_verified else ExamRevaluationApplicationStatus.FEE_PENDING

    doc = ExamRevaluationApplication(
        tenant_id=tenant_id,
        application_id=_app_id(),
        application_type=payload.application_type,
        student_user_id=student_oid,
        exam_session_id=session_oid,
        course_code=course,
        subject_result_id=result.result_id,
        publication_id=publication.publication_id if publication else None,
        season_id=payload.season_id,
        status=status,
        fee_code=fee_code,
        fee_amount=fee_amount,
        fee_verified=fee_verified,
        payment_request_id=payload.payment_request_id,
        deadline_at=window.application_close_at if window else None,
        original_marks=result.marks_obtained,
        original_grade=result.grade_letter,
    )
    await doc.insert()
    await _reval_history(
        tenant_id,
        application_id=doc.application_id,
        action=ExamRevaluationHistoryAction.CREATED,
        actor_id=actor.id,
        after=doc.model_dump(mode="json"),
    )
    return ExamRevaluationApplicationRead.from_doc(doc)


async def assign_revaluation_evaluator(
    scope: AccessScope,
    actor: User,
    application_id: str,
    payload: ExamRevaluationAssignEvaluator,
) -> ExamRevaluationApplicationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_revaluation_manage(scope)

    doc = await ExamRevaluationApplication.find_one(
        Eq(ExamRevaluationApplication.tenant_id, tenant_id),
        Eq(ExamRevaluationApplication.application_id, application_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    if not doc.fee_verified:
        raise AppError(code="FEE_REQUIRED", message="Fee not verified", status_code=422)

    evaluator = to_object_id(payload.evaluator_user_id, "evaluator_user_id")
    doc.evaluator_user_id = evaluator
    doc.status = ExamRevaluationApplicationStatus.ASSIGNED
    doc.updated_at = utcnow()
    await doc.save()
    await _reval_history(
        tenant_id,
        application_id=doc.application_id,
        action=ExamRevaluationHistoryAction.EVALUATOR_ASSIGNED,
        actor_id=actor.id,
        note=str(evaluator),
    )
    return ExamRevaluationApplicationRead.from_doc(doc)


async def record_revaluation_evaluation(
    scope: AccessScope,
    actor: User,
    application_id: str,
    payload: ExamRevaluationRecordEvaluation,
) -> ExamRevaluationApplicationRead:
    tenant_id = require_college_tenant(scope)

    app = await ExamRevaluationApplication.find_one(
        Eq(ExamRevaluationApplication.tenant_id, tenant_id),
        Eq(ExamRevaluationApplication.application_id, application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    is_evaluator = app.evaluator_user_id is not None and actor.id == app.evaluator_user_id
    if is_evaluator:
        pass
    elif Permission.EXAMINATION_CELL_REVALUATION_MANAGE in scope.effective_permissions:
        authorize_examination_cell_revaluation_manage(scope)
    else:
        raise AppError(code="FORBIDDEN", message="Only assigned evaluator may record evaluation", status_code=403)

    result = await ExamStudentSubjectResult.find_one(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.result_id, app.subject_result_id),
    )
    before = result.model_dump(mode="json") if result else {}

    await ExamRevaluationEvaluation(
        tenant_id=tenant_id,
        evaluation_id=_eval_id(),
        application_id=application_id,
        evaluator_user_id=actor.id,
        original_marks=app.original_marks,
        original_max_marks=result.max_marks if result else payload.revised_max_marks,
        revised_marks=payload.revised_marks,
        revised_max_marks=payload.revised_max_marks,
        findings=payload.findings,
    ).insert()

    app.status = ExamRevaluationApplicationStatus.PENDING_APPROVAL
    app.updated_at = utcnow()
    await app.save()
    await _reval_history(
        tenant_id,
        application_id=application_id,
        action=ExamRevaluationHistoryAction.EVALUATION_RECORDED,
        actor_id=actor.id,
        before=before,
        after={"revised_marks": payload.revised_marks},
    )
    return ExamRevaluationApplicationRead.from_doc(app)


async def decide_revaluation(
    scope: AccessScope,
    actor: User,
    application_id: str,
    payload: ExamRevaluationApprovalDecision,
) -> ExamRevaluationApplicationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_revaluation_manage(scope)

    app = await ExamRevaluationApplication.find_one(
        Eq(ExamRevaluationApplication.tenant_id, tenant_id),
        Eq(ExamRevaluationApplication.application_id, application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    if app.status != ExamRevaluationApplicationStatus.PENDING_APPROVAL:
        raise AppError(code="INVALID_STATE", message="Application not pending approval", status_code=409)

    await ExamRevaluationApproval(
        tenant_id=tenant_id,
        approval_id=_approval_id(),
        application_id=application_id,
        approved=payload.approved,
        approver_id=actor.id,
        comment=payload.comment,
    ).insert()

    if not payload.approved:
        app.status = ExamRevaluationApplicationStatus.REJECTED
        app.updated_at = utcnow()
        await app.save()
        await _reval_history(tenant_id, application_id=application_id, action=ExamRevaluationHistoryAction.REJECTED, actor_id=actor.id)
        from app.modules.examinations.exam_cell_notification_triggers import notify_revaluation_update

        await notify_revaluation_update(
            tenant_id,
            student_user_id=app.student_user_id,
            application_id=application_id,
            status_message="Revaluation application rejected",
            exam_session_id=app.exam_session_id,
        )
        return ExamRevaluationApplicationRead.from_doc(app)

    eval_row = await ExamRevaluationEvaluation.find_one(
        Eq(ExamRevaluationEvaluation.tenant_id, tenant_id),
        Eq(ExamRevaluationEvaluation.application_id, application_id),
    )
    if eval_row is None:
        raise AppError(code="NOT_FOUND", message="Evaluation record missing", status_code=404)

    result = await ExamStudentSubjectResult.find_one(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.result_id, app.subject_result_id),
    )
    if result is None:
        raise AppError(code="NOT_FOUND", message="Subject result missing", status_code=404)

    before = result.model_dump(mode="json")
    result.marks_obtained = eval_row.revised_marks
    result.max_marks = eval_row.revised_max_marks
    if eval_row.revised_max_marks and eval_row.revised_marks is not None:
        result.percentage = percentage_from_marks(eval_row.revised_marks, eval_row.revised_max_marks)
    result.status = ExamSubjectResultStatus.PROVISIONAL
    result.calculation_inputs = {
        **result.calculation_inputs,
        "revaluation_application_id": application_id,
        "preserved_original": before,
    }
    result.updated_at = utcnow()
    await result.save()

    app.status = ExamRevaluationApplicationStatus.APPROVED
    app.updated_at = utcnow()
    await app.save()

    await _reval_history(
        tenant_id,
        application_id=application_id,
        action=ExamRevaluationHistoryAction.MARKS_APPLIED,
        actor_id=actor.id,
        before=before,
        after=result.model_dump(mode="json"),
    )

    await recalculate_for_student_course(
        scope,
        actor,
        exam_session_id=str(app.exam_session_id),
        student_user_id=str(app.student_user_id),
        course_code=app.course_code,
    )
    now = utcnow()
    await ExamStudentSubjectResult.find(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, app.exam_session_id),
    ).update({"$set": {"status": ExamSubjectResultStatus.APPROVED.value, "updated_at": now}})
    await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, app.exam_session_id),
    ).update({"$set": {"status": ExamSubjectResultStatus.APPROVED.value, "updated_at": now}})
    await _reval_history(
        tenant_id,
        application_id=application_id,
        action=ExamRevaluationHistoryAction.GRADES_RECALCULATED,
        actor_id=actor.id,
    )

    publication = None
    if app.publication_id:
        publication = await ExamResultPublication.find_one(
            Eq(ExamResultPublication.tenant_id, tenant_id),
            Eq(ExamResultPublication.publication_id, app.publication_id),
        )
    if publication and publication.status == ExamPublicationStatus.PUBLISHED:
        revised = await revise_publication(scope, actor, publication.publication_id, ExamPublicationReviseRequest(note="Revaluation revision"))
        revised_pub = await publish_results(scope, actor, revised.publication_id)
        await _reval_history(
            tenant_id,
            application_id=application_id,
            action=ExamRevaluationHistoryAction.REVISED_PUBLISHED,
            actor_id=actor.id,
            note=revised_pub.publication_id,
        )

    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_revaluation_approved",
        summary=f"Revaluation applied for {app.course_code}",
        exam_session_id=app.exam_session_id,
        metadata={"application_id": application_id},
    )
    from app.modules.examinations.exam_cell_notification_triggers import notify_revaluation_update

    await notify_revaluation_update(
        tenant_id,
        student_user_id=app.student_user_id,
        application_id=application_id,
        status_message="Revaluation approved and marks updated",
        exam_session_id=app.exam_session_id,
    )
    return ExamRevaluationApplicationRead.from_doc(app)


async def supplementary_eligibility(scope: AccessScope, student_user_id: str) -> ExamSupplementaryEligibilityRead:
    tenant_id = require_examination_cell_tenant(scope)
    student_oid = to_object_id(student_user_id, "student_user_id")
    rows = await StudentArrearReference.find(
        Eq(StudentArrearReference.tenant_id, tenant_id),
        Eq(StudentArrearReference.user_id, student_oid),
        Eq(StudentArrearReference.backlog_status, BacklogStatus.PENDING),
    ).to_list()
    codes = sorted({r.course_code.upper() for r in rows if r.course_code})
    restrictions: list[str] = []
    if not codes:
        restrictions.append("No active arrear courses on record")
    return ExamSupplementaryEligibilityRead(student_user_id=student_user_id, eligible_courses=codes, restrictions=restrictions)


async def _link_supplementary_to_session(
    scope: AccessScope,
    actor: User,
    *,
    tenant_id: PydanticObjectId,
    session_oid: PydanticObjectId,
    student_oid: PydanticObjectId,
    course_codes: list[str],
) -> None:
    active = await ExamRegistration.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": student_oid,
            "exam_session_id": session_oid,
            "status": {
                "$nin": [
                    ExamRegistrationStatus.CANCELLED.value,
                    ExamRegistrationStatus.REJECTED.value,
                ]
            },
        }
    )
    if active is None:
        await register_student(
            scope,
            actor,
            ExamRegistrationCreate(
                exam_session_id=str(session_oid),
                student_user_id=str(student_oid),
                subjects=[
                    ExamRegistrationSubjectInput(course_code=code, subject_type=ExamRegistrationSubjectType.SUPPLEMENTARY)
                    for code in course_codes
                ],
                confirm=True,
            ),
        )
        return

    existing = await ExamRegistrationSubject.find(
        Eq(ExamRegistrationSubject.tenant_id, tenant_id),
        Eq(ExamRegistrationSubject.registration_id, active.registration_id),
    ).to_list()
    existing_codes = {s.course_code.upper() for s in existing}
    for code in course_codes:
        if code.upper() in existing_codes:
            continue
        await ExamRegistrationSubject(
            tenant_id=tenant_id,
            registration_id=active.registration_id,
            student_user_id=student_oid,
            exam_session_id=session_oid,
            course_code=code,
            subject_type=ExamRegistrationSubjectType.SUPPLEMENTARY,
        ).insert()


async def register_supplementary(scope: AccessScope, actor: User, payload: ExamSupplementaryRegister) -> ExamSupplementaryRegistrationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_supplementary_manage(scope)

    student_oid = to_object_id(payload.student_user_id, "student_user_id")
    eligibility = await supplementary_eligibility(scope, str(student_oid))
    for code in payload.course_codes:
        if code not in eligibility.eligible_courses:
            raise AppError(code="NOT_ELIGIBLE", message=f"Course {code} not eligible for supplementary", status_code=422)

    fee_verified = True
    if payload.payment_request_id:
        fee_verified = await _verify_review_fee(
            tenant_id,
            student_user_id=student_oid,
            payment_request_id=payload.payment_request_id,
            fee_code="supplementary_exam_fee",
        )

    session_oid = to_object_id(payload.exam_session_id, "exam_session_id") if payload.exam_session_id else None

    doc = ExamSupplementaryRegistration(
        tenant_id=tenant_id,
        registration_id=_supp_reg_id(),
        student_user_id=student_oid,
        exam_session_id=session_oid,
        supplementary_season_id=payload.supplementary_season_id,
        course_codes=payload.course_codes,
        status=ExamSupplementaryRegistrationStatus.FEE_VERIFIED if fee_verified else ExamSupplementaryRegistrationStatus.SUBMITTED,
        fee_verified=fee_verified,
        payment_request_id=payload.payment_request_id,
    )
    await doc.insert()

    if session_oid and fee_verified:
        await _link_supplementary_to_session(
            scope,
            actor,
            tenant_id=tenant_id,
            session_oid=session_oid,
            student_oid=student_oid,
            course_codes=payload.course_codes,
        )
        doc.status = ExamSupplementaryRegistrationStatus.CONFIRMED
        await doc.save()

    prior = await ExamSupplementaryAttempt.find(
        Eq(ExamSupplementaryAttempt.tenant_id, tenant_id),
        Eq(ExamSupplementaryAttempt.student_user_id, student_oid),
        In(ExamSupplementaryAttempt.course_code, payload.course_codes),
    ).to_list()
    attempt_base = max([a.attempt_number for a in prior], default=0)
    for code in payload.course_codes:
        await ExamSupplementaryAttempt(
            tenant_id=tenant_id,
            attempt_id=_attempt_id(),
            registration_id=doc.registration_id,
            student_user_id=student_oid,
            course_code=code,
            exam_session_id=session_oid,
            attempt_number=attempt_base + 1,
        ).insert()

    return ExamSupplementaryRegistrationRead.from_doc(doc)