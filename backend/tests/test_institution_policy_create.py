"""Create institutional policy."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.institution_policies_page_service import (
    create_institution_policy,
    get_institution_policies_page,
)
from app.modules.college_admin.schemas import InstitutionPolicyCreate
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


async def _scope(suffix: str) -> AccessScope:
    tenant = Tenant(name=f"College PL {suffix}", code=f"pl_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+pl+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    return AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )


@pytest.mark.anyio
async def test_create_institution_policy(db_ready):
    suffix = uuid4().hex[:8]
    scope = await _scope(suffix)
    result = await create_institution_policy(
        scope,
        InstitutionPolicyCreate(
            title="Student Code of Conduct",
            category="Conduct",
            audience="students",
            version_label="1.0",
            status="draft",
            owner_label="Dean of Students",
        ),
    )
    assert result.policy_id
    page = await get_institution_policies_page(scope)
    assert page.policies
    assert page.policies[0].title == "Student Code of Conduct"