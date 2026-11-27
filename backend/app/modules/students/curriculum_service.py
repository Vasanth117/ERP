"""Student read-only curriculum, syllabus, and course information."""

import re
from collections import defaultdict
from datetime import date
from typing import NamedTuple

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import (
    CourseLearningOutcome,
    CourseRecord,
    CurriculumRecord,
    SubjectRecord,
    SyllabusUnit,
)
from app.modules.academics.models import AcademicYearContext
from app.modules.academics.repositories import AcademicQueryRepository, CourseRepository
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.auth.models import User
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment
from app.modules.students.course_access import assert_student_course_access, resolve_course_id
from app.modules.students.curriculum_models import (
    CourseCatalogReference,
    CoursePrerequisite,
    CurriculumReference,
    ProgrammeCurriculumVersionReference,
    ElectiveGroup,
    ElectiveOption,
    SubjectCatalogReference,
    SyllabusReference,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.student_lms_reader import published_materials_for_student
from app.modules.students.student_lms_models import StudentMaterialAccessLog
from app.modules.students.policy import require_student_scope
from app.modules.students.profile_service import ensure_student_profile
from app.modules.students.curriculum_schemas import (
    CourseInfoRead,
    CurriculumOverviewKpisRead,
    CurriculumOverviewRead,
    CurriculumOverviewSemesterRowRead,
    CurriculumSemesterCourseRowRead,
    CurriculumSemesterCreditCategoryRead,
    CurriculumSemesterPageRead,
    CurriculumSemesterTabRead,
    CurriculumSubjectAssessmentRead,
    CurriculumCreditComponentRowRead,
    CurriculumSubjectCreditDetailsRead,
    CurriculumSubjectDetailRead,
    CurriculumSubjectFilterOptionRead,
    CurriculumSubjectListRead,
    CurriculumSubjectListRowRead,
    CurriculumSubjectResourceRead,
    CurriculumSyllabusPageRead,
    CurriculumSyllabusResourceRead,
    CurriculumSyllabusTopicRead,
    CurriculumSyllabusUnitDetailRead,
    CurriculumSyllabusUnitRowRead,
    CurriculumCategoriesElectivesPageRead,
    CurriculumHistoryPageRead,
    CurriculumHistoryRowRead,
    CurriculumCategoryCourseRowRead,
    CurriculumCategoryPanelRead,
    CurriculumElectiveCatalogueRowRead,
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
from app.modules.students.registration_enums import CourseRegistrationType

_academic = AcademicQueryRepository()
_course_repo = CourseRepository()
_student_reader = StudentDataReader()

_REGISTRATION_TYPE_LABELS = {
    CourseRegistrationType.CORE.value: "Professional core",
    CourseRegistrationType.ELECTIVE.value: "Professional elective",
    CourseRegistrationType.OPEN.value: "Open elective",
}

_COURSE_TYPE_FALLBACK = [
    ("professional_core", "Professional core"),
    ("basic_science", "Basic science"),
    ("mandatory", "Mandatory"),
    ("humanities", "Humanities"),
    ("elective", "Professional elective"),
    ("open_elective", "Open elective"),
]


def _parse_semester_number(label: str) -> int | None:
    if not label:
        return None
    match = re.search(r"(\d+)", label)
    return int(match.group(1)) if match else None


def _catalog_credits(entry: CourseCatalogReference, course: CourseRecord | None) -> float:
    if entry.credit_units > 0:
        return float(entry.credit_units)
    if course is not None and course.credit_units > 0:
        return float(course.credit_units)
    if course is not None:
        return float(course.lecture_hours) + course.tutorial_hours / 2 + course.practical_hours / 2
    return 0.0


def _ltp_label(course: CourseRecord) -> str:
    return f"{course.lecture_hours}-{course.tutorial_hours}-{course.practical_hours}"


def _course_type_label(raw: str | None) -> str:
    if not raw:
        return "—"
    for key, label in _COURSE_TYPE_FALLBACK:
        if key == raw or label.lower() == raw.lower():
            return label
    return raw.replace("_", " ").title()


def _student_course_status(
    course: CourseRecord,
    curriculum_row: CurriculumRecord | None,
) -> tuple[str, str, str]:
    if curriculum_row and curriculum_row.approved:
        return "approved", "Approved", "success"
    if course.configuration_status == "draft":
        return "pending", "Pending approval", "warning"
    if not course.is_active:
        return "inactive", "Inactive", "muted"
    return "published", "Published", "success"


class _ProgrammeCatalogMaps(NamedTuple):
    unique_catalog: dict[str, CourseCatalogReference]
    course_by_id: dict[str, CourseRecord]
    course_by_code: dict[str, CourseRecord]


async def _load_programme_catalog_maps(
    tenant_id: PydanticObjectId,
    programme_code: str,
) -> _ProgrammeCatalogMaps:
    catalog_rows = await CourseCatalogReference.find(
        Eq(CourseCatalogReference.tenant_id, tenant_id),
        Eq(CourseCatalogReference.programme_code, programme_code),
    ).to_list()
    courses_all = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    course_by_id = {c.course_id: c for c in courses_all}
    course_by_code = {c.course_code.upper(): c for c in courses_all}
    unique_catalog: dict[str, CourseCatalogReference] = {}
    for entry in catalog_rows:
        existing = unique_catalog.get(entry.course_id)
        if existing is None or entry.credit_units > existing.credit_units:
            unique_catalog[entry.course_id] = entry
    return _ProgrammeCatalogMaps(unique_catalog, course_by_id, course_by_code)


async def _resolve_curriculum_reference(
    tenant_id: PydanticObjectId,
    programme_code: str,
    *,
    academic_year_label: str,
    semester_label: str,
) -> CurriculumReference | None:
    ref = await CurriculumReference.find_one(
        {
            "tenant_id": tenant_id,
            "programme_code": programme_code,
            "academic_year_label": academic_year_label,
            "semester_label": semester_label,
        }
    )
    if ref is not None:
        return ref
    return (
        await CurriculumReference.find(
            Eq(CurriculumReference.tenant_id, tenant_id),
            Eq(CurriculumReference.programme_code, programme_code),
        )
        .sort("-updated_at")
        .first_or_none()
    )


def _resolve_semester_number(entry: CourseCatalogReference, course: CourseRecord | None) -> int | None:
    parsed = _parse_semester_number(entry.semester_label)
    if parsed is not None:
        return parsed
    if course is not None and course.semester_number is not None:
        return course.semester_number
    return None


async def _current_semester_number(tenant_id: PydanticObjectId) -> int | None:
    context = await AcademicYearContext.find_one(
        Eq(AcademicYearContext.tenant_id, tenant_id),
        Eq(AcademicYearContext.is_current, True),
    )
    if context is None:
        return None
    if context.semester_number is not None:
        return context.semester_number
    return _parse_semester_number(context.semester_label)


async def _load_academic_programme(
    tenant_id: PydanticObjectId,
    programme_code: str,
) -> AcademicProgramme | None:
    programme = await AcademicProgramme.find_one(
        Eq(AcademicProgramme.tenant_id, tenant_id),
        Eq(AcademicProgramme.programme_code, programme_code),
    )
    if programme is not None:
        return programme
    normalised = programme_code.replace(" ", "").replace(".", "").upper()
    cursor = AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id))
    async for row in cursor:
        row_key = row.programme_code.replace(" ", "").replace(".", "").upper()
        if row_key == normalised or normalised in row_key or row_key in normalised:
            return row
    return None


