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
from app.modules.students.curriculum_models import (
    CourseCatalogReference,
    CoursePrerequisite,
    CurriculumReference,
    ElectiveGroup,
    ElectiveOption,
    RegistrationPolicyReference,
)
from app.modules.students.curriculum_service import get_syllabus, list_enrolled_courses
from app.modules.students.models import StudentProfile
from app.modules.students.curriculum_schemas import RegistrationSelectionInput
from app.modules.students.registration_enums import CourseRegistrationType
from app.modules.students.registration_service import (
    concurrent_registration_guard,
    submit_registration,
    validate_course_selection,
)
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
        await connect_redis()
    except Exception as exc:
        pytest.skip(f"Dependencies not available: {exc}")
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
    if profile:
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
    if profile:
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
    assert result.status.value in {"submitted", "pending_approval"}
    with pytest.raises(AppError) as exc:
        await submit_registration(scope, user, selections)
    assert exc.value.code == "CONFLICT"


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
