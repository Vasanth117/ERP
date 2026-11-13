"""Subscription API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.subscriptions.enums import BillingInterval, PlanTier, SubscriptionStatus
from app.modules.subscriptions.models import PlanEntitlement, SubscriptionPlan, TenantSubscription


class PlanCreate(BaseModel):
    code: str
    name: str
    tier: PlanTier = PlanTier.BASIC
    price_cents: int = Field(ge=0)
    currency: str = "USD"
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    trial_days: int = Field(default=0, ge=0)
    description: str = ""


class PlanUpdate(BaseModel):
    name: str | None = None
    price_cents: int | None = Field(default=None, ge=0)
    enabled: bool | None = None
    trial_days: int | None = Field(default=None, ge=0)
    description: str | None = None


class PlanRead(BaseModel):
    id: str
    code: str
    name: str
    tier: PlanTier
    enabled: bool
    price_cents: int
    currency: str
    billing_interval: BillingInterval
    trial_days: int

    @classmethod
    def from_document(cls, doc: SubscriptionPlan) -> "PlanRead":
        return cls(
            id=str(doc.id),
            code=doc.code,
            name=doc.name,
            tier=doc.tier,
            enabled=doc.enabled,
            price_cents=doc.price_cents,
            currency=doc.currency,
            billing_interval=doc.billing_interval,
            trial_days=doc.trial_days,
        )


class EntitlementUpdate(BaseModel):
    limits: dict[str, Any] = Field(default_factory=dict)
    modules: list[str] = Field(default_factory=list)


class EntitlementRead(BaseModel):
    plan_id: str
    limits: dict[str, Any]
    modules: list[str]

    @classmethod
    def from_document(cls, doc: PlanEntitlement) -> "EntitlementRead":
        return cls(plan_id=str(doc.plan_id), limits=doc.limits, modules=doc.modules)


class AssignPlanRequest(BaseModel):
    plan_code: str
    start_trial: bool = True


class SubscriptionRead(BaseModel):
    id: str
    tenant_id: str
    plan_code: str
    status: SubscriptionStatus
    trial_ends_at: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool

    @classmethod
    def from_document(cls, doc: TenantSubscription) -> "SubscriptionRead":
        return cls(
            id=str(doc.id),
            tenant_id=str(doc.tenant_id),
            plan_code=doc.plan_code,
            status=doc.status,
            trial_ends_at=doc.trial_ends_at,
            current_period_end=doc.current_period_end,
            cancel_at_period_end=doc.cancel_at_period_end,
        )


class SubscriptionChangeRequest(BaseModel):
    target_plan_code: str
    effective_immediately: bool = False


class CancelRequest(BaseModel):
    at_period_end: bool = True
    reason: str = ""


class WebhookIngest(BaseModel):
    provider: str
    event_type: str
    idempotency_key: str
    tenant_external_ref: str | None = None
    invoice_external_ref: str | None = None
    payment_status: str | None = None
    signature: str
    timestamp: str
    payload: dict[str, Any] = Field(default_factory=dict)
