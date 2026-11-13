"""Finance administration API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.finance_admin_models import FinancialPeriodStatus, InstitutionFeeStructure
from app.modules.finance.finance_enums import RefundStatus


class FeeStructureUpsert(BaseModel):
    structure_id: str
    programme_code: str
    academic_year_label: str
    semester_label: str
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    total_amount: float = Field(ge=0)


class FeeStructureRead(BaseModel):
    structure_id: str
    programme_code: str
    total_amount: float
    published: bool
    version: int

    @classmethod
    def from_document(cls, doc: InstitutionFeeStructure) -> "FeeStructureRead":
        return cls(
            structure_id=doc.structure_id,
            programme_code=doc.programme_code,
            total_amount=doc.total_amount,
            published=doc.published,
            version=doc.version,
        )


class FeeAssessmentCreate(BaseModel):
    student_user_id: str
    structure_id: str
    academic_year_label: str
    semester_label: str
    concession_amount: float = 0


class OfflineCollectionCreate(BaseModel):
    student_user_id: str
    demand_id: str
    amount: float = Field(ge=0)
    idempotency_key: str
    offline_reference: str


class RefundDecision(BaseModel):
    refund_id: str
    decision: RefundStatus
    note: str | None = None


class ConcessionCreate(BaseModel):
    student_user_id: str
    title: str
    amount: float = Field(ge=0)
    percent: float | None = Field(default=None, ge=0, le=100)


class FinancialPeriodUpsert(BaseModel):
    period_code: str
    label: str
    start_date: date
    end_date: date


class ReconciliationConfirm(BaseModel):
    transaction_id: str
    gateway_reference: str | None = None
    discrepancy_note: str | None = None
