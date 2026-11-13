"""Faculty course and academic content access."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import SubjectRecord
from app.modules.academics.repositories import AcademicQueryRepository, CourseRepository
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.faculty.course_access import require_course_access, resolve_course_id
from app.modules.faculty.enums import FacultyActivityType
from app.modules.faculty.models import CourseCoverage, FacultyAssignment
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.repositories import FacultyActivityRepository, FacultyAssignmentRepository
from app.modules.faculty.content_schemas import (
    AssignedCourseListItem,
    AssignedSubjectItem,
    CourseCoverageRead,
    CourseCoverageUpdate,
    CourseDetailRead,
    EnrolledStudentRead,
    LearningOutcomesRead,
    SectionBatchRead,
    SyllabusRead,
    TeachingProgressRead,
)

_assignment_repo = FacultyAssignmentRepository()
_course_repo = CourseRepository()
_academic = AcademicQueryRepository()
_activity_repo = FacultyActivityRepository()


async def list_assigned_courses(scope: AccessScope, user: User) -> list[AssignedCourseListItem]:
    authorize(scope, Permission.FACULTY_COURSE_READ)
    tenant_id = require_faculty_scope(scope)
    assignments = await _assignment_repo.list_active_for_user(tenant_id, user.id)
    return [
        AssignedCourseListItem(
            assignment_id=str(a.id),
            course_id=a.course_id,
            course_code=a.course_code,
            course_name=a.course_name,
            section=a.section,
            academic_year_label=a.academic_year_label,
            semester_label=a.semester_label,
        )
        for a in assignments
    ]


async def list_assigned_subjects(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    section: str | None = None,
) -> list[AssignedSubjectItem]:
    authorize(scope, Permission.FACULTY_COURSE_READ)
    tenant_id = require_faculty_scope(scope)
    await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    course_id = await resolve_course_id(tenant_id, course_code)
    mappings = await _academic.subject_mappings(tenant_id, course_id)
    subjects: list[AssignedSubjectItem] = []
    for mapping in mappings:
        subject = await SubjectRecord.find_one({"tenant_id": tenant_id, "subject_id": mapping.subject_id})
        if subject is None:
            continue
        subjects.append(
            AssignedSubjectItem(
                subject_id=subject.subject_id,
                subject_code=subject.subject_code,
                name=subject.name,
                description=subject.description,
            )
        )
    from app.modules.faculty.enums import AssignmentStatus

    assignment = await FacultyAssignment.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": user.id,
            "course_code": course_code,
            "status": AssignmentStatus.ACTIVE,
        }
    )
    if assignment and assignment.subject_id and assignment.subject_code:
        if not any(s.subject_id == assignment.subject_id for s in subjects):
            subjects.append(
                AssignedSubjectItem(
                    subject_id=assignment.subject_id,
                    subject_code=assignment.subject_code,
                    name=assignment.subject_name or assignment.subject_code,
                )
            )
    return subjects


async def get_course_details(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    section: str | None = None,
) -> CourseDetailRead:
    authorize(scope, Permission.FACULTY_COURSE_READ)
    tenant_id = require_faculty_scope(scope)
    assignment = await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    course = await _course_repo.get_by_code(tenant_id, course_code)
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)
    return CourseDetailRead(
        course_id=course.course_id,
        course_code=course.course_code,
        name=course.name,
        description=course.description,
        credit_units=course.credit_units,
        academic_year_label=assignment.academic_year_label,
        semester_label=assignment.semester_label,
    )


async def get_approved_syllabus(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    section: str | None = None,
    subject_id: str | None = None,
) -> SyllabusRead:
    authorize(scope, Permission.FACULTY_COURSE_READ)
    tenant_id = require_faculty_scope(scope)
    assignment = await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    course_id = await resolve_course_id(tenant_id, course_code)
    syllabus = await _academic.syllabus(
        tenant_id,
        course_id,
        subject_id=subject_id,
        year=assignment.academic_year_label,
        semester=assignment.semester_label,
    )
    if syllabus is None:
        raise AppError(code="NOT_FOUND", message="Approved syllabus not found", status_code=404)
    return SyllabusRead(
        course_id=syllabus.course_id,
        subject_id=syllabus.subject_id,
        academic_year_label=syllabus.academic_year_label,
        semester_label=syllabus.semester_label,
        units=syllabus.units,
        objectives=syllabus.objectives,
        teaching_materials=syllabus.teaching_materials,
        locked=syllabus.locked,
    )


async def get_learning_outcomes(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    section: str | None = None,
) -> LearningOutcomesRead:
    authorize(scope, Permission.FACULTY_COURSE_READ)
    tenant_id = require_faculty_scope(scope)
    assignment = await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    course_id = await resolve_course_id(tenant_id, course_code)
    doc = await _academic.learning_outcomes(
        tenant_id, course_id, assignment.academic_year_label, assignment.semester_label
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Learning outcomes not found", status_code=404)
    return LearningOutcomesRead(
        course_id=doc.course_id,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        outcomes=doc.outcomes,
        locked=doc.locked,
    )


async def get_enrolled_students(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    section: str,
    subject_id: str | None = None,
) -> list[EnrolledStudentRead]:
    authorize(scope, Permission.FACULTY_COURSE_READ)
    tenant_id = require_faculty_scope(scope)
    await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    course_id = await resolve_course_id(tenant_id, course_code)
    roster = await _academic.roster(tenant_id, course_id, section, subject_id=subject_id)
    return [
        EnrolledStudentRead(
            roll_number=entry.roll_number,
            display_name=entry.display_name,
            student_user_id=str(entry.student_user_id),
        )
        for entry in roster
    ]


async def get_sections_batches(
    scope: AccessScope,
    user: User,
    course_code: str,
) -> list[SectionBatchRead]:
    authorize(scope, Permission.FACULTY_COURSE_READ)
    tenant_id = require_faculty_scope(scope)
    await require_course_access(tenant_id, user.id, course_code=course_code)
    course_id = await resolve_course_id(tenant_id, course_code)
    sections = await _academic.sections_for_course(tenant_id, course_id)
    return [
        SectionBatchRead(
            section_id=s.section_id,
            section_code=s.section_code,
            batch_label=s.batch_label,
        )
        for s in sections
    ]


async def get_course_coverage(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    section: str,
) -> CourseCoverageRead:
    authorize(scope, Permission.FACULTY_COURSE_READ)
    tenant_id = require_faculty_scope(scope)
    assignment = await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    course_id = assignment.course_id or await resolve_course_id(tenant_id, course_code)
    coverage = await CourseCoverage.find_one(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "course_id": course_id,
            "section": section,
        }
    )
    if coverage is None:
        return CourseCoverageRead(
            course_id=course_id,
            course_code=course_code,
            section=section,
            subject_id=assignment.subject_id,
            academic_year_label=assignment.academic_year_label,
            semester_label=assignment.semester_label,
            units_completed=[],
            percent_complete=0,
            progress_log=[],
            updated_at=utcnow(),
        )
    return _coverage_to_read(coverage)


def _coverage_to_read(coverage: CourseCoverage) -> CourseCoverageRead:
    return CourseCoverageRead(
        course_id=coverage.course_id,
        course_code=coverage.course_code,
        section=coverage.section,
        subject_id=coverage.subject_id,
        academic_year_label=coverage.academic_year_label,
        semester_label=coverage.semester_label,
        units_completed=coverage.units_completed,
        percent_complete=coverage.percent_complete,
        progress_log=[
            TeachingProgressRead(
                unit_no=n.unit_no,
                notes=n.notes,
                percent_complete=n.percent_complete,
                recorded_at=n.recorded_at,
            )
            for n in coverage.progress_log
        ],
        updated_at=coverage.updated_at,
    )


async def update_course_coverage(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    section: str,
    payload: CourseCoverageUpdate,
) -> CourseCoverageRead:
    authorize(scope, Permission.FACULTY_COVERAGE_UPDATE)
    tenant_id = require_faculty_scope(scope)
    assignment = await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    course_id = assignment.course_id or await resolve_course_id(tenant_id, course_code)
    coverage = await CourseCoverage.find_one(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "course_id": course_id,
            "section": section,
        }
    )
    if coverage is None:
        coverage = CourseCoverage(
            tenant_id=tenant_id,
            faculty_user_id=user.id,
            course_id=course_id,
            course_code=course_code,
            section=section,
            subject_id=assignment.subject_id,
            academic_year_label=assignment.academic_year_label,
            semester_label=assignment.semester_label,
        )
    if payload.units_completed is not None:
        coverage.units_completed = sorted(set(payload.units_completed))
    if payload.percent_complete is not None:
        coverage.percent_complete = payload.percent_complete
    if payload.progress_note:
        from app.modules.faculty.models import TeachingProgressNote

        coverage.progress_log.append(
            TeachingProgressNote(
                unit_no=payload.unit_no,
                notes=payload.progress_note,
                percent_complete=payload.percent_complete,
            )
        )
    coverage.updated_at = utcnow()
    if coverage.id is None:
        await coverage.insert()
    else:
        await coverage.save()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.COVERAGE_UPDATED,
        title=f"Coverage updated for {course_code} {section}",
        metadata={"percent_complete": coverage.percent_complete},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.coverage.updated",
        resource_type="course_coverage",
        resource_id=str(coverage.id),
        tenant_id=tenant_id,
        metadata={"course_code": course_code, "section": section},
    )
    return _coverage_to_read(coverage)
