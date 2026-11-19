"""Phase 2 — assessment and invoice workflow enumerations."""

from enum import Enum


class FeeAssessmentWorkflowStatus(str, Enum):
    DRAFT = "draft"
    PREVIEW = "preview"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    POSTED = "posted"


class FeeAssessmentExceptionCode(str, Enum):
    NO_ENROLLMENT = "no_enrollment"
    NO_STRUCTURE = "no_structure"
    DUPLICATE = "duplicate"
    INACTIVE_STUDENT = "inactive_student"
    MISSING_PROGRAMME = "missing_programme"
    OVERLAPPING_FEES = "overlapping_fees"
    INVALID_CONCESSION = "invalid_concession"
    DATA_CONFLICT = "data_conflict"


class StudentInvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    ADJUSTED = "adjusted"
    UNDER_RECONCILIATION = "under_reconciliation"


class InvoiceAdjustmentType(str, Enum):
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    CANCELLATION = "cancellation"
    REVISED = "revised"
    ADDITIONAL_DEMAND = "additional_demand"