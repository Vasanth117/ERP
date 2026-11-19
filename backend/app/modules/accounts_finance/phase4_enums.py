"""Phase 4 ledger and receipt enumerations."""

from enum import Enum


class LedgerEntryType(str, Enum):
    FEE_ASSESSMENT = "fee_assessment"
    FEE_INVOICE = "fee_invoice"
    VERIFIED_PAYMENT = "verified_payment"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    SCHOLARSHIP_CREDIT = "scholarship_credit"
    CONCESSION_CREDIT = "concession_credit"
    FEE_WAIVER = "fee_waiver"
    REFUND = "refund"
    PAYMENT_REVERSAL = "payment_reversal"
    LATE_FEE = "late_fee"
    LATE_FEE_WAIVER = "late_fee_waiver"
    ADJUSTMENT = "adjustment"
    ADVANCE_PAYMENT = "advance_payment"
    ADVANCE_ALLOCATION = "advance_allocation"
    OTHER = "other"


class LedgerAdjustmentStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"


class ReceiptStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    CANCELLED = "cancelled"
    REISSUED = "reissued"
    SUPERSEDED = "superseded"