"""Department & designation assignment (CA 07.07)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.department_designation_assignment_page_service import (
    get_department_designation_assignment_page,
)
from app.modules.college_admin.faculty_admin_models import FacultyRecord
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
async def test_department_designation_assignment_picker(db_ready):
    suffix = uuid4().hex[:8]
    tenant, scope = await _scope(suffix)
    page = await get_department_designation_assignment_page(scope, None)
    assert page.page_title == "Department & Designation Assignment"
    assert page.requires_record is True

    dept = InstitutionDepartment(
        tenant_id=tenant.id,
        department_code="CSE",
        name="Computer Science & Engg.",
        kind=DepartmentKind.ACADEMIC,
        status=DepartmentStatus.ACTIVE,
    )
    await dept.insert()
    faculty_user = User(
        email=f"faculty+{suffix}@northbridge.edu",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. Nisha Varma",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=dept.id,
        is_active=True,
    )
    await faculty_user.insert()
    record = FacultyRecord(
        tenant_id=tenant.id,
        user_id=faculty_user.id,
        department_id=dept.id,
        designation="Assistant Professor",
        faculty_code="EMP-3012",
    )
    await record.insert()

    loaded = await get_department_designation_assignment_page(scope, str(record.id))
    assert loaded.requires_record is False
    assert loaded.employee_display
    assert "Dr. Nisha Varma" in loaded.employee_display