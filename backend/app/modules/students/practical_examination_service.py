"""Student laboratory, practical and model examination views (read-only)."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.attendance.enums import AttendanceSessionStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.examinations.enums import StudentMarkStatus
from app.modules.examinations.grading import get_grading_policy, letter_grade, weighted_percentage
from app.modules.examinations.models import AssessmentComponent, StudentAssessmentMark
from app.modules.students.assessment_enums import MarkVisibility
from app.modules.students.examination_portal_schemas import (
    LaboratoryAttendanceRead,
    LaboratorySubjectRead,
    MarksCorrectionStudentRead,
    ModelExamMarkRead,
    ModelExamScheduleRead,
    PracticalComponentRead,
    PracticalExamHistoryItemRead,
    PracticalFeedbackRead,
    PracticalMarkRead,
    PracticalScheduleRead,
    UnpublishedPracticalMarkRead,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.practical_examination_reader import (
    MODEL_EXAM_TYPES,
    PRACTICAL_EXAM_TYPES,
    corrections_for_student,
    examination_schedules_by_types,
    laboratory_subjects,
    model_examination_components,
    practical_class_sessions,
    practical_components,
    student_model_marks,
    student_practical_marks,
)
from app.modules.students.policy import require_student_scope

_reader = StudentDataReader()
_PUBLISHED = frozenset({StudentMarkStatus.APPROVED, StudentMarkStatus.LOCKED})


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def get_laboratory_subjects(scope: AccessScope, user: User) -> list[LaboratorySubjectRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    rows = await laboratory_subjects(tenant_id, user.id, year=year, semester=semester)
    return [LaboratorySubjectRead(**row) for row in rows]


async def get_practical_schedules(scope: AccessScope, user: User) -> list[PracticalScheduleRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    items: list[PracticalScheduleRead] = []
    for row in await examination_schedules_by_types(
        tenant_id, user.id, year=year, semester=semester, exam_types=PRACTICAL_EXAM_TYPES
    ):
        items.append(
            PracticalScheduleRead(
                id=str(row.id),
                title=row.title,
                course_code=row.course_code,
                section=row.section,
                exam_type=row.exam_type,
                scheduled_at=row.scheduled_at,
                scheduled_end=row.scheduled_end,
                room=row.room,
                laboratory=row.metadata.get("laboratory") or row.centre_name,
                source="examination_schedules",
            )
        )
    for session in await practical_class_sessions(tenant_id, user.id, year=year, semester=semester):
        items.append(
            PracticalScheduleRead(
                id=str(session.id),
                title=session.topic or "Laboratory session",
                course_code=session.course_code,
                section=session.section,
                exam_type="laboratory",
                scheduled_at=session.scheduled_start,
                scheduled_end=session.scheduled_end,
                room=session.room,
                laboratory=session.laboratory,
                source="class_sessions",
            )
        )
    items.sort(key=lambda x: x.scheduled_at)
    return items


async def get_practical_assessment_details(scope: AccessScope, user: User) -> list[PracticalComponentRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    pairs = await practical_components(tenant_id, user.id, year=year, semester=semester)
    return [
        PracticalComponentRead(
            assessment_id=assessment.assessment_id,
            component_id=comp.component_id,
            course_code=assessment.course_code,
            code=comp.code,
            name=comp.name,
            component_type=comp.component_type,
            max_marks=comp.max_marks,
            weight_percent=comp.weight_percent,
        )
        for assessment, comp in pairs
    ]


async def get_published_practical_marks(scope: AccessScope, user: User) -> list[PracticalMarkRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    policy = await get_grading_policy(tenant_id)
    year, semester = await _term(tenant_id)
    pairs = await practical_components(tenant_id, user.id, year=year, semester=semester)
    assessment_by_id = {a.assessment_id: a for a, _ in pairs}
    comp_names = {c.component_id: c.name for _, c in pairs}
    marks = await student_practical_marks(tenant_id, user.id, published_only=True)
    result: list[PracticalMarkRead] = []
    for mark in marks:
        assessment = assessment_by_id.get(mark.assessment_id)
        if assessment is None:
            continue
        pct = weighted_percentage(mark.marks_obtained, mark.max_marks)
        result.append(
            PracticalMarkRead(
                assessment_id=mark.assessment_id,
                component_id=mark.component_id,
                course_code=assessment.course_code,
                component_name=comp_names.get(mark.component_id),
                marks_obtained=mark.marks_obtained,
                max_marks=mark.max_marks,
                percentage=pct,
                grade_letter=letter_grade(pct, policy),
                published_at=mark.updated_at,
                visibility="published",
            )
        )
    return result


async def get_unpublished_practical_marks(scope: AccessScope, user: User) -> list[UnpublishedPracticalMarkRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    pairs = await practical_components(tenant_id, user.id, year=year, semester=semester)
    rows: list[UnpublishedPracticalMarkRead] = []
    for assessment, comp in pairs:
        published = await StudentAssessmentMark.find_one(
            {
                "tenant_id": tenant_id,
                "student_user_id": user.id,
                "assessment_id": assessment.assessment_id,
                "component_id": comp.component_id,
                "status": {"$in": list(_PUBLISHED)},
            }
        )
        if published is not None:
            continue
        draft = await StudentAssessmentMark.find_one(
            {
                "tenant_id": tenant_id,
                "student_user_id": user.id,
                "assessment_id": assessment.assessment_id,
                "component_id": comp.component_id,
            }
        )
        visibility = MarkVisibility.UNPUBLISHED if draft else MarkVisibility.MISSING
        rows.append(
            UnpublishedPracticalMarkRead(
                assessment_id=assessment.assessment_id,
                component_id=comp.component_id,
                course_code=assessment.course_code,
                component_name=comp.name,
                visibility=visibility.value,
            )
        )
    return rows


async def get_model_examination_schedules(scope: AccessScope, user: User) -> list[ModelExamScheduleRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    rows = await examination_schedules_by_types(
        tenant_id, user.id, year=year, semester=semester, exam_types=MODEL_EXAM_TYPES
    )
    return [
        ModelExamScheduleRead(
            id=str(row.id),
            title=row.title,
            course_code=row.course_code,
            section=row.section,
            scheduled_at=row.scheduled_at,
            room=row.room,
            centre_name=row.centre_name,
        )
        for row in rows
    ]


async def get_published_model_marks(scope: AccessScope, user: User) -> list[ModelExamMarkRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    pairs = await model_examination_components(tenant_id, user.id, year=year, semester=semester)
    assessment_by_id = {a.assessment_id: a for a, _ in pairs}
    marks = await student_model_marks(tenant_id, user.id, year=year, semester=semester)
    result: list[ModelExamMarkRead] = []
    for mark in marks:
        assessment = assessment_by_id.get(mark.assessment_id)
        if assessment is None:
            continue
        pct = weighted_percentage(mark.marks_obtained, mark.max_marks)
        result.append(
            ModelExamMarkRead(
                assessment_id=mark.assessment_id,
                component_id=mark.component_id,
                course_code=assessment.course_code,
                marks_obtained=mark.marks_obtained,
                max_marks=mark.max_marks,
                percentage=pct,
                published_at=mark.updated_at,
            )
        )
    return result


async def get_practical_feedback(scope: AccessScope, user: User, assessment_id: str, component_id: str) -> PracticalFeedbackRead:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    mark = await StudentAssessmentMark.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": user.id,
            "assessment_id": assessment_id,
            "component_id": component_id,
            "status": {"$in": list(_PUBLISHED)},
        }
    )
    if mark is None:
        raise AppError(code="NOT_FOUND", message="Published practical marks not available", status_code=404)
    pairs = await practical_components(tenant_id, user.id, year=year, semester=semester)
    course_code = next((a.course_code for a, c in pairs if c.component_id == component_id), "unknown")
    await record_audit(
        actor_id=scope.user_id,
        action="student.practical.feedback_viewed",
        resource_type="assessment_component",
        resource_id=component_id,
        tenant_id=tenant_id,
    )
    return PracticalFeedbackRead(
        assessment_id=assessment_id,
        component_id=component_id,
        course_code=course_code,
        feedback=None,
        published_at=mark.updated_at,
    )


async def get_laboratory_attendance(scope: AccessScope, user: User) -> list[LaboratoryAttendanceRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    lab_courses = {(row["course_code"], row["section"]) for row in await laboratory_subjects(tenant_id, user.id, year=year, semester=semester)}
    if not lab_courses:
        return []
    policy_doc = await AttendancePolicyReference.find_one({"tenant_id": tenant_id, "is_active": True})
    policy_rules = policy_doc.rules if policy_doc else AttendancePolicyReference(tenant_id=tenant_id).rules
    items: list[LaboratoryAttendanceRead] = []
    for course_code, section in sorted(lab_courses):
        sessions = await AttendanceSession.find(
            {
                "tenant_id": tenant_id,
                "course_code": course_code,
                "section": section,
                "academic_year_label": year,
                "semester_label": semester,
                "status": {"$in": [AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED]},
            }
        ).to_list()
        session_ids = [s.id for s in sessions]
        records = (
            await AttendanceRecord.find(
                {"tenant_id": tenant_id, "student_user_id": user.id, "session_id": {"$in": session_ids}}
            ).to_list()
            if session_ids
            else []
        )
        pct = calculate_percentage(records, policy_rules) if records else None
        items.append(
            LaboratoryAttendanceRead(
                course_code=course_code,
                section=section,
                percentage=pct,
                sessions_held=len(sessions),
                sessions_recorded=len(records),
                authorized=True,
            )
        )
    return items


async def get_practical_examination_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[PracticalExamHistoryItemRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    pairs = await practical_components(tenant_id, user.id, year=year, semester=semester)
    component_ids = {c.component_id for _, c in pairs}
    assessment_by_id = {a.assessment_id: a for a, _ in pairs}
    if not component_ids:
        return Page(items=[], total=0, limit=pagination.limit, offset=pagination.offset)
    query = StudentAssessmentMark.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user.id,
            "component_id": {"$in": list(component_ids)},
        }
    ).sort("-updated_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        PracticalExamHistoryItemRead(
            component_id=r.component_id,
            assessment_id=r.assessment_id,
            course_code=assessment_by_id.get(r.assessment_id).course_code if assessment_by_id.get(r.assessment_id) else "unknown",
            marks_obtained=r.marks_obtained,
            max_marks=r.max_marks,
            status=r.status.value,
            updated_at=r.updated_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_practical_correction_status(scope: AccessScope, user: User, pagination: Pagination) -> Page[MarksCorrectionStudentRead]:
    authorize(scope, Permission.STUDENT_PRACTICAL_EXAM_READ)
    tenant_id = require_student_scope(scope)
    rows = await corrections_for_student(tenant_id, user.id)
    slice_rows = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[
            MarksCorrectionStudentRead(
                id=str(r.id),
                batch_id=str(r.batch_id),
                status=r.status.value,
                reason=r.reason,
                created_at=r.created_at,
                resolved_at=r.resolved_at,
            )
            for r in slice_rows
        ],
        total=len(rows),
        limit=pagination.limit,
        offset=pagination.offset,
    )
