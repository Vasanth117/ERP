"""Integration provider routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AccessScope, get_access_scope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.modules.integrations.enums import IntegrationScope
from app.modules.integrations.schemas import (
    IntegrationConfigRead,
    IntegrationConfigUpdate,
    IntegrationProviderCreate,
    IntegrationProviderRead,
    WebhookDeliveryRead,
)
from app.modules.integrations.service import (
    configure_integration,
    get_connection_health,
    get_integration_config,
    get_provider,
    list_configuration_history,
    list_providers,
    list_sync_history,
    list_webhook_deliveries,
    register_provider,
    retry_webhook_delivery,
    rotate_credential,
    set_integration_enabled,
    test_integration_connection,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/providers", response_model=ApiResponse[list[IntegrationProviderRead]])
async def list_providers_route(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> ApiResponse[list[IntegrationProviderRead]]:
    data = await list_providers(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/providers", response_model=ApiResponse[IntegrationProviderRead])
async def register_provider_route(
    payload: IntegrationProviderCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[IntegrationProviderRead]:
    data = await register_provider(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/providers/{code}", response_model=ApiResponse[IntegrationProviderRead])
async def get_provider_route(
    code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[IntegrationProviderRead]:
    data = await get_provider(scope, code)
    return success_response(data, request_id=get_request_id())


@router.patch("/providers/{code}/configuration", response_model=ApiResponse[IntegrationConfigRead])
async def configure_provider_route(
    code: str,
    payload: IntegrationConfigUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[IntegrationConfigRead]:
    data = await configure_integration(scope, code, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/providers/{code}/configuration", response_model=ApiResponse[IntegrationConfigRead])
async def get_configuration_route(
    code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    config_scope: Annotated[IntegrationScope, Query(alias="scope")] = IntegrationScope.GLOBAL,
    tenant_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[IntegrationConfigRead]:
    tid = to_object_id(tenant_id, "tenant id") if tenant_id else None
    data = await get_integration_config(scope, code, config_scope, tid)
    return success_response(data, request_id=get_request_id())


@router.post("/providers/{code}/enable", response_model=ApiResponse[IntegrationConfigRead])
async def enable_provider_route(
    code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    enabled: Annotated[bool, Query()] = True,
    config_scope: Annotated[IntegrationScope, Query(alias="scope")] = IntegrationScope.GLOBAL,
    tenant_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[IntegrationConfigRead]:
    tid = to_object_id(tenant_id, "tenant id") if tenant_id else None
    data = await set_integration_enabled(scope, code, enabled=enabled, config_scope=config_scope, tenant_id=tid)
    return success_response(data, request_id=get_request_id())


@router.post("/providers/{code}/test-connection", response_model=ApiResponse[dict])
async def test_connection_route(
    code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    config_scope: Annotated[IntegrationScope, Query(alias="scope")] = IntegrationScope.GLOBAL,
    tenant_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    tid = to_object_id(tenant_id, "tenant id") if tenant_id else None
    data = await test_integration_connection(scope, code, config_scope, tid)
    return success_response(data, request_id=get_request_id())


@router.get("/providers/{code}/health", response_model=ApiResponse[dict])
async def connection_health_route(
    code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    config_scope: Annotated[IntegrationScope, Query(alias="scope")] = IntegrationScope.GLOBAL,
    tenant_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    tid = to_object_id(tenant_id, "tenant id") if tenant_id else None
    data = await get_connection_health(scope, code, config_scope, tid)
    return success_response(data, request_id=get_request_id())


@router.get("/providers/{code}/sync-history", response_model=ApiResponse[list])
async def sync_history_route(
    code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    config_scope: Annotated[IntegrationScope, Query(alias="scope")] = IntegrationScope.GLOBAL,
    tenant_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list]:
    tid = to_object_id(tenant_id, "tenant id") if tenant_id else None
    data = await list_sync_history(scope, code, config_scope, tid)
    return success_response(data, request_id=get_request_id())


@router.get("/configurations/{configuration_id}/webhooks", response_model=ApiResponse[list[WebhookDeliveryRead]])
async def webhook_deliveries_route(
    configuration_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[WebhookDeliveryRead]]:
    data = await list_webhook_deliveries(scope, to_object_id(configuration_id, "configuration id"))
    return success_response(data, request_id=get_request_id())


@router.post("/webhooks/{event_id}/retry", response_model=ApiResponse[WebhookDeliveryRead])
async def retry_webhook_route(
    event_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[WebhookDeliveryRead]:
    data = await retry_webhook_delivery(scope, to_object_id(event_id, "event id"))
    return success_response(data, request_id=get_request_id())


@router.get("/configurations/{configuration_id}/history", response_model=ApiResponse[list])
async def configuration_history_route(
    configuration_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list]:
    data = await list_configuration_history(scope, to_object_id(configuration_id, "configuration id"))
    return success_response(data, request_id=get_request_id())


@router.post("/configurations/{configuration_id}/credentials/{credential_key}/rotate", response_model=ApiResponse[dict])
async def rotate_credential_route(
    configuration_id: str,
    credential_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    secret_ref: Annotated[str, Query(min_length=8)],
) -> ApiResponse[dict]:
    data = await rotate_credential(
        scope,
        to_object_id(configuration_id, "configuration id"),
        credential_key,
        secret_ref,
    )
    return success_response(data, request_id=get_request_id())
