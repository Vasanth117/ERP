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
    demand_id: str | None = None
    amount: float = Field(ge=0)
    issued_at: datetime
    due_date: date
    published: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_invoices"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("invoice_id", ASCENDING)],
                unique=True,
                name="unique_fee_invoice",
            ),
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
        ]


class PaymentTransaction(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    transaction_id: str
    idempotency_key: str
    demand_id: str | None = None
    amount: float = Field(ge=0)
    currency: str = "INR"
    status: PaymentTransactionStatus = PaymentTransactionStatus.INITIATED
    gateway: str = "stub"
    gateway_reference: str | None = None
    offline_reference: str | None = Field(default=None, max_length=120)
    payment_mode: str = Field(default="online", max_length=16)
    webhook_verified: bool = False
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
    transaction_id: str
    amount: float = Field(ge=0)
    issued_at: datetime
    storage_token: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_receipts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("receipt_id", ASCENDING)],
                unique=True,
                name="unique_payment_receipt",
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
    title: str
    description: str | None = None
    applications_open: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "scholarship_programs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("programme_id", ASCENDING)],
                unique=True,
                name="unique_scholarship_program",
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
    amount: float = Field(ge=0)
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
