"""Department Admin phase 5.1 — assessment and marks monitoring."""

from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import CourseRecord, EnrollmentRosterEntry
from app.modules.auth.models import User
from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate
from app.modules.college_admin.organization_service import create_institution_department
from app.modules.department_admin.assessment_monitoring_service import (
    list_assessments,
    marks_submission_overview,
    student_submission_statuses,
)
from app.modules.department_admin.phase5_schemas import AssessmentMonitoringFilters
from app.modules.examinations.enums import AssessmentComponentType, MarksBatchStatus, StudentMarkStatus
from app.modules.examinations.models import (
    Assessment,
    AssessmentComponent,
    FacultyAssessmentAssignment,
    MarksSubmissionBatch,
    StudentAssessmentMark,
)
from app.modules.faculty.models import FacultyProfile
from app.modules.students.models import StudentProfile
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
    from app.core.database import document_models

    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed(suffix: str) -> tuple[User, AccessScope, Department, User]:
    tenant = Tenant(name=f"C {suffix}", code=f"p5_{suffix}", institution_email=f"i+{suffix}@ex.com")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    admin = User(
        email=f"ca+{suffix}@ex.com",
        hashed_password=hash_password("password1234567890"),
        full_name="CA",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    admin_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    await create_institution_department(
        admin_scope,
        InstitutionDepartmentCreate(department_code="CSE", name="CSE", programme_codes=["BTECH-CSE"]),
    )
    faculty_user = User(
        email=f"fac+{suffix}@ex.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await faculty_user.insert()
    await FacultyProfile(tenant_id=tenant.id, user_id=faculty_user.id, department_id=dept.id).insert()
    dept_admin = User(
        email=f"da+{suffix}@ex.com",
        hashed_password=hash_password("password1234567890"),
        full_name="DA",
        role=Role.DEPARTMENT_ADMIN,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await dept_admin.insert()
    dept_scope = AccessScope(
        role=Role.DEPARTMENT_ADMIN,
        user_id=dept_admin.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.DEPARTMENT_ADMIN),
    )
    course = CourseRecord(
        tenant_id=tenant.id,
        course_id="CS101",
        course_code="CS101",
        name="Intro",
        department_id=dept.id,
        is_active=True,
    )
    await course.insert()
    assessment = Assessment(
        tenant_id=tenant.id,
        assessment_id="ASM1",
        course_id="CS101",
        course_code="CS101",
        title="CIA 1",
        academic_year_label="2025-26",
        semester_label="odd",
    )
    await assessment.insert()
    await AssessmentComponent(
        tenant_id=tenant.id,
        assessment_id="ASM1",
        component_id="C1",
        code="CIA1",
        name="CIA 1",
        component_type=AssessmentComponentType.INTERNAL,
        max_marks=25,
        faculty_may_enter=True,
    ).insert()
    await FacultyAssessmentAssignment(
        tenant_id=tenant.id,
        faculty_user_id=faculty_user.id,
        assessment_id="ASM1",
        course_id="CS101",
        course_code="CS101",
        section="A",
        academic_year_label="2025-26",
        semester_label="odd",
    ).insert()
    batch = MarksSubmissionBatch(
        tenant_id=tenant.id,
        faculty_user_id=faculty_user.id,
        assessment_id="ASM1",
        component_id="C1",
        course_code="CS101",
        section="A",
        status=MarksBatchStatus.DRAFT,
    )
    await batch.insert()
    student = User(
        email=f"stu+{suffix}@ex.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await student.insert()
    await StudentProfile(
        tenant_id=tenant.id,
        user_id=student.id,
        department_id=dept.id,
        programme_code="BTECH-CSE",
        section_code="A",
        batch_label="2025",
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id="CS101",
        course_code="CS101",
        section_code="A",
        student_user_id=student.id,
        roll_number="R1",
        display_name="Student",
        academic_year_label="2025-26",
        semester_label="odd",
    ).insert()
    await StudentAssessmentMark(
        tenant_id=tenant.id,
        batch_id=batch.id,
        assessment_id="ASM1",
        component_id="C1",
        student_user_id=student.id,
        marks_obtained=20,
        max_marks=25,
        status=StudentMarkStatus.DRAFT,
    ).insert()
    return dept_admin, dept_scope, dept, faculty_user


def test_department_admin_has_assessment_read_permission() -> None:
    perms = permissions_for_role(Role.DEPARTMENT_ADMIN)
    assert Permission.DEPARTMENT_ASSESSMENT_READ in perms
    assert Permission.DEPARTMENT_ASSESSMENT_MANAGE in perms
    assert Permission.DEPARTMENT_PERFORMANCE_READ in perms
    assert Permission.DEPARTMENT_ASSESSMENT_MARKS_DETAIL_READ not in perms


@pytest.mark.asyncio
async def test_department_assessment_list(db_ready) -> None:
    suffix = uuid4().hex[:8]
    user, scope, _, _ = await _seed(suffix)
    page = await list_assessments(scope, user, filters=AssessmentMonitoringFilters(), pagination=Pagination(page=1, page_size=20))
    assert page.total >= 1
    assert page.items[0].course_code == "CS101"
    assert page.items[0].marks_batch_summary.get("draft", 0) >= 1


@pytest.mark.asyncio
async def test_marks_submission_overview(db_ready) -> None:
    suffix = uuid4().hex[:8]
    user, scope, _, _ = await _seed(suffix)
    overview = await marks_submission_overview(scope, user, filters=AssessmentMonitoringFilters())
    assert overview.marks_detail_visible is False
    assert overview.totals.get("draft", 0) >= 1


@pytest.mark.asyncio
async def test_student_submission_hides_marks_by_default(db_ready) -> None:
    suffix = uuid4().hex[:8]
    user, scope, _, _ = await _seed(suffix)
    page = await student_submission_statuses(
        scope,
        user,
        assessment_id="ASM1",
        component_id="C1",
        section="A",
        course_code="CS101",
        pagination=Pagination(page=1, page_size=50),
    )
    assert page.total >= 1
    row = page.items[0]
    assert row.submission_status == "draft"
    assert row.marks_obtained is None
    assert row.max_marks is None


@pytest.mark.asyncio
async def test_faculty_role_denied(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, dept, faculty = await _seed(suffix)
    faculty_scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=faculty.tenant_id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    from app.core.exceptions import AppError

    with pytest.raises(AppError) as exc:
        await list_assessments(
            faculty_scope,
            faculty,
            filters=AssessmentMonitoringFilters(),
            pagination=Pagination(page=1, page_size=20),
        )
    assert exc.value.status_code == 403