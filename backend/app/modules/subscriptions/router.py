"""Subscription management routes (optional SaaS billing module)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import AccessScope, get_access_scope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.modules.subscriptions.schemas import (
    AssignPlanRequest,
    CancelRequest,
    EntitlementRead,
    EntitlementUpdate,
    PlanCreate,
    PlanRead,
    PlanUpdate,
    SubscriptionChangeRequest,
    SubscriptionRead,
    WebhookIngest,
)
from app.modules.subscriptions.service import (
    assign_plan_to_tenant,
    cancel_subscription,
    suspend_subscription,
    configure_entitlements,
    create_plan,
    downgrade_subscription,
    get_plan,
    get_tenant_subscription_detail,
    ingest_subscription_webhook,
    list_invoices,
    list_payments,
    list_plans,
    list_subscription_history,
    record_usage,
    renew_subscription,
    subscription_summary,
    update_plan,
    upgrade_subscription,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/plans", response_model=ApiResponse[PlanRead])
async def create_plan_route(
    payload: PlanCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlanRead]:
    data = await create_plan(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/plans", response_model=ApiResponse[list[PlanRead]])
async def list_plans_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[PlanRead]]:
    data = await list_plans(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/plans/{code}", response_model=ApiResponse[PlanRead])
async def get_plan_route(
    code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlanRead]:
    data = await get_plan(scope, code)
    return success_response(data, request_id=get_request_id())


@router.patch("/plans/{code}", response_model=ApiResponse[PlanRead])
async def update_plan_route(
    code: str,
    payload: PlanUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlanRead]:
    data = await update_plan(scope, code, payload)
    return success_response(data, request_id=get_request_id())


@router.patch("/plans/{code}/entitlements", response_model=ApiResponse[EntitlementRead])
async def configure_entitlements_route(
    code: str,
    payload: EntitlementUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[EntitlementRead]:
    data = await configure_entitlements(scope, code, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/assign", response_model=ApiResponse[SubscriptionRead])
async def assign_plan_route(
    tenant_id: str,
    payload: AssignPlanRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SubscriptionRead]:
    data = await assign_plan_to_tenant(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}", response_model=ApiResponse[SubscriptionRead])
async def tenant_subscription_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SubscriptionRead]:
    data = await get_tenant_subscription_detail(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/upgrade", response_model=ApiResponse[SubscriptionRead])
async def upgrade_route(
    tenant_id: str,
    payload: SubscriptionChangeRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SubscriptionRead]:
    data = await upgrade_subscription(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/downgrade", response_model=ApiResponse[SubscriptionRead])
async def downgrade_route(
    tenant_id: str,
    payload: SubscriptionChangeRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SubscriptionRead]:
    data = await downgrade_subscription(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/renew", response_model=ApiResponse[SubscriptionRead])
async def renew_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SubscriptionRead]:
    data = await renew_subscription(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/suspend", response_model=ApiResponse[SubscriptionRead])
async def suspend_subscription_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    reason: str = "",
) -> ApiResponse[SubscriptionRead]:
    data = await suspend_subscription(scope, to_object_id(tenant_id, "tenant id"), reason=reason)
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/cancel", response_model=ApiResponse[SubscriptionRead])
async def cancel_route(
    tenant_id: str,
    payload: CancelRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SubscriptionRead]:
    data = await cancel_subscription(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/history", response_model=ApiResponse[list])
async def subscription_history_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list]:
    data = await list_subscription_history(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/invoices", response_model=ApiResponse[list])
async def invoices_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list]:
    data = await list_invoices(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/payments", response_model=ApiResponse[list])
async def payments_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list]:
    data = await list_payments(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/usage", response_model=ApiResponse[dict])
async def usage_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    metric_key: str,
    value: int,
) -> ApiResponse[dict]:
    data = await record_usage(scope, to_object_id(tenant_id, "tenant id"), metric_key, value)
    return success_response(data, request_id=get_request_id())


@router.get("/summary", response_model=ApiResponse[dict])
async def summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await subscription_summary(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/webhooks/ingest", response_model=ApiResponse[dict])
async def webhook_route(
    payload: WebhookIngest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await ingest_subscription_webhook(scope, payload)
    return success_response(data, request_id=get_request_id())
