"""Seed default SaaS subscription plans and entitlements."""

import asyncio

from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.modules.subscriptions.enums import BillingInterval, PlanTier
from app.modules.subscriptions.models import PlanEntitlement, SubscriptionPlan


PLANS = (
    ("trial", "Trial", PlanTier.TRIAL, 0, 14, ["tenant_registry"], {"max_students": 100}),
    ("basic", "Basic", PlanTier.BASIC, 9900, 0, ["tenant_registry", "students"], {"max_students": 500}),
    ("standard", "Standard", PlanTier.STANDARD, 19900, 0, ["tenant_registry", "students", "finance"], {"max_students": 2000}),
    ("professional", "Professional", PlanTier.PROFESSIONAL, 39900, 0, ["*"], {"max_students": 10000}),
    ("enterprise", "Enterprise", PlanTier.ENTERPRISE, 0, 0, ["*"], {"max_students": 100000}),
)


async def main() -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        for code, name, tier, price, trial_days, modules, limits in PLANS:
            existing = await SubscriptionPlan.find_one(SubscriptionPlan.code == code)
            if existing is not None:
                continue
            plan = SubscriptionPlan(
                code=code,
                name=name,
                tier=tier,
                price_cents=price,
                billing_interval=BillingInterval.MONTHLY,
                trial_days=trial_days,
            )
            await plan.insert()
            await PlanEntitlement(plan_id=plan.id, modules=modules, limits=limits).insert()
            print(f"seeded plan {code}")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
