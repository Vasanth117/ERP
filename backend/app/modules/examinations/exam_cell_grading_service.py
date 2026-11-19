"""Examination cell — grading policies and GPA/CGPA calculation."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In
from pymongo.errors import DuplicateKeyError

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_grading_calc import (
    apply_supplementary_cap,
    compute_gpa,
    credits_earned_for_outcome,
    outcome_from_candidate_status,
    percentage_from_marks,
    resolve_boundary,
    round_value,
)
from app.modules.examinations.exam_cell_grading_enums import (
    ExamGradingPolicyStatus,
    ExamSubjectResultOutcome,
    ExamSubjectResultStatus,
)
from app.modules.examinations.exam_cell_grading_models import (
    ExamCgpaCalculation,
    ExamGpaCalculation,
    ExamGradeBoundary,
    ExamGradingPolicy,
    ExamGradingPolicyVersion,
    ExamSemesterResult,
    ExamStudentSubjectResult,
)
from app.modules.examinations.exam_cell_grading_schemas import (
    ExamGradeBoundaryInput,
    ExamGradeBoundaryRead,
    ExamGradingPolicyActivate,
    ExamGradingPolicyCreate,
    ExamGradingPolicyRead,
    ExamGradingPolicyVersionRead,
    ExamProvisionalCalculateRequest,
    ExamProvisionalCalculateSummary,
    ExamSemesterResultRead,
    ExamStudentSubjectResultRead,
)
from app.modules.examinations.exam_cell_marks_enums import (
    ExamMarksCandidateStatus,
    ExamMarksSubmissionStatus,
)
from app.modules.examinations.exam_cell_marks_models import ExamMarksEntry, ExamMarksSubmission
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_grading_manage,
    require_examination_cell_tenant,
)
from app.modules.students.curriculum_models import CourseCatalogReference
from app.modules.students.models import StudentProfile


def _policy_id() -> str:
    return f"egp_{uuid4().hex[:10]}"


def _boundary_id() -> str:
    return f"egb_{uuid4().hex[:10]}"


def _result_id() -> str:
    return f"esr_{uuid4().hex[:10]}"


def _semester_result_id() -> str:
    return f"esm_{uuid4().hex[:10]}"


def _gpa_id() -> str:
    return f"egpa_{uuid4().hex[:10]}"


def _cgpa_id() -> str:
    return f"ecgpa_{uuid4().hex[:10]}"


def _validate_boundaries(rows: list[ExamGradeBoundaryInput]) -> None:
    for row in rows:
        if row.min_percent > row.max_percent:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Invalid boundary range for grade {row.grade_letter}",
                status_code=422,
            )


async def _session(tenant_id: PydanticObjectId, session_oid: PydanticObjectId) -> ExamSession:
    row = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, session_oid))
    if row is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    return row


async def create_grading_policy(scope: AccessScope, actor: User, payload: ExamGradingPolicyCreate) -> ExamGradingPolicyRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_grading_manage(scope)
    _validate_boundaries(payload.boundaries)

    policy = ExamGradingPolicy(
        tenant_id=tenant_id,
        policy_id=_policy_id(),
        policy_code=payload.policy_code,
        title=payload.title.strip(),
        programme_code=payload.programme_code,
        batch_label=payload.batch_label,
        academic_year_label=payload.academic_year_label,
        grade_system=payload.grade_system,
        passing_min_percent=payload.passing_min_percent,
        min_grade_point_to_pass=payload.min_grade_point_to_pass,
        theory_min_percent=payload.theory_min_percent,
        practical_min_percent=payload.practical_min_percent,
        mark_rounding=payload.mark_rounding,
        decimal_precision=payload.decimal_precision,
        arrear_rules=dict(payload.arrear_rules),
        supplementary_rules=dict(payload.supplementary_rules),
        effective_from=payload.effective_from,
        created_by=actor.id,
    )
    try:
        await policy.insert()
    except DuplicateKeyError as exc:
        raise AppError(code="CONFLICT", message="Grading policy code already exists", status_code=409) from exc

    for item in payload.boundaries:
        await ExamGradeBoundary(
            tenant_id=tenant_id,
            boundary_id=_boundary_id(),
            policy_id=policy.policy_id,
            min_percent=item.min_percent,
            max_percent=item.max_percent,
            grade_letter=item.grade_letter.strip().upper(),
            grade_point=item.grade_point,
            is_passing=item.is_passing,
            component_scope=item.component_scope,
            sort_order=item.sort_order,
        ).insert()

    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_grading_policy_created",
        summary=f"Policy {policy.policy_code} created",
        metadata={"policy_id": policy.policy_id},
    )
    return ExamGradingPolicyRead.from_doc(policy)


async def list_grade_boundaries(scope: AccessScope, policy_id: str) -> list[ExamGradeBoundaryRead]:
    tenant_id = require_examination_cell_tenant(scope)
    rows = await ExamGradeBoundary.find(
        Eq(ExamGradeBoundary.tenant_id, tenant_id),
        Eq(ExamGradeBoundary.policy_id, policy_id),
    ).sort("+sort_order").to_list()
    return [ExamGradeBoundaryRead.from_doc(r) for r in rows]


async def activate_grading_policy(
    scope: AccessScope,
    actor: User,
    policy_id: str,
    payload: ExamGradingPolicyActivate,
) -> ExamGradingPolicyVersionRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_grading_manage(scope)

    policy = await ExamGradingPolicy.find_one(
        Eq(ExamGradingPolicy.tenant_id, tenant_id),
        Eq(ExamGradingPolicy.policy_id, policy_id),
    )
    if policy is None:
        raise AppError(code="NOT_FOUND", message="Grading policy not found", status_code=404)

    boundaries = await ExamGradeBoundary.find(
        Eq(ExamGradeBoundary.tenant_id, tenant_id),
        Eq(ExamGradeBoundary.policy_id, policy_id),
    ).to_list()
    if not boundaries:
        raise AppError(code="VALIDATION_ERROR", message="Policy has no grade boundaries", status_code=422)

    old_active = await ExamGradingPolicy.find(
        Eq(ExamGradingPolicy.tenant_id, tenant_id),
        Eq(ExamGradingPolicy.status, ExamGradingPolicyStatus.ACTIVE),
    ).to_list()
    for row in old_active:
        if row.policy_id == policy.policy_id:
            continue
        if policy.programme_code and row.programme_code and row.programme_code != policy.programme_code:
            continue
        row.status = ExamGradingPolicyStatus.SUPERSEDED
        row.updated_at = utcnow()
        await row.save()

    policy.status = ExamGradingPolicyStatus.ACTIVE
    policy.version += 1
    if payload.effective_from:
        policy.effective_from = payload.effective_from
    policy.updated_at = utcnow()
    await policy.save()

    snapshot = policy.model_dump(mode="json")
    version = ExamGradingPolicyVersion(
        tenant_id=tenant_id,
        policy_id=policy.policy_id,
        version_number=policy.version,
        snapshot=snapshot,
        boundaries_snapshot=[b.model_dump(mode="json") for b in boundaries],
        effective_from=policy.effective_from,
        change_summary=payload.change_summary,
        created_by=actor.id,
    )
    await version.insert()
    return ExamGradingPolicyVersionRead.from_doc(version)


async def resolve_active_policy(
    tenant_id: PydanticObjectId,
    *,
    session: ExamSession,
    explicit_policy_id: str | None,
    programme_code: str | None,
) -> tuple[ExamGradingPolicy, list[ExamGradeBoundary]]:
    if explicit_policy_id:
        policy = await ExamGradingPolicy.find_one(
            Eq(ExamGradingPolicy.tenant_id, tenant_id),
            Eq(ExamGradingPolicy.policy_id, explicit_policy_id),
        )
        if policy is None:
            raise AppError(code="NOT_FOUND", message="Grading policy not found", status_code=404)
    else:
        prog = programme_code or None
        filters = [
            Eq(ExamGradingPolicy.tenant_id, tenant_id),
            Eq(ExamGradingPolicy.status, ExamGradingPolicyStatus.ACTIVE),
        ]
        candidates = await ExamGradingPolicy.find(*filters).to_list()
        policy = None
        for row in candidates:
            if prog and row.programme_code and row.programme_code != prog:
                continue
            if row.academic_year_label and row.academic_year_label != session.academic_year_label:
                continue
            policy = row
            break
        if policy is None and candidates:
            policy = candidates[0]
        if policy is None:
            raise AppError(code="NOT_FOUND", message="No active grading policy for this session", status_code=404)

    boundaries = await ExamGradeBoundary.find(
        Eq(ExamGradeBoundary.tenant_id, tenant_id),
        Eq(ExamGradeBoundary.policy_id, policy.policy_id),
    ).to_list()
    return policy, boundaries


async def _credit_units(
    tenant_id: PydanticObjectId,
    *,
    session: ExamSession,
    course_code: str,
    programme_code: str | None,
) -> float:
    filters = {
        "tenant_id": tenant_id,
        "course_code": course_code,
        "academic_year_label": session.academic_year_label,
        "semester_label": session.semester_label,
    }
    if programme_code:
        filters["programme_code"] = programme_code
    ref = await CourseCatalogReference.find_one(filters)
    return float(ref.credit_units) if ref else 0.0


async def calculate_provisional_results(
    scope: AccessScope,
    actor: User,
    payload: ExamProvisionalCalculateRequest,
) -> ExamProvisionalCalculateSummary:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_grading_manage(scope)

    session_oid = to_object_id(payload.exam_session_id, "exam_session_id")
    session = await _session(tenant_id, session_oid)
    policy, boundaries = await resolve_active_policy(
        tenant_id,
        session=session,
        explicit_policy_id=payload.policy_id,
        programme_code=payload.programme_code,
    )

    submissions = await ExamMarksSubmission.find(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.exam_session_id, session_oid),
        Eq(ExamMarksSubmission.status, ExamMarksSubmissionStatus.APPROVED),
    ).to_list()
    if not submissions:
        raise AppError(code="VALIDATION_ERROR", message="No approved marks submissions for session", status_code=422)

    submission_ids = [s.submission_id for s in submissions]
    entries = await ExamMarksEntry.find(
        Eq(ExamMarksEntry.tenant_id, tenant_id),
        In(ExamMarksEntry.submission_id, submission_ids),
    ).to_list()

    subjects_computed = 0
    students_seen: set[str] = set()
    missing_marks = 0
    invalid_records = 0
    student_subject_terms: dict[str, list[tuple[float, float, float, str]]] = {}

    for entry in entries:
        students_seen.add(str(entry.student_user_id))
        profile = await StudentProfile.find_one(
            Eq(StudentProfile.tenant_id, tenant_id),
            Eq(StudentProfile.user_id, entry.student_user_id),
        )
        programme = profile.programme_code if profile else payload.programme_code
        credit_units = await _credit_units(tenant_id, session=session, course_code=entry.course_code, programme_code=programme)

        existing = await ExamStudentSubjectResult.find_one(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            Eq(ExamStudentSubjectResult.exam_session_id, session_oid),
            Eq(ExamStudentSubjectResult.student_user_id, entry.student_user_id),
            Eq(ExamStudentSubjectResult.course_code, entry.course_code),
        )
        revaluation_marks = (
            existing is not None
            and payload.recalculate
            and bool((existing.calculation_inputs or {}).get("revaluation_application_id"))
        )
        marks_obtained = existing.marks_obtained if revaluation_marks else entry.total_marks
        marks_max = existing.max_marks if revaluation_marks else entry.max_marks

        special = outcome_from_candidate_status(entry.candidate_status)
        if special is not None:
            outcome = special
            percent = None
            grade_letter = None
            grade_point = None
        elif marks_obtained is None or marks_max is None:
            missing_marks += 1
            outcome = ExamSubjectResultOutcome.INCOMPLETE
            percent = None
            grade_letter = None
            grade_point = None
        else:
            percent_raw = percentage_from_marks(marks_obtained, marks_max)
            if percent_raw is None:
                invalid_records += 1
                outcome = ExamSubjectResultOutcome.INCOMPLETE
                percent = None
                grade_letter = None
                grade_point = None
            else:
                percent = round_value(percent_raw, policy.mark_rounding, policy.decimal_precision)
                boundary = resolve_boundary(percent, boundaries)
                if boundary is None:
                    invalid_records += 1
                    outcome = ExamSubjectResultOutcome.FAIL
                    grade_letter = "F"
                    grade_point = 0.0
                else:
                    grade_letter = boundary.grade_letter
                    grade_point = apply_supplementary_cap(
                        boundary.grade_point,
                        policy,
                        is_supplementary=entry.candidate_status == ExamMarksCandidateStatus.PRESENT and False,
                    )
                    if percent >= policy.passing_min_percent and boundary.is_passing and grade_point >= policy.min_grade_point_to_pass:
                        outcome = ExamSubjectResultOutcome.PASS
                    else:
                        outcome = ExamSubjectResultOutcome.FAIL

        credits_earned = credits_earned_for_outcome(outcome, credit_units=credit_units, grade_point=grade_point, policy=policy)

        if existing and existing.status in {
            ExamSubjectResultStatus.LOCKED,
            ExamSubjectResultStatus.APPROVED,
        } and not payload.recalculate:
            raise AppError(code="RESULT_LOCKED", message="Approved results cannot be recalculated", status_code=409)

        calculation_inputs = {
            "entry_id": entry.entry_id,
            "submission_id": entry.submission_id,
            "candidate_status": entry.candidate_status.value,
            "marks_obtained": marks_obtained,
            "max_marks": marks_max,
            "policy_id": policy.policy_id,
            "policy_version": policy.version,
        }
        if revaluation_marks and existing is not None:
            calculation_inputs["revaluation_application_id"] = existing.calculation_inputs.get("revaluation_application_id")
            if existing.calculation_inputs.get("preserved_original"):
                calculation_inputs["preserved_original"] = existing.calculation_inputs.get("preserved_original")

        if existing is None:
            doc = ExamStudentSubjectResult(
                tenant_id=tenant_id,
                result_id=_result_id(),
                exam_session_id=session_oid,
                student_user_id=entry.student_user_id,
                course_code=entry.course_code,
                policy_id=policy.policy_id,
                policy_version=policy.version,
            )
        else:
            doc = existing
            if doc.status != ExamSubjectResultStatus.PROVISIONAL and not payload.recalculate:
                continue

        doc.marks_obtained = marks_obtained
        doc.max_marks = marks_max
        doc.percentage = percent
        doc.grade_letter = grade_letter
        doc.grade_point = grade_point
        doc.credit_units = credit_units
        doc.credits_earned = credits_earned
        doc.outcome = outcome
        doc.status = ExamSubjectResultStatus.PROVISIONAL
        doc.calculation_inputs = calculation_inputs
        doc.calculated_at = utcnow()
        doc.updated_at = utcnow()
        if doc.id is None:
            await doc.insert()
        else:
            await doc.save()
        subjects_computed += 1

        if grade_point is not None and credit_units > 0:
            bucket = student_subject_terms.setdefault(str(entry.student_user_id), [])
            bucket.append((credit_units, grade_point, credits_earned, entry.course_code))

    for student_id, terms in student_subject_terms.items():
        student_oid = to_object_id(student_id, "student_user_id")
        attempted, earned, qp, gpa_val = compute_gpa([(t[0], t[1], t[2]) for t in terms])
        gpa_val = round_value(gpa_val, policy.mark_rounding, policy.decimal_precision)

        gpa_doc = ExamGpaCalculation(
            tenant_id=tenant_id,
            calculation_id=_gpa_id(),
            exam_session_id=session_oid,
            student_user_id=student_oid,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            credits_attempted=attempted,
            credits_earned=earned,
            quality_points=qp,
            gpa=gpa_val,
            calculation_inputs={"subjects": [t[3] for t in terms]},
        )
        await gpa_doc.insert()

        prior_results = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            Eq(ExamStudentSubjectResult.student_user_id, student_oid),
            Eq(ExamStudentSubjectResult.status, ExamSubjectResultStatus.APPROVED),
        ).to_list()
        cumulative_terms = [(r.credit_units, r.grade_point or 0.0, r.credits_earned) for r in prior_results if r.grade_point is not None]
        cumulative_terms.extend([(t[0], t[1], t[2]) for t in terms])
        c_attempted, c_earned, c_qp, cgpa_val = compute_gpa(cumulative_terms)
        cgpa_val = round_value(cgpa_val, policy.mark_rounding, policy.decimal_precision)
        cgpa_doc = ExamCgpaCalculation(
            tenant_id=tenant_id,
            calculation_id=_cgpa_id(),
            student_user_id=student_oid,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            credits_attempted=c_attempted,
            credits_earned=c_earned,
            quality_points=c_qp,
            cgpa=cgpa_val,
            calculation_inputs={"session_id": str(session_oid)},
        )
        await cgpa_doc.insert()

        roster_credits = sum(t[0] for t in terms)
        sem = await ExamSemesterResult.find_one(
            Eq(ExamSemesterResult.tenant_id, tenant_id),
            Eq(ExamSemesterResult.exam_session_id, session_oid),
            Eq(ExamSemesterResult.student_user_id, student_oid),
        )
        if sem is None:
            profile = await StudentProfile.find_one(
                Eq(StudentProfile.tenant_id, tenant_id),
                Eq(StudentProfile.user_id, student_oid),
            )
            sem = ExamSemesterResult(
                tenant_id=tenant_id,
                semester_result_id=_semester_result_id(),
                exam_session_id=session_oid,
                student_user_id=student_oid,
                academic_year_label=session.academic_year_label,
                semester_label=session.semester_label,
                programme_code=profile.programme_code if profile else None,
            )
            await sem.insert()
        sem.credits_registered = roster_credits
        sem.credits_earned = earned
        sem.gpa = gpa_val
        sem.gpa_calculation_id = gpa_doc.calculation_id
        sem.cgpa = cgpa_val
        sem.cgpa_calculation_id = cgpa_doc.calculation_id
        sem.status = ExamSubjectResultStatus.PROVISIONAL
        sem.calculated_at = utcnow()
        sem.updated_at = utcnow()
        await sem.save()

    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_provisional_results_calculated",
        summary=f"Computed {subjects_computed} subject results",
        exam_session_id=session_oid,
        metadata={"policy_id": policy.policy_id, "policy_version": policy.version},
    )

    return ExamProvisionalCalculateSummary(
        subjects_computed=subjects_computed,
        students_computed=len(students_seen),
        missing_marks=missing_marks,
        invalid_records=invalid_records,
        policy_id=policy.policy_id,
        policy_version=policy.version,
    )


async def list_subject_results(scope: AccessScope, exam_session_id: str) -> list[ExamStudentSubjectResultRead]:
    tenant_id = require_examination_cell_tenant(scope)
    session_oid = to_object_id(exam_session_id, "exam_session_id")
    rows = await ExamStudentSubjectResult.find(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, session_oid),
    ).to_list()
    return [ExamStudentSubjectResultRead.from_doc(r) for r in rows]


async def list_semester_results(scope: AccessScope, exam_session_id: str) -> list[ExamSemesterResultRead]:
    tenant_id = require_examination_cell_tenant(scope)
    session_oid = to_object_id(exam_session_id, "exam_session_id")
    rows = await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, session_oid),
    ).to_list()
    return [ExamSemesterResultRead.from_doc(r) for r in rows]


async def recalculate_for_student_course(
    scope: AccessScope,
    actor: User,
    *,
    exam_session_id: str,
    student_user_id: str,
    course_code: str,
) -> ExamStudentSubjectResultRead:
    payload = ExamProvisionalCalculateRequest(exam_session_id=exam_session_id, recalculate=True)
    await calculate_provisional_results(scope, actor, payload)
    tenant_id = require_examination_cell_tenant(scope)
    session_oid = to_object_id(exam_session_id, "exam_session_id")
    student_oid = to_object_id(student_user_id, "student_user_id")
    doc = await ExamStudentSubjectResult.find_one(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, session_oid),
        Eq(ExamStudentSubjectResult.student_user_id, student_oid),
        Eq(ExamStudentSubjectResult.course_code, course_code.strip().upper()),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Subject result not found", status_code=404)
    return ExamStudentSubjectResultRead.from_doc(doc)