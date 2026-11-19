"""Phase 7 refund and reconciliation enumerations."""

from enum import Enum


class RefundWorkflowStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    AWAITING_PROCESSING = "awaiting_processing"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    RECONCILIATION_PENDING = "reconciliation_pending"


class ReversalRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"


class ReconciliationPeriodStatus(str, Enum):
    NOT_STARTED = "not_started"
    IMPORTED = "imported"
    PROCESSING = "processing"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    EXCEPTION = "exception"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    RECONCILED = "reconciled"
    REJECTED = "rejected"


class ReconciliationMatchStatus(str, Enum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    UNMATCHED = "unmatched"