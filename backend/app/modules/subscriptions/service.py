"""Subscription plan and tenant billing operations."""

from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.integrations.webhook_security import verify_webhook_signature
from app.modules.platform_security.audit import record_platform_audit
from app.modules.subscriptions.enforcement import billing_enabled, plan_for_code, require_billing_enabled
from app.modules.subscriptions.enums import (
    PaymentStatus,
    SubscriptionChangeType,
    SubscriptionStatus,
)
from app.modules.subscriptions.models import (
    PlanEntitlement,
    SubscriptionHistory,
    SubscriptionInvoice,
    SubscriptionPayment,
    SubscriptionPlan,
    SubscriptionUsageMetric,
    SubscriptionWebhookEvent,
    TenantSubscription,
)
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
from app.repositories.tenant_repository import TenantRepository

_tenant_repo = TenantRepository()


async def _history(
    tenant_id: PydanticObjectId,
    subscription_id: PydanticObjectId,
    change: SubscriptionChangeType,
    *,
    actor_id: PydanticObjectId | None,
    from_plan: str | None = None,
    to_plan: str | None = None,
    metadata: dict | None = None,
) -> None:
    await SubscriptionHistory(
        tenant_id=tenant_id,
        subscription_id=subscription_id,
        change_type=change,
        from_plan_code=from_plan,
        to_plan_code=to_plan,
        actor_id=actor_id,
        metadata=metadata or {},
    ).insert()


async def create_plan(scope: AccessScope, payload: PlanCreate) -> PlanRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    existing = await SubscriptionPlan.find_one(Eq(SubscriptionPlan.code, payload.code))
    if existing:
        raise AppError(code="CONFLICT", message="Plan code exists", status_code=409)
    doc = SubscriptionPlan(**payload.model_dump())
    await doc.insert()
    await PlanEntitlement(plan_id=doc.id, limits={}, modules=[]).insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="subscription.plan.created",
        module="subscriptions",
        resource_type="subscription_plan",
        resource_id=doc.code,
    )
    return PlanRead.from_document(doc)


async def list_plans(scope: AccessScope) -> list[PlanRead]:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_READ)
    rows = await SubscriptionPlan.find_all().sort("code").to_list()
    return [PlanRead.from_document(r) for r in rows]


async def get_plan(scope: AccessScope, code: str) -> PlanRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_READ)
    return PlanRead.from_document(await plan_for_code(code))


async def update_plan(scope: AccessScope, code: str, payload: PlanUpdate) -> PlanRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    doc = await plan_for_code(code)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    doc.updated_at = utcnow()
    await doc.save()
    return PlanRead.from_document(doc)


async def configure_entitlements(scope: AccessScope, code: str, payload: EntitlementUpdate) -> EntitlementRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    plan = await plan_for_code(code)
    ent = await PlanEntitlement.find_one(Eq(PlanEntitlement.plan_id, plan.id))
    if ent is None:
        ent = PlanEntitlement(plan_id=plan.id)
        await ent.insert()
    ent.limits = payload.limits
    ent.modules = payload.modules
    ent.updated_at = utcnow()
    await ent.save()
    return EntitlementRead.from_document(ent)


async def assign_plan_to_tenant(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: AssignPlanRequest,
) -> SubscriptionRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    if await _tenant_repo.get_tenant(tenant_id) is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    plan = await plan_for_code(payload.plan_code)
    if not plan.enabled:
        raise AppError(code="CONFLICT", message="Plan is disabled", status_code=409)

    existing = await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))
    settings = get_settings()
    now = utcnow()
    trial_end = now + timedelta(days=plan.trial_days or settings.subscription_trial_days) if payload.start_trial else None
    status = SubscriptionStatus.TRIAL if trial_end else SubscriptionStatus.ACTIVE
    period_end = trial_end or (now + timedelta(days=30))

    if existing is None:
        sub = TenantSubscription(
            tenant_id=tenant_id,
            plan_id=plan.id,
            plan_code=plan.code,
            status=status,
            trial_ends_at=trial_end,
            current_period_start=now,
            current_period_end=period_end,
        )
        await sub.insert()
        await _history(tenant_id, sub.id, SubscriptionChangeType.ASSIGNED, actor_id=scope.user_id, to_plan=plan.code)
    else:
        previous = existing.plan_code
        existing.plan_id = plan.id
        existing.plan_code = plan.code
        existing.status = status
        existing.trial_ends_at = trial_end
        existing.current_period_start = now
        existing.current_period_end = period_end
        existing.updated_at = now
        await existing.save()
        await _history(
            tenant_id,
            existing.id,
            SubscriptionChangeType.ASSIGNED,
            actor_id=scope.user_id,
            from_plan=previous,
            to_plan=plan.code,
        )
        sub = existing
    return SubscriptionRead.from_document(sub)


