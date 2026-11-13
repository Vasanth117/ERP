"""Faculty phase 2 — course content and timetable."""

from datetime import date, datetime, time, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import (
    CourseRecord,
    CourseSubjectMapping,
    EnrollmentRosterEntry,
    SyllabusRecord,
    SyllabusUnit,
)
from app.modules.academics.enums import SessionType, TimetableEntryStatus
from app.modules.academics.models import ClassSession, TimetableEntry
from app.modules.auth.models import User
from app.modules.faculty.content_schemas import CourseCoverageUpdate
from app.modules.faculty.course_content_service import (
    get_enrolled_students,
    list_assigned_courses,
    update_course_coverage,
)
from app.modules.faculty.enums import AssignmentRole, AssignmentStatus
from app.modules.faculty.models import FacultyAssignment
from app.modules.faculty.timetable_service import get_daily_timetable, get_weekly_timetable
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


async def _seed_faculty_with_course(suffix: str) -> tuple[AccessScope, User, str]:
    tenant = Tenant(name=f"College {suffix}", code=f"c2_{suffix}")
    await tenant.insert()
    department = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await department.insert()
    user = User(
        email=f"faculty2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. Phase2",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=department.id,
    )
    await user.insert()
    course = CourseRecord(
        tenant_id=tenant.id,
        course_id=f"cid-{suffix}",
        course_code="CS201",
        name="Operating Systems",
        description="Core OS course",
        credit_units=4,
    )
    await course.insert()
    await FacultyAssignment(
        tenant_id=tenant.id,
        user_id=user.id,
        course_id=course.course_id,
        course_code="CS201",
        course_name="Operating Systems",
        section="A",
        academic_year_label="2025-26",
        semester_label="Odd",
        assignment_role=AssignmentRole.PRIMARY,
        status=AssignmentStatus.ACTIVE,
    ).insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=department.id,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    return scope, user, course.course_id


@pytest.mark.anyio
async def test_assigned_course_retrieval(db_ready) -> None:
    scope, user, _ = await _seed_faculty_with_course(uuid4().hex[:8])
    courses = await list_assigned_courses(scope, user)
    assert len(courses) == 1
    assert courses[0].course_code == "CS201"


@pytest.mark.anyio
async def test_unauthorized_course_access(db_ready) -> None:
    scope, user, _ = await _seed_faculty_with_course(uuid4().hex[:8])
    with pytest.raises(AppError) as exc:
        await get_enrolled_students(scope, user, "CS999", section="A")
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_syllabus_retrieval(db_ready) -> None:
    from app.modules.faculty.course_content_service import get_approved_syllabus

    scope, user, course_id = await _seed_faculty_with_course(uuid4().hex[:8])
    await SyllabusRecord(
        tenant_id=scope.tenant_id,
        course_id=course_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        units=[SyllabusUnit(unit_no=1, title="Intro", topics=["Overview"])],
        approved=True,
        locked=True,
    ).insert()
    syllabus = await get_approved_syllabus(scope, user, "CS201", section="A")
    assert syllabus.locked is True
    assert len(syllabus.units) == 1


@pytest.mark.anyio
async def test_coverage_update(db_ready) -> None:
    scope, user, _ = await _seed_faculty_with_course(uuid4().hex[:8])
    result = await update_course_coverage(
        scope,
        user,
        "CS201",
        section="A",
        payload=CourseCoverageUpdate(units_completed=[1], percent_complete=10, progress_note="Unit 1 done"),
    )
    assert 1 in result.units_completed
    assert result.percent_complete == 10


@pytest.mark.anyio
async def test_student_list_restricted_fields(db_ready) -> None:
    scope, user, course_id = await _seed_faculty_with_course(uuid4().hex[:8])
    await EnrollmentRosterEntry(
        tenant_id=scope.tenant_id,
        course_id=course_id,
        course_code="CS201",
        section_code="A",
        student_user_id=user.id,
        roll_number="21CS001",
        display_name="Student One",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    students = await get_enrolled_students(scope, user, "CS201", section="A")
    assert students[0].roll_number == "21CS001"
    assert students[0].display_name == "Student One"
    assert "email" not in students[0].model_fields


@pytest.mark.anyio
async def test_daily_weekly_timetable_and_conflicts(db_ready) -> None:
    scope, user, _ = await _seed_faculty_with_course(uuid4().hex[:8])
    day = date.today().weekday()
    await TimetableEntry(
        tenant_id=scope.tenant_id,
        faculty_user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        day_of_week=day,
        start_time=time(9, 0),
        end_time=time(10, 0),
        course_code="CS201",
        course_name="OS",
        section="A",
        session_type=SessionType.LECTURE,
        status=TimetableEntryStatus.ACTIVE,
    ).insert()
    await TimetableEntry(
        tenant_id=scope.tenant_id,
        faculty_user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        day_of_week=day,
        start_time=time(9, 30),
        end_time=time(10, 30),
        course_code="CS202",
        course_name="Networks",
        section="B",
        session_type=SessionType.LABORATORY,
        laboratory="Lab-1",
        status=TimetableEntryStatus.ACTIVE,
    ).insert()
    daily = await get_daily_timetable(scope, user)
    assert len(daily.slots) == 2
    assert len(daily.conflicts) >= 1
    weekly = await get_weekly_timetable(scope, user)
    assert len(weekly.days) == 7


@pytest.mark.anyio
async def test_cancelled_session_listing(db_ready) -> None:
    from app.modules.faculty.timetable_service import list_cancelled_rescheduled_sessions

    scope, user, _ = await _seed_faculty_with_course(uuid4().hex[:8])
    await ClassSession(
        tenant_id=scope.tenant_id,
        faculty_user_id=user.id,
        course_code="CS201",
        section="A",
        session_type=SessionType.LECTURE,
        scheduled_start=datetime.now(timezone.utc),
        scheduled_end=datetime.now(timezone.utc),
        status="cancelled",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    sessions = await list_cancelled_rescheduled_sessions(scope, user)
    assert len(sessions) == 1
    assert sessions[0].status == "cancelled"


@pytest.mark.anyio
async def test_cross_tenant_course_access(db_ready) -> None:
    scope_a, user_a, _ = await _seed_faculty_with_course(uuid4().hex[:8])
    suffix = uuid4().hex[:8]
    tenant_b = Tenant(name="B", code=f"tb_{suffix}")
    await tenant_b.insert()
    user_b = User(
        email=f"b+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other",
        role=Role.FACULTY,
        tenant_id=tenant_b.id,
    )
    await user_b.insert()
    with pytest.raises(AppError) as exc:
        await list_assigned_courses(scope_a, user_b)
    assert exc.value.code == "FORBIDDEN"


def test_coverage_schema_blocks_syllabus_fields() -> None:
    with pytest.raises(ValidationError):
        CourseCoverageUpdate.model_validate({"syllabus_units": [1, 2, 3]})