async def _regulation_label_for_programme(
    tenant_id: PydanticObjectId,
    programme_code: str,
) -> str | None:
    refs = await CurriculumReference.find(
        Eq(CurriculumReference.tenant_id, tenant_id),
        Eq(CurriculumReference.programme_code, programme_code),
    ).sort("-updated_at").to_list()
    for ref in refs:
        if ref.central_version:
            return ref.central_version
        if ref.academic_regulations:
            return ref.academic_regulations[0]
    return None


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
    ref = await _resolve_curriculum_reference(
        tenant_id,
        programme,
        academic_year_label=year,
        semester_label=semester,
    )
    central = None
    if ref is not None:
        central = await _academic.curriculum(
            tenant_id,
            ref.primary_course_id,
            ref.academic_year_label,
            ref.semester_label,
        )
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


def _semester_status(
    semester_number: int,
    current_semester: int | None,
) -> tuple[str, str, str]:
    if current_semester is None:
        return "upcoming", "Upcoming", "muted"
    if semester_number < current_semester:
        return "completed", "Completed", "success"
    if semester_number == current_semester:
        return "current", "Current", "info"
    return "upcoming", "Upcoming", "muted"


async def get_curriculum_overview(scope: AccessScope, user: User) -> CurriculumOverviewRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    programme_code = profile.programme_code
    if not programme_code:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)

    programme_doc = await _load_academic_programme(tenant_id, programme_code)
    programme_name = profile.programme_name or (programme_doc.name if programme_doc else programme_code)
    regulation = await _regulation_label_for_programme(tenant_id, programme_code)

    total_semesters = programme_doc.duration_semesters if programme_doc else 8
    current_semester = await _current_semester_number(tenant_id)

    catalog_rows = await CourseCatalogReference.find(
        Eq(CourseCatalogReference.tenant_id, tenant_id),
        Eq(CourseCatalogReference.programme_code, programme_code),
    ).to_list()

    courses_all = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    course_by_id = {c.course_id: c for c in courses_all}
    course_by_code = {c.course_code.upper(): c for c in courses_all}

    unique_catalog: dict[str, CourseCatalogReference] = {}
    for entry in catalog_rows:
        existing = unique_catalog.get(entry.course_id)
        if existing is None or entry.credit_units > existing.credit_units:
            unique_catalog[entry.course_id] = entry

    semester_buckets: dict[int, list[CourseCatalogReference]] = defaultdict(list)
    core_count = 0
    elective_count = 0
    elective_credits = 0.0
    lab_count = 0
    total_credits = 0.0

    for entry in unique_catalog.values():
        course = course_by_id.get(entry.course_id) or course_by_code.get(entry.course_code.upper())
        credits = _catalog_credits(entry, course)
        total_credits += credits

        reg_type = entry.registration_type
        if reg_type == CourseRegistrationType.CORE:
            core_count += 1
        elif reg_type in (CourseRegistrationType.ELECTIVE, CourseRegistrationType.OPEN):
            elective_count += 1
            elective_credits += credits

        if course is not None and course.practical_hours > 0:
            lab_count += 1

        sem_num = _resolve_semester_number(entry, course)
        if sem_num is not None and 1 <= sem_num <= total_semesters:
            semester_buckets[sem_num].append(entry)

    if programme_doc is not None and programme_doc.credits_required > 0 and total_credits == 0:
        total_credits = float(programme_doc.credits_required)

    subject_refs = await SubjectCatalogReference.find(
        Eq(SubjectCatalogReference.tenant_id, tenant_id),
        Eq(SubjectCatalogReference.programme_code, programme_code),
    ).to_list()
    subjects_by_course: dict[str, set[str]] = defaultdict(set)
    for ref in subject_refs:
        subjects_by_course[ref.course_id].add(ref.subject_id)

    semester_rows: list[CurriculumOverviewSemesterRowRead] = []
    populated_semesters = 0
    for sem in range(1, total_semesters + 1):
        entries = semester_buckets.get(sem, [])
        sem_credits = sum(_catalog_credits(e, course_by_id.get(e.course_id)) for e in entries)
        course_ids = [e.course_id for e in entries]
        subject_ids: set[str] = set()
        for cid in course_ids:
            subject_ids |= subjects_by_course.get(cid, set())
        subject_count = len(subject_ids) if subject_ids else len(entries)
        if entries:
            populated_semesters += 1
        status_code, status_label, status_tone = _semester_status(sem, current_semester)
        semester_rows.append(
            CurriculumOverviewSemesterRowRead(
                semester_number=sem,
                label=f"Semester {sem}",
                subject_count=subject_count,
                credits=round(sem_credits, 1) if sem_credits % 1 else int(sem_credits),
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    headline = programme_name
    if regulation:
        headline = f"{programme_name} · Regulation {regulation}"

    kpis = CurriculumOverviewKpisRead(
        total_credits=round(total_credits, 1) if total_credits % 1 else int(total_credits),
        total_semesters=total_semesters,
        total_credits_semester_hint=f"{total_semesters} semesters" if total_semesters else None,
        core_subjects=core_count,
        electives=elective_count,
        elective_credits=round(elective_credits, 1) if elective_credits % 1 else int(elective_credits),
        elective_credits_hint=(
            f"{int(elective_credits) if elective_credits == int(elective_credits) else elective_credits} credits"
            if elective_credits > 0
            else None
        ),
        labs=lab_count,
    )

    return CurriculumOverviewRead(
        programme_headline=headline,
        programme_code=programme_code,
        regulation_label=regulation,
        kpis=kpis,
        semesters=semester_rows,
        semesters_footer_label=f"{populated_semesters} of {total_semesters}",
    )


def _catalog_for_semester(
    prog_catalog: list[CourseCatalogReference],
    semester: int,
    course_by_id: dict[str, CourseRecord],
    course_by_code: dict[str, CourseRecord],
    courses_all: list[CourseRecord],
) -> list[CourseCatalogReference]:
    semester_key = str(semester)
    sem_catalog = [
        c
        for c in prog_catalog
        if _parse_semester_number(c.semester_label) == semester or c.semester_label.strip() == semester_key
    ]
    if sem_catalog:
        return sem_catalog
    sem_catalog = []
    for c in prog_catalog:
        course = course_by_id.get(c.course_id) or course_by_code.get(c.course_code.upper())
        if course is not None and course.semester_number == semester:
            sem_catalog.append(c)
    if sem_catalog:
        return sem_catalog
    # Fallback: courses tagged on central registry only (no catalog row yet)
    seen: set[str] = set()
    for course in courses_all:
        if course.semester_number != semester or course.course_id in seen:
            continue
        seen.add(course.course_id)
        sem_catalog.append(
            CourseCatalogReference(
                tenant_id=course.tenant_id,
                programme_code="",
                academic_year_label="",
                semester_label=str(semester),
                course_id=course.course_id,
                course_code=course.course_code,
                registration_type=CourseRegistrationType.CORE,
                credit_units=course.credit_units,
            )
        )
    return sem_catalog


async def get_curriculum_semester_page(
    scope: AccessScope,
    user: User,
    *,
    semester: int | None = None,
) -> CurriculumSemesterPageRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    programme_code = profile.programme_code
    if not programme_code:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)

    programme_doc = await _load_academic_programme(tenant_id, programme_code)
    programme_name = profile.programme_name or (programme_doc.name if programme_doc else programme_code)
    regulation = await _regulation_label_for_programme(tenant_id, programme_code)
    total_semesters = programme_doc.duration_semesters if programme_doc else 8
    current_semester = await _current_semester_number(tenant_id)

    if semester is None:
        semester = current_semester if current_semester is not None else 1
    semester = max(1, min(semester, total_semesters))

    catalog_rows = await CourseCatalogReference.find(
        Eq(CourseCatalogReference.tenant_id, tenant_id),
        Eq(CourseCatalogReference.programme_code, programme_code),
    ).to_list()

    courses_all = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    course_by_id = {c.course_id: c for c in courses_all}
    course_by_code = {c.course_code.upper(): c for c in courses_all}

    unique_catalog: dict[str, CourseCatalogReference] = {}
    for entry in catalog_rows:
        existing = unique_catalog.get(entry.course_id)
        if existing is None or entry.credit_units > existing.credit_units:
            unique_catalog[entry.course_id] = entry
    prog_catalog = list(unique_catalog.values())

    curriculum_records = await CurriculumRecord.find(Eq(CurriculumRecord.tenant_id, tenant_id)).to_list()
    curriculum_by_course = {row.course_id: row for row in curriculum_records}

    sem_entries = _catalog_for_semester(prog_catalog, semester, course_by_id, course_by_code, courses_all)

    table_rows: list[CurriculumSemesterCourseRowRead] = []
    total_credits = 0.0
    credits_by_category: dict[str, float] = defaultdict(float)

    for entry in sorted(sem_entries, key=lambda e: e.course_code):
        course = course_by_id.get(entry.course_id) or course_by_code.get(entry.course_code.upper())
        if course is None:
            continue
        credits = _catalog_credits(entry, course)
        total_credits += credits
        type_label = _REGISTRATION_TYPE_LABELS.get(
            entry.registration_type.value,
            _course_type_label(course.course_type),
        )
        credits_by_category[entry.registration_type.value] += credits
        cur_row = curriculum_by_course.get(course.course_id)
        status_code, status_label, status_tone = _student_course_status(course, cur_row)
        syllabus_href = f"/student/curriculum/course-syllabus?course={entry.course_code}"
        table_rows.append(
            CurriculumSemesterCourseRowRead(
                course_id=course.course_id,
                course_code=course.course_code,
                course_name=course.name,
                type_label=type_label,
                ltp_label=_ltp_label(course),
                credits=round(credits, 1) if credits % 1 else int(credits),
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                syllabus_href=syllabus_href,
            )
        )

    total_category_credits = sum(credits_by_category.values()) or total_credits
    credit_categories: list[CurriculumSemesterCreditCategoryRead] = []
    for key, cr in sorted(credits_by_category.items(), key=lambda item: -item[1]):
        label = _REGISTRATION_TYPE_LABELS.get(key, key.replace("_", " ").title())
        share = round((cr / total_category_credits) * 100, 1) if total_category_credits else None
        credit_categories.append(
            CurriculumSemesterCreditCategoryRead(
                category_key=key,
                category_label=label,
                credits=round(cr, 1) if cr % 1 else int(cr),
                share_pct=share,
            )
        )

    headline = programme_name
    if regulation:
        headline = f"{programme_name} · Regulation {regulation}"

    status_code, status_label, status_tone = _semester_status(semester, current_semester)
    credits_display = int(total_credits) if total_credits == int(total_credits) else round(total_credits, 1)

    return CurriculumSemesterPageRead(
        programme_headline=headline,
        programme_code=programme_code,
        selected_semester=semester,
        total_semesters=total_semesters,
        semester_tabs=[
            CurriculumSemesterTabRead(semester_number=n, tab_label=f"Sem {n}")
            for n in range(1, total_semesters + 1)
        ],
        courses_panel_title=f"Semester {semester} courses",
        courses_panel_meta=f"{credits_display} credits · {len(table_rows)} courses",
        courses=table_rows,
        credit_categories=credit_categories,
        semester_status_code=status_code,
        semester_status_label=status_label,
        semester_status_tone=status_tone,
        courses_footer_label=f"{len(table_rows)} courses · {credits_display} credits",
    )


def _category_short_label(entry: CourseCatalogReference, course: CourseRecord) -> str:
    if entry.registration_type in (CourseRegistrationType.ELECTIVE, CourseRegistrationType.OPEN):
        return "Elective"
    if course.practical_hours > 0 and course.lecture_hours == 0:
        return "Lab"
    return "Theory"


def _is_practical_category(entry: CourseCatalogReference, course: CourseRecord) -> bool:
    if entry.registration_type in (CourseRegistrationType.ELECTIVE, CourseRegistrationType.OPEN):
        return False
    if _category_short_label(entry, course) == "Lab":
        return True
    kind = (course.course_type or "").lower()
    if kind in ("lab", "practical"):
        return True
    return course.practical_hours > 0 and course.lecture_hours == 0


def _offered_in_label(semester_number: int | None, semester_label: str | None) -> str:
    if semester_number is not None:
        return f"Sem {semester_number}"
    parsed = _parse_semester_number(semester_label or "")
    if parsed is not None:
        return f"Sem {parsed}"
    return semester_label or "—"


def _category_course_row(entry: CourseCatalogReference, course: CourseRecord) -> CurriculumCategoryCourseRowRead:
    credits = _catalog_credits(entry, course)
    display = int(credits) if credits % 1 == 0 else round(credits, 1)
    return CurriculumCategoryCourseRowRead(
        course_code=course.course_code,
        course_name=course.name,
        credits=display,
    )


def _category_detail_label(entry: CourseCatalogReference, course: CourseRecord) -> str:
    base = _REGISTRATION_TYPE_LABELS.get(entry.registration_type.value, _course_type_label(course.course_type))
    short = _category_short_label(entry, course)
    return f"{base} · {short}" if short not in base else base


def _completion_status(
    course_code: str,
    semester_number: int | None,
    current_semester: int | None,
    enrolled_codes: set[str],
) -> tuple[str, str, str]:
    if course_code.upper() in enrolled_codes:
        return "in_progress", "In progress", "info"
    if semester_number is not None and current_semester is not None:
        if semester_number < current_semester:
            return "completed", "Completed", "success"
    return "upcoming", "Upcoming", "muted"


def _build_subject_credit_details(
    course: CourseRecord,
    catalog: CourseCatalogReference,
) -> CurriculumSubjectCreditDetailsRead:
    total_credit = float(_catalog_credits(catalog, course))
    lec_h = float(course.lecture_hours)
    tut_h = float(course.tutorial_hours)
    prac_h = float(course.practical_hours)
    contact = lec_h + tut_h + prac_h

    cia = (course.internal_assessment_label or "").strip()
    ese = (course.end_semester_exam_label or "").strip()
    if cia and ese:
        theory_assessed = f"{cia} + {ese}"
    elif course.exam_type_label:
        theory_assessed = course.exam_type_label
    elif cia or ese:
        theory_assessed = cia or ese
    else:
        theory_assessed = "CIA + End semester"
    lab_assessed = "Lab assessment" if prac_h > 0 else "—"

    rows: list[CurriculumCreditComponentRowRead] = []
    if contact > 0:
        theory_hours = lec_h + tut_h
        theory_cr = round(total_credit * theory_hours / contact, 2) if theory_hours else 0.0
        pr_cr = round(total_credit - theory_cr, 2) if prac_h > 0 else 0.0
        if theory_hours > 0:
            if theory_cr == int(theory_cr):
                theory_cr = int(theory_cr)
            rows.append(
                CurriculumCreditComponentRowRead(
                    component_label="Lecture" if tut_h == 0 else "Lecture / Tutorial",
                    hours_per_week=theory_hours,
                    credits=theory_cr,
                    assessed_by=theory_assessed,
                )
            )
        if prac_h > 0:
            if pr_cr == int(pr_cr):
                pr_cr = int(pr_cr)
            rows.append(
                CurriculumCreditComponentRowRead(
                    component_label="Practical",
                    hours_per_week=prac_h,
                    credits=pr_cr,
                    assessed_by=lab_assessed,
                )
            )
    elif total_credit > 0:
        rows.append(
            CurriculumCreditComponentRowRead(
                component_label="Course",
                hours_per_week=0,
                credits=total_credit if total_credit == int(total_credit) else round(total_credit, 1),
                assessed_by=theory_assessed,
            )
        )

    total_hours = contact
    total_cr = total_credit if total_credit == int(total_credit) else round(total_credit, 1)
    rows.append(
        CurriculumCreditComponentRowRead(
            component_label="Total",
            hours_per_week=total_hours,
            credits=total_cr,
            assessed_by="—",
            is_total=True,
        )
    )

    return CurriculumSubjectCreditDetailsRead(
        rows=rows,
        footer_label=course.name,
    )


async def _programme_catalog_course(
    tenant_id: PydanticObjectId,
    programme_code: str,
    course_code: str,
) -> tuple[CourseRecord, CourseCatalogReference]:
    course = await _course_repo.get_by_code(tenant_id, course_code)
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)
    catalog = await CourseCatalogReference.find_one(
        {
            "tenant_id": tenant_id,
            "programme_code": programme_code,
            "course_id": course.course_id,
        }
    )
    if catalog is None:
        catalog = await CourseCatalogReference.find_one(
            {
                "tenant_id": tenant_id,
                "programme_code": programme_code,
                "course_code": course_code,
            }
        )
    if catalog is None:
        raise AppError(code="NOT_FOUND", message="Subject is not in your programme curriculum", status_code=404)
    return course, catalog


