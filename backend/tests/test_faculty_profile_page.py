"""Faculty profile page (CA 07.03)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.faculty_profile_page_service import get_faculty_profile_page
from app.modules.college_admin.identity_models import DepartmentKind, DepartmentStatus, InstitutionDepartment
from app.modules.faculty.models import QualificationRecord
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
async def test_faculty_profile_page_loads(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College FP {suffix}", code=f"fp_{suffix}")
    await tenant.insert()
    user = User(
        email=f"hari+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. S. Hari",
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
        department_code="ECE",
        name="Electronics & Communication",
        department_kind=DepartmentKind.ACADEMIC,
        status=DepartmentStatus.ACTIVE,
    )
    await dept.insert()
    record = FacultyRecord(
        tenant_id=tenant.id,
        user_id=user.id,
        faculty_code="EMP-1107",
        designation="Associate Professor",
        department_id=dept.id,
        employment_status=FacultyEmploymentStatus.ACTIVE,
        qualifications=[
            QualificationRecord(degree="Ph.D.", institution="IIT Madras", year=2014),
        ],
    )
    await record.insert()

    page = await get_faculty_profile_page(scope, str(record.id))
    assert page.page_title == "Faculty Profile"
    assert page.profile_name == "Dr. S. Hari"
    assert len(page.qualification_rows) == 1
    assert "EMP-1107" in page.profile_summary_line