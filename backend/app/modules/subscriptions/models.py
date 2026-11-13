"""Subscription and billing documents."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.subscriptions.enums import (
    BillingInterval,
    InvoiceStatus,
    PaymentStatus,
    PlanTier,
    SubscriptionChangeType,
    SubscriptionStatus,
)


class SubscriptionPlan(Document):
    code: str
    name: str
    tier: PlanTier = PlanTier.BASIC
    enabled: bool = True
    price_cents: int = 0
    currency: str = "USD"
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    trial_days: int = 0
    description: str = ""
    version: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "subscription_plans"
        indexes = [IndexModel([("code", ASCENDING)], unique=True, name="unique_subscription_plan")]


class PlanEntitlement(Document):
    plan_id: PydanticObjectId
    limits: dict[str, Any] = Field(default_factory=dict)
    modules: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "plan_entitlements"
        indexes = [IndexModel([("plan_id", ASCENDING)], unique=True, name="unique_plan_entitlements")]


class TenantSubscription(Document):
    tenant_id: PydanticObjectId
    plan_id: PydanticObjectId
    plan_code: str
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    trial_ends_at: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancelled_at: datetime | None = None
    cancel_at_period_end: bool = False
    external_customer_ref: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_subscriptions"
        indexes = [IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_tenant_subscription")]


class SubscriptionHistory(Document):
    tenant_id: PydanticObjectId
    subscription_id: PydanticObjectId
    change_type: SubscriptionChangeType
    from_plan_code: str | None = None
    to_plan_code: str | None = None
    actor_id: PydanticObjectId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "subscription_history"
        indexes = [IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="subscription_history_tenant")]


class SubscriptionInvoice(Document):
    tenant_id: PydanticObjectId
    subscription_id: PydanticObjectId
    status: InvoiceStatus = InvoiceStatus.DRAFT
    amount_cents: int
    currency: str = "USD"
    period_start: datetime
    period_end: datetime
    external_invoice_ref: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "subscription_invoices"
        indexes = [IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="subscription_invoices_tenant")]


class SubscriptionPayment(Document):
    tenant_id: PydanticObjectId
    invoice_id: PydanticObjectId
    status: PaymentStatus = PaymentStatus.PENDING
    amount_cents: int
    currency: str = "USD"
    idempotency_key: str
    provider_ref: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "subscription_payments"
        indexes = [
            IndexModel([("idempotency_key", ASCENDING)], unique=True, name="unique_subscription_payment"),
        ]


class SubscriptionWebhookEvent(Document):
    provider: str
    event_type: str
    idempotency_key: str
    payload_summary: dict[str, Any] = Field(default_factory=dict)
    processed: bool = False
    received_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "subscription_webhook_events"
        indexes = [
            IndexModel([("idempotency_key", ASCENDING)], unique=True, name="unique_subscription_webhook"),
        ]


class SubscriptionUsageMetric(Document):
    tenant_id: PydanticObjectId
    metric_key: str
    value: int
    period_start: datetime
    period_end: datetime
    recorded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "subscription_usage_metrics"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("metric_key", ASCENDING), ("period_start", ASCENDING)],
                name="subscription_usage_tenant_metric",
            ),
        ]
