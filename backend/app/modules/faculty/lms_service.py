"""Faculty LMS workflows."""

from datetime import datetime

from beanie import PydanticObjectId
from fastapi import UploadFile

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.faculty.course_access import require_course_access, resolve_course_id
from app.modules.faculty.enums import FacultyActivityType
from app.modules.faculty.lms_schemas import (
    EvaluationCreate,
    EvaluationRead,
    LearningMaterialRead,
    LearningMaterialUpdate,
    LmsAssignmentCreate,
    LmsAssignmentRead,
    LmsAssignmentUpdate,
    ResubmissionAuthorize,
    SubmissionRead,
)
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.repositories import FacultyActivityRepository
from app.modules.lms.enums import LmsAssignmentStatus, MaterialPublishState, SubmissionStatus
from app.modules.lms.models import (
    AssignmentEvaluation,
    AssignmentFeedback,
    AssignmentResubmissionHistory,
    AssignmentRule,
    AssignmentSubmission,
    CourseAssignment,
    LearningMaterial,
)
from app.modules.lms import storage as lms_storage

_activity_repo = FacultyActivityRepository()


async def _default_rules(tenant_id: PydanticObjectId) -> AssignmentRule:
    rule = await AssignmentRule.find_one({"tenant_id": tenant_id})
    if rule is None:
        rule = AssignmentRule(tenant_id=tenant_id)
        await rule.insert()
    return rule


def _material_read(doc: LearningMaterial) -> LearningMaterialRead:
    return LearningMaterialRead(
        id=str(doc.id),
        title=doc.title,
        course_code=doc.course_code,
        section=doc.section,
        subject_id=doc.subject_id,
        unit_no=doc.unit_no,
        file_id=doc.file_id,
        file_name=doc.file_name,
        mime_type=doc.mime_type,
        size_bytes=doc.size_bytes,
        publish_state=doc.publish_state,
    )


async def upload_learning_material(
    scope: AccessScope,
    user: User,
    *,
    course_code: str,
    section: str | None,
    subject_id: str | None,
    unit_no: int | None,
    title: str,
    upload: UploadFile,
) -> LearningMaterialRead:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    if section:
        await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    else:
        await require_course_access(tenant_id, user.id, course_code=course_code)
    course_id = await resolve_course_id(tenant_id, course_code)
    file_name = upload.filename or "upload.bin"
    mime = upload.content_type or "application/octet-stream"
    raw = await upload.read()
    lms_storage.validate_upload(file_name, mime, len(raw))
    storage_key, checksum = lms_storage.write_bytes(
        lms_storage.storage_key_for(str(tenant_id), "materials", file_name),
        raw,
    )
    doc = LearningMaterial(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        course_id=course_id,
        course_code=course_code,
        section=section,
        subject_id=subject_id,
        unit_no=unit_no,
        title=title.strip(),
        file_id=checksum,
        storage_key=storage_key,
        file_name=file_name,
        mime_type=mime,
        size_bytes=len(raw),
    )
    await doc.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.lms.material.uploaded",
        resource_type="learning_material",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"course_code": course_code},
    )
    return _material_read(doc)


async def list_learning_materials(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    section: str | None = None,
    published_only: bool = False,
) -> list[LearningMaterialRead]:
    authorize(scope, Permission.FACULTY_LMS_READ)
    tenant_id = require_faculty_scope(scope)
    await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    filters: dict = {"tenant_id": tenant_id, "course_code": course_code, "faculty_user_id": user.id}
    if section:
        filters["section"] = section
    if published_only:
        filters["publish_state"] = MaterialPublishState.PUBLISHED
    docs = await LearningMaterial.find(filters).sort("-created_at").to_list()
    return [_material_read(d) for d in docs]


