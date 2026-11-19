"""Phase 4 ledger and receipt supporting collections."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase4_enums import LedgerAdjustmentStatus


class StudentFinancialAccount(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    opening_balance: float = 0.0
    total_charges: float = 0.0
    total_credits: float = 0.0
    outstanding_balance: float = 0.0
    overdue_balance: float = 0.0
    advance_unallocated: float = 0.0
    programme_code: str | None = None
    department_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_financial_accounts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_student_financial_account",
            ),
        ]


class StudentLedgerPostingHistory(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    ledger_entry_id: str
    posting_key: str
    entry_type: str
    source_reference: str
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_ledger_posting_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("posting_key", ASCENDING)],
                unique=True,
                name="unique_ledger_posting_history",
            ),
        ]


class StudentLedgerAdjustment(Document):
    tenant_id: PydanticObjectId
    adjustment_id: str
    student_user_id: PydanticObjectId
    original_entry_id: str | None = None
    status: LedgerAdjustmentStatus = LedgerAdjustmentStatus.DRAFT
    reason: str
    debit: float = 0.0
    credit: float = 0.0
    reversal_entry_id: str | None = None
    correction_entry_id: str | None = None
    requested_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_ledger_adjustments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("adjustment_id", ASCENDING)], unique=True, name="unique_ledger_adjustment"),
        ]


class StudentAdvancePayment(Document):
    tenant_id: PydanticObjectId
    advance_id: str
    student_user_id: PydanticObjectId
    amount: float = Field(ge=0)
    unallocated_amount: float = Field(ge=0)
    transaction_id: str | None = None
    receipt_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_advance_payments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("advance_id", ASCENDING)], unique=True, name="unique_advance_payment"),
        ]


class StudentAdvanceAllocation(Document):
    tenant_id: PydanticObjectId
    allocation_id: str
    advance_id: str
    invoice_id: str
    amount: float = Field(ge=0)
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_advance_allocations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("allocation_id", ASCENDING)], unique=True, name="unique_advance_alloc"),
        ]


class StudentLedgerReconciliationRecord(Document):
    tenant_id: PydanticObjectId
    reconciliation_id: str
    student_user_id: PydanticObjectId | None = None
    exception_type: str
    detail: str
    resolved: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_ledger_reconciliation_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("reconciliation_id", ASCENDING)], unique=True, name="unique_ledger_recon"),
        ]


class PaymentReceiptVersion(Document):
    tenant_id: PydanticObjectId
    receipt_id: str
    version: int
    snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_receipt_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("receipt_id", ASCENDING), ("version", ASCENDING)],
                unique=True,
                name="unique_receipt_version",
            ),
        ]


class PaymentReceiptCancellation(Document):
    tenant_id: PydanticObjectId
    cancellation_id: str
    receipt_id: str
    reason: str
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_receipt_cancellations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("cancellation_id", ASCENDING)], unique=True, name="unique_receipt_cancel"),
        ]


class PaymentReceiptNumberSequence(Document):
    tenant_id: PydanticObjectId
    fiscal_year: str
    last_value: int = 0
    prefix: str = "RCT"
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_receipt_number_sequences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("fiscal_year", ASCENDING)],
                unique=True,
                name="unique_receipt_sequence",
            ),
        ]


class PaymentReceiptDocumentHistory(Document):
    tenant_id: PydanticObjectId
    receipt_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_receipt_document_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("receipt_id", ASCENDING), ("created_at", DESCENDING)], name="receipt_doc_history"),
        ]