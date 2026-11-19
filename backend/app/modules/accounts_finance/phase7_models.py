"""Phase 7 refunds, reversals and payment reconciliation."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase7_enums import ReconciliationMatchStatus, ReconciliationPeriodStatus, RefundWorkflowStatus, ReversalRequestStatus


class StudentRefundRequest(Document):
    tenant_id: PydanticObjectId
    refund_request_id: str
    student_user_id: PydanticObjectId
    transaction_id: str
    invoice_id: str | None = None
    receipt_id: str | None = None
    category: str
    requested_amount: float = Field(ge=0)
    approved_amount: float | None = None
    reason: str
    document_refs: list[str] = Field(default_factory=list)
    expected_refund_method: str | None = None
    status: RefundWorkflowStatus = RefundWorkflowStatus.SUBMITTED
    requested_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    payout_reference: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_refund_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("refund_request_id", ASCENDING)], unique=True, name="unique_refund_request"),
            IndexModel([("tenant_id", ASCENDING), ("transaction_id", ASCENDING)], name="refunds_by_tx"),
        ]


class StudentRefundApprovalHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    refund_request_id: str
    action: str
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_refund_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_refund_approval_hist"),
        ]


class StudentRefundTransaction(Document):
    tenant_id: PydanticObjectId
    refund_tx_id: str
    refund_request_id: str
    transaction_id: str
    amount: float = Field(ge=0)
    payout_reference: str | None = None
    ledger_entry_id: str | None = None
    posting_key: str
    status: str = "processing"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_refund_transactions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("refund_tx_id", ASCENDING)], unique=True, name="unique_refund_tx"),
            IndexModel([("tenant_id", ASCENDING), ("posting_key", ASCENDING)], unique=True, name="unique_refund_posting"),
        ]


class StudentRefundReference(Document):
    tenant_id: PydanticObjectId
    reference_id: str
    refund_request_id: str
    ref_type: str
    ref_value: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_refund_references"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("reference_id", ASCENDING)], unique=True, name="unique_refund_reference"),
        ]


class StudentPaymentReversalRequest(Document):
    tenant_id: PydanticObjectId
    reversal_request_id: str
    student_user_id: PydanticObjectId
    transaction_id: str
    receipt_id: str | None = None
    amount: float = Field(ge=0)
    reason: str
    status: ReversalRequestStatus = ReversalRequestStatus.SUBMITTED
    requested_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    ledger_entry_id: str | None = None
    posting_key: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_payment_reversal_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("reversal_request_id", ASCENDING)], unique=True, name="unique_reversal_request"),
        ]


class StudentPaymentReversalHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    reversal_request_id: str
    action: str
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_payment_reversal_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_reversal_hist"),
        ]


class PaymentReconciliationPeriod(Document):
    tenant_id: PydanticObjectId
    period_id: str
    label: str
    period_start: date
    period_end: date
    status: ReconciliationPeriodStatus = ReconciliationPeriodStatus.NOT_STARTED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_reconciliation_periods"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("period_id", ASCENDING)], unique=True, name="unique_recon_period"),
        ]


class PaymentReconciliationBatch(Document):
    tenant_id: PydanticObjectId
    batch_id: str
    period_id: str
    source_type: str
    status: ReconciliationPeriodStatus = ReconciliationPeriodStatus.IMPORTED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_reconciliation_batches"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("batch_id", ASCENDING)], unique=True, name="unique_recon_batch"),
        ]


class PaymentReconciliationImport(Document):
    tenant_id: PydanticObjectId
    import_id: str
    batch_id: str
    file_name: str | None = None
    format: str = "csv"
    row_count: int = 0
    quarantined_count: int = 0
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_reconciliation_imports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("import_id", ASCENDING)], unique=True, name="unique_recon_import"),
        ]


class PaymentReconciliationSourceRecord(Document):
    tenant_id: PydanticObjectId
    source_record_id: str
    batch_id: str
    external_reference: str | None = None
    gateway_reference: str | None = None
    bank_reference: str | None = None
    transaction_date: date | None = None
    amount: float = Field(ge=0)
    currency: str = "INR"
    payment_method: str | None = None
    settlement_reference: str | None = None
    gross_amount: float | None = None
    provider_fee: float | None = None
    net_settlement: float | None = None
    quarantined: bool = False
    raw: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_reconciliation_source_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("source_record_id", ASCENDING)], unique=True, name="unique_recon_source"),
            IndexModel([("tenant_id", ASCENDING), ("batch_id", ASCENDING)], name="source_by_batch"),
        ]


class PaymentReconciliationMatch(Document):
    tenant_id: PydanticObjectId
    match_id: str
    batch_id: str
    source_record_id: str
    erp_transaction_id: str | None = None
    match_status: ReconciliationMatchStatus = ReconciliationMatchStatus.SUGGESTED
    match_rule: str | None = None
    amount_delta: float = 0.0
    confirmed_by: PydanticObjectId | None = None
    remark: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_reconciliation_matches"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("match_id", ASCENDING)], unique=True, name="unique_recon_match"),
            IndexModel([("tenant_id", ASCENDING), ("source_record_id", ASCENDING)], unique=True, name="one_match_per_source"),
        ]


class PaymentReconciliationException(Document):
    tenant_id: PydanticObjectId
    exception_id: str
    batch_id: str
    exception_type: str
    detail: str
    source_record_id: str | None = None
    erp_transaction_id: str | None = None
    resolved: bool = False
    resolved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_reconciliation_exceptions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("exception_id", ASCENDING)], unique=True, name="unique_recon_exception"),
        ]


class PaymentSettlementRecord(Document):
    tenant_id: PydanticObjectId
    settlement_id: str
    batch_id: str
    settlement_reference: str
    settlement_date: date | None = None
    gross_amount: float = Field(ge=0)
    provider_fee: float = 0.0
    tax_on_fee: float = 0.0
    net_amount: float = Field(ge=0)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_settlement_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("settlement_id", ASCENDING)], unique=True, name="unique_settlement"),
        ]


class PaymentReconciliationHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    batch_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_reconciliation_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_recon_history"),
            IndexModel([("tenant_id", ASCENDING), ("batch_id", ASCENDING), ("created_at", DESCENDING)], name="recon_hist_by_batch"),
        ]