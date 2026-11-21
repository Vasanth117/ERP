"""Results pages (CA 09.09)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.result_approval_page_service import get_result_approval_page
from app.modules.college_admin.result_processing_page_service import get_result_processing_page
from app.modules.college_admin.result_publication_page_service import get_result_publication_page
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
async def test_result_processing_page_empty(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"ResP {suffix}", code=f"rp_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+rp+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    page = await get_result_processing_page(_scope(tenant, admin))
    assert page.page_title == "Result Processing"
    assert any(item.active and item.key == "processing" for item in page.sub_nav)


@pytest.mark.anyio
async def test_result_approval_page_empty(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"ResA {suffix}", code=f"ra_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+ra+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    page = await get_result_approval_page(_scope(tenant, admin))
    assert page.page_title == "Result Approval"
    assert len(page.approval_route_steps) == 3
    assert any(item.active and item.key == "approval" for item in page.sub_nav)


@pytest.mark.anyio
async def test_result_publication_page_empty(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"ResPub {suffix}", code=f"rpub_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+rpub+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    page = await get_result_publication_page(_scope(tenant, admin))
    assert page.page_title == "Result Publication"
    assert page.warning_title == "Publishing is final"
    assert any(item.active and item.key == "publication" for item in page.sub_nav)