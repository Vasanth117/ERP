"""Central finance collections (authoritative)."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.finance.finance_enums import (
    FeeDemandStatus,
    PaymentTransactionStatus,
    RefundStatus,
    ScholarshipApplicationStatus,
)


class StudentFeeStructure(Document):
    tenant_id: PydanticObjectId
    programme_code: str
    academic_year_label: str
    semester_label: str
    structure_id: str
    line_items: list[dict] = Field(default_factory=list)
    total_amount: float = Field(ge=0)
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_structures"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("structure_id", ASCENDING)],
                unique=True,
                name="unique_fee_structure",
            ),
        ]


class StudentFeeDemand(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    demand_id: str
    academic_year_label: str
    semester_label: str
    description: str
    amount: float = Field(ge=0)
    due_date: date
    status: FeeDemandStatus = FeeDemandStatus.OPEN
    late_fee: float = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_demands"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("demand_id", ASCENDING)],
                unique=True,
                name="unique_fee_demand",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)],
                name="demands_by_student",
            ),
        ]


class StudentFeeInvoice(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    invoice_id: str
    invoice_number: str | None = None
    assessment_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    demand_id: str | None = None
    original_amount: float = Field(default=0, ge=0)
    amount: float = Field(ge=0)
    tax_reference: str | None = None
    invoice_status: str = Field(default="draft", max_length=32)
    billing_date: date | None = None
    issued_at: datetime
    due_date: date
    published: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_invoices"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("invoice_id", ASCENDING)],
                unique=True,
                name="unique_fee_invoice",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("invoice_number", ASCENDING)],
                unique=True,
                name="unique_invoice_number",
                partialFilterExpression={"invoice_number": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("invoice_status", ASCENDING)],
                name="invoices_by_student_status",
            ),
            IndexModel([("tenant_id", ASCENDING), ("assessment_id", ASCENDING)], name="invoices_by_assessment"),
        ]


class StudentFinancialLedgerEntry(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    entry_id: str
    entry_type: str
    description: str
    debit: float = Field(default=0, ge=0)
    credit: float = Field(default=0, ge=0)
    balance_after: float
    reference_id: str | None = None
    posting_key: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    invoice_id: str | None = None
    payment_transaction_id: str | None = None
    receipt_id: str | None = None
    transaction_status: str = "posted"
    narration: str | None = None
    posted_by: PydanticObjectId | None = None
    transaction_date: date | None = None
    posted_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_financial_ledger"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("entry_id", ASCENDING)],
                unique=True,
                name="unique_ledger_entry",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("posted_at", DESCENDING)],
                name="ledger_by_student",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("posting_key", ASCENDING)],
                unique=True,
                name="unique_ledger_posting_key",
                partialFilterExpression={"posting_key": {"$type": "string"}},
            ),
        ]


class PaymentTransaction(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    transaction_id: str
    idempotency_key: str
    demand_id: str | None = None
    invoice_id: str | None = None
    amount: float = Field(ge=0)
    currency: str = "INR"
    status: PaymentTransactionStatus = PaymentTransactionStatus.INITIATED
    gateway: str = "stub"
    gateway_reference: str | None = None
    offline_reference: str | None = Field(default=None, max_length=120)
    payment_mode: str = Field(default="online", max_length=16)
    webhook_verified: bool = False
    refunded_total: float = Field(default=0, ge=0)
    reversed_total: float = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_transactions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("transaction_id", ASCENDING)],
                unique=True,
                name="unique_payment_transaction",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_payment_idempotency",
            ),
        ]


class PaymentReceipt(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    receipt_id: str
    receipt_number: str | None = None
    transaction_id: str
    invoice_id: str | None = None
    demand_id: str | None = None
    amount: float = Field(ge=0)
    payment_mode: str | None = None
    receipt_type: str = "payment"
    remaining_balance: float | None = None
    fee_breakdown: list[dict] = Field(default_factory=list)
    academic_year_label: str | None = None
    semester_label: str | None = None
    receipt_status: str = "issued"
    published: bool = True
    issuer_user_id: PydanticObjectId | None = None
    superseded_by: str | None = None
    issued_at: datetime
    storage_token: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_receipts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("receipt_id", ASCENDING)],
                unique=True,
                name="unique_payment_receipt",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("transaction_id", ASCENDING)],
                unique=True,
                name="unique_receipt_per_transaction",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("receipt_number", ASCENDING)],
                unique=True,
                name="unique_receipt_number",
                partialFilterExpression={"receipt_number": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("issued_at", DESCENDING)],
                name="receipts_by_student",
            ),
        ]


class FeeInstallmentSchedule(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    schedule_id: str
    academic_year_label: str
    semester_label: str
    installments: list[dict] = Field(default_factory=list)
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_installment_schedules"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("schedule_id", ASCENDING)],
                unique=True,
                name="unique_installment_schedule",
            ),
        ]


class ScholarshipProgram(Document):
    tenant_id: PydanticObjectId
    programme_id: str
    scholarship_code: str | None = None
    title: str
    description: str | None = None
    funding_source: str | None = None
    scholarship_type: str | None = None
    academic_year_label: str | None = None
    applicable_programmes: list[str] = Field(default_factory=list)
    applicable_departments: list[str] = Field(default_factory=list)
    eligible_student_categories: list[str] = Field(default_factory=list)
    eligibility_conditions: dict = Field(default_factory=dict)
    max_award_amount: float | None = Field(default=None, ge=0)
    award_calculation_method: str | None = None
    fund_budget_reference: str | None = None
    max_awards: int | None = Field(default=None, ge=0)
    application_start: date | None = None
    application_deadline: date | None = None
    approval_requirements: list[str] = Field(default_factory=list)
    renewal_rules: dict = Field(default_factory=dict)
    effective_from: date | None = None
    effective_to: date | None = None
    program_status: str = "draft"
    applications_open: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "scholarship_programs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("programme_id", ASCENDING)],
                unique=True,
                name="unique_scholarship_program",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("scholarship_code", ASCENDING)],
                unique=True,
                name="unique_scholarship_code",
                partialFilterExpression={"scholarship_code": {"$type": "string"}},
            ),
        ]


class StudentScholarshipEligibility(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    programme_id: str
    eligible: bool = False
    reasons: list[str] = Field(default_factory=list)
    published: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_scholarship_eligibility"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("programme_id", ASCENDING),
                ],
                unique=True,
                name="unique_scholarship_eligibility",
            ),
        ]


class OfficialScholarshipApplication(Document):
    """Finance office record after student portal submission."""

    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    application_id: str
    programme_id: str
    status: ScholarshipApplicationStatus = ScholarshipApplicationStatus.SUBMITTED
    workflow_status: str = "application_submitted"
    document_refs: list[str] = Field(default_factory=list)
    requested_award_amount: float | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "official_scholarship_applications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING)],
                unique=True,
                name="unique_official_scholarship_app",
            ),
        ]


class FeeConcession(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    concession_id: str
    title: str
    amount: float = Field(ge=0)
    percent: float | None = Field(default=None, ge=0, le=100)
    policy_id: str | None = None
    award_id: str | None = None
    published: bool = True
    effective_from: date | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_concessions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("concession_id", ASCENDING)],
                unique=True,
                name="unique_fee_concession",
            ),
        ]


class RefundRecord(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    refund_id: str
    transaction_id: str | None = None
    refund_request_id: str | None = None
    invoice_id: str | None = None
    receipt_id: str | None = None
    amount: float = Field(ge=0)
    category: str | None = None
    status: RefundStatus = RefundStatus.REQUESTED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "refund_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("refund_id", ASCENDING)],
                unique=True,
                name="unique_refund_record",
            ),
        ]
