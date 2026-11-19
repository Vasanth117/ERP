"""Integration management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
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
from app.modules.college_admin.integration_admin_service import (
    disable_integration,
    get_integration_health,
    list_integrations,
    list_sync_history,
    register_integration,
    retry_sync,
    revoke_integration,
    rotate_credentials,
    test_connectivity,
    update_integration_config,
    upsert_webhook_endpoint,
    verify_inbound_webhook,
)

router = APIRouter()


@router.post("/integrations", response_model=ApiResponse[IntegrationRead])
async def register_integration_route(
    payload: IntegrationRegisterRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[IntegrationRead]:
    return success_response(await register_integration(scope, user, payload), request_id=get_request_id())


@router.get("/integrations", response_model=ApiResponse[list[IntegrationRead]])
async def list_integrations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[IntegrationRead]]:
    return success_response(await list_integrations(scope), request_id=get_request_id())


@router.patch("/integrations/{integration_key}", response_model=ApiResponse[IntegrationRead])
async def update_integration_route(
    integration_key: str,
    payload: IntegrationConfigUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[IntegrationRead]:
    return success_response(await update_integration_config(scope, user, integration_key, payload), request_id=get_request_id())


@router.post("/integrations/{integration_key}/test", response_model=ApiResponse[dict])
async def test_integration_route(
    integration_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await test_connectivity(scope, integration_key), request_id=get_request_id())


@router.get("/integrations/{integration_key}/health", response_model=ApiResponse[IntegrationHealthRead])
async def integration_health_route(
    integration_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[IntegrationHealthRead]:
    return success_response(await get_integration_health(scope, integration_key), request_id=get_request_id())


@router.get("/integrations/{integration_key}/sync-history", response_model=ApiResponse[list[SyncHistoryRead]])
async def sync_history_route(
    integration_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[SyncHistoryRead]]:
    return success_response(await list_sync_history(scope, integration_key), request_id=get_request_id())


@router.post("/integrations/{integration_key}/sync-retry", response_model=ApiResponse[dict])
async def sync_retry_route(
    integration_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await retry_sync(scope, integration_key), request_id=get_request_id())


@router.put("/webhooks", response_model=ApiResponse[WebhookEndpointRead])
async def webhook_upsert_route(
    payload: WebhookEndpointUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[WebhookEndpointRead]:
    return success_response(await upsert_webhook_endpoint(scope, user, payload), request_id=get_request_id())


@router.post("/webhooks/verify", response_model=ApiResponse[dict])
async def webhook_verify_route(
    payload: WebhookVerifyRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await verify_inbound_webhook(scope, user, payload), request_id=get_request_id())


@router.post("/integrations/{integration_key}/credentials/rotate", response_model=ApiResponse[dict])
async def credential_rotate_route(
    integration_key: str,
    payload: CredentialRotateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await rotate_credentials(scope, user, integration_key, payload), request_id=get_request_id())


@router.post("/integrations/{integration_key}/disable", response_model=ApiResponse[IntegrationRead])
async def disable_integration_route(
    integration_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[IntegrationRead]:
    return success_response(await disable_integration(scope, user, integration_key), request_id=get_request_id())


@router.post("/integrations/{integration_key}/revoke", response_model=ApiResponse[IntegrationRead])
async def revoke_integration_route(
    integration_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[IntegrationRead]:
    return success_response(await revoke_integration(scope, user, integration_key), request_id=get_request_id())