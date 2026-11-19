"""College Admin phase 10 — import/migration and integration admin."""

import base64
import os
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.import_admin_schemas import ImportApproveRequest, ImportUploadRequest
from app.modules.college_admin.import_admin_service import (
    approve_import,
    execute_import,
    upload_import_file,
    validate_import_job,
)
from app.modules.college_admin.integration_admin_schemas import (
    IntegrationConfigUpdate,
    IntegrationRegisterRequest,
    WebhookEndpointUpsert,
    WebhookVerifyRequest,
)
from app.modules.college_admin.integration_admin_service import (
    register_integration,
    update_integration_config,
    upsert_webhook_endpoint,
    verify_inbound_webhook,
)
from app.modules.integrations.enums import IntegrationProviderType
from app.modules.integrations.models import IntegrationProvider
from app.modules.integrations.webhook_security import compute_webhook_signature
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
    tenant = Tenant(name=f"College P10 {suffix}", code=f"p10_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p10+{suffix}@example.com",
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


def _csv_b64(content: str) -> str:
    return base64.b64encode(content.encode("utf-8")).decode()


@pytest.mark.anyio
async def test_import_validate_duplicates(db_ready):
    _, user, scope = await _seed_admin(uuid4().hex[:6])
    csv = "student_id,email,full_name\nS1,a@ex.com,A\nS1,b@ex.com,B\n"
    job = await upload_import_file(
        scope,
        user,
        ImportUploadRequest(
            template_id="students_v1",
            file_name="students.csv",
            content_base64=_csv_b64(csv),
            idempotency_key=f"idem_{uuid4().hex[:8]}",
        ),
    )
    report = await validate_import_job(scope, user, job.job_id)
    assert report.valid_rows == 1
    assert report.duplicate_rows == 1


@pytest.mark.anyio
async def test_import_approve_and_execute(db_ready):
    _, user, scope = await _seed_admin(uuid4().hex[:6])
    csv = "student_id,email,full_name\nS2,c@ex.com,C\n"
    job = await upload_import_file(
        scope,
        user,
        ImportUploadRequest(
            template_id="students_v1",
            file_name="students.csv",
            content_base64=_csv_b64(csv),
            idempotency_key=f"idem_{uuid4().hex[:8]}",
        ),
    )
    await validate_import_job(scope, user, job.job_id)
    with pytest.raises(AppError) as exc:
        await execute_import(scope, user, job.job_id)
    assert exc.value.status_code == 403
    await approve_import(scope, user, job.job_id, ImportApproveRequest())
    done = await execute_import(scope, user, job.job_id)
    assert done.executed_rows == 1


@pytest.mark.anyio
async def test_integration_ssrf_blocked(db_ready):
    _, user, scope = await _seed_admin(uuid4().hex[:6])
    await IntegrationProvider(
        code="sms_tenant",
        name="SMS",
        provider_type=IntegrationProviderType.SMS,
        supports_tenant_credentials=True,
    ).insert()
    reg = await register_integration(
        scope,
        user,
        IntegrationRegisterRequest(integration_key="sms_main", provider_code="sms_tenant", title="SMS"),
    )
    with pytest.raises(AppError) as exc:
        await update_integration_config(
            scope,
            user,
            reg.integration_key,
            IntegrationConfigUpdate(connection_url="http://127.0.0.1/hook"),
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_webhook_signature_and_replay(db_ready):
    _, user, scope = await _seed_admin(uuid4().hex[:6])
    os.environ["TEST_WEBHOOK_SECRET"] = "phase10-secret-value-here-32"
    await IntegrationProvider(
        code="wh_provider",
        name="Webhook",
        provider_type=IntegrationProviderType.WEBHOOK,
        supports_tenant_credentials=True,
    ).insert()
    await register_integration(
        scope,
        user,
        IntegrationRegisterRequest(integration_key="wh1", provider_code="wh_provider", title="WH"),
    )
    endpoint = await upsert_webhook_endpoint(
        scope,
        user,
        WebhookEndpointUpsert(
            endpoint_id="ep1",
            integration_key="wh1",
            path_suffix="/inbound",
            signing_secret_ref="env://TEST_WEBHOOK_SECRET",
        ),
    )
    body = b'{"event":"test"}'
    ts = str(int(__import__("time").time()))
    sig = compute_webhook_signature("phase10-secret-value-here-32", body, ts)
    idem = f"idem_{uuid4().hex[:8]}"
    await verify_inbound_webhook(
        scope,
        user,
        WebhookVerifyRequest(
            timestamp=ts,
            signature=sig,
            body_base64=base64.b64encode(body).decode(),
            endpoint_id=endpoint.endpoint_id,
            idempotency_key=idem,
        ),
    )
    with pytest.raises(AppError) as exc:
        await verify_inbound_webhook(
            scope,
            user,
            WebhookVerifyRequest(
                timestamp=ts,
                signature=sig,
                body_base64=base64.b64encode(body).decode(),
                endpoint_id=endpoint.endpoint_id,
                idempotency_key=idem,
            ),
        )
    assert exc.value.status_code == 409