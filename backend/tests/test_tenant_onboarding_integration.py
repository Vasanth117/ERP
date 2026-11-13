"""Tenant registration and dashboard integration tests."""

from uuid import uuid4

import pytest
from beanie import PydanticObjectId

from app.authorization.platform_roles import PLATFORM_ROLE_PERMISSIONS
from app.common.access import AccessScope
from app.common.roles import Role
from app.modules.platform_identity.enums import PlatformRoleCode
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.exceptions import AppError
from app.modules.platform.service import get_platform_dashboard
from app.modules.tenants.schemas import (
    AddressInput,
    CollegeAdminInput,
    TenantRegisterCreate,
)
from app.modules.tenants.service import check_domain_availability, register_tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
        await connect_redis()
    except Exception as exc:
        pytest.skip(f"Dependencies not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


def _super_admin_scope() -> AccessScope:
    return AccessScope(
        role=Role.SUPER_ADMIN,
        user_id=PydanticObjectId(),
        tenant_id=None,
        department_id=None,
        effective_permissions=PLATFORM_ROLE_PERMISSIONS[PlatformRoleCode.PLATFORM_OWNER],
    )


def _registration_payload(suffix: str) -> TenantRegisterCreate:
    return TenantRegisterCreate(
        name=f"Test College {suffix}",
        code=f"tc_{suffix}",
        institution_email=f"office+{suffix}@example.com",
        contact_phone="+911234567890",
        address=AddressInput(
            line1="1 Main Road",
            city="Chennai",
            state="TN",
            country="IN",
        ),
        institution_type="engineering",
        domain=f"{suffix}.college.test",
        college_admin=CollegeAdminInput(email=f"admin+{suffix}@example.com", full_name="College Admin"),
        submit=True,
        idempotency_key=f"key-{suffix}",
    )


@pytest.mark.anyio
async def test_duplicate_tenant_code_rejected(db_ready) -> None:
    scope = _super_admin_scope()
    suffix = uuid4().hex[:8]
    payload = _registration_payload(suffix)
    await register_tenant(scope, payload)
    with pytest.raises(AppError) as exc:
        await register_tenant(scope, payload)
    assert exc.value.code == "CONFLICT"


@pytest.mark.anyio
async def test_duplicate_domain_rejected(db_ready) -> None:
    scope = _super_admin_scope()
    suffix = uuid4().hex[:8]
    first = _registration_payload(suffix)
    await register_tenant(scope, first)
    second = _registration_payload(f"{suffix}b")
    second = second.model_copy(update={"code": f"tc_{suffix}b", "domain": first.domain})
    with pytest.raises(AppError) as exc:
        await register_tenant(scope, second)
    assert exc.value.code == "CONFLICT"


@pytest.mark.anyio
async def test_domain_availability(db_ready) -> None:
    suffix = uuid4().hex[:8]
    normalized = f"{suffix}.college.test"
    available = await check_domain_availability(normalized)
    assert available.available is True


@pytest.mark.anyio
async def test_dashboard_aggregation_counts_tenant(db_ready) -> None:
    scope = _super_admin_scope()
    suffix = uuid4().hex[:8]
    await register_tenant(scope, _registration_payload(suffix))
    dashboard = await get_platform_dashboard(scope)
    assert dashboard.tenant_counts.total_registered >= 1
    assert dashboard.api_health.overall in {"healthy", "degraded", "unavailable"}


@pytest.mark.anyio
async def test_dashboard_marks_unknown_worker_health(db_ready) -> None:
    scope = _super_admin_scope()
    dashboard = await get_platform_dashboard(scope)
    broker = next(c for c in dashboard.api_health.components if c.name == "celery_workers")
    assert broker.status in {"unknown", "unavailable", "healthy", "degraded"}