async def get_tenant_subscription_detail(scope: AccessScope, tenant_id: PydanticObjectId) -> SubscriptionRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_READ)
    sub = await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))
    if sub is None:
        raise AppError(code="NOT_FOUND", message="Subscription not found", status_code=404)
    return SubscriptionRead.from_document(sub)


async def upgrade_subscription(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: SubscriptionChangeRequest,
) -> SubscriptionRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    sub = await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))
    if sub is None:
        raise AppError(code="NOT_FOUND", message="Subscription not found", status_code=404)
    plan = await plan_for_code(payload.target_plan_code)
    previous = sub.plan_code
    sub.plan_id = plan.id
    sub.plan_code = plan.code
    sub.status = SubscriptionStatus.ACTIVE
    sub.updated_at = utcnow()
    await sub.save()
    await _history(
        tenant_id,
        sub.id,
        SubscriptionChangeType.UPGRADED,
        actor_id=scope.user_id,
        from_plan=previous,
        to_plan=plan.code,
    )
    return SubscriptionRead.from_document(sub)


async def downgrade_subscription(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: SubscriptionChangeRequest,
) -> SubscriptionRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    sub = await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))
    if sub is None:
        raise AppError(code="NOT_FOUND", message="Subscription not found", status_code=404)
    plan = await plan_for_code(payload.target_plan_code)
    previous = sub.plan_code
    sub.plan_id = plan.id
    sub.plan_code = plan.code
    sub.updated_at = utcnow()
    await sub.save()
    await _history(
        tenant_id,
        sub.id,
        SubscriptionChangeType.DOWNGRADED,
        actor_id=scope.user_id,
        from_plan=previous,
        to_plan=plan.code,
    )
    return SubscriptionRead.from_document(sub)


async def renew_subscription(scope: AccessScope, tenant_id: PydanticObjectId) -> SubscriptionRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    sub = await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))
    if sub is None:
        raise AppError(code="NOT_FOUND", message="Subscription not found", status_code=404)
    now = utcnow()
    sub.current_period_start = now
    sub.current_period_end = now + timedelta(days=30)
    sub.status = SubscriptionStatus.ACTIVE
    sub.updated_at = now
    await sub.save()
    await _history(tenant_id, sub.id, SubscriptionChangeType.RENEWED, actor_id=scope.user_id, to_plan=sub.plan_code)
    return SubscriptionRead.from_document(sub)


async def suspend_subscription(scope: AccessScope, tenant_id: PydanticObjectId, reason: str = "") -> SubscriptionRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    sub = await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))
    if sub is None:
        raise AppError(code="NOT_FOUND", message="Subscription not found", status_code=404)
    previous = sub.status
    sub.status = SubscriptionStatus.SUSPENDED
    sub.updated_at = utcnow()
    await sub.save()
    await _history(
        tenant_id,
        sub.id,
        SubscriptionChangeType.SUSPENDED,
        actor_id=scope.user_id,
        to_plan=sub.plan_code,
        metadata={"reason": reason, "previous_status": previous.value},
    )
    return SubscriptionRead.from_document(sub)


async def cancel_subscription(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: CancelRequest,
) -> SubscriptionRead:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    sub = await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))
    if sub is None:
        raise AppError(code="NOT_FOUND", message="Subscription not found", status_code=404)
    sub.cancel_at_period_end = payload.at_period_end
    if not payload.at_period_end:
        sub.status = SubscriptionStatus.CANCELLED
        sub.cancelled_at = utcnow()
    sub.updated_at = utcnow()
    await sub.save()
    await _history(
        tenant_id,
        sub.id,
        SubscriptionChangeType.CANCELLED,
        actor_id=scope.user_id,
        to_plan=sub.plan_code,
        metadata={"reason": payload.reason},
    )
    return SubscriptionRead.from_document(sub)


