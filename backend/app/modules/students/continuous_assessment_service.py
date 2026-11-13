"""Student LMS assignments, quizzes (schedules), and continuous assessment marks."""

from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.lms.enums import LmsAssignmentStatus, SubmissionStatus
from app.modules.lms.models import (
    AssignmentEvaluation,
    AssignmentFeedback,
    AssignmentResubmissionHistory,
    AssignmentRule,
    AssignmentSubmission,
    CourseAssignment,
)
from app.modules.students.integrations.assessment_reader import cia_schedules
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.assessment_enums import AssessmentNotificationKind, MarkVisibility
from app.modules.students.assessment_models import StudentAssessmentNotification, StudentAssignmentProgress
from app.modules.students.assessment_schemas import (
    AssessmentProgressRead,
    AssignmentDetailRead,
    AssignmentListRead,
    ContinuousAssessmentMarkRead,
    FeedbackRead,
    QuizScheduleRead,
    ResubmissionEligibilityRead,
    SubmissionStatusRead,
)
from app.modules.students.policy import require_student_scope

_reader = StudentDataReader()


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _roster_pairs(tenant_id: PydanticObjectId, user_id: PydanticObjectId, year: str, semester: str) -> set[tuple[str, str]]:
    roster = await _reader.roster_entries(tenant_id, user_id, academic_year_label=year, semester_label=semester)
    return {(r.course_code, r.section_code) for r in roster}


async def _published_assignments(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    year: str,
    semester: str,
) -> list[CourseAssignment]:
    pairs = await _roster_pairs(tenant_id, user_id, year, semester)
    if not pairs:
        return []
    or_clauses = [{"course_code": c, "section": s} for c, s in pairs]
    return await CourseAssignment.find(
        {
            "tenant_id": tenant_id,
            "academic_year_label": year,
            "semester_label": semester,
            "status": LmsAssignmentStatus.PUBLISHED,
            "$or": or_clauses,
        }
    ).sort("deadline_at").to_list()


async def list_assignments(scope: AccessScope, user: User) -> list[AssignmentListRead]:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    rows = await _published_assignments(tenant_id, user.id, year, semester)
    return [
        AssignmentListRead(
            id=str(a.id),
            title=a.title,
            course_code=a.course_code,
            section=a.section,
            deadline_at=a.deadline_at,
            max_marks=a.max_marks,
            instructions_preview=a.instructions[:240],
        )
        for a in rows
    ]


async def get_assignment_detail(scope: AccessScope, user: User, assignment_id: str) -> AssignmentDetailRead:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    tenant_id = require_student_scope(scope)
    aid = PydanticObjectId(assignment_id)
    doc = await CourseAssignment.get(aid)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or doc.status != LmsAssignmentStatus.PUBLISHED:
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    year, semester = await _term(tenant_id)
    pairs = await _roster_pairs(tenant_id, user.id, year, semester)
    if (doc.course_code, doc.section) not in pairs:
        raise AppError(code="FORBIDDEN", message="Assignment is outside your enrolled classes", status_code=403)
    await _touch_progress(tenant_id, user.id, doc)
    return AssignmentDetailRead(
        id=str(doc.id),
        title=doc.title,
        course_code=doc.course_code,
        section=doc.section,
        instructions=doc.instructions,
        max_marks=doc.max_marks,
        deadline_at=doc.deadline_at,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
    )


async def _touch_progress(tenant_id: PydanticObjectId, user_id: PydanticObjectId, assignment: CourseAssignment) -> None:
    sub = await AssignmentSubmission.find_one(
        {"tenant_id": tenant_id, "assignment_id": assignment.id, "student_user_id": user_id}
    )
    row = await StudentAssignmentProgress.find_one(
        {"tenant_id": tenant_id, "user_id": user_id, "assignment_id": assignment.id}
    )
    status = sub.status.value if sub else SubmissionStatus.MISSING.value
    evaluated = False
    if sub:
        evaluated = await AssignmentEvaluation.find_one({"submission_id": sub.id}) is not None
    if row is None:
        row = StudentAssignmentProgress(
            tenant_id=tenant_id,
            user_id=user_id,
            assignment_id=assignment.id,
            course_code=assignment.course_code,
            submission_status=status,
            evaluation_published=evaluated,
        )
        await row.insert()
    else:
        row.last_viewed_at = utcnow()
        row.submission_status = status
        row.evaluation_published = evaluated
        await row.save()


