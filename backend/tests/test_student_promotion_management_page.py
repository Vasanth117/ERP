"""Student promotion management page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.college_admin.student_promotion_management_page_service import get_student_promotion_management_page
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
async def test_promotion_management_page_returns_rules_and_kpis(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College PRM {suffix}", code=f"prm_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+prm+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"student+prm+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Eligible Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number=f"22CS{suffix[:4]}",
        programme_code="CSE",
        batch_label="2022",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    await record.insert()

    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_student_promotion_management_page(scope)
    assert page.page_title == "Student Promotion Management"
    assert len(page.kpis) == 4
    assert len(page.promotion_rules_rows) == 3
    assert page.kpis[0].key == "eligible"