async def get_curriculum_subject_list(
    scope: AccessScope,
    user: User,
    *,
    semester: int | None = None,
    category: str = "all",
    status: str = "all",
    search_query: str | None = None,
) -> CurriculumSubjectListRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    programme_code = profile.programme_code
    if not programme_code:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)

    programme_doc = await _load_academic_programme(tenant_id, programme_code)
    total_semesters = programme_doc.duration_semesters if programme_doc else 8
    current_semester = await _current_semester_number(tenant_id)

    enrolled = await list_enrolled_courses(scope, user)
    enrolled_codes = {c.course_code.upper() for c in enrolled}

    catalog_maps = await _load_programme_catalog_maps(tenant_id, programme_code)
    unique_catalog = catalog_maps.unique_catalog
    course_by_id = catalog_maps.course_by_id
    course_by_code = catalog_maps.course_by_code

    all_rows: list[CurriculumSubjectListRowRead] = []
    for entry in unique_catalog.values():
        course = course_by_id.get(entry.course_id) or course_by_code.get(entry.course_code.upper())
        if course is None:
            continue
        sem_num = _resolve_semester_number(entry, course)
        status_code, status_label, status_tone = _completion_status(
            course.course_code, sem_num, current_semester, enrolled_codes
        )
        credits = _catalog_credits(entry, course)
        all_rows.append(
            CurriculumSubjectListRowRead(
                course_id=course.course_id,
                course_code=course.course_code,
                course_name=course.name,
                category_label=_category_short_label(entry, course),
                ltp_label=_ltp_label(course),
                credits=round(credits, 1) if credits % 1 else int(credits),
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                semester_number=sem_num,
            )
        )

    all_rows.sort(key=lambda r: (r.semester_number or 0, r.course_code))

    filtered = all_rows
    if semester is not None:
        filtered = [r for r in filtered if r.semester_number == semester]
    cat = (category or "all").lower()
    if cat not in ("", "all"):
        if cat == "core":
            filtered = [
                r
                for r in filtered
                if unique_catalog.get(r.course_id)
                and unique_catalog[r.course_id].registration_type == CourseRegistrationType.CORE
            ]
        elif cat in ("elective", "open"):
            filtered = [
                r
                for r in filtered
                if unique_catalog.get(r.course_id)
                and unique_catalog[r.course_id].registration_type.value == cat
            ]
        else:
            filtered = [r for r in filtered if r.category_label.lower() == cat.lower()]
    st = (status or "all").lower()
    if st not in ("", "all"):
        filtered = [r for r in filtered if r.status_code == st]
    q = (search_query or "").strip().lower()
    if q:
        filtered = [
            r
            for r in filtered
            if q in r.course_code.lower() or q in r.course_name.lower()
        ]

    semester_options = [CurriculumSubjectFilterOptionRead(value="all", label="All semesters")]
    for n in range(1, total_semesters + 1):
        semester_options.append(CurriculumSubjectFilterOptionRead(value=str(n), label=f"Semester {n}"))

    category_options = [
        CurriculumSubjectFilterOptionRead(value="all", label="All categories"),
        CurriculumSubjectFilterOptionRead(value="core", label="Core"),
        CurriculumSubjectFilterOptionRead(value="theory", label="Theory"),
        CurriculumSubjectFilterOptionRead(value="elective", label="Elective"),
    ]
    status_options = [
        CurriculumSubjectFilterOptionRead(value="all", label="All statuses"),
        CurriculumSubjectFilterOptionRead(value="in_progress", label="In progress"),
        CurriculumSubjectFilterOptionRead(value="completed", label="Completed"),
        CurriculumSubjectFilterOptionRead(value="upcoming", label="Upcoming"),
    ]

    return CurriculumSubjectListRead(
        filter_semester=semester,
        filter_category=cat,
        filter_status=st,
        search_query=search_query,
        semester_options=semester_options,
        category_options=category_options,
        status_options=status_options,
        subjects=filtered,
        footer_label=f"{len(filtered)} of {len(all_rows)}",
        total_matching=len(filtered),
    )


