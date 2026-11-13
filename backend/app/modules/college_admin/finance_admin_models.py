"""College admin finance administration collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.finance.finance_enums import RefundStatus


class FinancialPeriodStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class InstitutionFeeStructure(Document):
    """Admin fee structure; syncs `student_fee_structures`."""

    tenant_id: PydanticObjectId
    structure_id: str
    programme_code: str
    academic_year_label: str
    semester_label: str
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    total_amount: float = Field(ge=0)
    authoritative_structure_id: PydanticObjectId | None = None
    published: bool = False
    version: int = 1
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_fee_structures"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("structure_id", ASCENDING)],
                unique=True,
                name="unique_institution_fee_structure",
            ),
        ]


class StudentFeeAssessment(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    assessment_id: str
    structure_id: str
    academic_year_label: str
    semester_label: str
    assessed_amount: float = Field(ge=0)
    concession_amount: float = Field(default=0, ge=0)
    net_amount: float = Field(ge=0)
    demand_id: str | None = None
    invoice_id: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_assessments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("assessment_id", ASCENDING)],
                unique=True,
                name="unique_fee_assessment",
            ),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING)], name="assessments_by_student"),
        ]


class FinancialPeriod(Document):
    tenant_id: PydanticObjectId
    period_code: str
    label: str
    start_date: date
    end_date: date
    status: FinancialPeriodStatus = FinancialPeriodStatus.OPEN
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "financial_periods"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("period_code", ASCENDING)],
                unique=True,
                name="unique_financial_period",
            ),
        ]


class PaymentReconciliationRecord(Document):
    tenant_id: PydanticObjectId
    transaction_id: str
    gateway_reference: str | None = None
    reconciled: bool = False
    discrepancy_note: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_reconciliation_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("transaction_id", ASCENDING)],
                unique=True,
                name="unique_reconciliation_per_tx",
            ),
        ]


class FinancialApprovalRecord(Document):
    tenant_id: PydanticObjectId
    scope: str
    resource_type: str
    resource_id: str
    decision: str
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "financial_approval_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("scope", ASCENDING), ("created_at", DESCENDING)], name="financial_approvals"),
        ]


class RefundRequest(Document):
    """Admin refund workflow overlay on `refund_records`."""

    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    refund_id: str
    refund_record_id: PydanticObjectId | None = None
    amount: float = Field(ge=0)
    status: RefundStatus = RefundStatus.REQUESTED
    requires_approval: bool = True
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "refund_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("refund_id", ASCENDING)], unique=True, name="unique_refund_request"),
        ]
