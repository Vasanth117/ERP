"""Add new faculty / employee wizard."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.add_new_faculty_employee_page_service import (
    create_add_new_faculty_employee,
    get_add_new_faculty_employee_page,
    save_add_new_faculty_employee_draft,
)
from app.modules.college_admin.identity_models import DepartmentKind, DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.schemas import AddNewFacultyEmployeeCreatePayload, AddNewFacultyEmployeeDraftUpdate
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


async def _scope(suffix: str) -> tuple[Tenant, AccessScope]:
    tenant = Tenant(name=f"College NH {suffix}", code=f"nh_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+nh+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
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
    return tenant, scope


@pytest.mark.anyio
async def test_add_new_faculty_employee_page_loads(db_ready):
    suffix = uuid4().hex[:8]
    tenant, scope = await _scope(suffix)
    dept = InstitutionDepartment(
        tenant_id=tenant.id,
        department_code="CSE",
        name="Computer Science & Engg.",
        kind=DepartmentKind.ACADEMIC,
        status=DepartmentStatus.ACTIVE,
    )
    await dept.insert()

    page = await get_add_new_faculty_employee_page(scope)
    assert page.page_title == "Add New Faculty / Employee"
    assert len(page.steps) == 5
    assert page.current_step_key == "personal"
    assert page.employee_id_card.next_id_value.startswith("EMP-")


@pytest.mark.anyio
async def test_create_faculty_from_wizard(db_ready):
    suffix = uuid4().hex[:8]
    tenant, scope = await _scope(suffix)
    dept = InstitutionDepartment(
        tenant_id=tenant.id,
        department_code="CSE",
        name="Computer Science & Engg.",
        kind=DepartmentKind.ACADEMIC,
        status=DepartmentStatus.ACTIVE,
    )
    await dept.insert()

    page = await get_add_new_faculty_employee_page(scope)
    values = {
        "full_name": "Dr. New Faculty",
        "mobile": "+91 90000 10001",
        "employee_type": "faculty",
        "department_id": str(dept.id),
        "designation": "Assistant Professor",
        "joining_date": "2026-12-01",
        "employment_status": "probation",
        "official_email": f"new.faculty+{suffix}@northbridge.edu",
        "password": "password1234567890",
        "confirm_password": "password1234567890",
    }
    page = await save_add_new_faculty_employee_draft(
        scope,
        AddNewFacultyEmployeeDraftUpdate(draft_id=page.draft_id, step_key="account", values=values),
    )
    result = await create_add_new_faculty_employee(
        scope,
        AddNewFacultyEmployeeCreatePayload(draft_id=page.draft_id, values=values),
    )
    assert result.record_id
    assert result.employee_id
    assert "faculty-profile" in result.detail_href