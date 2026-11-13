"""SaaS subscription enums."""

from enum import Enum


class PlanTier(str, Enum):
    TRIAL = "trial"
    BASIC = "basic"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingInterval(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionChangeType(str, Enum):
    ASSIGNED = "assigned"
    UPGRADED = "upgraded"
    DOWNGRADED = "downgraded"
    RENEWED = "renewed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL_STARTED = "trial_started"
