"""Student details page (CA 06.03)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.college_admin.student_details_page_service import get_student_details_page
from app.modules.students.models import StudentProfile
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


async def _seed_student(suffix: str) -> tuple[Tenant, StudentRecord, AccessScope]:
    tenant = Tenant(name=f"College SD {suffix}", code=f"sd_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+sd+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student_user = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Aarav Menon",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student_user.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student_user.id,
        roll_number=f"22CS{suffix[:4]}",
        programme_code="CSE",
        batch_label="2022-2026",
        section_code="A",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    await record.insert()
    profile = StudentProfile(
        tenant_id=tenant.id,
        user_id=student_user.id,
        programme_name="B.E. Computer Science",
        roll_number=record.roll_number,
        section_code="A",
        contact_phone="+91 98400 11220",
    )
    await profile.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, record, scope


@pytest.mark.anyio
async def test_student_details_page_loads(db_ready):
    suffix = uuid4().hex[:8]
    _tenant, record, scope = await _seed_student(suffix)
    page = await get_student_details_page(scope, str(record.id))
    assert page.profile_name == "Aarav Menon"
    assert "B.E. Computer Science" in page.profile_summary_line
    assert any(row.label == "Programme" for row in page.enrollment_rows)


@pytest.mark.anyio
async def test_student_details_page_not_found(db_ready):
    suffix = uuid4().hex[:8]
    _tenant, _record, scope = await _seed_student(suffix)
    with pytest.raises(AppError) as exc:
        await get_student_details_page(scope, "000000000000000000000001")
    assert exc.value.status_code == 404