async def get_curriculum_subject_detail(
    scope: AccessScope,
    user: User,
    course_code: str,
) -> CurriculumSubjectDetailRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    programme_code = profile.programme_code
    if not programme_code:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)

    year, semester_label = await _term(tenant_id)
    regulation = await _regulation_label_for_programme(tenant_id, programme_code)
    course, catalog = await _programme_catalog_course(tenant_id, programme_code, course_code)
    credits = _catalog_credits(catalog, course)

    faculty_names: list[str] = []
    try:
        info = await get_course_information(scope, user, course_code)
        faculty_names = [f.display_name for f in info.faculty if f.display_name]
    except AppError:
        assignments = await FacultyAssignment.find(
            {
                "tenant_id": tenant_id,
                "course_code": course_code,
                "academic_year_label": year,
                "semester_label": semester_label,
                "status": AssignmentStatus.ACTIVE,
            }
        ).to_list()
        if assignments:
            user_ids = {a.user_id for a in assignments}
            users = await User.find({"_id": {"$in": list(user_ids)}}).to_list()
            faculty_names = [u.full_name for u in users if u.full_name]

    objectives: list[str] = []
    outcomes_doc = await CourseLearningOutcome.find_one(
        {
            "tenant_id": tenant_id,
            "course_id": course.course_id,
            "academic_year_label": year,
            "semester_label": semester_label,
        }
    )
    if outcomes_doc is not None:
        objectives = list(outcomes_doc.outcomes)
    if not objectives:
        syllabus = await _academic.syllabus(tenant_id, course.course_id, year=year, semester=semester_label)
        if syllabus is not None and syllabus.approved:
            objectives = list(syllabus.objectives)

    assessments: list[CurriculumSubjectAssessmentRead] = []
    if course.internal_assessment_label:
        assessments.append(
            CurriculumSubjectAssessmentRead(
                label="Continuous internal",
                marks_label=course.internal_assessment_label,
                kind="internal",
            )
        )
    if course.end_semester_exam_label:
        assessments.append(
            CurriculumSubjectAssessmentRead(
                label="End semester",
                marks_label=course.end_semester_exam_label,
                kind="external",
            )
        )

    resources: list[CurriculumSubjectResourceRead] = []
    syllabus = await _academic.syllabus(tenant_id, course.course_id, year=year, semester=semester_label)
    if syllabus is not None and syllabus.approved:
        for material in syllabus.teaching_materials:
            kind = (material.material_type or "document").lower()
            if "lms" in material.title.lower() or material.url:
                kind = "lms" if "lms" in material.title.lower() else kind
            resources.append(
                CurriculumSubjectResourceRead(
                    title=material.title,
                    subtitle=material.material_type.replace("_", " ").title() if material.material_type else None,
                    kind=kind,
                )
            )

    faculty_label = ", ".join(faculty_names) if faculty_names else "—"
    if not regulation and course.regulation_label:
        regulation = course.regulation_label

    return CurriculumSubjectDetailRead(
        headline=f"{course.course_code} – {course.name}",
        course_code=course.course_code,
        course_name=course.name,
        code=course.course_code,
        category_label=_category_detail_label(catalog, course),
        credits=round(credits, 1) if credits % 1 else int(credits),
        ltp_label=_ltp_label(course),
        faculty_label=faculty_label,
        regulation_label=regulation,
        objectives=objectives,
        assessments=assessments,
        resources=resources,
        syllabus_href=f"/student/curriculum/course-syllabus?course={course.course_code}",
        credit_details=_build_subject_credit_details(course, catalog),
    )