async def list_subscription_history(scope: AccessScope, tenant_id: PydanticObjectId) -> list[dict]:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_READ)
    rows = await SubscriptionHistory.find(Eq(SubscriptionHistory.tenant_id, tenant_id)).sort("-created_at").to_list()
    return [
        {
            "change_type": r.change_type.value,
            "from_plan": r.from_plan_code,
            "to_plan": r.to_plan_code,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


async def list_invoices(scope: AccessScope, tenant_id: PydanticObjectId) -> list[dict]:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_READ)
    rows = await SubscriptionInvoice.find(Eq(SubscriptionInvoice.tenant_id, tenant_id)).sort("-created_at").to_list()
    return [
        {
            "id": str(r.id),
            "status": r.status.value,
            "amount_cents": r.amount_cents,
            "period_start": r.period_start.isoformat(),
            "period_end": r.period_end.isoformat(),
        }
        for r in rows
    ]


async def list_payments(scope: AccessScope, tenant_id: PydanticObjectId) -> list[dict]:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_READ)
    rows = await SubscriptionPayment.find(Eq(SubscriptionPayment.tenant_id, tenant_id)).sort("-created_at").to_list()
    return [{"id": str(r.id), "status": r.status.value, "amount_cents": r.amount_cents} for r in rows]


async def record_usage(scope: AccessScope, tenant_id: PydanticObjectId, metric_key: str, value: int) -> dict:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_READ)
    now = utcnow()
    doc = SubscriptionUsageMetric(
        tenant_id=tenant_id,
        metric_key=metric_key,
        value=value,
        period_start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        period_end=now,
    )
    await doc.insert()
    return {"metric_key": metric_key, "value": value}


async def subscription_summary(scope: AccessScope) -> dict:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_READ)
    active = await TenantSubscription.find(Eq(TenantSubscription.status, SubscriptionStatus.ACTIVE)).count()
    trial = await TenantSubscription.find(Eq(TenantSubscription.status, SubscriptionStatus.TRIAL)).count()
    past_due = await TenantSubscription.find(Eq(TenantSubscription.status, SubscriptionStatus.PAST_DUE)).count()
    return {"active": active, "trial": trial, "past_due": past_due}


async def ingest_subscription_webhook(scope: AccessScope, payload: WebhookIngest) -> dict:
    require_billing_enabled()
    authorize(scope, Permission.SUBSCRIPTION_MANAGE)
    import json

    body = json.dumps(
        {
            "event_type": payload.event_type,
            "idempotency_key": payload.idempotency_key,
            "tenant_external_ref": payload.tenant_external_ref,
        },
        sort_keys=True,
    ).encode("utf-8")
    from app.core.config import get_settings

    verify_webhook_signature(
        secret=get_settings().jwt_secret,
        body=body,
        timestamp=payload.timestamp,
        provided_signature=payload.signature,
        max_age_seconds=600,
    )
    existing = await SubscriptionWebhookEvent.find_one(Eq(SubscriptionWebhookEvent.idempotency_key, payload.idempotency_key))
    if existing is not None:
        return {"status": "duplicate", "processed": existing.processed}
    event = SubscriptionWebhookEvent(
        provider=payload.provider,
        event_type=payload.event_type,
        idempotency_key=payload.idempotency_key,
        payload_summary={
            "payment_status": payload.payment_status,
            "invoice_external_ref": payload.invoice_external_ref,
        },
    )
    await event.insert()
    if payload.payment_status == "failed":
        if payload.tenant_external_ref:
            sub = await TenantSubscription.find_one(
                Eq(TenantSubscription.external_customer_ref, payload.tenant_external_ref)
            )
            if sub:
                sub.status = SubscriptionStatus.PAST_DUE
                await sub.save()
    elif payload.payment_status == "succeeded":
        if payload.tenant_external_ref:
            sub = await TenantSubscription.find_one(
                Eq(TenantSubscription.external_customer_ref, payload.tenant_external_ref)
            )
            if sub:
                sub.status = SubscriptionStatus.ACTIVE
                await sub.save()
                invoice_rows = await SubscriptionInvoice.find(Eq(SubscriptionInvoice.tenant_id, sub.tenant_id)).limit(1).to_list()
                invoice_id = invoice_rows[0].id if invoice_rows else sub.id
                await SubscriptionPayment(
                    tenant_id=sub.tenant_id,
                    invoice_id=invoice_id,
                    status=PaymentStatus.SUCCEEDED,
                    amount_cents=0,
                    idempotency_key=payload.idempotency_key,
                ).insert()
    event.processed = True
    await event.save()
    return {"status": "processed"}
