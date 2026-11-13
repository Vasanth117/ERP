"""Faculty assessment marks and grading."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.repositories import AcademicQueryRepository
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.examinations.enums import MarksBatchStatus, MarksCorrectionStatus, StudentMarkStatus
from app.modules.examinations.grading import get_grading_policy, letter_grade, weighted_percentage
from app.modules.examinations.models import (
    Assessment,
    AssessmentComponent,
    FacultyAssessmentAssignment,
    MarksApprovalHistory,
    MarksCorrectionRequest,
    MarksSubmissionBatch,
    StudentAssessmentMark,
)
from app.modules.faculty.assessment_access import (
    assert_assessment_not_published,
    assert_faculty_may_enter,
    get_component_or_404,
    require_assessment_assignment,
)
from app.modules.faculty.assessment_schemas import (
    ApprovalHistoryRead,
    AssessmentComponentRead,
    AssessmentReportRead,
    AssignedAssessmentRead,
    EligibleStudentRead,
    MarksBatchRead,
    MarksCorrectionCreate,
    MarksCorrectionRead,
    MarksDraftSave,
    MarksSubmitRequest,
    StudentMarkRead,
)
from app.modules.faculty.enums import FacultyActivityType
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.repositories import FacultyActivityRepository
_academic = AcademicQueryRepository()
_activity_repo = FacultyActivityRepository()

_ACTIVE_BATCH_STATUSES = {
    MarksBatchStatus.SUBMITTED,
    MarksBatchStatus.PENDING_APPROVAL,
    MarksBatchStatus.APPROVED,
}


async def list_assigned_assessments(scope: AccessScope, user: User) -> list[AssignedAssessmentRead]:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await FacultyAssessmentAssignment.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).to_list()
    result: list[AssignedAssessmentRead] = []
    for row in rows:
        assessment = await Assessment.find_one({"tenant_id": tenant_id, "assessment_id": row.assessment_id})
        result.append(
            AssignedAssessmentRead(
                assessment_id=row.assessment_id,
                title=assessment.title if assessment else row.assessment_id,
                course_code=row.course_code,
                section=row.section,
                subject_id=row.subject_id,
            )
        )
    return result


async def list_assessment_components(
    scope: AccessScope,
    user: User,
    assessment_id: str,
) -> list[AssessmentComponentRead]:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    await require_assessment_assignment(tenant_id, user.id, assessment_id)
    components = await AssessmentComponent.find({"tenant_id": tenant_id, "assessment_id": assessment_id}).to_list()
    return [
        AssessmentComponentRead(
            component_id=c.component_id,
            code=c.code,
            name=c.name,
            component_type=c.component_type,
            max_marks=c.max_marks,
            weight_percent=c.weight_percent,
            faculty_may_enter=c.faculty_may_enter,
            is_official_final=c.is_official_final,
        )
        for c in components
    ]


async def eligible_students(
    scope: AccessScope,
    user: User,
    assessment_id: str,
    course_code: str,
    section: str,
) -> list[EligibleStudentRead]:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    assignment = await require_assessment_assignment(
        tenant_id, user.id, assessment_id, course_code=course_code, section=section
    )
    roster = await _academic.roster(tenant_id, assignment.course_id, section)
    return [
        EligibleStudentRead(
            student_user_id=str(e.student_user_id),
            roll_number=e.roll_number,
            display_name=e.display_name,
        )
        for e in roster
    ]


async def _get_or_create_draft_batch(
    tenant_id: PydanticObjectId,
    user: User,
    payload: MarksDraftSave,
) -> MarksSubmissionBatch:
    existing_active = await MarksSubmissionBatch.find_one(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "component_id": payload.component_id,
            "section": payload.section,
            "status": {"$in": list(_ACTIVE_BATCH_STATUSES)},
        }
    )
    if existing_active:
        raise AppError(
            code="CONFLICT",
            message="Marks for this component are already submitted or approved",
            status_code=409,
        )
    batch = await MarksSubmissionBatch.find_one(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "component_id": payload.component_id,
            "section": payload.section,
            "status": MarksBatchStatus.DRAFT,
        }
    )
    if batch is None:
        batch = MarksSubmissionBatch(
            tenant_id=tenant_id,
            faculty_user_id=user.id,
            assessment_id=payload.assessment_id,
            component_id=payload.component_id,
            course_code=payload.course_code,
            section=payload.section,
        )
        await batch.insert()
    return batch


async def save_marks_draft(scope: AccessScope, user: User, payload: MarksDraftSave) -> MarksBatchRead:
    authorize(scope, Permission.FACULTY_ASSESSMENT_MANAGE)
    tenant_id = require_faculty_scope(scope)
    await require_assessment_assignment(
        tenant_id, user.id, payload.assessment_id, course_code=payload.course_code, section=payload.section
    )
    await assert_assessment_not_published(tenant_id, payload.assessment_id)
    component = await get_component_or_404(tenant_id, payload.assessment_id, payload.component_id)
    await assert_faculty_may_enter(component)
    roster = await eligible_students(scope, user, payload.assessment_id, payload.course_code, payload.section)
    allowed = {s.student_user_id for s in roster}
    batch = await _get_or_create_draft_batch(tenant_id, user, payload)
    for entry in payload.entries:
        if entry.student_user_id not in allowed:
            raise AppError(code="FORBIDDEN", message="Student is not eligible for this assessment", status_code=403)
        if entry.marks_obtained > component.max_marks:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Marks exceed maximum of {component.max_marks}",
                status_code=422,
            )
        student_id = to_object_id(entry.student_user_id, "student id")
        record = await StudentAssessmentMark.find_one({"batch_id": batch.id, "student_user_id": student_id})
        if record is None:
            record = StudentAssessmentMark(
                tenant_id=tenant_id,
                batch_id=batch.id,
                assessment_id=payload.assessment_id,
                component_id=payload.component_id,
                student_user_id=student_id,
                marks_obtained=entry.marks_obtained,
                max_marks=component.max_marks,
            )
            await record.insert()
        else:
            if record.status in {StudentMarkStatus.APPROVED, StudentMarkStatus.LOCKED}:
                raise AppError(code="FORBIDDEN", message="Approved marks cannot be modified", status_code=403)
            record.marks_obtained = entry.marks_obtained
            record.max_marks = component.max_marks
            record.status = StudentMarkStatus.DRAFT
            record.updated_at = utcnow()
            await record.save()
    batch.updated_at = utcnow()
    await batch.save()
    return _batch_read(batch)


def _batch_read(batch: MarksSubmissionBatch) -> MarksBatchRead:
    return MarksBatchRead(
        id=str(batch.id),
        assessment_id=batch.assessment_id,
        component_id=batch.component_id,
        course_code=batch.course_code,
        section=batch.section,
        status=batch.status,
        submitted_at=batch.submitted_at,
    )


async def submit_marks(scope: AccessScope, user: User, payload: MarksSubmitRequest) -> MarksBatchRead:
    authorize(scope, Permission.FACULTY_ASSESSMENT_MANAGE)
    tenant_id = require_faculty_scope(scope)
    batch_id = to_object_id(payload.batch_id, "batch id")
    batch = await MarksSubmissionBatch.get(batch_id)
    if batch is None or str(batch.tenant_id) != str(tenant_id) or str(batch.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Marks batch not found", status_code=404)
    if batch.status != MarksBatchStatus.DRAFT:
        raise AppError(code="CONFLICT", message="Only draft batches can be submitted", status_code=409)
    component = await get_component_or_404(tenant_id, batch.assessment_id, batch.component_id)
    await assert_faculty_may_enter(component)
    marks = await StudentAssessmentMark.find({"batch_id": batch_id}).to_list()
    if not marks:
        raise AppError(code="VALIDATION_ERROR", message="No marks entered", status_code=422)
    for mark in marks:
        if mark.marks_obtained > mark.max_marks:
            raise AppError(code="VALIDATION_ERROR", message="Marks exceed configured maximum", status_code=422)
        mark.status = StudentMarkStatus.SUBMITTED
        await mark.save()
    batch.status = MarksBatchStatus.PENDING_APPROVAL if payload.submit_for_approval else MarksBatchStatus.SUBMITTED
    batch.submitted_at = utcnow()
    batch.updated_at = utcnow()
    await batch.save()
    await MarksApprovalHistory(
        tenant_id=tenant_id,
        batch_id=batch_id,
        action="submitted",
        actor_id=user.id,
        note="Faculty submitted marks batch",
    ).insert()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.ASSESSMENT_PUBLISHED,
        title="Marks batch submitted",
        metadata={"batch_id": str(batch_id)},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.marks.submitted",
        resource_type="marks_submission_batch",
        resource_id=str(batch_id),
        tenant_id=tenant_id,
    )
    return _batch_read(batch)


async def list_marks_batches(scope: AccessScope, user: User) -> list[MarksBatchRead]:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    batches = await MarksSubmissionBatch.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-updated_at").to_list()
    return [_batch_read(b) for b in batches]


async def incomplete_evaluations(scope: AccessScope, user: User) -> list[MarksBatchRead]:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    batches = await MarksSubmissionBatch.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "status": {"$in": [MarksBatchStatus.DRAFT, MarksBatchStatus.PENDING_APPROVAL]},
        }
    ).to_list()
    return [_batch_read(b) for b in batches]


async def approved_marks(
    scope: AccessScope,
    user: User,
    assessment_id: str,
    component_id: str,
    section: str,
) -> list[StudentMarkRead]:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    await require_assessment_assignment(tenant_id, user.id, assessment_id, section=section)
    batch = await MarksSubmissionBatch.find_one(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "assessment_id": assessment_id,
            "component_id": component_id,
            "section": section,
            "status": MarksBatchStatus.APPROVED,
        }
    )
    if batch is None:
        return []
    policy = await get_grading_policy(tenant_id)
    marks = await StudentAssessmentMark.find({"batch_id": batch.id, "status": StudentMarkStatus.APPROVED}).to_list()
    return [_mark_read(m, policy) for m in marks]


def _mark_read(mark: StudentAssessmentMark, policy) -> StudentMarkRead:
    pct = weighted_percentage(mark.marks_obtained, mark.max_marks)
    return StudentMarkRead(
        student_user_id=str(mark.student_user_id),
        marks_obtained=mark.marks_obtained,
        max_marks=mark.max_marks,
        status=mark.status.value,
        grade_letter=letter_grade(pct, policy),
    )


async def submit_marks_correction(
    scope: AccessScope,
    user: User,
    payload: MarksCorrectionCreate,
) -> MarksCorrectionRead:
    authorize(scope, Permission.FACULTY_ASSESSMENT_MANAGE)
    tenant_id = require_faculty_scope(scope)
    batch_id = to_object_id(payload.batch_id, "batch id")
    batch = await MarksSubmissionBatch.get(batch_id)
    if batch is None or str(batch.tenant_id) != str(tenant_id) or str(batch.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Marks batch not found", status_code=404)
    if batch.status != MarksBatchStatus.APPROVED:
        raise AppError(code="VALIDATION_ERROR", message="Corrections require an approved batch", status_code=422)
    student_id = to_object_id(payload.student_user_id, "student id") if payload.student_user_id else None
    req = MarksCorrectionRequest(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        batch_id=batch_id,
        student_user_id=student_id,
        requested_marks=payload.requested_marks,
        reason=payload.reason,
        status=MarksCorrectionStatus.PENDING,
    )
    await req.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.marks.correction_requested",
        resource_type="marks_correction_request",
        resource_id=str(req.id),
        tenant_id=tenant_id,
    )
    return MarksCorrectionRead(
        id=str(req.id),
        batch_id=str(batch_id),
        status=req.status.value,
        reason=req.reason,
        created_at=req.created_at,
        resolved_at=req.resolved_at,
    )


async def correction_history(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[MarksCorrectionRead]:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    query = MarksCorrectionRequest.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-created_at")
    total = await query.count()
    items = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            MarksCorrectionRead(
                id=str(i.id),
                batch_id=str(i.batch_id),
                status=i.status.value,
                reason=i.reason,
                created_at=i.created_at,
                resolved_at=i.resolved_at,
            )
            for i in items
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def approval_history_for_batch(
    scope: AccessScope,
    user: User,
    batch_id: PydanticObjectId,
) -> list[ApprovalHistoryRead]:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    batch = await MarksSubmissionBatch.get(batch_id)
    if batch is None or str(batch.tenant_id) != str(tenant_id) or str(batch.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Marks batch not found", status_code=404)
    rows = await MarksApprovalHistory.find({"tenant_id": tenant_id, "batch_id": batch_id}).sort("created_at").to_list()
    return [ApprovalHistoryRead(action=r.action, note=r.note, created_at=r.created_at) for r in rows]


async def subject_marks_report(
    scope: AccessScope,
    user: User,
    assessment_id: str,
    component_id: str,
    course_code: str,
    section: str,
) -> AssessmentReportRead:
    authorize(scope, Permission.FACULTY_ASSESSMENT_READ)
    tenant_id = require_faculty_scope(scope)
    await require_assessment_assignment(tenant_id, user.id, assessment_id, course_code=course_code, section=section)
    policy = await get_grading_policy(tenant_id)
    batch = await MarksSubmissionBatch.find_one(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "assessment_id": assessment_id,
            "component_id": component_id,
            "section": section,
        }
    )
    entries: list[StudentMarkRead] = []
    if batch:
        marks = await StudentAssessmentMark.find({"batch_id": batch.id}).to_list()
        entries = [_mark_read(m, policy) for m in marks]
    return AssessmentReportRead(
        course_code=course_code,
        section=section,
        assessment_id=assessment_id,
        component_id=component_id,
        entries=entries,
        generated_at=utcnow(),
    )
