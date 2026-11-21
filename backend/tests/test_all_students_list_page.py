"""All students list page (CA 06.02)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.all_students_list_page_service import get_all_students_list_page
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
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


async def _seed_admin(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College ASL {suffix}", code=f"asl_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+asl+{suffix}@example.com",
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
    return tenant, user, scope


@pytest.mark.anyio
async def test_all_students_list_page_lists_record(db_ready):
    suffix = uuid4().hex[:8]
    tenant, student_user, scope = await _seed_admin(suffix)
    student_user.full_name = "Ananya Krishnan"
    await student_user.save()

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

    page = await get_all_students_list_page(scope, search="Ananya")
    assert page.page_title == "All Students List"
    assert len(page.students) == 1
    assert page.students[0].student_name == "Ananya Krishnan"
    assert page.students[0].status_label == "Active"