_CO_CODE_PATTERN = re.compile(r"\bCO\d+\b", re.IGNORECASE)


def _co_labels_from_outcomes(outcomes: list[str]) -> list[str]:
    labels: list[str] = []
    for idx, line in enumerate(outcomes):
        matches = _CO_CODE_PATTERN.findall(line)
        if matches:
            labels.extend(m.upper() for m in matches)
        else:
            labels.append(f"CO{idx + 1}")
    seen: set[str] = set()
    unique: list[str] = []
    for label in labels:
        key = label.upper()
        if key in seen:
            continue
        seen.add(key)
        unique.append(label if label.startswith("CO") else key)
    return unique


def _co_mapping_for_unit(unit_no: int, outcomes: list[str]) -> str | None:
    labels = _co_labels_from_outcomes(outcomes)
    if not labels:
        return None
    start = (unit_no - 1) * 2
    chunk = labels[start : start + 2]
    return ", ".join(chunk) if chunk else None


def _topic_rows(unit: SyllabusUnit) -> list[CurriculumSyllabusTopicRead]:
    topics = list(unit.topics or [])
    if not topics:
        return []
    total = float(unit.planned_hours or 0)
    if total <= 0:
        return [CurriculumSyllabusTopicRead(title=t, hours=0) for t in topics]
    per = round(total / len(topics), 1)
    return [CurriculumSyllabusTopicRead(title=t, hours=per) for t in topics]


