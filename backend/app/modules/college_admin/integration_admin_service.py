"""Institution-level integration administration."""

import base64
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from httpx import AsyncClient, Timeout

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.secrets import assert_secret_reference
from app.core.url_safety import validate_outbound_url
from app.modules.auth.models import User
from app.modules.college_admin.integration_admin_models import (
    InstitutionIntegration,
    InstitutionIntegrationAuditLog,
    InstitutionIntegrationConfiguration,
    InstitutionIntegrationHealth,
    InstitutionIntegrationStatus,
    InstitutionProviderCredentialReference,
    InstitutionSyncHistory,
    InstitutionWebhookDeliveryLog,
    InstitutionWebhookEndpoint,
)
from app.modules.college_admin.integration_admin_schemas import (
    CredentialRotateRequest,
    IntegrationConfigUpdate,
    IntegrationHealthRead,
    IntegrationRead,
    IntegrationRegisterRequest,
    SyncHistoryRead,
    WebhookEndpointRead,
    WebhookEndpointUpsert,
    WebhookVerifyRequest,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.integrations.enums import IntegrationOperationalStatus, IntegrationScope
from app.modules.integrations.models import IntegrationConfiguration, IntegrationHealth, IntegrationProvider
from app.modules.integrations.webhook_security import new_idempotency_key, verify_webhook_signature


async def _audit(tenant_id: PydanticObjectId, integration_key: str, action: str, actor_id: PydanticObjectId | None, metadata: dict | None = None) -> None:
    await InstitutionIntegrationAuditLog(
        tenant_id=tenant_id,
        integration_key=integration_key,
        action=action,
        actor_id=actor_id,
        metadata=metadata or {},
    ).insert()


async def register_integration(scope: AccessScope, user: User, payload: IntegrationRegisterRequest) -> IntegrationRead:
    authorize(scope, Permission.INTEGRATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    key = payload.integration_key.strip().lower()
    provider = await IntegrationProvider.find_one(Eq(IntegrationProvider.code, payload.provider_code))
    if provider is None:
        raise AppError(code="NOT_FOUND", message="Provider not registered on platform", status_code=404)
    if not provider.supports_tenant_credentials:
        raise AppError(code="VALIDATION_ERROR", message="Provider does not support tenant credentials", status_code=422)
    if await InstitutionIntegration.find_one(
        Eq(InstitutionIntegration.tenant_id, tenant_id),
        Eq(InstitutionIntegration.integration_key, key),
    ):
        raise AppError(code="CONFLICT", message="Integration key exists", status_code=409)
    config = await IntegrationConfiguration.find_one(
        Eq(IntegrationConfiguration.provider_code, payload.provider_code),
        Eq(IntegrationConfiguration.scope, IntegrationScope.TENANT),
        Eq(IntegrationConfiguration.tenant_id, tenant_id),
    )
    if config is None:
        config = IntegrationConfiguration(
            provider_code=payload.provider_code,
            scope=IntegrationScope.TENANT,
            tenant_id=tenant_id,
        )
        await config.insert()
        await IntegrationHealth(configuration_id=config.id).insert()
    doc = InstitutionIntegration(
        tenant_id=tenant_id,
        integration_key=key,
        provider_code=payload.provider_code,
        title=payload.title,
        configuration_id=config.id,
        actor_id=user.id,
    )
    await doc.insert()
    await InstitutionIntegrationConfiguration(
        tenant_id=tenant_id,
        integration_key=key,
        configuration_id=config.id,
    ).insert()
    await InstitutionIntegrationHealth(tenant_id=tenant_id, integration_key=key).insert()
    await _audit(tenant_id, key, "register", user.id, {"provider": payload.provider_code})
    return IntegrationRead(
        integration_key=doc.integration_key,
        provider_code=doc.provider_code,
        title=doc.title,
        version=doc.version,
        status=doc.status,
        configuration_id=str(config.id),
    )


async def list_integrations(scope: AccessScope) -> list[IntegrationRead]:
    authorize(scope, Permission.INTEGRATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    docs = await InstitutionIntegration.find(Eq(InstitutionIntegration.tenant_id, tenant_id)).to_list()
    return [
        IntegrationRead(
            integration_key=d.integration_key,
            provider_code=d.provider_code,
            title=d.title,
            version=d.version,
            status=d.status,
            configuration_id=str(d.configuration_id) if d.configuration_id else None,
        )
        for d in docs
    ]


async def update_integration_config(
    scope: AccessScope,
    user: User,
    integration_key: str,
    payload: IntegrationConfigUpdate,
) -> IntegrationRead:
    authorize(scope, Permission.INTEGRATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    key = integration_key.strip().lower()
    doc = await InstitutionIntegration.find_one(
        Eq(InstitutionIntegration.tenant_id, tenant_id),
        Eq(InstitutionIntegration.integration_key, key),
    )
    if doc is None or doc.status == InstitutionIntegrationStatus.REVOKED:
        raise AppError(code="NOT_FOUND", message="Integration not found", status_code=404)
    overlay = await InstitutionIntegrationConfiguration.find_one(
        Eq(InstitutionIntegrationConfiguration.tenant_id, tenant_id),
        Eq(InstitutionIntegrationConfiguration.integration_key, key),
    )
    config = await IntegrationConfiguration.get(doc.configuration_id)
    if config is None:
        raise AppError(code="NOT_FOUND", message="Configuration missing", status_code=404)
    if payload.connection_url is not None:
        try:
            validate_outbound_url(payload.connection_url)
        except ValueError as exc:
            raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc
        config.connection_url = payload.connection_url
        overlay.connection_url = payload.connection_url
    if payload.settings is not None:
        overlay.settings = payload.settings
        config.metadata = {**config.metadata, **payload.settings}
    for cred_key, secret_ref in payload.credential_refs.items():
        assert_secret_reference(secret_ref)
        ref = await InstitutionProviderCredentialReference.find_one(
            Eq(InstitutionProviderCredentialReference.tenant_id, tenant_id),
            Eq(InstitutionProviderCredentialReference.integration_key, key),
            Eq(InstitutionProviderCredentialReference.credential_key, cred_key),
        )
        if ref is None:
            await InstitutionProviderCredentialReference(
                tenant_id=tenant_id,
                integration_key=key,
                credential_key=cred_key,
                secret_ref=secret_ref,
                configuration_id=config.id,
            ).insert()
        else:
            ref.secret_ref = secret_ref
            ref.rotated_at = utcnow()
            await ref.save()
    if payload.enabled is not None:
        config.enabled = payload.enabled
        doc.status = InstitutionIntegrationStatus.ENABLED if payload.enabled else InstitutionIntegrationStatus.DISABLED
        await doc.save()
    config.version += 1
    config.updated_by = user.id
    config.updated_at = utcnow()
    await config.save()
    overlay.version += 1
    overlay.updated_by = user.id
    overlay.updated_at = utcnow()
    await overlay.save()
    await _audit(tenant_id, key, "config.update", user.id)
    return IntegrationRead(
        integration_key=doc.integration_key,
        provider_code=doc.provider_code,
        title=doc.title,
        version=overlay.version,
        status=doc.status,
        configuration_id=str(config.id),
    )


async def test_connectivity(scope: AccessScope, integration_key: str) -> dict:
    authorize(scope, Permission.INTEGRATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    key = integration_key.strip().lower()
    doc = await InstitutionIntegration.find_one(
        Eq(InstitutionIntegration.tenant_id, tenant_id),
        Eq(InstitutionIntegration.integration_key, key),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Integration not found", status_code=404)
    config = await IntegrationConfiguration.get(doc.configuration_id)
    if not config or not config.connection_url:
        raise AppError(code="VALIDATION_ERROR", message="Connection URL not configured", status_code=422)
    try:
        validate_outbound_url(config.connection_url)
    except ValueError as exc:
        raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc
    health = await InstitutionIntegrationHealth.find_one(
        Eq(InstitutionIntegrationHealth.tenant_id, tenant_id),
        Eq(InstitutionIntegrationHealth.integration_key, key),
    )
    sync_id = f"sync_{uuid4().hex[:10]}"
    try:
        async with AsyncClient(timeout=Timeout(5.0)) as client:
            response = await client.head(config.connection_url)
            ok = response.status_code < 500
    except Exception as exc:
        if health:
            health.status = "failed"
            health.last_failure_at = utcnow()
            health.detail = str(exc)[:120]
            await health.save()
        await InstitutionSyncHistory(
            tenant_id=tenant_id,
            integration_key=key,
            sync_id=sync_id,
            status="failed",
            detail=str(exc)[:200],
            finished_at=utcnow(),
        ).insert()
        raise AppError(code="CONNECTION_FAILED", message="Connectivity test failed", status_code=502) from exc
    if health:
        health.status = "active" if ok else "degraded"
        health.last_check_at = utcnow()
        health.last_success_at = utcnow() if ok else health.last_success_at
        await health.save()
    await InstitutionSyncHistory(
        tenant_id=tenant_id,
        integration_key=key,
        sync_id=sync_id,
        status="succeeded" if ok else "degraded",
        finished_at=utcnow(),
    ).insert()
    await _audit(tenant_id, key, "connectivity.test", scope.user_id, {"ok": ok})
    return {"status": "ok" if ok else "degraded", "sync_id": sync_id}


async def get_integration_health(scope: AccessScope, integration_key: str) -> IntegrationHealthRead:
    authorize(scope, Permission.INTEGRATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    health = await InstitutionIntegrationHealth.find_one(
        Eq(InstitutionIntegrationHealth.tenant_id, tenant_id),
        Eq(InstitutionIntegrationHealth.integration_key, integration_key.strip().lower()),
    )
    if health is None:
        raise AppError(code="NOT_FOUND", message="Health record not found", status_code=404)
    return IntegrationHealthRead(
        integration_key=integration_key,
        status=health.status,
        last_check_at=health.last_check_at,
        detail=health.detail,
    )


async def list_sync_history(scope: AccessScope, integration_key: str, *, limit: int = 30) -> list[SyncHistoryRead]:
    authorize(scope, Permission.INTEGRATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    docs = (
        await InstitutionSyncHistory.find(
            Eq(InstitutionSyncHistory.tenant_id, tenant_id),
            Eq(InstitutionSyncHistory.integration_key, integration_key.strip().lower()),
        )
        .sort("-started_at")
        .limit(limit)
        .to_list()
    )
    return [
        SyncHistoryRead(
            sync_id=d.sync_id,
            status=d.status,
            detail=d.detail,
            started_at=d.started_at,
            finished_at=d.finished_at,
        )
        for d in docs
    ]


async def retry_sync(scope: AccessScope, integration_key: str) -> dict:
    return await test_connectivity(scope, integration_key)


async def upsert_webhook_endpoint(scope: AccessScope, user: User, payload: WebhookEndpointUpsert) -> WebhookEndpointRead:
    authorize(scope, Permission.INTEGRATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    assert_secret_reference(payload.signing_secret_ref)
    eid = payload.endpoint_id.strip()
    doc = await InstitutionWebhookEndpoint.find_one(
        Eq(InstitutionWebhookEndpoint.tenant_id, tenant_id),
        Eq(InstitutionWebhookEndpoint.endpoint_id, eid),
    )
    if doc is None:
        doc = InstitutionWebhookEndpoint(
            tenant_id=tenant_id,
            endpoint_id=eid,
            integration_key=payload.integration_key.strip().lower(),
            path_suffix=payload.path_suffix,
            signing_secret_ref=payload.signing_secret_ref,
            replay_window_seconds=payload.replay_window_seconds,
        )
        await doc.insert()
    else:
        doc.integration_key = payload.integration_key.strip().lower()
        doc.path_suffix = payload.path_suffix
        doc.signing_secret_ref = payload.signing_secret_ref
        doc.replay_window_seconds = payload.replay_window_seconds
        doc.updated_at = utcnow()
        await doc.save()
    await _audit(tenant_id, doc.integration_key, "webhook.upsert", user.id, {"endpoint_id": eid})
    return WebhookEndpointRead(
        endpoint_id=doc.endpoint_id,
        integration_key=doc.integration_key,
        path_suffix=doc.path_suffix,
        signing_secret_ref=doc.signing_secret_ref,
        enabled=doc.enabled,
    )


async def verify_inbound_webhook(scope: AccessScope, user: User, payload: WebhookVerifyRequest) -> dict:
    authorize(scope, Permission.INTEGRATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    endpoint = await InstitutionWebhookEndpoint.find_one(
        Eq(InstitutionWebhookEndpoint.tenant_id, tenant_id),
        Eq(InstitutionWebhookEndpoint.endpoint_id, payload.endpoint_id),
    )
    if endpoint is None or not endpoint.enabled:
        raise AppError(code="NOT_FOUND", message="Webhook endpoint not found", status_code=404)
    idem = payload.idempotency_key or new_idempotency_key()
    if await InstitutionWebhookDeliveryLog.find_one(
        Eq(InstitutionWebhookDeliveryLog.tenant_id, tenant_id),
        Eq(InstitutionWebhookDeliveryLog.idempotency_key, idem),
    ):
        raise AppError(code="WEBHOOK_REPLAY", message="Idempotency key already processed", status_code=409)
    body = base64.b64decode(payload.body_base64, validate=True)
    from app.core.secrets import SecretReference

    secret = SecretReference(endpoint.signing_secret_ref).resolve()
    verify_webhook_signature(
        secret=secret,
        body=body,
        timestamp=payload.timestamp,
        provided_signature=payload.signature,
        max_age_seconds=endpoint.replay_window_seconds,
    )
    delivery_id = f"wh_{uuid4().hex[:10]}"
    await InstitutionWebhookDeliveryLog(
        tenant_id=tenant_id,
        delivery_id=delivery_id,
        endpoint_id=endpoint.endpoint_id,
        event_type="inbound",
        idempotency_key=idem,
        signature_valid=True,
        status="delivered",
        attempt_count=1,
    ).insert()
    return {"delivery_id": delivery_id, "status": "verified"}


async def rotate_credentials(
    scope: AccessScope,
    user: User,
    integration_key: str,
    payload: CredentialRotateRequest,
) -> dict:
    authorize(scope, Permission.INTEGRATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    assert_secret_reference(payload.secret_ref)
    key = integration_key.strip().lower()
    ref = await InstitutionProviderCredentialReference.find_one(
        Eq(InstitutionProviderCredentialReference.tenant_id, tenant_id),
        Eq(InstitutionProviderCredentialReference.integration_key, key),
        Eq(InstitutionProviderCredentialReference.credential_key, payload.credential_key),
    )
    if ref is None:
        raise AppError(code="NOT_FOUND", message="Credential reference not found", status_code=404)
    ref.secret_ref = payload.secret_ref
    ref.rotated_at = utcnow()
    await ref.save()
    await _audit(tenant_id, key, "credential.rotate", user.id, {"credential_key": payload.credential_key})
    return {"status": "rotated", "credential_key": payload.credential_key}


async def disable_integration(scope: AccessScope, user: User, integration_key: str) -> IntegrationRead:
    authorize(scope, Permission.INTEGRATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    key = integration_key.strip().lower()
    doc = await InstitutionIntegration.find_one(
        Eq(InstitutionIntegration.tenant_id, tenant_id),
        Eq(InstitutionIntegration.integration_key, key),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Integration not found", status_code=404)
    doc.status = InstitutionIntegrationStatus.DISABLED
    doc.updated_at = utcnow()
    await doc.save()
    if doc.configuration_id:
        config = await IntegrationConfiguration.get(doc.configuration_id)
        if config:
            config.enabled = False
            config.updated_at = utcnow()
            await config.save()
    await _audit(tenant_id, key, "disable", user.id)
    return IntegrationRead(
        integration_key=doc.integration_key,
        provider_code=doc.provider_code,
        title=doc.title,
        version=doc.version,
        status=doc.status,
        configuration_id=str(doc.configuration_id) if doc.configuration_id else None,
    )


async def revoke_integration(scope: AccessScope, user: User, integration_key: str) -> IntegrationRead:
    authorize(scope, Permission.INTEGRATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    key = integration_key.strip().lower()
    doc = await InstitutionIntegration.find_one(
        Eq(InstitutionIntegration.tenant_id, tenant_id),
        Eq(InstitutionIntegration.integration_key, key),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Integration not found", status_code=404)
    doc.status = InstitutionIntegrationStatus.REVOKED
    doc.updated_at = utcnow()
    await doc.save()
    await _audit(tenant_id, key, "revoke", user.id)
    return IntegrationRead(
        integration_key=doc.integration_key,
        provider_code=doc.provider_code,
        title=doc.title,
        version=doc.version,
        status=doc.status,
        configuration_id=str(doc.configuration_id) if doc.configuration_id else None,
    )