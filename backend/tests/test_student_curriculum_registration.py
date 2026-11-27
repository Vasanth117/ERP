"""Student phase 2 — curriculum and course registration."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import (
    CourseLearningOutcome,
    CourseRecord,
    CurriculumRecord,
    EnrollmentRosterEntry,
    SyllabusRecord,
    SyllabusUnit,
)
from app.modules.academics.models import AcademicYearContext, TimetableEntry
from app.modules.auth.models import User
from datetime import date

from app.modules.students.curriculum_models import (
    CourseCatalogReference,
    CoursePrerequisite,
    CurriculumReference,
    ProgrammeCurriculumVersionReference,
    ElectiveGroup,
    ElectiveOption,
    RegistrationPolicyReference,
)
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.students.curriculum_service import (
    get_curriculum_overview,
    get_curriculum_semester_page,
    get_curriculum_subject_detail,
    get_curriculum_subject_list,
    get_curriculum_categories_electives_page,
    get_curriculum_history_page,
    get_curriculum_syllabus_page,
    get_syllabus,
    list_enrolled_courses,
)
from app.modules.students.models import StudentProfile
from app.modules.students.curriculum_schemas import RegistrationSelectionInput
from app.modules.students.registration_enums import CourseRegistrationType
from app.modules.students.registration_service import (
    concurrent_registration_guard,
    get_registration_courses_page,
    get_registration_electives_page,
    get_registration_review_page,
    get_registration_status_page,
    get_registration_overview_page,
    list_confirmed_registrations,
    submit_registration,
    validate_course_selection,
)
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    try:
        await connect_redis()
    except Exception:
        pass
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed_student(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College {suffix}", code=f"s2_{suffix}")
    await tenant.insert()
    department = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await department.insert()
    user = User(
        email=f"stu2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Sam Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=department.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.STUDENT,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=department.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    return tenant, user, scope


async def _seed_curriculum_stack(tenant: Tenant, user: User) -> None:
    now = datetime.now(timezone.utc)
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await CourseRecord(
        tenant_id=tenant.id,
        course_id="cse101",
        course_code="CSE101",
        name="Programming",
        credit_units=4,
    ).insert()
    await CourseRecord(
        tenant_id=tenant.id,
        course_id="cse201",
        course_code="CSE201",
        name="Data Structures",
        credit_units=4,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id="cse101",
        course_code="CSE101",
        section_code="A",
        student_user_id=user.id,
        roll_number="21CSE010",
        display_name="Sam Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    profile = await StudentProfile.find_one({"user_id": user.id})
    if profile is None:
        profile = StudentProfile(tenant_id=tenant.id, user_id=user.id)
        await profile.insert()
    profile.programme_code = "BTECH-CSE"
    profile.programme_name = "B.Tech CSE"
    await profile.save()
    await SyllabusRecord(
        tenant_id=tenant.id,
        course_id="cse101",
        academic_year_label="2025-26",
        semester_label="Odd",
        units=[SyllabusUnit(unit_no=1, title="Intro", topics=["Basics"])],
        objectives=["Understand basics"],
        approved=True,
        locked=True,
    ).insert()
    await CurriculumRecord(
        tenant_id=tenant.id,
        course_id="cse101",
        academic_year_label="2025-26",
        semester_label="Odd",
        version="v1",
        approved=True,
        summary="B.Tech Odd term",
    ).insert()
    await CurriculumReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="Odd",
        primary_course_id="cse101",
        academic_regulations=["Minimum 75% attendance"],
    ).insert()
    await CourseLearningOutcome(
        tenant_id=tenant.id,
        course_id="cse101",
        academic_year_label="2025-26",
        semester_label="Odd",
        outcomes=["Write basic programs"],
    ).insert()
    await CourseCatalogReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="Odd",
        course_id="cse201",
        course_code="CSE201",
        registration_type=CourseRegistrationType.ELECTIVE,
        is_open_for_registration=True,
        credit_units=4,
    ).insert()
    await CoursePrerequisite(
        tenant_id=tenant.id,
        course_id="cse201",
        course_code="CSE201",
        prerequisite_course_ids=["cse101"],
    ).insert()
    await RegistrationPolicyReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="Odd",
        min_credits=4,
        max_credits=24,
        registration_open_at=now - timedelta(days=1),
        registration_close_at=now + timedelta(days=7),
        modification_deadline=now + timedelta(days=6),
    ).insert()
    group = ElectiveGroup(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="Odd",
        group_code="OE1",
        title="Open Elective I",
        min_selections=1,
        max_selections=1,
    )
    await group.insert()
    await ElectiveOption(
        tenant_id=tenant.id,
        elective_group_id=group.id,
        course_id="cse201",
        course_code="CSE201",
        course_name="Data Structures",
        credit_units=4,
    ).insert()
    await _mark_cse101_approved(tenant, user)


async def _mark_cse101_approved(tenant: Tenant, user: User) -> None:
    from app.modules.students.curriculum_models import StudentCourseRegistration
    from app.modules.students.registration_enums import CourseRegistrationStatus

    await StudentCourseRegistration(
        tenant_id=tenant.id,
        user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        programme_code="BTECH-CSE",
        course_id="cse101",
        course_code="CSE101",
        registration_type=CourseRegistrationType.CORE,
        credit_units=4,
        status=CourseRegistrationStatus.APPROVED,
    ).insert()


@pytest.mark.anyio
async def test_curriculum_overview(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    await AcademicProgramme(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        name="B.Tech CSE",
        duration_semesters=8,
        credits_required=160,
        is_active=True,
    ).insert()
    course = await CourseRecord.find_one({"tenant_id": tenant.id, "course_code": "CSE101"})
    assert course is not None
    course.semester_number = 1
    course.practical_hours = 2
    await course.save()
    await CourseCatalogReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="1",
        course_id="cse101",
        course_code="CSE101",
        registration_type=CourseRegistrationType.CORE,
        credit_units=4,
    ).insert()
    overview = await get_curriculum_overview(scope, user)
    assert overview.programme_code == "BTECH-CSE"
    assert overview.kpis.total_semesters == 8
    assert overview.kpis.core_subjects >= 1
    assert len(overview.semesters) == 8
    first = overview.semesters[0]
    assert first.semester_number == 1
    assert first.subject_count >= 1


@pytest.mark.anyio
async def test_curriculum_semester_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    await AcademicProgramme(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        name="B.Tech CSE",
        duration_semesters=8,
        credits_required=160,
        is_active=True,
    ).insert()
    course = await CourseRecord.find_one({"tenant_id": tenant.id, "course_code": "CSE101"})
    assert course is not None
    course.semester_number = 1
    await course.save()
    await CourseCatalogReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="1",
        course_id="cse101",
        course_code="CSE101",
        registration_type=CourseRegistrationType.CORE,
        credit_units=4,
    ).insert()
    page = await get_curriculum_semester_page(scope, user, semester=1)
    assert page.selected_semester == 1
    assert len(page.semester_tabs) == 8
    assert any(row.course_code == "CSE101" for row in page.courses)
    assert page.courses_panel_meta.endswith("1 courses") or "courses" in page.courses_panel_meta


@pytest.mark.anyio
async def test_curriculum_subject_list_and_detail(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    await CourseCatalogReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="1",
        course_id="cse101",
        course_code="CSE101",
        registration_type=CourseRegistrationType.CORE,
        credit_units=4,
    ).insert()
    course = await CourseRecord.find_one({"course_code": "CSE101"})
    assert course is not None
    course.semester_number = 1
    course.internal_assessment_label = "40 marks"
    course.end_semester_exam_label = "60 marks"
    await course.save()
    listing = await get_curriculum_subject_list(scope, user, semester=1)
    assert listing.total_matching >= 1
    detail = await get_curriculum_subject_detail(scope, user, "CSE101")
    assert detail.course_code == "CSE101"
    assert len(detail.assessments) == 2
    assert detail.credit_details.rows
    assert detail.credit_details.rows[-1].is_total


@pytest.mark.anyio
async def test_curriculum_history_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    profile = await StudentProfile.find_one({"user_id": user.id})
    assert profile is not None
    profile.programme_code = "BTECH-CSE"
    profile.batch_label = "2024"
    await profile.save()
    await ProgrammeCurriculumVersionReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        version_label="v2.0",
        regulation_label="R2022",
        effective_from=date(2022, 8, 1),
        change_summary="Initial curriculum",
        applies_to_existing_students=True,
    ).insert()
    page = await get_curriculum_history_page(scope, user)
    assert len(page.rows) == 1
    assert page.rows[0].applies_label == "Yes"


@pytest.mark.anyio
async def test_curriculum_categories_electives_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    await CourseCatalogReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="1",
        course_id="cse101",
        course_code="CSE101",
        registration_type=CourseRegistrationType.CORE,
        credit_units=4,
    ).insert()
    page = await get_curriculum_categories_electives_page(scope, user)
    assert page.theory_panel.panel_title == "Theory"
    assert page.practical_panel.panel_title == "Practical"


@pytest.mark.anyio
async def test_curriculum_syllabus_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    await CourseCatalogReference(
        tenant_id=tenant.id,
        programme_code="BTECH-CSE",
        academic_year_label="2025-26",
        semester_label="1",
        course_id="cse101",
        course_code="CSE101",
        registration_type=CourseRegistrationType.CORE,
        credit_units=4,
    ).insert()
    syllabus_doc = await SyllabusRecord.find_one({"course_id": "cse101"})
    assert syllabus_doc is not None
    syllabus_doc.units = [
        SyllabusUnit(unit_no=1, title="Intro", topics=["Basics", "Setup"], planned_hours=4),
        SyllabusUnit(unit_no=2, title="Advanced", topics=["Patterns"], planned_hours=2),
    ]
    await syllabus_doc.save()

    page = await get_curriculum_syllabus_page(scope, user, "CSE101")
    assert page.course_code == "CSE101"
    assert len(page.units) == 2
    assert page.unit_detail is not None
    assert page.unit_detail.unit_no == 1
    assert len(page.unit_detail.topics) == 2

    page_unit2 = await get_curriculum_syllabus_page(scope, user, "CSE101", unit_no=2)
    assert page_unit2.selected_unit_no == 2
    assert page_unit2.unit_detail is not None
    assert page_unit2.unit_detail.headline.endswith("Advanced")


@pytest.mark.anyio
async def test_enrolled_courses_and_syllabus(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    courses = await list_enrolled_courses(scope, user)
    assert len(courses) == 1
    assert courses[0].course_code == "CSE101"
    syllabus = await get_syllabus(scope, user, "CSE101")
    assert syllabus.units[0].title == "Intro"


@pytest.mark.anyio
async def test_syllabus_forbidden_without_access(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await CourseRecord(
        tenant_id=tenant.id,
        course_id="xyz",
        course_code="XYZ999",
        name="Secret",
        credit_units=1,
    ).insert()
    profile = await StudentProfile.find_one({"user_id": user.id})
    if profile is None:
        profile = StudentProfile(tenant_id=tenant.id, user_id=user.id)
        await profile.insert()
    profile.programme_code = "BTECH-CSE"
    await profile.save()
    await SyllabusRecord(
        tenant_id=tenant.id,
        course_id="xyz",
        academic_year_label="2025-26",
        semester_label="Odd",
        units=[],
        approved=True,
    ).insert()
    with pytest.raises(AppError) as exc:
        await get_syllabus(scope, user, "XYZ999")
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_prerequisite_and_credit_validation(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    ok = await validate_course_selection(
        scope,
        user,
        [
            RegistrationSelectionInput(
                course_id="cse201",
                course_code="CSE201",
                registration_type=CourseRegistrationType.ELECTIVE,
            )
        ],
    )
    assert ok.valid is True
    fail = await validate_course_selection(
        scope,
        user,
        [
            RegistrationSelectionInput(
                course_id="cse201",
                course_code="CSE201",
                section_code="A",
                registration_type=CourseRegistrationType.ELECTIVE,
            ),
            RegistrationSelectionInput(
                course_id="cse201",
                course_code="CSE201",
                section_code="B",
                registration_type=CourseRegistrationType.ELECTIVE,
            ),
        ],
    )
    assert fail.valid is False


@pytest.mark.anyio
async def test_list_confirmed_registrations_after_submit(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    selections = [
        RegistrationSelectionInput(
            course_id="cse201",
            course_code="CSE201",
            registration_type=CourseRegistrationType.ELECTIVE,
        )
    ]
    await submit_registration(scope, user, selections)
    rows = await list_confirmed_registrations(scope, user)
    assert any(r.course_code == "CSE201" for r in rows)
    assert rows[0].semester_label == "Odd"


@pytest.mark.anyio
async def test_submit_and_duplicate_prevention(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    selections = [
        RegistrationSelectionInput(
            course_id="cse201",
            course_code="CSE201",
            registration_type=CourseRegistrationType.ELECTIVE,
        )
    ]
    result = await submit_registration(scope, user, selections)
    assert result.status.value in {"submitted", "under_review"}
    with pytest.raises(AppError) as exc:
        await submit_registration(scope, user, selections)
    assert exc.value.code in {"CONFLICT", "VALIDATION_ERROR"}


@pytest.mark.anyio
async def test_registration_courses_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    page = await get_registration_courses_page(scope, user)
    assert page.page_title == "Available Courses"
    assert page.search_placeholder == "Search course or code"
    assert " of " in page.courses_footer_label


@pytest.mark.anyio
async def test_registration_electives_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    page = await get_registration_electives_page(scope, user)
    assert page.selection.page_title == "Elective Selection"
    assert page.catalogue.page_title == "Elective Catalogue"


@pytest.mark.anyio
async def test_registration_review_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    page = await get_registration_review_page(scope, user)
    assert page.summary.page_title == "Selected Courses Summary"
    assert page.validation.page_title == "Registration Validation"
    assert "checks" in page.validation.checks_footer_label


@pytest.mark.anyio
async def test_registration_status_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    page = await get_registration_status_page(scope, user)
    assert page.status.page_title == "Registration Status"
    assert page.history.page_title == "Registration History"
    assert page.history.page_subtitle == "Earlier semesters"


@pytest.mark.anyio
async def test_registration_overview_page(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    page = await get_registration_overview_page(scope, user)
    assert page.page_title == "Course Registration Dashboard"
    assert page.kpis.credit_limit_label == "4 – 24"
    assert len(page.steps) == 6
    assert " of " in page.courses_footer_label


@pytest.mark.anyio
async def test_concurrent_registration_attempts(db_ready) -> None:
    tenant, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_curriculum_stack(tenant, user)
    selections = [
        RegistrationSelectionInput(
            course_id="cse201",
            course_code="CSE201",
            registration_type=CourseRegistrationType.ELECTIVE,
        )
    ]
    outcomes = await asyncio.gather(
        concurrent_registration_guard(scope, user, selections),
        concurrent_registration_guard(scope, user, selections),
    )
    assert sum(1 for o in outcomes if o.valid) <= 1