def _unit_weightage_pct(unit: SyllabusUnit, units: list[SyllabusUnit]) -> float | None:
    hours = [float(u.planned_hours or 0) for u in units]
    total = sum(hours)
    if total <= 0:
        return None
    return round((float(unit.planned_hours or 0) / total) * 100, 1)


async def _accessed_material_ids(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    course_code: str,
) -> set[str]:
    logs = await StudentMaterialAccessLog.find(
        {"tenant_id": tenant_id, "user_id": user_id, "course_code": course_code}
    ).to_list()
    return {str(log.material_id) for log in logs}


def _progress_from_materials(
    unit_no: int,
    material_ids: list[str],
    accessed_ids: set[str],
    *,
    fallback: tuple[str, str, str],
) -> tuple[str, str, str]:
    if not material_ids:
        return fallback
    viewed = sum(1 for mid in material_ids if mid in accessed_ids)
    if viewed >= len(material_ids):
        return "covered", "Covered", "success"
    if viewed > 0:
        return "ongoing", "Ongoing", "info"
    return "upcoming", "Upcoming", "muted"


def _fallback_progress_for_unit(
    unit_no: int,
    *,
    course_status_code: str,
) -> tuple[str, str, str]:
    if course_status_code == "completed":
        return "covered", "Covered", "success"
    if course_status_code == "upcoming":
        return "upcoming", "Upcoming", "muted"
    if course_status_code == "in_progress" and unit_no == 1:
        return "ongoing", "Ongoing", "info"
    if course_status_code == "in_progress":
        return "upcoming", "Upcoming", "muted"
    return "upcoming", "Upcoming", "muted"


