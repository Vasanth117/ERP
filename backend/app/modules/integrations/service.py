"""Integration provider configuration and health."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from httpx import AsyncClient, Timeout

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.secrets import SecretReference, assert_secret_reference, redact_for_response
from app.core.url_safety import validate_outbound_url
from app.modules.integrations.enums import IntegrationOperationalStatus, IntegrationProviderType, IntegrationScope
from app.modules.integrations.models import (
    IntegrationConfiguration,
    IntegrationConfigurationHistory,
    IntegrationHealth,
    IntegrationProvider,
    IntegrationSyncHistory,
    ProviderCredentialReference,
    WebhookDeliveryEvent,
)
from app.modules.integrations.schemas import (
    IntegrationConfigRead,
    IntegrationConfigUpdate,
    IntegrationProviderCreate,
    IntegrationProviderRead,
    WebhookDeliveryRead,
)
from app.modules.integrations.webhook_security import new_idempotency_key
from app.modules.platform_security.audit import record_platform_audit


async def list_providers(scope: AccessScope) -> list[IntegrationProviderRead]:
    authorize(scope, Permission.INTEGRATION_READ)
    rows = await IntegrationProvider.find_all().sort("code").to_list()
    return [IntegrationProviderRead.from_document(r) for r in rows]


async def register_provider(scope: AccessScope, payload: IntegrationProviderCreate) -> IntegrationProviderRead:
    authorize(scope, Permission.INTEGRATION_MANAGE)
    existing = await IntegrationProvider.find_one(Eq(IntegrationProvider.code, payload.code))
    if existing is not None:
        raise AppError(code="CONFLICT", message="Provider code already exists", status_code=409)
    doc = IntegrationProvider(
        code=payload.code,
        name=payload.name,
        provider_type=payload.provider_type,
        version=payload.version,
        description=payload.description,
        supports_tenant_credentials=payload.supports_tenant_credentials,
        supports_global_shared=payload.supports_global_shared,
    )
    await doc.insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="integration.provider.registered",
        module="integrations",
        resource_type="integration_provider",
        resource_id=doc.code,
    )
    return IntegrationProviderRead.from_document(doc)


async def get_provider(scope: AccessScope, code: str) -> IntegrationProviderRead:
    authorize(scope, Permission.INTEGRATION_READ)
    doc = await IntegrationProvider.find_one(Eq(IntegrationProvider.code, code))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Provider not found", status_code=404)
    return IntegrationProviderRead.from_document(doc)


async def _get_or_create_config(
    provider_code: str,
    *,
    scope: IntegrationScope,
    tenant_id: PydanticObjectId | None,
) -> IntegrationConfiguration:
    doc = await IntegrationConfiguration.find_one(
        Eq(IntegrationConfiguration.provider_code, provider_code),
        Eq(IntegrationConfiguration.scope, scope),
        Eq(IntegrationConfiguration.tenant_id, tenant_id),
    )
    if doc is None:
        doc = IntegrationConfiguration(
            provider_code=provider_code,
            scope=scope,
            tenant_id=tenant_id,
        )
        await doc.insert()
        await IntegrationHealth(configuration_id=doc.id).insert()
    return doc


async def configure_integration(
    scope: AccessScope,
    provider_code: str,
    payload: IntegrationConfigUpdate,
) -> IntegrationConfigRead:
    authorize(scope, Permission.INTEGRATION_MANAGE)
    provider = await IntegrationProvider.find_one(Eq(IntegrationProvider.code, provider_code))
    if provider is None:
        raise AppError(code="NOT_FOUND", message="Provider not found", status_code=404)

    if payload.scope == IntegrationScope.TENANT and not provider.supports_tenant_credentials:
        raise AppError(code="VALIDATION_ERROR", message="Provider does not support tenant credentials", status_code=422)
    if payload.scope == IntegrationScope.GLOBAL and payload.tenant_id is not None:
        raise AppError(code="VALIDATION_ERROR", message="Global config cannot have tenant_id", status_code=422)

    doc = await _get_or_create_config(provider_code, scope=payload.scope, tenant_id=payload.tenant_id)
    changed: list[str] = []
    if payload.connection_url is not None:
        validate_outbound_url(payload.connection_url)
        doc.connection_url = payload.connection_url
        changed.append("connection_url")
    if payload.metadata is not None:
        doc.metadata = payload.metadata
        changed.append("metadata")
    if payload.credential_refs:
        for key, ref in payload.credential_refs.items():
            assert_secret_reference(ref)
            existing = await ProviderCredentialReference.find_one(
                Eq(ProviderCredentialReference.configuration_id, doc.id),
                Eq(ProviderCredentialReference.credential_key, key),
            )
            if existing is None:
                await ProviderCredentialReference(
                    configuration_id=doc.id,
                    credential_key=key,
                    secret_ref=ref,
                ).insert()
            else:
                existing.secret_ref = ref
                existing.rotated_at = utcnow()
                await existing.save()
            changed.append(f"credential:{key}")

    doc.version += 1
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await IntegrationConfigurationHistory(
        configuration_id=doc.id,
        version_number=doc.version,
        changed_keys=changed,
        actor_id=scope.user_id,
    ).insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="integration.configured",
        module="integrations",
        resource_type="integration_configuration",
        resource_id=str(doc.id),
        tenant_id=payload.tenant_id,
        metadata={"keys": changed},
    )
    return await get_integration_config(scope, provider_code, payload.scope, payload.tenant_id)


async def get_integration_config(
    scope: AccessScope,
    provider_code: str,
    config_scope: IntegrationScope,
    tenant_id: PydanticObjectId | None,
) -> IntegrationConfigRead:
    authorize(scope, Permission.INTEGRATION_READ)
    doc = await IntegrationConfiguration.find_one(
        Eq(IntegrationConfiguration.provider_code, provider_code),
        Eq(IntegrationConfiguration.scope, config_scope),
        Eq(IntegrationConfiguration.tenant_id, tenant_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Integration configuration not found", status_code=404)
    creds = await ProviderCredentialReference.find(
        Eq(ProviderCredentialReference.configuration_id, doc.id)
    ).to_list()
    health = await IntegrationHealth.find_one(Eq(IntegrationHealth.configuration_id, doc.id))
    return IntegrationConfigRead.from_parts(doc, creds, health)


async def set_integration_enabled(
    scope: AccessScope,
    provider_code: str,
    *,
    enabled: bool,
    config_scope: IntegrationScope,
    tenant_id: PydanticObjectId | None,
) -> IntegrationConfigRead:
    authorize(scope, Permission.INTEGRATION_MANAGE)
    doc = await _get_or_create_config(provider_code, scope=config_scope, tenant_id=tenant_id)
    doc.enabled = enabled
    doc.updated_at = utcnow()
    await doc.save()
    health = await IntegrationHealth.find_one(Eq(IntegrationHealth.configuration_id, doc.id))
    if health is not None:
        health.status = IntegrationOperationalStatus.ACTIVE if enabled else IntegrationOperationalStatus.DISABLED
        await health.save()
    return await get_integration_config(scope, provider_code, config_scope, tenant_id)


async def test_integration_connection(
    scope: AccessScope,
    provider_code: str,
    config_scope: IntegrationScope,
    tenant_id: PydanticObjectId | None,
) -> dict:
    authorize(scope, Permission.INTEGRATION_MANAGE)
    doc = await IntegrationConfiguration.find_one(
        Eq(IntegrationConfiguration.provider_code, provider_code),
        Eq(IntegrationConfiguration.scope, config_scope),
        Eq(IntegrationConfiguration.tenant_id, tenant_id),
    )
    if doc is None or not doc.connection_url:
        raise AppError(code="NOT_FOUND", message="Configured connection URL missing", status_code=404)
    validate_outbound_url(doc.connection_url)
    health = await IntegrationHealth.find_one(Eq(IntegrationHealth.configuration_id, doc.id))
    try:
        async with AsyncClient(timeout=Timeout(5.0)) as client:
            response = await client.head(doc.connection_url)
            ok = response.status_code < 500
    except Exception as exc:
        if health:
            health.status = IntegrationOperationalStatus.FAILED
            health.last_failure_at = utcnow()
            health.detail = "connection_failed"
            await health.save()
        await IntegrationSyncHistory(
            configuration_id=doc.id,
            status="failed",
            detail=str(exc)[:200],
            finished_at=utcnow(),
        ).insert()
        raise AppError(code="CONNECTION_FAILED", message="Provider connection test failed", status_code=502) from exc

    if health:
        health.status = IntegrationOperationalStatus.ACTIVE if ok else IntegrationOperationalStatus.DEGRADED
        health.last_check_at = utcnow()
        health.last_success_at = utcnow() if ok else health.last_success_at
        await health.save()
    await IntegrationSyncHistory(
        configuration_id=doc.id,
        status="succeeded" if ok else "degraded",
        finished_at=utcnow(),
    ).insert()
    return {"status": "ok" if ok else "degraded", "http_status": response.status_code}


async def get_connection_health(
    scope: AccessScope,
    provider_code: str,
    config_scope: IntegrationScope,
    tenant_id: PydanticObjectId | None,
) -> dict:
    authorize(scope, Permission.INTEGRATION_READ)
    doc = await IntegrationConfiguration.find_one(
        Eq(IntegrationConfiguration.provider_code, provider_code),
        Eq(IntegrationConfiguration.scope, config_scope),
        Eq(IntegrationConfiguration.tenant_id, tenant_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Configuration not found", status_code=404)
    health = await IntegrationHealth.find_one(Eq(IntegrationHealth.configuration_id, doc.id))
    if health is None:
        return {"status": "unknown"}
    return {
        "status": health.status.value,
        "last_check_at": health.last_check_at,
        "last_success_at": health.last_success_at,
        "last_failure_at": health.last_failure_at,
        "detail": health.detail,
    }


async def list_sync_history(
    scope: AccessScope,
    provider_code: str,
    config_scope: IntegrationScope,
    tenant_id: PydanticObjectId | None,
) -> list[dict]:
    authorize(scope, Permission.INTEGRATION_READ)
    doc = await IntegrationConfiguration.find_one(
        Eq(IntegrationConfiguration.provider_code, provider_code),
        Eq(IntegrationConfiguration.scope, config_scope),
        Eq(IntegrationConfiguration.tenant_id, tenant_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Configuration not found", status_code=404)
    rows = (
        await IntegrationSyncHistory.find(Eq(IntegrationSyncHistory.configuration_id, doc.id))
        .sort("-started_at")
        .limit(50)
        .to_list()
    )
    return [
        {"status": r.status, "detail": r.detail, "started_at": r.started_at, "finished_at": r.finished_at}
        for r in rows
    ]


async def list_webhook_deliveries(scope: AccessScope, configuration_id: PydanticObjectId) -> list[WebhookDeliveryRead]:
    authorize(scope, Permission.INTEGRATION_READ)
    rows = (
        await WebhookDeliveryEvent.find(Eq(WebhookDeliveryEvent.configuration_id, configuration_id))
        .sort("-created_at")
        .limit(50)
        .to_list()
    )
    return [WebhookDeliveryRead.from_document(r) for r in rows]


async def retry_webhook_delivery(scope: AccessScope, event_id: PydanticObjectId) -> WebhookDeliveryRead:
    authorize(scope, Permission.INTEGRATION_MANAGE)
    event = await WebhookDeliveryEvent.get(event_id)
    if event is None:
        raise AppError(code="NOT_FOUND", message="Webhook delivery not found", status_code=404)
    if event.status not in {"failed", "pending"}:
        raise AppError(code="CONFLICT", message="Delivery is not eligible for retry", status_code=409)
    event.status = "retrying"
    event.attempt_count += 1
    await event.save()
    event.status = "pending"
    await event.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="webhook.delivery.retry",
        module="integrations",
        resource_type="webhook_delivery_event",
        resource_id=str(event.id),
        tenant_id=event.tenant_id,
    )
    return WebhookDeliveryRead.from_document(event)


async def list_configuration_history(
    scope: AccessScope,
    configuration_id: PydanticObjectId,
) -> list[dict]:
    authorize(scope, Permission.INTEGRATION_READ)
    rows = (
        await IntegrationConfigurationHistory.find(
            Eq(IntegrationConfigurationHistory.configuration_id, configuration_id)
        )
        .sort("-version_number")
        .to_list()
    )
    return [
        {
            "version_number": r.version_number,
            "changed_keys": r.changed_keys,
            "actor_id": str(r.actor_id) if r.actor_id else None,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def rotate_credential(
    scope: AccessScope,
    configuration_id: PydanticObjectId,
    credential_key: str,
    secret_ref: str,
) -> dict:
    authorize(scope, Permission.INTEGRATION_MANAGE)
    assert_secret_reference(secret_ref)
    ref = await ProviderCredentialReference.find_one(
        Eq(ProviderCredentialReference.configuration_id, configuration_id),
        Eq(ProviderCredentialReference.credential_key, credential_key),
    )
    if ref is None:
        ref = ProviderCredentialReference(
            configuration_id=configuration_id,
            credential_key=credential_key,
            secret_ref=secret_ref,
        )
        await ref.insert()
    else:
        ref.secret_ref = secret_ref
        ref.rotated_at = utcnow()
        await ref.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="integration.credential.rotated",
        module="integrations",
        resource_type="provider_credential_reference",
        resource_id=str(ref.id),
        metadata={"credential_key": credential_key},
    )
    return redact_for_response(secret_ref)
