"""Hostel Admin phase 7 — integrations, audit and configuration."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.hostel.audit_config_schemas import HostelAuditSearch, HostelConfigTransition, HostelConfigUpsert
from app.modules.hostel.audit_config_service import audit_dashboard, search_audit, transition_config, upsert_config
from app.modules.hostel.hostel_audit_helper import record_hostel_audit
from app.modules.hostel.integration_models import HostelIntegrationCategory
from app.modules.hostel.integration_schemas import IntegrationBindingUpsert, ManualSyncRequest, WebhookIngest
from app.modules.hostel.integration_service import ingest_webhook, integration_dashboard, run_manual_sync, upsert_binding
from app.modules.tenants.models import Tenant
from app.common.schemas import Pagination


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


async def _seed():
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"H P7 {suffix}", code=f"hp7_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"ha7+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Hostel Admin",
        role=Role.HOSTEL_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = AccessScope(
        user_id=admin.id,
        tenant_id=tenant.id,
        role=Role.HOSTEL_ADMIN,
        effective_permissions=permissions_for_role(Role.HOSTEL_ADMIN),
    )
    return tenant, scope


@pytest.mark.anyio
async def test_integration_dashboard_and_student_sync(db_ready) -> None:
    _, scope = await _seed()
    dash = await integration_dashboard(scope)
    assert dash.total_bindings >= 6
    await upsert_binding(
        scope,
        IntegrationBindingUpsert(category=HostelIntegrationCategory.STUDENT, provider_code="student_profile", enabled=True),
    )
    job = await run_manual_sync(scope, ManualSyncRequest(category=HostelIntegrationCategory.STUDENT))
    assert job.status.value in ("completed", "failed")


@pytest.mark.anyio
async def test_webhook_idempotency(db_ready) -> None:
    tenant, scope = await _seed()
    ext_id = f"ext_{uuid4().hex[:8]}"
    first = await ingest_webhook(
        scope,
        HostelIntegrationCategory.GATE_SECURITY,
        WebhookIngest(external_event_id=ext_id, payload={"movement": "entry"}),
    )
    assert first["status"] == "received"
    second = await ingest_webhook(
        scope,
        HostelIntegrationCategory.GATE_SECURITY,
        WebhookIngest(external_event_id=ext_id, payload={"movement": "entry"}),
    )
    assert second["status"] == "duplicate_ignored"


@pytest.mark.anyio
async def test_configuration_lifecycle_and_audit_search(db_ready) -> None:
    tenant, scope = await _seed()
    cfg = await upsert_config(
        scope,
        HostelConfigUpsert(policy_section="visitor", payload={"max_duration_hours": 2}, change_reason="initial"),
    )
    assert cfg.status.value == "draft"
    active = await transition_config(
        scope,
        HostelConfigTransition(policy_section="visitor", action="publish"),
    )
    assert active.status.value in ("active", "scheduled")
    await record_hostel_audit(
        tenant.id,
        actor_id=scope.user_id,
        action="hostel.test.action",
        module="hostel",
        resource_type="test",
        hostel_code="H1",
    )
    board = await audit_dashboard(scope)
    assert board.total_entries >= 1
    page = await search_audit(scope, Pagination(page=1, page_size=20), HostelAuditSearch(hostel_code="H1"))
    assert page.total >= 1