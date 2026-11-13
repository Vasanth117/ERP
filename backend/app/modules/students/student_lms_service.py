"""Student LMS and study materials portal."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.lms.download_tokens import issue_material_download_token
from app.modules.lms.enums import LmsAssignmentStatus, SubmissionStatus
from app.modules.lms.models import AssignmentRule, AssignmentSubmission, CourseAssignment, LearningMaterial
from app.modules.lms.storage import read_bytes, storage_key_for, validate_upload, write_bytes
from app.modules.students.continuous_assessment_service import (
    assessment_progress,
    get_assignment_detail,
    get_feedback,
    list_assignments,
    quiz_schedules,
    submission_status,
)
from app.modules.students.integrations.assessment_reader import cia_schedules
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.student_lms_reader import authorized_material, published_materials_for_student
from app.modules.students.policy import require_student_scope
from app.modules.students.student_lms_models import (
    StudentLearningProgress,
    StudentLmsNotificationLog,
    StudentLmsPreferences,
    StudentMaterialAccessLog,
)
from app.modules.students.student_lms_schemas import (
    CourseAnnouncementRead,
    LearningMaterialRead,
    LearningProgressRead,
    MaterialDownloadRead,
    QuizParticipationRead,
)

_reader = StudentDataReader()


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


def _material_read(doc: LearningMaterial) -> LearningMaterialRead:
    recorded = doc.metadata.get("recorded_url") if doc.metadata else None
    if recorded is None and doc.material_type == "recording":
        recorded = doc.metadata.get("url") if doc.metadata else None
    return LearningMaterialRead(
        id=str(doc.id),
        course_code=doc.course_code,
        section=doc.section,
        unit_no=doc.unit_no,
        material_type=doc.material_type,
        title=doc.title,
        file_name=doc.file_name,
        mime_type=doc.mime_type,
        size_bytes=doc.size_bytes,
        recorded_url=recorded,
    )


async def _bump_progress(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    course_code: str,
    *,
    materials_delta: int = 0,
    assignments_delta: int = 0,
    quizzes_delta: int = 0,
) -> None:
    row = await StudentLearningProgress.find_one(
        {"tenant_id": tenant_id, "user_id": user_id, "course_code": course_code}
    )
    if row is None:
        row = StudentLearningProgress(
            tenant_id=tenant_id,
            user_id=user_id,
            course_code=course_code,
            materials_viewed=max(0, materials_delta),
            assignments_submitted=max(0, assignments_delta),
            quizzes_completed=max(0, quizzes_delta),
            last_activity_at=utcnow(),
        )
        await row.insert()
        return
    row.materials_viewed += materials_delta
    row.assignments_submitted += assignments_delta
    row.quizzes_completed += quizzes_delta
    row.last_activity_at = utcnow()
    row.updated_at = utcnow()
    await row.save()


async def list_course_materials(
    scope: AccessScope,
    user: User,
    *,
    course_code: str | None = None,
    subject_id: str | None = None,
    unit_no: int | None = None,
) -> list[LearningMaterialRead]:
    authorize(scope, Permission.STUDENT_LMS_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    docs = await published_materials_for_student(
        tenant_id,
        user.id,
        year=year,
        semester=semester,
        course_code=course_code,
        subject_id=subject_id,
        unit_no=unit_no,
    )
    return [_material_read(d) for d in docs]


async def list_recorded_lectures(scope: AccessScope, user: User, course_code: str | None = None) -> list[LearningMaterialRead]:
    authorize(scope, Permission.STUDENT_LMS_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    docs = await published_materials_for_student(
        tenant_id,
        user.id,
        year=year,
        semester=semester,
        course_code=course_code,
        material_type="recording",
    )
    return [_material_read(d) for d in docs]


async def issue_material_download(scope: AccessScope, user: User, material_id: str) -> MaterialDownloadRead:
    authorize(scope, Permission.STUDENT_LMS_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    mid = PydanticObjectId(material_id)
    doc = await authorized_material(tenant_id, user.id, mid, year=year, semester=semester)
    if doc is None:
        raise AppError(code="FORBIDDEN", message="Material not authorized", status_code=403)
    token = await issue_material_download_token(
        tenant_id=str(tenant_id),
        user_id=str(user.id),
        material_id=material_id,
    )
    await StudentMaterialAccessLog(
        tenant_id=tenant_id,
        user_id=user.id,
        material_id=mid,
        course_code=doc.course_code,
        action="download_token",
    ).insert()
    await _bump_progress(tenant_id, user.id, doc.course_code, materials_delta=1)
    await record_audit(
        actor_id=scope.user_id,
        action="student.lms.material_download_issued",
        resource_type="learning_material",
        resource_id=material_id,
        tenant_id=tenant_id,
    )
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    return MaterialDownloadRead(
        material_id=material_id,
        download_token=token,
        content_type=doc.mime_type,
        expires_at=expires_at,
    )


async def fetch_material_bytes(
    scope: AccessScope,
    user: User,
    material_id: str,
) -> tuple[bytes, str, str]:
    authorize(scope, Permission.STUDENT_LMS_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    mid = PydanticObjectId(material_id)
    doc = await authorized_material(tenant_id, user.id, mid, year=year, semester=semester)
    if doc is None:
        raise AppError(code="FORBIDDEN", message="Material not authorized", status_code=403)
    data = read_bytes(doc.storage_key)
    await StudentMaterialAccessLog(
        tenant_id=tenant_id,
        user_id=user.id,
        material_id=mid,
        course_code=doc.course_code,
        action="download",
    ).insert()
    return data, doc.file_name, doc.mime_type


async def course_announcements(
    scope: AccessScope,
    user: User,
    *,
    course_code: str | None = None,
    pagination: Pagination,
) -> Page[CourseAnnouncementRead]:
    authorize(scope, Permission.STUDENT_LMS_READ)
    tenant_id = require_student_scope(scope)
    raw = await _reader.academic_notifications(tenant_id, user.id, limit=pagination.offset + pagination.limit)
    items = [
        CourseAnnouncementRead(
            id=r["id"],
            title=r["title"],
            body=r["body"],
            course_code=r.get("course_code"),
            created_at=r["created_at"],
        )
        for r in raw
        if course_code is None or r.get("course_code") == course_code
    ]
    slice_items = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_items, total=len(items), limit=pagination.limit, offset=pagination.offset)


async def learning_progress(scope: AccessScope, user: User) -> list[LearningProgressRead]:
    authorize(scope, Permission.STUDENT_LMS_READ)
    tenant_id = require_student_scope(scope)
    rows = await StudentLearningProgress.find({"tenant_id": tenant_id, "user_id": user.id}).to_list()
    return [
        LearningProgressRead(
            course_code=r.course_code,
            materials_viewed=r.materials_viewed,
            assignments_submitted=r.assignments_submitted,
            quizzes_completed=r.quizzes_completed,
            last_activity_at=r.last_activity_at,
        )
        for r in rows
    ]


async def lms_notifications(scope: AccessScope, user: User, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.STUDENT_LMS_READ)
    tenant_id = require_student_scope(scope)
    rows = (
        await StudentLmsNotificationLog.find({"tenant_id": tenant_id, "user_id": user.id})
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    total = await StudentLmsNotificationLog.find({"tenant_id": tenant_id, "user_id": user.id}).count()
    items = [
        {
            "id": str(r.id),
            "title": r.title,
            "body": r.body,
            "course_code": r.course_code,
            "read_at": r.read_at,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def submit_assignment_file(
    scope: AccessScope,
    user: User,
    assignment_id: str,
    file_name: str,
    mime_type: str,
    data: bytes,
) -> SubmissionStatus:
    authorize(scope, Permission.STUDENT_LMS_MANAGE)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    aid = PydanticObjectId(assignment_id)
    assignment = await CourseAssignment.get(aid)
    if assignment is None or assignment.tenant_id != tenant_id or assignment.status != LmsAssignmentStatus.PUBLISHED:
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    roster = await _reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    pairs = {(r.course_code, r.section_code) for r in roster}
    if (assignment.course_code, assignment.section) not in pairs:
        raise AppError(code="FORBIDDEN", message="Assignment is outside your enrolled classes", status_code=403)
    rule = await AssignmentRule.get(assignment.rule_id)
    max_size = rule.max_file_size_bytes if rule else 10 * 1024 * 1024
    validate_upload(file_name, mime_type, len(data))
    if len(data) > max_size:
        raise AppError(code="VALIDATION_ERROR", message="File exceeds assignment size limit", status_code=422)
    if rule:
        from pathlib import Path

        ext = Path(file_name).suffix.lower()
        if ext not in {e.lower() for e in rule.allowed_extensions}:
            raise AppError(code="VALIDATION_ERROR", message="File type is not allowed", status_code=422)
    now = datetime.now(timezone.utc)
    late = now > assignment.deadline_at
    if late and rule and not rule.late_submission_allowed:
        raise AppError(code="VALIDATION_ERROR", message="Late submission is not allowed", status_code=422)
    existing = await AssignmentSubmission.find_one(
        {"tenant_id": tenant_id, "assignment_id": aid, "student_user_id": user.id}
    )
    if existing is not None and existing.status in {
        SubmissionStatus.SUBMITTED,
        SubmissionStatus.LATE,
        SubmissionStatus.EVALUATED,
    }:
        raise AppError(code="CONFLICT", message="Assignment already submitted", status_code=409)
    storage_key = storage_key_for(str(tenant_id), "submissions", file_name)
    write_bytes(storage_key, data)
    status = SubmissionStatus.LATE if late else SubmissionStatus.SUBMITTED
    if existing is None:
        await AssignmentSubmission(
            tenant_id=tenant_id,
            assignment_id=aid,
            student_user_id=user.id,
            status=status,
            submitted_at=now,
            storage_key=storage_key,
            file_name=file_name,
        ).insert()
    else:
        existing.status = status
        existing.submitted_at = now
        existing.storage_key = storage_key
        existing.file_name = file_name
        await existing.save()
    await _bump_progress(tenant_id, user.id, assignment.course_code, assignments_delta=1)
    await StudentLmsNotificationLog(
        tenant_id=tenant_id,
        user_id=user.id,
        title=f"Submitted — {assignment.title}",
        body="Your assignment was received by the LMS",
        course_code=assignment.course_code,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.lms.assignment_submitted",
        resource_type="course_assignment",
        resource_id=assignment_id,
        tenant_id=tenant_id,
    )
    return status


async def participate_quiz(scope: AccessScope, user: User, quiz_id: str) -> QuizParticipationRead:
    authorize(scope, Permission.STUDENT_LMS_MANAGE)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    qid = PydanticObjectId(quiz_id)
    schedules = await cia_schedules(tenant_id, user.id, year=year, semester=semester)
    match = next((s for s in schedules if s.id == qid), None)
    if match is None:
        raise AppError(code="NOT_FOUND", message="Quiz not found or not authorized", status_code=404)
    enabled = match.scheduled_at <= datetime.now(timezone.utc) + timedelta(hours=1)
    if enabled:
        await _bump_progress(tenant_id, user.id, match.course_code, quizzes_delta=1)
        message = "Quiz participation recorded; complete the assessment in the examination hall or online portal when enabled by the institution."
    else:
        message = "Quiz is scheduled for a future time."
    return QuizParticipationRead(
        quiz_id=quiz_id,
        title=match.title,
        course_code=match.course_code,
        scheduled_at=match.scheduled_at,
        participation_enabled=enabled,
        message=message,
    )


# Re-export assessment helpers under LMS permission checks for dedicated routes.
async def lms_list_assignments(scope: AccessScope, user: User):
    authorize(scope, Permission.STUDENT_LMS_READ)
    return await list_assignments(scope, user)


async def lms_assignment_detail(scope: AccessScope, user: User, assignment_id: str):
    authorize(scope, Permission.STUDENT_LMS_READ)
    return await get_assignment_detail(scope, user, assignment_id)


async def lms_submission_status(scope: AccessScope, user: User, assignment_id: str):
    authorize(scope, Permission.STUDENT_LMS_READ)
    return await submission_status(scope, user, assignment_id)


async def lms_assignment_feedback(scope: AccessScope, user: User, assignment_id: str):
    authorize(scope, Permission.STUDENT_LMS_READ)
    return await get_feedback(scope, user, assignment_id)


async def lms_assessment_progress(scope: AccessScope, user: User):
    authorize(scope, Permission.STUDENT_LMS_READ)
    return await assessment_progress(scope, user)


async def lms_quiz_schedules(scope: AccessScope, user: User):
    authorize(scope, Permission.STUDENT_LMS_READ)
    return await quiz_schedules(scope, user)


async def get_lms_preferences(scope: AccessScope, user: User) -> dict:
    authorize(scope, Permission.STUDENT_LMS_READ)
    tenant_id = require_student_scope(scope)
    row = await StudentLmsPreferences.find_one({"tenant_id": tenant_id, "user_id": user.id})
    if row is None:
        return {"group_by_unit": True, "show_recorded_lectures": True}
    return {"group_by_unit": row.group_by_unit, "show_recorded_lectures": row.show_recorded_lectures}


async def update_lms_preferences(scope: AccessScope, user: User, *, group_by_unit: bool | None, show_recorded: bool | None) -> dict:
    authorize(scope, Permission.STUDENT_LMS_MANAGE)
    tenant_id = require_student_scope(scope)
    row = await StudentLmsPreferences.find_one({"tenant_id": tenant_id, "user_id": user.id})
    if row is None:
        row = StudentLmsPreferences(tenant_id=tenant_id, user_id=user.id)
    if group_by_unit is not None:
        row.group_by_unit = group_by_unit
    if show_recorded is not None:
        row.show_recorded_lectures = show_recorded
    row.updated_at = utcnow()
    existing = await StudentLmsPreferences.find_one({"tenant_id": tenant_id, "user_id": user.id})
    if existing is None:
        await row.insert()
    else:
        if group_by_unit is not None:
            existing.group_by_unit = group_by_unit
        if show_recorded is not None:
            existing.show_recorded_lectures = show_recorded
        existing.updated_at = utcnow()
        await existing.save()
    return await get_lms_preferences(scope, user)
