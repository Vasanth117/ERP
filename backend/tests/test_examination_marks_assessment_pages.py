"""Marks & assessment pages (CA 09.08)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.internal_external_assessment_page_service import get_internal_external_assessment_page
from app.modules.college_admin.marks_entry_management_page_service import get_marks_entry_management_page
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


def _scope(tenant: Tenant, admin: User) -> AccessScope:
    return AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )


@pytest.mark.anyio
async def test_marks_entry_management_page_empty(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"Marks {suffix}", code=f"m_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+m+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    page = await get_marks_entry_management_page(_scope(tenant, admin))
    assert page.page_title == "Marks Entry Management"
    assert len(page.workflow_steps) == 6
    assert any(item.active and item.key == "marks_entry" for item in page.sub_nav)


@pytest.mark.anyio
async def test_internal_external_assessment_page_empty(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"Asm {suffix}", code=f"a_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+a+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    page = await get_internal_external_assessment_page(_scope(tenant, admin))
    assert page.page_title == "Internal & External Assessment"
    assert any(item.active and item.key == "assessment" for item in page.sub_nav)