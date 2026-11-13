"""Backend entitlement and subscription enforcement."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.subscriptions.enums import SubscriptionStatus
from app.modules.subscriptions.models import PlanEntitlement, SubscriptionPlan, TenantSubscription

ACTIVE_STATUSES = frozenset(
    {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}
)


def billing_enabled() -> bool:
    return get_settings().saas_billing_enabled


def require_billing_enabled() -> None:
    if not billing_enabled():
        raise AppError(
            code="BILLING_DISABLED",
            message="SaaS billing module is disabled",
            status_code=404,
        )


async def get_tenant_subscription(tenant_id: PydanticObjectId) -> TenantSubscription | None:
    if not billing_enabled():
        return None
    return await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))


async def assert_no_active_subscription_blockers(tenant_id: PydanticObjectId) -> None:
    if not billing_enabled():
        return
    sub = await get_tenant_subscription(tenant_id)
    if sub is None:
        return
    if sub.status in {SubscriptionStatus.PAST_DUE, SubscriptionStatus.ACTIVE}:
        raise AppError(
            code="SUBSCRIPTION_OUTSTANDING",
            message="Resolve subscription obligations before offboarding",
            status_code=409,
        )


async def enforce_active_subscription(tenant_id: PydanticObjectId) -> TenantSubscription:
    require_billing_enabled()
    sub = await get_tenant_subscription(tenant_id)
    if sub is None or sub.status not in ACTIVE_STATUSES:
        raise AppError(
            code="SUBSCRIPTION_INACTIVE",
            message="No active subscription for this college",
            status_code=403,
        )
    if sub.status == SubscriptionStatus.EXPIRED:
        raise AppError(code="SUBSCRIPTION_EXPIRED", message="Subscription expired", status_code=403)
    return sub


async def get_entitlements_for_tenant(tenant_id: PydanticObjectId) -> dict:
    if not billing_enabled():
        return {"modules": ["*"], "limits": {}}
    sub = await get_tenant_subscription(tenant_id)
    if sub is None:
        return {"modules": [], "limits": {}}
    ent = await PlanEntitlement.find_one(Eq(PlanEntitlement.plan_id, sub.plan_id))
    if ent is None:
        return {"modules": [], "limits": {}}
    return {"modules": ent.modules, "limits": ent.limits}


async def check_entitlement_limit(tenant_id: PydanticObjectId, limit_key: str, current_usage: int) -> None:
    if not billing_enabled():
        return
    await enforce_active_subscription(tenant_id)
    entitlements = await get_entitlements_for_tenant(tenant_id)
    limits = entitlements.get("limits") or {}
    cap = limits.get(limit_key)
    if cap is None:
        return
    if current_usage >= int(cap):
        raise AppError(
            code="ENTITLEMENT_LIMIT",
            message=f"Usage limit reached for {limit_key}",
            status_code=403,
        )


async def assert_module_entitled(tenant_id: PydanticObjectId, module_code: str) -> None:
    if not billing_enabled():
        return
    await enforce_active_subscription(tenant_id)
    entitlements = await get_entitlements_for_tenant(tenant_id)
    modules = entitlements.get("modules") or []
    if "*" in modules:
        return
    if module_code not in modules:
        raise AppError(
            code="ENTITLEMENT_MODULE",
            message=f"Module {module_code} is not included in the current plan",
            status_code=403,
        )


async def plan_for_code(code: str) -> SubscriptionPlan:
    plan = await SubscriptionPlan.find_one(Eq(SubscriptionPlan.code, code))
    if plan is None:
        raise AppError(code="NOT_FOUND", message="Plan not found", status_code=404)
    return plan
