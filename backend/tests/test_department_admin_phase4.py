"""Department Admin phase 4 — timetable and attendance."""

from datetime import time
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.auth.models import User
from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate
from app.modules.college_admin.organization_service import create_institution_department
from app.modules.department_admin.attendance_oversight_service import attendance_overview
from app.modules.department_admin.phase4_schemas import AttendanceOverviewFilters, TimetablePlanCreate, TimetableSlotCreate
from app.modules.department_admin.timetable_management_service import (
    add_slot,
    create_timetable,
    validate_timetable,
)
from app.modules.faculty.models import FacultyProfile
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


async def _seed(suffix: str) -> tuple[User, AccessScope, User]:
    tenant = Tenant(name=f"C {suffix}", code=f"p4_{suffix}", institution_email=f"i+{suffix}@ex.com")
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
    await FacultyProfile(tenant_id=tenant.id, user_id=faculty_user.id, department_id=dept.id, designation="Professor").insert()
    await CourseRecord(
        tenant_id=tenant.id,
        course_id="CRS1",
        course_code="CS101",
        name="Programming",
        department_id=dept.id,
    ).insert()
    dept_admin = User(
        email=f"da+{suffix}@ex.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dept Admin",
        role=Role.DEPARTMENT_ADMIN,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await dept_admin.insert()
    scope = AccessScope(
        role=Role.DEPARTMENT_ADMIN,
        user_id=dept_admin.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.DEPARTMENT_ADMIN),
    )
    return dept_admin, scope, faculty_user


@pytest.mark.anyio
async def test_timetable_plan_and_validate(db_ready) -> None:
    suffix = uuid4().hex[:8]
    dept_admin, scope, faculty_user = await _seed(suffix)
    plan = await create_timetable(
        scope,
        dept_admin,
        TimetablePlanCreate(academic_year_label="2025-26", semester_label="ODD", title="CSE Timetable"),
    )
    await add_slot(
        scope,
        dept_admin,
        plan.timetable_id,
        TimetableSlotCreate(
            faculty_user_id=str(faculty_user.id),
            section="A",
            course_code="CS101",
            course_name="Programming",
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(10, 0),
        ),
    )
    result = await validate_timetable(scope, dept_admin, plan.timetable_id)
    assert result.valid is True


@pytest.mark.anyio
async def test_attendance_overview(db_ready) -> None:
    suffix = uuid4().hex[:8]
    dept_admin, scope, _ = await _seed(suffix)
    overview = await attendance_overview(scope, dept_admin, AttendanceOverviewFilters())
    assert overview.sessions_submitted >= 0