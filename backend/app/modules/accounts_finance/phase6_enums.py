"""Phase 6 installment and late fee enumerations."""

from enum import Enum


class PaymentPlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class InstallmentStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    WAIVED = "waived"


class AssignmentStatus(str, Enum):
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    RESTRUCTURED = "restructured"


class RescheduleStatus(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class LateFeeCalcType(str, Enum):
    FIXED = "fixed"
    PERCENT = "percent"
    DAILY = "daily"
    PERIODIC = "periodic"


class LateFeeAssessmentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    POSTED = "posted"
    WAIVED = "waived"
    CANCELLED = "cancelled"


class DueStatus(str, Enum):
    NOT_DUE = "not_due"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    LATE_FEE_APPLIED = "late_fee_applied"
    WAIVER_PENDING = "waiver_pending"
    PARTIALLY_SETTLED = "partially_settled"
    FULLY_SETTLED = "fully_settled"