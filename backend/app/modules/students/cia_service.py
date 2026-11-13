"""Student CIA and internal assessment marks (read-only)."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.examinations.enums import StudentMarkStatus
from app.modules.examinations.grading import get_grading_policy, letter_grade, weighted_percentage
from app.modules.examinations.models import Assessment, MarksCorrectionRequest, StudentAssessmentMark
from app.modules.students.integrations.assessment_reader import (
    all_marks_for_student,
    assessments_for_student,
    cia_components,
    cia_examination_slots,
    cia_schedules,
    published_mark,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.assessment_enums import MarkVisibility
from app.modules.students.assessment_models import StudentCiaViewPreferences
from app.modules.students.assessment_schemas import (
    AssessmentComponentStudentRead,
    CiaHistoryItemRead,
    CiaScheduleRead,
    CiaSummaryRead,
    MarksCorrectionStatusRead,
    PublishedMarkRead,
    SubjectInternalMarksRead,
    UnpublishedComponentRead,
)
from app.modules.students.policy import require_student_scope

_reader = StudentDataReader()
_PUBLISHED = frozenset({StudentMarkStatus.APPROVED, StudentMarkStatus.LOCKED})


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _prefs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> StudentCiaViewPreferences:
    row = await StudentCiaViewPreferences.find_one({"tenant_id": tenant_id, "user_id": user_id})
    if row is not None:
        return row
    row = StudentCiaViewPreferences(tenant_id=tenant_id, user_id=user_id)
    await row.insert()
    return row


async def get_cia_schedules(scope: AccessScope, user: User) -> list[CiaScheduleRead]:
    authorize(scope, Permission.STUDENT_CIA_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    upcoming = await cia_schedules(tenant_id, user.id, year=year, semester=semester)
    exams = await cia_examination_slots(tenant_id, user.id, year=year, semester=semester)
    items: list[CiaScheduleRead] = [
        CiaScheduleRead(
            id=str(u.id),
            title=u.title,
            course_code=u.course_code,
            assessment_type=u.assessment_type,
            scheduled_at=u.scheduled_at,
            source="upcoming_assessments",
        )
        for u in upcoming
    ]
    items.extend(
        CiaScheduleRead(
            id=str(e.id),
            title=e.title,
            course_code=e.course_code,
            assessment_type=e.exam_type,
            scheduled_at=e.scheduled_at,
            source="examination_schedules",
        )
        for e in exams
    )
    items.sort(key=lambda x: x.scheduled_at)
    return items


async def get_assessment_components(scope: AccessScope, user: User, assessment_id: str) -> list[AssessmentComponentStudentRead]:
    authorize(scope, Permission.STUDENT_CIA_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    assessment = await Assessment.find_one({"tenant_id": tenant_id, "assessment_id": assessment_id})
    if assessment is None:
        raise AppError(code="NOT_FOUND", message="Assessment not found", status_code=404)
    if not await assessment_reader_course_check(tenant_id, user.id, year, semester, assessment.course_code):
        raise AppError(code="FORBIDDEN", message="Assessment is outside your enrolled courses", status_code=403)
    components = await cia_components(tenant_id, assessment_id)
    return [
        AssessmentComponentStudentRead(
            assessment_id=c.assessment_id,
            component_id=c.component_id,
            code=c.code,
            name=c.name,
            component_type=c.component_type,
            max_marks=c.max_marks,
            weight_percent=c.weight_percent,
        )
        for c in components
    ]


async def assessment_reader_course_check(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, year: str, semester: str, course_code: str
) -> bool:
    roster = await _reader.roster_entries(tenant_id, user_id, academic_year_label=year, semester_label=semester)
    return any(r.course_code == course_code for r in roster)


async def get_published_cia_marks(scope: AccessScope, user: User) -> list[PublishedMarkRead]:
    authorize(scope, Permission.STUDENT_CIA_READ)
    tenant_id = require_student_scope(scope)
    policy = await get_grading_policy(tenant_id)
    marks = await all_marks_for_student(tenant_id, user.id, published_only=True)
    return [_mark_to_read(m, policy) for m in marks]


def _mark_to_read(mark: StudentAssessmentMark, policy) -> PublishedMarkRead:
    pct = weighted_percentage(mark.marks_obtained, mark.max_marks)
    return PublishedMarkRead(
        assessment_id=mark.assessment_id,
        component_id=mark.component_id,
        marks_obtained=mark.marks_obtained,
        max_marks=mark.max_marks,
        percentage=pct,
        grade_letter=letter_grade(pct, policy),
        published_at=mark.updated_at,
    )


async def get_subject_wise_internal_marks(scope: AccessScope, user: User) -> list[SubjectInternalMarksRead]:
    authorize(scope, Permission.STUDENT_CIA_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    roster = await _reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    policy = await get_grading_policy(tenant_id)
    by_course: dict[str, list[PublishedMarkRead]] = {}
    marks = await all_marks_for_student(tenant_id, user.id, published_only=True)
    assessments = {a.assessment_id: a for a in await assessments_for_student(tenant_id, user.id, year=year, semester=semester)}
    for m in marks:
        assessment = assessments.get(m.assessment_id)
        course = assessment.course_code if assessment else "unknown"
        read = _mark_to_read(m, policy)
        read.course_code = course
        by_course.setdefault(course, []).append(read)
    results: list[SubjectInternalMarksRead] = []
    for entry in roster:
        course_marks = by_course.get(entry.course_code, [])
        total_o = sum(m.marks_obtained for m in course_marks)
        total_m = sum(m.max_marks for m in course_marks)
        wp = round((total_o / total_m) * 100, 2) if total_m else None
        results.append(
            SubjectInternalMarksRead(
                course_code=entry.course_code,
                subject_id=entry.subject_id,
                components=course_marks,
                total_obtained=total_o,
                total_max=total_m,
                weighted_percentage=wp,
            )
        )
    return results


async def get_cia_summary(scope: AccessScope, user: User) -> CiaSummaryRead:
    authorize(scope, Permission.STUDENT_CIA_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    subjects = await get_subject_wise_internal_marks(scope, user)
    published = sum(len(s.components) for s in subjects)
    assessments = await assessments_for_student(tenant_id, user.id, year=year, semester=semester)
    unpublished: list[UnpublishedComponentRead] = []
    missing = 0
    for assessment in assessments:
        for comp in await cia_components(tenant_id, assessment.assessment_id):
            mark = await published_mark(
                tenant_id, user.id, assessment_id=assessment.assessment_id, component_id=comp.component_id
            )
            if mark is None:
                draft = await StudentAssessmentMark.find_one(
                    {
                        "tenant_id": tenant_id,
                        "student_user_id": user.id,
                        "assessment_id": assessment.assessment_id,
                        "component_id": comp.component_id,
                    }
                )
                if draft and draft.status not in _PUBLISHED:
                    unpublished.append(
                        UnpublishedComponentRead(
                            assessment_id=assessment.assessment_id,
                            component_id=comp.component_id,
                            component_name=comp.name,
                            course_code=assessment.course_code,
                            visibility=MarkVisibility.UNPUBLISHED,
                        )
                    )
                else:
                    missing += 1
                    unpublished.append(
                        UnpublishedComponentRead(
                            assessment_id=assessment.assessment_id,
                            component_id=comp.component_id,
                            component_name=comp.name,
                            course_code=assessment.course_code,
                            visibility=MarkVisibility.MISSING,
                        )
                    )
    await record_audit(
        actor_id=scope.user_id,
        action="student.cia.summary_viewed",
        resource_type="student_user",
        resource_id=str(user.id),
        tenant_id=tenant_id,
    )
    return CiaSummaryRead(
        academic_year_label=year,
        semester_label=semester,
        published_count=published,
        unpublished_count=sum(1 for u in unpublished if u.visibility == MarkVisibility.UNPUBLISHED),
        missing_count=missing,
        subjects=subjects,
        unpublished_components=unpublished,
    )


async def get_marks_correction_status(scope: AccessScope, user: User, pagination: Pagination) -> Page[MarksCorrectionStatusRead]:
    authorize(scope, Permission.STUDENT_CIA_READ)
    tenant_id = require_student_scope(scope)
    query = MarksCorrectionRequest.find({"tenant_id": tenant_id, "student_user_id": user.id}).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            MarksCorrectionStatusRead(
                id=str(r.id),
                batch_id=str(r.batch_id),
                status=r.status.value,
                reason=r.reason,
                created_at=r.created_at,
                resolved_at=r.resolved_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_cia_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[CiaHistoryItemRead]:
    authorize(scope, Permission.STUDENT_CIA_READ)
    tenant_id = require_student_scope(scope)
    query = StudentAssessmentMark.find({"tenant_id": tenant_id, "student_user_id": user.id}).sort("-updated_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            CiaHistoryItemRead(
                component_id=r.component_id,
                assessment_id=r.assessment_id,
                marks_obtained=r.marks_obtained,
                max_marks=r.max_marks,
                status=r.status.value,
                updated_at=r.updated_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_published_feedback_for_component(
    scope: AccessScope, user: User, assessment_id: str, component_id: str
) -> dict:
    """Feedback for CIA may be stored in assignment_feedback linked via LMS; placeholder for published metadata."""
    authorize(scope, Permission.STUDENT_CIA_READ)
    tenant_id = require_student_scope(scope)
    mark = await published_mark(tenant_id, user.id, assessment_id=assessment_id, component_id=component_id)
    if mark is None:
        raise AppError(code="NOT_FOUND", message="Published marks not available", status_code=404)
    return {
        "assessment_id": assessment_id,
        "component_id": component_id,
        "feedback": None,
        "published_at": mark.updated_at.isoformat(),
    }
