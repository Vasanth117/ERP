"""Phase 2 assessment and invoice supporting collections."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase2_enums import FeeAssessmentExceptionCode, InvoiceAdjustmentType


class StudentFeeAssessmentItem(Document):
    tenant_id: PydanticObjectId
    assessment_id: str
    item_id: str
    fee_category_code: str
    description: str
    structure_id: str
    component_id: str | None = None
    original_amount: float = Field(ge=0)
    adjustment_amount: float = Field(default=0)
    tax_reference: str | None = None
    net_amount: float = Field(ge=0)
    mandatory: bool = True
    optional_selected: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_assessment_items"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("assessment_id", ASCENDING), ("item_id", ASCENDING)],
                unique=True,
                name="unique_assessment_item",
            ),
        ]


class StudentFeeAssessmentHistory(Document):
    tenant_id: PydanticObjectId
    assessment_id: str
    action: str
    from_status: str | None = None
    to_status: str | None = None
    actor_id: PydanticObjectId
    note: str | None = None
    snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_assessment_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("assessment_id", ASCENDING), ("created_at", DESCENDING)],
                name="assessment_history_trail",
            ),
        ]


class StudentFeeAssessmentException(Document):
    tenant_id: PydanticObjectId
    batch_id: str | None = None
    student_user_id: PydanticObjectId | None = None
    assessment_id: str | None = None
    code: FeeAssessmentExceptionCode
    message: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_assessment_exceptions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("batch_id", ASCENDING)], name="assessment_exceptions_batch"),
        ]


class StudentInvoiceItem(Document):
    tenant_id: PydanticObjectId
    invoice_id: str
    item_id: str
    fee_category_code: str
    description: str
    assessment_id: str | None = None
    structure_id: str | None = None
    original_amount: float = Field(ge=0)
    adjustment_amount: float = Field(default=0)
    tax_reference: str | None = None
    net_amount: float = Field(ge=0)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_invoice_items"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("invoice_id", ASCENDING), ("item_id", ASCENDING)],
                unique=True,
                name="unique_invoice_item",
            ),
        ]


class StudentInvoiceHistory(Document):
    tenant_id: PydanticObjectId
    invoice_id: str
    action: str
    from_status: str | None = None
    to_status: str | None = None
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_invoice_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("invoice_id", ASCENDING), ("created_at", DESCENDING)],
                name="invoice_history_trail",
            ),
        ]


class StudentCreditNote(Document):
    tenant_id: PydanticObjectId
    credit_note_id: str
    invoice_id: str
    student_user_id: PydanticObjectId
    amount: float = Field(ge=0)
    reason: str
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_credit_notes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("credit_note_id", ASCENDING)],
                unique=True,
                name="unique_credit_note",
            ),
        ]


class StudentDebitNote(Document):
    tenant_id: PydanticObjectId
    debit_note_id: str
    invoice_id: str
    student_user_id: PydanticObjectId
    amount: float = Field(ge=0)
    reason: str
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_debit_notes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("debit_note_id", ASCENDING)],
                unique=True,
                name="unique_debit_note",
            ),
        ]


class InvoiceAdjustmentHistory(Document):
    tenant_id: PydanticObjectId
    adjustment_id: str
    invoice_id: str
    adjustment_type: InvoiceAdjustmentType
    amount: float = Field(ge=0)
    related_document_id: str | None = None
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "invoice_adjustment_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("adjustment_id", ASCENDING)],
                unique=True,
                name="unique_invoice_adjustment",
            ),
        ]


class FinanceInvoiceSequence(Document):
    """Per-tenant atomic invoice number sequence."""

    tenant_id: PydanticObjectId
    fiscal_year: str
    last_value: int = 0
    prefix: str = "INV"
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_invoice_sequences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("fiscal_year", ASCENDING)],
                unique=True,
                name="unique_invoice_sequence",
            ),
        ]