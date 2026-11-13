"""Tenant lifecycle HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AccessScope, get_access_scope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.modules.tenants.lifecycle_service import (
    activate_tenant,
    approve_offboarding,
    cancel_scheduled_lifecycle_operation,
    get_lifecycle_history,
    get_lifecycle_status,
    get_offboarding_status,
    initiate_offboarding,
    reactivate_tenant,
    retry_failed_lifecycle_operation,
    start_offboarding,
    suspend_tenant,
)
from app.modules.tenants.schemas_lifecycle import (
    LifecycleOperationRead,
    LifecycleStatusRead,
    LifecycleTransitionRequest,
    OffboardingInitiateRequest,
    OffboardingStatusRead,
)

router = APIRouter()


@router.get("/status", response_model=ApiResponse[LifecycleStatusRead])
async def lifecycle_status_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[LifecycleStatusRead]:
    data = await get_lifecycle_status(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/history", response_model=ApiResponse[list[LifecycleOperationRead]])
async def lifecycle_history_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[LifecycleOperationRead]]:
    data = await get_lifecycle_history(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/activate", response_model=ApiResponse[LifecycleStatusRead])
async def activate_tenant_route(
    tenant_id: str,
    payload: LifecycleTransitionRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[LifecycleStatusRead]:
    data = await activate_tenant(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/suspend", response_model=ApiResponse[LifecycleStatusRead])
async def suspend_tenant_route(
    tenant_id: str,
    payload: LifecycleTransitionRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[LifecycleStatusRead]:
    data = await suspend_tenant(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/reactivate", response_model=ApiResponse[LifecycleStatusRead])
async def reactivate_tenant_route(
    tenant_id: str,
    payload: LifecycleTransitionRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[LifecycleStatusRead]:
    data = await reactivate_tenant(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/offboarding/initiate", response_model=ApiResponse[OffboardingStatusRead])
async def initiate_offboarding_route(
    tenant_id: str,
    payload: OffboardingInitiateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingStatusRead]:
    data = await initiate_offboarding(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/offboarding/status", response_model=ApiResponse[OffboardingStatusRead])
async def offboarding_status_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingStatusRead]:
    data = await get_offboarding_status(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/offboarding/approve", response_model=ApiResponse[OffboardingStatusRead])
async def approve_offboarding_route(
    tenant_id: str,
    payload: LifecycleTransitionRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingStatusRead]:
    data = await approve_offboarding(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/offboarding/start", response_model=ApiResponse[LifecycleStatusRead])
async def start_offboarding_route(
    tenant_id: str,
    payload: LifecycleTransitionRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[LifecycleStatusRead]:
    data = await start_offboarding(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/operations/{operation_id}/cancel", response_model=ApiResponse[LifecycleOperationRead])
async def cancel_lifecycle_operation_route(
    tenant_id: str,
    operation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    reason: Annotated[str, Query(min_length=3, max_length=500)],
) -> ApiResponse[LifecycleOperationRead]:
    data = await cancel_scheduled_lifecycle_operation(
        scope,
        to_object_id(tenant_id, "tenant id"),
        operation_id,
        reason=reason,
    )
    return success_response(data, request_id=get_request_id())


@router.post("/operations/{operation_id}/retry", response_model=ApiResponse[LifecycleStatusRead])
async def retry_lifecycle_operation_route(
    tenant_id: str,
    operation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[LifecycleStatusRead]:
    data = await retry_failed_lifecycle_operation(
        scope,
        to_object_id(tenant_id, "tenant id"),
        operation_id,
    )
    return success_response(data, request_id=get_request_id())
