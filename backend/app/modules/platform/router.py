"""Platform dashboard routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AccessScope, pagination_params, require_permission
from app.authorization.permissions import Permission
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.platform.schemas import (
    PlatformActivityItem,
    PlatformAlertRead,
    PlatformDashboard,
    TenantCountSummary,
)
from app.modules.configuration.router import platform_router as platform_configuration_router
from app.modules.platform_identity.router import router as platform_operators_router
from app.modules.platform_security.router import router as platform_security_router
from app.modules.support_access.router import router as support_access_router
from app.modules.platform_ops.router import router as platform_ops_router
from app.modules.integrations.router import router as integrations_router
from app.modules.data_governance.router import router as data_governance_router
from app.modules.subscriptions.router import router as subscriptions_router
from app.modules.tenants.lifecycle_service import list_pending_lifecycle_operations
from app.modules.tenants.schemas_lifecycle import LifecycleOperationRead
from app.modules.platform.service import (
    get_platform_activity_summary,
    get_platform_alerts,
    get_platform_dashboard,
    get_service_health_summary,
    get_tenant_statistics,
)
from app.modules.tenants.enums import TenantOperationalStatus

router = APIRouter()
router.include_router(platform_configuration_router, tags=["platform-configuration"])
router.include_router(platform_operators_router)
router.include_router(platform_security_router)
router.include_router(support_access_router)
router.include_router(platform_ops_router)
router.include_router(integrations_router)
router.include_router(data_governance_router)
router.include_router(subscriptions_router)


@router.get("/dashboard", response_model=ApiResponse[PlatformDashboard])
async def platform_dashboard_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_DASHBOARD_READ))],
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
    tenant_status: Annotated[TenantOperationalStatus | None, Query()] = None,
) -> ApiResponse[PlatformDashboard]:
    data = await get_platform_dashboard(
        scope,
        created_from=created_from,
        created_to=created_to,
        tenant_status=tenant_status,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/tenant-statistics", response_model=ApiResponse[TenantCountSummary])
async def tenant_statistics_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_DASHBOARD_READ))],
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
) -> ApiResponse[TenantCountSummary]:
    data = await get_tenant_statistics(scope, created_from=created_from, created_to=created_to)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/activity", response_model=ApiResponse[Page[PlatformActivityItem]])
async def platform_activity_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_DASHBOARD_READ))],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[PlatformActivityItem]]:
    data = await get_platform_activity_summary(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/alerts", response_model=ApiResponse[Page[PlatformAlertRead]])
async def platform_alerts_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_DASHBOARD_READ))],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[PlatformAlertRead]]:
    data = await get_platform_alerts(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/service-health", response_model=ApiResponse[dict])
async def platform_service_health_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_DASHBOARD_READ))],
) -> ApiResponse[dict]:
    data = await get_service_health_summary(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/lifecycle/operations/pending", response_model=ApiResponse[list[LifecycleOperationRead]])
async def platform_pending_lifecycle_operations_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_TENANT_LIFECYCLE_READ))],
) -> ApiResponse[list[LifecycleOperationRead]]:
    data = await list_pending_lifecycle_operations(scope)
    return success_response(data, request_id=get_request_id())
