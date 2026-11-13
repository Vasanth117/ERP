"""Student phase 4 — CIA marks and continuous assessment."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import AcademicYearContext, UpcomingAssessment
from app.modules.auth.models import User
from app.modules.examinations.enums import AssessmentComponentType, StudentMarkStatus
from app.modules.examinations.models import Assessment, AssessmentComponent, StudentAssessmentMark
from app.modules.lms.enums import LmsAssignmentStatus, SubmissionStatus
from app.modules.lms.models import AssignmentRule, CourseAssignment
from app.modules.students.cia_service import get_published_cia_marks, get_cia_schedules
from app.modules.students.continuous_assessment_service import list_assignments, submission_status
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


async def _seed(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name="College", code=f"s4_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    user = User(
        email=f"s4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.STUDENT,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    return tenant, user, scope


async def _seed_data(tenant: Tenant, user: User) -> None:
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id="c101",
        course_code="CSE101",
        section_code="A",
        student_user_id=user.id,
        roll_number="R100",
        display_name="Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await UpcomingAssessment(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        course_code="CSE101",
        title="CIA 1",
        assessment_type="cia",
        scheduled_at=datetime.now(timezone.utc),
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await Assessment(
        tenant_id=tenant.id,
        assessment_id="asm1",
        course_id="c101",
        course_code="CSE101",
        title="CIA Bundle",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await AssessmentComponent(
        tenant_id=tenant.id,
        assessment_id="asm1",
        component_id="c1",
        code="CIA1",
        name="Internal 1",
        component_type=AssessmentComponentType.INTERNAL,
        max_marks=25,
        weight_percent=50,
    ).insert()
    await StudentAssessmentMark(
        tenant_id=tenant.id,
        batch_id=tenant.id,
        assessment_id="asm1",
        component_id="c1",
        student_user_id=user.id,
        marks_obtained=20,
        max_marks=25,
        status=StudentMarkStatus.DRAFT,
    ).insert()
    await StudentAssessmentMark(
        tenant_id=tenant.id,
        batch_id=tenant.id,
        assessment_id="asm1",
        component_id="c1pub",
        student_user_id=user.id,
        marks_obtained=22,
        max_marks=25,
        status=StudentMarkStatus.APPROVED,
    ).insert()
    rule = AssignmentRule(tenant_id=tenant.id)
    await rule.insert()
    await CourseAssignment(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        course_id="c101",
        course_code="CSE101",
        section="A",
        title="Assignment 1",
        instructions="Submit PDF",
        max_marks=10,
        deadline_at=datetime.now(timezone.utc),
        rule_id=rule.id,
        status=LmsAssignmentStatus.PUBLISHED,
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()


@pytest.mark.anyio
async def test_cia_schedules_and_published_only(db_ready) -> None:
    tenant, user, scope = await _seed(uuid4().hex[:8])
    await _seed_data(tenant, user)
    schedules = await get_cia_schedules(scope, user)
    assert len(schedules) >= 1
    marks = await get_published_cia_marks(scope, user)
    assert len(marks) == 1
    assert marks[0].marks_obtained == 22


@pytest.mark.anyio
async def test_assignments_and_submission_missing(db_ready) -> None:
    tenant, user, scope = await _seed(uuid4().hex[:8])
    await _seed_data(tenant, user)
    rows = await list_assignments(scope, user)
    assert len(rows) == 1
    assignment_id = rows[0].id
    status = await submission_status(scope, user, assignment_id)
    assert status.status == SubmissionStatus.MISSING
    assert status.missing is True


@pytest.mark.anyio
async def test_unpublished_marks_not_in_published_list(db_ready) -> None:
    """Draft marks exist in DB but must not appear in published endpoint."""
    tenant, user, scope = await _seed(uuid4().hex[:8])
    await _seed_data(tenant, user)
    published = await get_published_cia_marks(scope, user)
    assert all(m.component_id != "c1" for m in published)
