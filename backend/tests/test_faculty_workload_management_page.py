"""Faculty workload management (CA 07.09)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_workload_management_page_service import get_faculty_workload_management_page
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
async def test_faculty_workload_management_page_loads(db_ready):
    _, scope = await _scope(uuid4().hex[:8])
    page = await get_faculty_workload_management_page(scope, page=1)
    assert page.page_title == "Faculty Workload Management"
    assert len(page.kpis) == 4
    assert page.table_headers[0] == "Faculty"