async def get_curriculum_syllabus_page(
    scope: AccessScope,
    user: User,
    course_code: str,
    *,
    unit_no: int | None = None,
) -> CurriculumSyllabusPageRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    programme_code = profile.programme_code
    if not programme_code:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)

    year, semester_label = await _term(tenant_id)
    course, catalog = await _programme_catalog_course(tenant_id, programme_code, course_code)

    syllabus = await _academic.syllabus(tenant_id, course.course_id, year=year, semester=semester_label)
    if syllabus is None or not syllabus.approved:
        raise AppError(code="NOT_FOUND", message="Approved syllabus not available", status_code=404)

    enrolled = await list_enrolled_courses(scope, user)
    enrolled_codes = {c.course_code.upper() for c in enrolled}
    current_semester = await _current_semester_number(tenant_id)
    sem_num = _resolve_semester_number(catalog, course)
    course_status_code, _, _ = _completion_status(
        course.course_code, sem_num, current_semester, enrolled_codes
    )

    published = await published_materials_for_student(
        tenant_id,
        user.id,
        year=year,
        semester=semester_label,
        course_code=course.course_code,
    )
    materials_by_unit: dict[int, list[str]] = defaultdict(list)
    for doc in published:
        if doc.unit_no is not None:
            materials_by_unit[doc.unit_no].append(str(doc.id))

    accessed_ids = await _accessed_material_ids(tenant_id, user.id, course.course_code)

    units_sorted = sorted(syllabus.units or [], key=lambda u: u.unit_no)
    unit_rows: list[CurriculumSyllabusUnitRowRead] = []
    for unit in units_sorted:
        fallback = _fallback_progress_for_unit(unit.unit_no, course_status_code=course_status_code)
        progress = _progress_from_materials(
            unit.unit_no,
            materials_by_unit.get(unit.unit_no, []),
            accessed_ids,
            fallback=fallback,
        )
        hours = float(unit.planned_hours or 0)
        display_hours = int(hours) if hours % 1 == 0 else round(hours, 1)
        unit_rows.append(
            CurriculumSyllabusUnitRowRead(
                unit_no=unit.unit_no,
                title=unit.title,
                planned_hours=display_hours,
                topic_count=len(unit.topics or []),
                progress_code=progress[0],
                progress_label=progress[1],
                progress_tone=progress[2],
            )
        )

    total_hours = sum(float(u.planned_hours or 0) for u in units_sorted)
    total_display = int(total_hours) if total_hours % 1 == 0 else round(total_hours, 1)
    units_footer = (
        f"{len(unit_rows)} units · {total_display} hours"
        if unit_rows
        else "No units published"
    )

    outcomes_doc = await CourseLearningOutcome.find_one(
        {
            "tenant_id": tenant_id,
            "course_id": course.course_id,
            "academic_year_label": year,
            "semester_label": semester_label,
        }
    )
    outcome_lines = list(outcomes_doc.outcomes) if outcomes_doc is not None else []

    faculty_label = "—"
    try:
        info = await get_course_information(scope, user, course_code)
        names = [f.display_name for f in info.faculty if f.display_name]
        if names:
            faculty_label = ", ".join(names)
    except AppError:
        pass

    selected = unit_no
    if selected is None and unit_rows:
        selected = unit_rows[0].unit_no
    if selected is not None and not any(r.unit_no == selected for r in unit_rows):
        selected = unit_rows[0].unit_no if unit_rows else None

    unit_detail: CurriculumSyllabusUnitDetailRead | None = None
    if selected is not None:
        unit = next((u for u in units_sorted if u.unit_no == selected), None)
        if unit is not None:
            resources: list[CurriculumSyllabusResourceRead] = []
            open_url: str | None = None
            for doc in published:
                if doc.unit_no != unit.unit_no:
                    continue
                resources.append(
                    CurriculumSyllabusResourceRead(
                        title=doc.title,
                        subtitle=faculty_label if faculty_label != "—" else doc.material_type,
                        url=doc.metadata.get("url") if doc.metadata else None,
                        kind=doc.material_type or "document",
                    )
                )
                if open_url is None and doc.metadata and doc.metadata.get("url"):
                    open_url = str(doc.metadata["url"])
            for material in syllabus.teaching_materials:
                title_lower = material.title.lower()
                if f"unit {unit.unit_no}" in title_lower or f"unit{unit.unit_no}" in title_lower:
                    resources.append(
                        CurriculumSyllabusResourceRead(
                            title=material.title,
                            subtitle=faculty_label if faculty_label != "—" else None,
                            url=material.url,
                            kind=material.material_type or "document",
                        )
                    )
                    if open_url is None and material.url:
                        open_url = material.url

            unit_detail = CurriculumSyllabusUnitDetailRead(
                unit_no=unit.unit_no,
                headline=f"Unit {unit.unit_no} · {unit.title}",
                planned_hours=float(unit.planned_hours or 0),
                weightage_pct=_unit_weightage_pct(unit, units_sorted),
                co_mapping_label=_co_mapping_for_unit(unit.unit_no, outcome_lines),
                topics=_topic_rows(unit),
                learning_resources=resources,
                open_materials_url=open_url,
                faculty_label=faculty_label,
            )

    headline = f"{course.course_code} · {course.name}"
    return CurriculumSyllabusPageRead(
        headline=headline,
        course_code=course.course_code,
        course_name=course.name,
        units=unit_rows,
        units_footer_label=units_footer,
        selected_unit_no=selected,
        unit_detail=unit_detail,
    )


