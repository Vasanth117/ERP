"""Employee directory page (CA 07.04)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.employee_directory_page_service import get_employee_directory_page
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.identity_models import DepartmentKind, DepartmentStatus, InstitutionDepartment
from app.modules.tenants.models import Tenant


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


@pytest.mark.anyio
async def test_employee_directory_page_lists_staff(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College ED {suffix}", code=f"ed_{suffix}")
    await tenant.insert()
    user = User(
        email=f"arun+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Mr. Arun Prakash",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    dept = InstitutionDepartment(
        tenant_id=tenant.id,
        department_code="ACC",
        name="Accounts",
        department_kind=DepartmentKind.ADMINISTRATIVE,
        status=DepartmentStatus.ACTIVE,
    )
    await dept.insert()
    employee = EmployeeRecord(
        tenant_id=tenant.id,
        user_id=user.id,
        employee_id="EMP-4120",
        designation="Accounts Officer",
        department_id=dept.id,
        employment_type="permanent",
        employment_status=FacultyEmploymentStatus.ACTIVE,
        is_faculty=False,
    )
    await employee.insert()

    page = await get_employee_directory_page(scope, search="Arun")
    assert page.page_title == "Employee Directory"
    assert len(page.employee_rows) == 1
    assert page.employee_rows[0].employee_id_label == "EMP-4120"
    assert page.employee_rows[0].type_label == "Staff"