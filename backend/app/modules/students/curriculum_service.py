"""Student read-only curriculum, syllabus, and course information."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import SubjectRecord
from app.modules.academics.repositories import AcademicQueryRepository, CourseRepository
from app.modules.auth.models import User
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment
from app.modules.students.course_access import assert_student_course_access, resolve_course_id
from app.modules.students.curriculum_models import (
    CoursePrerequisite,
    CurriculumReference,
    SubjectCatalogReference,
    SyllabusReference,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.policy import require_student_scope
from app.modules.students.profile_service import ensure_student_profile
from app.modules.students.curriculum_schemas import (
    CourseInfoRead,
    CurriculumRead,
    EnrolledCourseItemRead,
    FacultyInfoRead,
    LearningOutcomesDetailRead,
    PrerequisiteRead,
    SemesterSubjectsRead,
    SubjectItemRead,
    SyllabusDetailRead,
    SyllabusRevisionRead,
)

_academic = AcademicQueryRepository()
_course_repo = CourseRepository()
_student_reader = StudentDataReader()


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _student_reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def list_enrolled_courses(scope: AccessScope, user: User) -> list[EnrolledCourseItemRead]:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    roster = await _student_reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    seen: set[str] = set()
    items: list[EnrolledCourseItemRead] = []
    for entry in roster:
        if entry.course_code in seen:
            continue
        seen.add(entry.course_code)
        course = await _course_repo.get_by_code(tenant_id, entry.course_code)
        items.append(
            EnrolledCourseItemRead(
                course_id=entry.course_id,
                course_code=entry.course_code,
                name=course.name if course else entry.course_code,
                section_code=entry.section_code,
                credit_units=course.credit_units if course else 0,
                academic_year_label=year,
                semester_label=semester,
                source="roster",
            )
        )
    return items


async def list_subjects_for_course(
    scope: AccessScope,
    user: User,
    course_code: str,
) -> list[SubjectItemRead]:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    await assert_student_course_access(tenant_id, user.id, course_code=course_code, academic_year_label=year, semester_label=semester)
    profile = await ensure_student_profile(scope, user)
    programme = profile.programme_code or "default"
    course_id = await resolve_course_id(tenant_id, course_code)
    catalog = await SubjectCatalogReference.find(
        {
            "tenant_id": tenant_id,
            "programme_code": programme,
            "course_id": course_id,
            "academic_year_label": year,
            "semester_label": semester,
        }
    ).sort("sequence_order").to_list()
    if catalog:
        return [
            SubjectItemRead(
                subject_id=row.subject_id,
                subject_code=row.subject_code,
                name=row.subject_code,
                credit_units=row.credit_units,
                sequence_order=row.sequence_order,
            )
            for row in catalog
        ]
    mappings = await _academic.subject_mappings(tenant_id, course_id)
    subjects: list[SubjectItemRead] = []
    for mapping in mappings:
        subject = await SubjectRecord.find_one({"tenant_id": tenant_id, "subject_id": mapping.subject_id})
        if subject is None:
            continue
        subjects.append(
            SubjectItemRead(
                subject_id=subject.subject_id,
                subject_code=subject.subject_code,
                name=subject.name,
                description=subject.description,
                sequence_order=mapping.sequence_order,
            )
        )
    return subjects


async def get_curriculum(scope: AccessScope, user: User, programme_code: str | None = None) -> CurriculumRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    profile = await ensure_student_profile(scope, user)
    programme = programme_code or profile.programme_code
    if not programme:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)
    ref = await CurriculumReference.find_one(
        {
            "tenant_id": tenant_id,
            "programme_code": programme,
            "academic_year_label": year,
            "semester_label": semester,
        }
    )
    central = None
    if ref is not None:
        central = await _academic.curriculum(tenant_id, ref.primary_course_id, year, semester)
    if central is None and ref is None:
        raise AppError(code="NOT_FOUND", message="Curriculum not published for this term", status_code=404)
    return CurriculumRead(
        programme_code=programme,
        academic_year_label=year,
        semester_label=semester,
        version=central.version if central else ref.central_version if ref else None,
        summary=central.summary if central else None,
        academic_regulations=ref.academic_regulations if ref else [],
        locked=True,
    )


async def get_syllabus(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    subject_id: str | None = None,
) -> SyllabusDetailRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    await assert_student_course_access(tenant_id, user.id, course_code=course_code, academic_year_label=year, semester_label=semester)
    course_id = await resolve_course_id(tenant_id, course_code)
    syllabus = await _academic.syllabus(tenant_id, course_id, subject_id=subject_id, year=year, semester=semester)
    if syllabus is None or not syllabus.approved:
        raise AppError(code="NOT_FOUND", message="Approved syllabus not available", status_code=404)
    ref = await SyllabusReference.find_one(
        {
            "tenant_id": tenant_id,
            "course_id": course_id,
            "subject_id": subject_id,
            "academic_year_label": year,
            "semester_label": semester,
        }
    )
    history = [
        SyllabusRevisionRead(version=e.version, effective_at=e.effective_at, summary=e.summary)
        for e in (ref.revision_history if ref else [])
    ]
    return SyllabusDetailRead(
        course_id=syllabus.course_id,
        subject_id=syllabus.subject_id,
        academic_year_label=syllabus.academic_year_label,
        semester_label=syllabus.semester_label,
        units=syllabus.units,
        objectives=syllabus.objectives,
        teaching_materials=syllabus.teaching_materials,
        revision_history=history,
        locked=syllabus.locked,
    )


async def get_course_outcomes(scope: AccessScope, user: User, course_code: str) -> LearningOutcomesDetailRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    await assert_student_course_access(tenant_id, user.id, course_code=course_code, academic_year_label=year, semester_label=semester)
    course_id = await resolve_course_id(tenant_id, course_code)
    doc = await _academic.learning_outcomes(tenant_id, course_id, year, semester)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Learning outcomes not found", status_code=404)
    return LearningOutcomesDetailRead(
        course_id=doc.course_id,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        outcomes=doc.outcomes,
        locked=doc.locked,
    )


async def get_prerequisites(scope: AccessScope, user: User, course_code: str) -> PrerequisiteRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    course = await _course_repo.get_by_code(tenant_id, course_code)
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)
    row = await CoursePrerequisite.find_one({"tenant_id": tenant_id, "course_id": course.course_id})
    if row is None:
        return PrerequisiteRead(
            course_id=course.course_id,
            course_code=course.course_code,
            prerequisite_course_ids=[],
            corequisite_course_ids=[],
        )
    return PrerequisiteRead(
        course_id=row.course_id,
        course_code=row.course_code,
        prerequisite_course_ids=row.prerequisite_course_ids,
        corequisite_course_ids=row.corequisite_course_ids,
        min_cgpa=row.min_cgpa,
        notes=row.notes,
    )


async def get_course_information(scope: AccessScope, user: User, course_code: str) -> CourseInfoRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    await assert_student_course_access(tenant_id, user.id, course_code=course_code, academic_year_label=year, semester_label=semester)
    course = await _course_repo.get_by_code(tenant_id, course_code)
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)
    faculty_rows: list[FacultyInfoRead] = []
    assignments = await FacultyAssignment.find(
        {
            "tenant_id": tenant_id,
            "course_code": course_code,
            "academic_year_label": year,
            "semester_label": semester,
            "status": AssignmentStatus.ACTIVE,
        }
    ).to_list()
    if assignments:
        user_ids = {a.user_id for a in assignments}
        users = await User.find({"_id": {"$in": list(user_ids)}}).to_list()
        names = {str(u.id): u.full_name for u in users}
        for a in assignments:
            faculty_rows.append(
                FacultyInfoRead(
                    faculty_user_id=str(a.user_id),
                    display_name=names.get(str(a.user_id), "Faculty"),
                    section=a.section,
                    subject_code=a.subject_code,
                )
            )
    return CourseInfoRead(
        course_id=course.course_id,
        course_code=course.course_code,
        name=course.name,
        description=course.description,
        credit_units=course.credit_units,
        faculty=faculty_rows,
    )


async def semester_subjects(scope: AccessScope, user: User) -> SemesterSubjectsRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    profile = await ensure_student_profile(scope, user)
    programme = profile.programme_code or "default"
    courses = await list_enrolled_courses(scope, user)
    subjects: list[SubjectItemRead] = []
    for c in courses:
        subs = await SubjectCatalogReference.find(
            {
                "tenant_id": tenant_id,
                "programme_code": programme,
                "course_id": c.course_id,
                "academic_year_label": year,
                "semester_label": semester,
            }
        ).to_list()
        if subs:
            subjects.extend(
                [
                    SubjectItemRead(
                        subject_id=s.subject_id,
                        subject_code=s.subject_code,
                        name=s.subject_code,
                        credit_units=s.credit_units,
                        sequence_order=s.sequence_order,
                    )
                    for s in subs
                ]
            )
        else:
            subjects.extend(await list_subjects_for_course(scope, user, c.course_code))
    return SemesterSubjectsRead(academic_year_label=year, semester_label=semester, subjects=subjects)