async def get_curriculum_categories_electives_page(
    scope: AccessScope,
    user: User,
) -> CurriculumCategoriesElectivesPageRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    programme_code = profile.programme_code
    if not programme_code:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)

    year, _semester_label = await _term(tenant_id)
    current_semester = await _current_semester_number(tenant_id)
    focus_semester = current_semester if current_semester is not None else 1

    catalog_maps = await _load_programme_catalog_maps(tenant_id, programme_code)
    unique_catalog = catalog_maps.unique_catalog
    course_by_id = catalog_maps.course_by_id
    course_by_code = catalog_maps.course_by_code

    theory_programme: list[CurriculumCategoryCourseRowRead] = []
    practical_programme: list[CurriculumCategoryCourseRowRead] = []
    theory_current: list[CurriculumCategoryCourseRowRead] = []
    practical_current: list[CurriculumCategoryCourseRowRead] = []

    for entry in unique_catalog.values():
        course = course_by_id.get(entry.course_id) or course_by_code.get(entry.course_code.upper())
        if course is None:
            continue
        if entry.registration_type in (CourseRegistrationType.ELECTIVE, CourseRegistrationType.OPEN):
            continue
        sem_num = _resolve_semester_number(entry, course)
        row = _category_course_row(entry, course)
        if _is_practical_category(entry, course):
            practical_programme.append(row)
            if sem_num == focus_semester:
                practical_current.append(row)
        else:
            theory_programme.append(row)
            if sem_num == focus_semester:
                theory_current.append(row)

    theory_programme.sort(key=lambda r: r.course_code)
    practical_programme.sort(key=lambda r: r.course_code)
    theory_current.sort(key=lambda r: r.course_code)
    practical_current.sort(key=lambda r: r.course_code)

    groups = await ElectiveGroup.find(
        {
            "tenant_id": tenant_id,
            "programme_code": programme_code,
            "academic_year_label": year,
            "is_active": True,
        }
    ).to_list()
    group_by_id = {g.id: g for g in groups}
    elective_rows: list[CurriculumElectiveCatalogueRowRead] = []
    if groups:
        options = await ElectiveOption.find(
            {
                "tenant_id": tenant_id,
                "elective_group_id": {"$in": list(group_by_id.keys())},
                "is_active": True,
            }
        ).to_list()
        seen_codes: set[str] = set()
        for opt in sorted(options, key=lambda o: (o.course_code, o.course_name)):
            group = group_by_id.get(opt.elective_group_id)
            if group is None:
                continue
            course = course_by_id.get(opt.course_id) or course_by_code.get(opt.course_code.upper())
            sem = course.semester_number if course else _parse_semester_number(group.semester_label)
            elective_rows.append(
                CurriculumElectiveCatalogueRowRead(
                    course_code=opt.course_code,
                    course_name=opt.course_name,
                    group_label=group.title,
                    credits=int(opt.credit_units) if opt.credit_units % 1 == 0 else round(opt.credit_units, 1),
                    offered_in_label=_offered_in_label(sem, group.semester_label),
                )
            )
            seen_codes.add(opt.course_code.upper())

    catalogue_elective_total = 0
    for entry in unique_catalog.values():
        if entry.registration_type not in (CourseRegistrationType.ELECTIVE, CourseRegistrationType.OPEN):
            continue
        catalogue_elective_total += 1
        if entry.course_code.upper() in {r.course_code.upper() for r in elective_rows}:
            continue
        course = course_by_id.get(entry.course_id) or course_by_code.get(entry.course_code.upper())
        if course is None:
            continue
        sem = _resolve_semester_number(entry, course)
        group_label = _REGISTRATION_TYPE_LABELS.get(
            entry.registration_type.value,
            entry.registration_type.value.replace("_", " ").title(),
        )
        credits = _catalog_credits(entry, course)
        elective_rows.append(
            CurriculumElectiveCatalogueRowRead(
                course_code=course.course_code,
                course_name=course.name,
                group_label=group_label,
                credits=int(credits) if credits % 1 == 0 else round(credits, 1),
                offered_in_label=_offered_in_label(sem, entry.semester_label),
            )
        )

    elective_rows.sort(key=lambda r: (r.offered_in_label, r.course_code))
    total_pool = max(catalogue_elective_total, len(elective_rows))
    elective_footer = (
        f"{len(elective_rows)} of {total_pool}" if elective_rows else "No electives published for your programme"
    )

    return CurriculumCategoriesElectivesPageRead(
        theory_panel=CurriculumCategoryPanelRead(
            panel_title="Theory",
            rows=theory_current,
            footer_label=f"{len(theory_current)} of {len(theory_programme)}",
        ),
        practical_panel=CurriculumCategoryPanelRead(
            panel_title="Practical",
            rows=practical_current,
            footer_label=f"{len(practical_current)} of {len(practical_programme)}",
        ),
        elective_rows=elective_rows,
        elective_footer_label=elective_footer,
        registration_href="/student/registration",
    )


def _batch_year(label: str | None) -> int | None:
    if not label:
        return None
    match = re.search(r"\d{4}", label)
    return int(match.group(0)) if match else None


def _applies_to_student(
    version: ProgrammeCurriculumVersionReference,
    *,
    batch_label: str | None,
) -> tuple[str, str, str]:
    if version.applies_to_existing_students:
        return "yes", "Yes", "success"
    threshold = _batch_year(version.applies_from_batch_label)
    student_year = _batch_year(batch_label)
    if threshold is None or student_year is None:
        return "unknown", "—", "muted"
    if student_year >= threshold:
        return "yes", "Yes", "success"
    return "no", "No", "muted"


def _format_effective_month_year(value: date) -> str:
    return value.strftime("%b %Y")


async def get_curriculum_history_page(
    scope: AccessScope,
    user: User,
) -> CurriculumHistoryPageRead:
    authorize(scope, Permission.STUDENT_CURRICULUM_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    programme_code = profile.programme_code
    if not programme_code:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)

    versions = await ProgrammeCurriculumVersionReference.find(
        Eq(ProgrammeCurriculumVersionReference.tenant_id, tenant_id),
        Eq(ProgrammeCurriculumVersionReference.programme_code, programme_code),
    ).sort("-effective_from").to_list()

    rows: list[CurriculumHistoryRowRead] = []
    for version in versions:
        applies_code, applies_label, applies_tone = _applies_to_student(
            version,
            batch_label=profile.batch_label,
        )
        rows.append(
            CurriculumHistoryRowRead(
                version_label=version.version_label,
                regulation_label=version.regulation_label,
                effective_from_label=_format_effective_month_year(version.effective_from),
                change_summary=version.change_summary,
                applies_code=applies_code,
                applies_label=applies_label,
                applies_tone=applies_tone,
            )
        )

    count = len(rows)
    footer = f"{count} version{'s' if count != 1 else ''}" if count else "No versions published"
    return CurriculumHistoryPageRead(rows=rows, footer_label=footer)
