"""Department Admin phase 2 — faculty and academic."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.auth.models import User
from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate
from app.modules.college_admin.organization_service import create_institution_department
from app.modules.department_admin.faculty_management_service import (
    create_teaching_assignment,
    list_faculty_directory,
    list_unassigned_subjects,
)
from app.modules.department_admin.phase2_schemas import FacultyDirectoryFilters, TeachingAssignmentCreate
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment, FacultyProfile
from app.modules.tenants.models import Department, Tenant
from app.common.schemas import Pagination


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


async def _seed(suffix: str) -> tuple[Tenant, Department, User, AccessScope, User]:
    tenant = Tenant(name=f"C {suffix}", code=f"p2_{suffix}", institution_email=f"i+{suffix}@ex.com")
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
        full_name="Faculty One",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=dept.id,
        is_active=True,
    )
    await faculty_user.insert()
    await FacultyProfile(tenant_id=tenant.id, user_id=faculty_user.id, department_id=dept.id, designation="Professor").insert()
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
    await CourseRecord(
        tenant_id=tenant.id,
        course_id="CRS1",
        course_code="CS101",
        name="Programming",
        department_id=dept.id,
    ).insert()
    return tenant, dept, dept_admin, scope, faculty_user


@pytest.mark.anyio
async def test_faculty_directory_and_assignment(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, dept_admin, scope, faculty_user = await _seed(suffix)
    page = await list_faculty_directory(
        scope,
        dept_admin,
        pagination=Pagination(limit=20, offset=0),
        filters=FacultyDirectoryFilters(),
    )
    assert page.total >= 1
    assignment = await create_teaching_assignment(
        scope,
        dept_admin,
        TeachingAssignmentCreate(
            faculty_user_id=str(faculty_user.id),
            academic_year_label="2025-26",
            semester_label="Odd",
            course_code="CS101",
            course_name="Programming",
            section="A",
        ),
    )
    assert assignment.course_code == "CS101"
    with pytest.raises(AppError) as dup:
        await create_teaching_assignment(
            scope,
            dept_admin,
            TeachingAssignmentCreate(
                faculty_user_id=str(faculty_user.id),
                academic_year_label="2025-26",
                semester_label="Odd",
                course_code="CS101",
                course_name="Programming",
                section="A",
            ),
        )
    assert dup.value.status_code == 409
    unassigned = await list_unassigned_subjects(scope, dept_admin, academic_year_label="2025-26", semester_label="Odd")
    assert all(u.course_code != "CS101" for u in unassigned) or not unassigned


@pytest.mark.anyio
async def test_inactive_faculty_assignment_rejected(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, dept, dept_admin, scope, faculty_user = await _seed(suffix)
    faculty_user.is_active = False
    await faculty_user.save()
    with pytest.raises(AppError) as exc:
        await create_teaching_assignment(
            scope,
            dept_admin,
            TeachingAssignmentCreate(
                faculty_user_id=str(faculty_user.id),
                academic_year_label="2025-26",
                semester_label="Odd",
                course_code="CS101",
                course_name="Programming",
                section="B",
            ),
        )
    assert exc.value.status_code == 422
    await FacultyAssignment.find({"tenant_id": tenant.id, "user_id": faculty_user.id, "status": AssignmentStatus.ACTIVE}).delete()