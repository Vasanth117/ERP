"""Phase 12 finance settings and audit enumerations."""

from enum import Enum


class FinanceSettingsDomain(str, Enum):
    GENERAL = "general"
    FEE = "fee"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    SCHOLARSHIP = "scholarship"
    INSTALLMENT = "installment"
    REFUND = "refund"
    ACCOUNTING = "accounting"
    BUDGET = "budget"
    TAX = "tax"
    REPORTING = "reporting"


class FinanceSettingStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class FinanceAccessScopeType(str, Enum):
    INSTITUTION = "institution"
    CAMPUS = "campus"
    DEPARTMENT = "department"
    COST_CENTRE = "cost_centre"


class FinanceTraceLinkType(str, Enum):
    ASSESSED_TO_INVOICE = "assessed_to_invoice"
    INVOICE_TO_PAYMENT = "invoice_to_payment"
    PAYMENT_TO_LEDGER = "payment_to_ledger"
    PAYMENT_TO_RECEIPT = "payment_to_receipt"
    LEDGER_TO_GL = "ledger_to_gl"
    PAYMENT_TO_REFUND = "payment_to_refund"
    PR_TO_PO = "pr_to_po"
    PO_TO_VENDOR_INVOICE = "po_to_vendor_invoice"
    VENDOR_INVOICE_TO_PAYMENT = "vendor_invoice_to_payment"