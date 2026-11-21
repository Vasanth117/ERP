"""Faculty directory page (CA 07.02)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.faculty_directory_page_service import get_faculty_directory_page
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


async def _seed(scope_suffix: str) -> tuple[Tenant, User, AccessScope, FacultyRecord]:
    tenant = Tenant(name=f"College FD {scope_suffix}", code=f"fd_{scope_suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+fd+{scope_suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Prof. Rekha Narayanan",
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
    year = AcademicYear(tenant_id=tenant.id, year_code="2026-27", label="2026-27", is_current=True)
    await year.insert()
    dept = InstitutionDepartment(
        tenant_id=tenant.id,
        department_code="CSE",
        name="Computer Science",
        department_kind=DepartmentKind.ACADEMIC,
        status=DepartmentStatus.ACTIVE,
    )
    await dept.insert()
    faculty = FacultyRecord(
        tenant_id=tenant.id,
        user_id=user.id,
        faculty_code="EMP-1042",
        designation="Professor",
        department_id=dept.id,
        employment_status=FacultyEmploymentStatus.ACTIVE,
    )
    await faculty.insert()
    return tenant, user, scope, faculty


@pytest.mark.anyio
async def test_faculty_directory_page_search(db_ready):
    suffix = uuid4().hex[:8]
    _tenant, _user, scope, faculty = await _seed(suffix)
    page = await get_faculty_directory_page(scope, search="Rekha")
    assert page.page_title == "Faculty Directory"
    assert len(page.faculty_rows) == 1
    assert page.faculty_rows[0].employee_id_label == "EMP-1042"
    assert page.faculty_rows[0].record_id == str(faculty.id)