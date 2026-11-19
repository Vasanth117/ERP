"""Phase 9 General Ledger and Budget enumerations."""

from enum import Enum


class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"


class AccountClassification(str, Enum):
    CURRENT_ASSET = "current_asset"
    FIXED_ASSET = "fixed_asset"
    BANK = "bank"
    CASH = "cash"
    STUDENT_RECEIVABLE = "student_receivable"
    VENDOR_PAYABLE = "vendor_payable"
    FEE_INCOME = "fee_income"
    OTHER_INCOME = "other_income"
    PAYROLL_EXPENSE = "payroll_expense"
    ADMIN_EXPENSE = "admin_expense"
    OPERATIONAL_EXPENSE = "operational_expense"
    TAX_LIABILITY = "tax_liability"
    OTHER = "other"


class NormalBalance(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class JournalStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"
    REVERSED = "reversed"


class JournalSource(str, Enum):
    MANUAL = "manual"
    SYSTEM = "system"
    ADJUSTMENT = "adjustment"
    OPENING = "opening"
    CLOSING = "closing"
    REVERSAL = "reversal"


class MappingEventType(str, Enum):
    FEE_INVOICE = "fee_invoice"
    VERIFIED_PAYMENT = "verified_payment"
    SCHOLARSHIP_CREDIT = "scholarship_credit"
    CONCESSION_CREDIT = "concession_credit"
    FEE_WAIVER = "fee_waiver"
    LATE_FEE = "late_fee"
    LATE_FEE_WAIVER = "late_fee_waiver"
    REFUND = "refund"
    PAYMENT_REVERSAL = "payment_reversal"
    ADJUSTMENT = "adjustment"


class FinanceBudgetStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    REJECTED = "rejected"
    CLOSED = "closed"


class BudgetCommitmentStatus(str, Enum):
    OPEN = "open"
    CONSUMED = "consumed"
    RELEASED = "released"