async def quiz_schedules(scope: AccessScope, user: User) -> list[QuizScheduleRead]:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    upcoming = await cia_schedules(tenant_id, user.id, year=year, semester=semester)
    return [
        QuizScheduleRead(
            id=str(u.id),
            title=u.title,
            course_code=u.course_code,
            scheduled_at=u.scheduled_at,
            assessment_type=u.assessment_type if u.assessment_type.lower() == "quiz" else "quiz",
        )
        for u in upcoming
        if "quiz" in u.assessment_type.lower() or u.assessment_type.lower() in {"test", "ia"}
    ]


async def quiz_results(scope: AccessScope, user: User) -> list[ContinuousAssessmentMarkRead]:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    from app.modules.students.cia_service import get_published_cia_marks

    marks = await get_published_cia_marks(scope, user)
    return [
        ContinuousAssessmentMarkRead(
            assignment_id=f"{m.assessment_id}:{m.component_id}",
            course_code=m.course_code or "",
            title=m.component_id,
            marks_awarded=m.marks_obtained,
            max_marks=m.max_marks,
            visibility=MarkVisibility.PUBLISHED,
            evaluated_at=m.published_at,
        )
        for m in marks
        if m.course_code
    ]


async def submission_status(scope: AccessScope, user: User, assignment_id: str) -> SubmissionStatusRead:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    tenant_id = require_student_scope(scope)
    aid = PydanticObjectId(assignment_id)
    assignment = await CourseAssignment.get(aid)
    if assignment is None or str(assignment.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    year, semester = await _term(tenant_id)
    pairs = await _roster_pairs(tenant_id, user.id, year, semester)
    if (assignment.course_code, assignment.section) not in pairs:
        raise AppError(code="FORBIDDEN", message="Assignment is outside your enrolled classes", status_code=403)
    sub = await AssignmentSubmission.find_one({"tenant_id": tenant_id, "assignment_id": aid, "student_user_id": user.id})
    if sub is None:
        return SubmissionStatusRead(
            assignment_id=assignment_id,
            status=SubmissionStatus.MISSING,
            missing=True,
        )
    now = datetime.now(timezone.utc)
    late = sub.status == SubmissionStatus.LATE or (
        sub.submitted_at is not None and sub.submitted_at > assignment.deadline_at
    )
    evaluated = await AssignmentEvaluation.find_one({"submission_id": sub.id}) is not None
    return SubmissionStatusRead(
        assignment_id=assignment_id,
        status=sub.status,
        submitted_at=sub.submitted_at,
        file_name=sub.file_name,
        late=late,
        missing=False,
        evaluated=evaluated,
    )


async def assignment_marks(scope: AccessScope, user: User) -> list[ContinuousAssessmentMarkRead]:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    assignments = await _published_assignments(tenant_id, user.id, year, semester)
    results: list[ContinuousAssessmentMarkRead] = []
    for assignment in assignments:
        sub = await AssignmentSubmission.find_one(
            {"tenant_id": tenant_id, "assignment_id": assignment.id, "student_user_id": user.id}
        )
        if sub is None:
            results.append(
                ContinuousAssessmentMarkRead(
                    assignment_id=str(assignment.id),
                    course_code=assignment.course_code,
                    title=assignment.title,
                    marks_awarded=None,
                    max_marks=assignment.max_marks,
                    visibility=MarkVisibility.MISSING,
                )
            )
            continue
        evaluation = await AssignmentEvaluation.find_one({"submission_id": sub.id})
        if evaluation is None:
            results.append(
                ContinuousAssessmentMarkRead(
                    assignment_id=str(assignment.id),
                    course_code=assignment.course_code,
                    title=assignment.title,
                    marks_awarded=None,
                    max_marks=assignment.max_marks,
                    visibility=MarkVisibility.UNPUBLISHED,
                    evaluated_at=None,
                )
            )
            continue
        results.append(
            ContinuousAssessmentMarkRead(
                assignment_id=str(assignment.id),
                course_code=assignment.course_code,
                title=assignment.title,
                marks_awarded=evaluation.marks_awarded,
                max_marks=assignment.max_marks,
                visibility=MarkVisibility.PUBLISHED,
                evaluated_at=evaluation.evaluated_at,
            )
        )
    return results


async def get_feedback(scope: AccessScope, user: User, assignment_id: str) -> FeedbackRead:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    tenant_id = require_student_scope(scope)
    aid = PydanticObjectId(assignment_id)
    sub = await AssignmentSubmission.find_one({"tenant_id": tenant_id, "assignment_id": aid, "student_user_id": user.id})
    if sub is None:
        raise AppError(code="NOT_FOUND", message="No submission found", status_code=404)
    fb = await AssignmentFeedback.find_one({"submission_id": sub.id})
    if fb is None:
        raise AppError(code="NOT_FOUND", message="Published feedback not available", status_code=404)
    await record_audit(
        actor_id=scope.user_id,
        action="student.assignment.feedback_viewed",
        resource_type="assignment_feedback",
        resource_id=str(fb.id),
        tenant_id=tenant_id,
    )
    return FeedbackRead(
        assignment_id=assignment_id,
        submission_id=str(sub.id),
        feedback=fb.feedback,
        created_at=fb.created_at,
    )


async def resubmission_eligibility(scope: AccessScope, user: User, assignment_id: str) -> ResubmissionEligibilityRead:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    tenant_id = require_student_scope(scope)
    aid = PydanticObjectId(assignment_id)
    assignment = await CourseAssignment.get(aid)
    if assignment is None or str(assignment.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    rule = await AssignmentRule.get(assignment.rule_id)
    reasons: list[str] = []
    eligible = False
    attempts = await AssignmentSubmission.find(
        {"tenant_id": tenant_id, "assignment_id": aid, "student_user_id": user.id}
    ).count()
    if rule is None:
        reasons.append("Assignment rules not configured")
    elif not rule.resubmission_allowed:
        reasons.append("Resubmission is not allowed for this assignment")
    elif attempts > rule.max_resubmissions:
        reasons.append("Maximum resubmissions reached")
    else:
        history = await AssignmentResubmissionHistory.find_one(
            {"tenant_id": tenant_id, "assignment_id": aid, "student_user_id": user.id}
        )
        if history:
            eligible = True
        else:
            reasons.append("Resubmission requires faculty authorization")
    return ResubmissionEligibilityRead(
        assignment_id=assignment_id,
        eligible=eligible,
        reasons=reasons,
        max_resubmissions=rule.max_resubmissions if rule else 0,
        attempts_used=attempts,
    )


async def assessment_progress(scope: AccessScope, user: User) -> list[AssessmentProgressRead]:
    authorize(scope, Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    assignments = await _published_assignments(tenant_id, user.id, year, semester)
    progress: list[AssessmentProgressRead] = []
    for a in assignments:
        sub = await AssignmentSubmission.find_one(
            {"tenant_id": tenant_id, "assignment_id": a.id, "student_user_id": user.id}
        )
        status = sub.status.value if sub else SubmissionStatus.MISSING.value
        evaluation = None
        if sub:
            evaluation = await AssignmentEvaluation.find_one({"submission_id": sub.id})
        marks = evaluation.marks_awarded if evaluation else None
        pending = sub is not None and evaluation is None
        if pending:
            await _maybe_eval_notification(tenant_id, user.id, a)
        progress.append(
            AssessmentProgressRead(
                assignment_id=str(a.id),
                course_code=a.course_code,
                title=a.title,
                submission_status=status,
                evaluation_published=evaluation is not None,
                marks_awarded=marks,
                pending_evaluation=pending,
            )
        )
        await _touch_progress(tenant_id, user.id, a)
    return progress


async def _maybe_eval_notification(tenant_id: PydanticObjectId, user_id: PydanticObjectId, assignment: CourseAssignment) -> None:
    exists = await StudentAssessmentNotification.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "kind": AssessmentNotificationKind.EVALUATION_PENDING,
            "reference_id": str(assignment.id),
            "read_at": None,
        }
    )
    if exists:
        return
    await StudentAssessmentNotification(
        tenant_id=tenant_id,
        user_id=user_id,
        kind=AssessmentNotificationKind.EVALUATION_PENDING,
        title=f"Evaluation pending — {assignment.title}",
        body="Your submission is awaiting faculty evaluation",
        course_code=assignment.course_code,
        reference_id=str(assignment.id),
    ).insert()