async def update_learning_material(
    scope: AccessScope,
    user: User,
    material_id: PydanticObjectId,
    payload: LearningMaterialUpdate,
) -> LearningMaterialRead:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await LearningMaterial.get(material_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Learning material not found", status_code=404)
    if payload.title is not None:
        doc.title = payload.title
    if payload.publish_state is not None:
        doc.publish_state = payload.publish_state
    if payload.unit_no is not None:
        doc.unit_no = payload.unit_no
    doc.updated_at = utcnow()
    await doc.save()
    return _material_read(doc)


async def delete_learning_material(
    scope: AccessScope,
    user: User,
    material_id: PydanticObjectId,
) -> None:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await LearningMaterial.get(material_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Learning material not found", status_code=404)
    await doc.delete()
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.lms.material.deleted",
        resource_type="learning_material",
        resource_id=str(material_id),
        tenant_id=tenant_id,
    )


async def download_learning_material(
    scope: AccessScope,
    user: User,
    material_id: PydanticObjectId,
) -> tuple[bytes, str, str]:
    authorize(scope, Permission.FACULTY_LMS_READ)
    tenant_id = require_faculty_scope(scope)
    doc = await LearningMaterial.get(material_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Learning material not found", status_code=404)
    if str(doc.faculty_user_id) != str(user.id):
        await require_course_access(tenant_id, user.id, course_code=doc.course_code, section=doc.section)
    data = lms_storage.read_bytes(doc.storage_key)
    return data, doc.file_name, doc.mime_type


def _assignment_read(doc: CourseAssignment) -> LmsAssignmentRead:
    return LmsAssignmentRead(
        id=str(doc.id),
        course_code=doc.course_code,
        section=doc.section,
        title=doc.title,
        instructions=doc.instructions,
        max_marks=doc.max_marks,
        deadline_at=doc.deadline_at,
        status=doc.status,
        subject_id=doc.subject_id,
    )


async def create_lms_assignment(
    scope: AccessScope,
    user: User,
    payload: LmsAssignmentCreate,
) -> LmsAssignmentRead:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    assignment = await require_course_access(
        tenant_id, user.id, course_code=payload.course_code, section=payload.section
    )
    course_id = assignment.course_id or await resolve_course_id(tenant_id, payload.course_code)
    base_rule = await _default_rules(tenant_id)
    if payload.rules:
        rule = AssignmentRule(
            tenant_id=tenant_id,
            allowed_extensions=payload.rules.allowed_extensions or base_rule.allowed_extensions,
            max_file_size_bytes=payload.rules.max_file_size_bytes or base_rule.max_file_size_bytes,
            late_submission_allowed=(
                payload.rules.late_submission_allowed
                if payload.rules.late_submission_allowed is not None
                else base_rule.late_submission_allowed
            ),
            late_penalty_percent=payload.rules.late_penalty_percent or base_rule.late_penalty_percent,
            resubmission_allowed=(
                payload.rules.resubmission_allowed
                if payload.rules.resubmission_allowed is not None
                else base_rule.resubmission_allowed
            ),
            max_resubmissions=payload.rules.max_resubmissions or base_rule.max_resubmissions,
        )
        await rule.insert()
    else:
        rule = base_rule
    doc = CourseAssignment(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        course_id=course_id,
        course_code=payload.course_code,
        section=payload.section,
        subject_id=payload.subject_id or assignment.subject_id,
        title=payload.title,
        instructions=payload.instructions,
        max_marks=payload.max_marks,
        deadline_at=payload.deadline_at,
        rule_id=rule.id,
        academic_year_label=assignment.academic_year_label,
        semester_label=assignment.semester_label,
    )
    await doc.insert()
    return _assignment_read(doc)


async def update_lms_assignment(
    scope: AccessScope,
    user: User,
    assignment_id: PydanticObjectId,
    payload: LmsAssignmentUpdate,
) -> LmsAssignmentRead:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await CourseAssignment.get(assignment_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    if doc.status == LmsAssignmentStatus.CANCELLED:
        raise AppError(code="CONFLICT", message="Assignment is cancelled", status_code=409)
    if doc.status == LmsAssignmentStatus.PUBLISHED:
        if payload.deadline_at is not None or payload.max_marks is not None:
            raise AppError(
                code="FORBIDDEN",
                message="Published assignment marks and deadlines cannot be changed",
                status_code=403,
            )
    if payload.title is not None:
        doc.title = payload.title
    if payload.instructions is not None:
        doc.instructions = payload.instructions
    if payload.max_marks is not None:
        doc.max_marks = payload.max_marks
    if payload.deadline_at is not None:
        doc.deadline_at = payload.deadline_at
    doc.updated_at = utcnow()
    await doc.save()
    return _assignment_read(doc)


async def publish_lms_assignment(
    scope: AccessScope,
    user: User,
    assignment_id: PydanticObjectId,
) -> LmsAssignmentRead:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await CourseAssignment.get(assignment_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    doc.status = LmsAssignmentStatus.PUBLISHED
    doc.updated_at = utcnow()
    await doc.save()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.ASSIGNMENT_PUBLISHED,
        title=f"Assignment published: {doc.title}",
        metadata={"assignment_id": str(doc.id)},
    )
    from app.modules.faculty.communication_schemas import AssignmentUpdateShare
    from app.modules.faculty.communication_service import share_assignment_update

    await share_assignment_update(
        scope,
        user,
        AssignmentUpdateShare(
            assignment_id=str(doc.id),
            body=f"Assignment '{doc.title}' is now published.",
        ),
    )
    return _assignment_read(doc)


async def cancel_lms_assignment(
    scope: AccessScope,
    user: User,
    assignment_id: PydanticObjectId,
) -> LmsAssignmentRead:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await CourseAssignment.get(assignment_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    doc.status = LmsAssignmentStatus.CANCELLED
    doc.updated_at = utcnow()
    await doc.save()
    return _assignment_read(doc)


async def list_lms_assignments(
    scope: AccessScope,
    user: User,
    course_code: str | None = None,
) -> list[LmsAssignmentRead]:
    authorize(scope, Permission.FACULTY_LMS_READ)
    tenant_id = require_faculty_scope(scope)
    filters: dict = {"tenant_id": tenant_id, "faculty_user_id": user.id}
    if course_code:
        await require_course_access(tenant_id, user.id, course_code=course_code)
        filters["course_code"] = course_code
    docs = await CourseAssignment.find(filters).sort("-created_at").to_list()
    return [_assignment_read(d) for d in docs]


async def list_submissions(
    scope: AccessScope,
    user: User,
    assignment_id: PydanticObjectId,
) -> list[SubmissionRead]:
    authorize(scope, Permission.FACULTY_LMS_READ)
    tenant_id = require_faculty_scope(scope)
    assignment = await CourseAssignment.get(assignment_id)
    if assignment is None or str(assignment.tenant_id) != str(tenant_id) or str(assignment.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    rows = await AssignmentSubmission.find({"assignment_id": assignment_id}).sort("-submitted_at").to_list()
    rule = await AssignmentRule.get(assignment.rule_id)
    for row in rows:
        if (
            row.submitted_at
            and row.submitted_at > assignment.deadline_at
            and row.status == SubmissionStatus.SUBMITTED
        ):
            row.status = SubmissionStatus.LATE
        if rule and not rule.late_submission_allowed and row.status == SubmissionStatus.LATE:
            pass
    return [_submission_read(r) for r in rows]


def _submission_read(row: AssignmentSubmission) -> SubmissionRead:
    return SubmissionRead(
        id=str(row.id),
        student_user_id=str(row.student_user_id),
        status=row.status,
        submitted_at=row.submitted_at,
        attempt_no=row.attempt_no,
        file_name=row.file_name,
    )


async def evaluate_submission(
    scope: AccessScope,
    user: User,
    submission_id: PydanticObjectId,
    payload: EvaluationCreate,
) -> EvaluationRead:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    submission = await AssignmentSubmission.get(submission_id)
    if submission is None or str(submission.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Submission not found", status_code=404)
    assignment = await CourseAssignment.get(submission.assignment_id)
    if assignment is None or str(assignment.faculty_user_id) != str(user.id):
        raise AppError(code="FORBIDDEN", message="You cannot evaluate this submission", status_code=403)
    if payload.marks_awarded > assignment.max_marks:
        raise AppError(code="VALIDATION_ERROR", message="Marks exceed maximum", status_code=422)
    evaluation = await AssignmentEvaluation.find_one({"submission_id": submission_id})
    if evaluation is None:
        evaluation = AssignmentEvaluation(
            tenant_id=tenant_id,
            submission_id=submission_id,
            evaluator_id=user.id,
            marks_awarded=payload.marks_awarded,
        )
        await evaluation.insert()
    else:
        evaluation.marks_awarded = payload.marks_awarded
        evaluation.evaluated_at = utcnow()
        await evaluation.save()
    feedback_text = None
    if payload.feedback:
        feedback = await AssignmentFeedback.find_one({"submission_id": submission_id})
        if feedback is None:
            feedback = AssignmentFeedback(
                tenant_id=tenant_id,
                submission_id=submission_id,
                feedback=payload.feedback,
                author_id=user.id,
            )
            await feedback.insert()
        else:
            feedback.feedback = payload.feedback
            await feedback.save()
        feedback_text = payload.feedback
    submission.status = SubmissionStatus.EVALUATED
    await submission.save()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.ASSIGNMENT_GRADED,
        title="Submission evaluated",
        metadata={"submission_id": str(submission_id)},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.lms.submission.evaluated",
        resource_type="assignment_submission",
        resource_id=str(submission_id),
        tenant_id=tenant_id,
    )
    return EvaluationRead(
        submission_id=str(submission_id),
        marks_awarded=evaluation.marks_awarded,
        feedback=feedback_text,
        evaluated_at=evaluation.evaluated_at,
    )


async def authorize_resubmission(
    scope: AccessScope,
    user: User,
    assignment_id: PydanticObjectId,
    payload: ResubmissionAuthorize,
) -> dict[str, str]:
    authorize(scope, Permission.FACULTY_LMS_MANAGE)
    tenant_id = require_faculty_scope(scope)
    assignment = await CourseAssignment.get(assignment_id)
    if assignment is None or str(assignment.tenant_id) != str(tenant_id) or str(assignment.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    rule = await AssignmentRule.get(assignment.rule_id)
    if rule is None or not rule.resubmission_allowed:
        raise AppError(code="FORBIDDEN", message="Resubmission is not allowed for this assignment", status_code=403)
    student_id = to_object_id(payload.student_user_id, "student id")
    latest = (
        await AssignmentSubmission.find({"assignment_id": assignment_id, "student_user_id": student_id})
        .sort("-attempt_no")
        .first_or_none()
    )
    attempt = latest.attempt_no if latest else 0
    if attempt >= rule.max_resubmissions + 1:
        raise AppError(code="CONFLICT", message="Resubmission limit reached", status_code=409)
    await AssignmentResubmissionHistory(
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        student_user_id=student_id,
        from_attempt=attempt,
        to_attempt=attempt + 1,
        reason=payload.reason,
        authorized_by=user.id,
    ).insert()
    return {"status": "authorized", "next_attempt": str(attempt + 1)}


async def submission_status_summary(
    scope: AccessScope,
    user: User,
    assignment_id: PydanticObjectId,
) -> dict[str, int]:
    authorize(scope, Permission.FACULTY_LMS_READ)
    rows = await list_submissions(scope, user, assignment_id)
    summary = {"submitted": 0, "late": 0, "evaluated": 0, "missing": 0}
    for row in rows:
        summary[row.status.value] = summary.get(row.status.value, 0) + 1
    return summary
