"""Hostel integration management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.integration_models import HostelIntegrationCategory
from app.modules.hostel.integration_schemas import (
    IntegrationBindingRead,
    IntegrationBindingUpsert,
    IntegrationDashboard,
    IntegrationEventRead,
    IntegrationFailureRead,
    ManualSyncRequest,
    ReconciliationRead,
    SyncJobRead,
    WebhookIngest,
)
from app.modules.hostel.integration_service import (
    connection_health,
    ingest_webhook,
    integration_dashboard,
    list_bindings,
    list_failures,
    list_integration_events,
    list_reconciliation,
    list_sync_jobs,
    retry_failure,
    run_manual_sync,
    upsert_binding,
)

router = APIRouter(prefix="/me", tags=["hostel-integrations"])


@router.get("/integrations/dashboard", response_model=ApiResponse[IntegrationDashboard])
async def integrations_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await integration_dashboard(scope), request_id=get_request_id())


@router.get("/integrations/bindings", response_model=ApiResponse[list[IntegrationBindingRead]])
async def list_bindings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await list_bindings(scope), request_id=get_request_id())


@router.put("/integrations/bindings", response_model=ApiResponse[IntegrationBindingRead])
async def upsert_binding_route(
    payload: IntegrationBindingUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_binding(scope, payload), request_id=get_request_id())


@router.post("/integrations/sync", response_model=ApiResponse[SyncJobRead])
async def manual_sync_route(
    payload: ManualSyncRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await run_manual_sync(scope, payload), request_id=get_request_id())


@router.get("/integrations/sync-jobs", response_model=ApiResponse[list[SyncJobRead]])
async def sync_jobs_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    limit: int = 50,
):
    return success_response(await list_sync_jobs(scope, limit), request_id=get_request_id())


@router.get("/integrations/failures", response_model=ApiResponse[list[IntegrationFailureRead]])
async def failures_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    open_only: bool = True,
    limit: int = 50,
):
    return success_response(await list_failures(scope, open_only=open_only, limit=limit), request_id=get_request_id())


@router.get("/integrations/events", response_model=ApiResponse[list[IntegrationEventRead]])
async def integration_events_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    limit: int = 50,
):
    return success_response(await list_integration_events(scope, limit), request_id=get_request_id())


@router.get("/integrations/health", response_model=ApiResponse[list[dict]])
async def integration_health_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await connection_health(scope), request_id=get_request_id())


@router.get("/integrations/reconciliation", response_model=ApiResponse[list[ReconciliationRead]])
async def reconciliation_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    category: HostelIntegrationCategory | None = None,
):
    return success_response(await list_reconciliation(scope, category), request_id=get_request_id())


@router.post("/integrations/webhooks/{category}", response_model=ApiResponse[dict])
async def webhook_ingest_route(
    category: HostelIntegrationCategory,
    payload: WebhookIngest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await ingest_webhook(scope, category, payload), request_id=get_request_id())


@router.post("/integrations/failures/{failure_id}/retry", response_model=ApiResponse[IntegrationFailureRead])
async def retry_failure_route(
    failure_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await retry_failure(scope, failure_id), request_id=get_request_id())