"""Fee category and structure API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.accounts_finance.enums import (
    BillingFrequency,
    FeeCategoryClassification,
    FeeStructureApprovalAction,
    FeeStructureLifecycleStatus,
    RefundabilityClass,
)
from app.modules.accounts_finance.models import FinanceFeeCategory, FinanceFeeStructure, FinanceFeeStructureComponent
from app.modules.accounts_finance.money import round_money


class FeeCategoryUpsert(BaseModel):
    fee_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    classification: FeeCategoryClassification = FeeCategoryClassification.OTHER
    programme_codes: list[str] = Field(default_factory=list)
    student_categories: list[str] = Field(default_factory=list)
    mandatory: bool = True
    optional_flag: bool = False
    refundability: RefundabilityClass = RefundabilityClass.NON_REFUNDABLE
    tax_reference: str | None = None
    active: bool = True

    @field_validator("fee_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class FeeCategoryRead(BaseModel):
    fee_code: str
    name: str
    description: str | None
    classification: FeeCategoryClassification
    programme_codes: list[str]
    student_categories: list[str]
    mandatory: bool
    optional_flag: bool
    refundability: RefundabilityClass
    tax_reference: str | None
    active: bool
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: FinanceFeeCategory) -> "FeeCategoryRead":
        return cls(
            fee_code=doc.fee_code,
            name=doc.name,
            description=doc.description,
            classification=doc.classification,
            programme_codes=doc.programme_codes,
            student_categories=doc.student_categories,
            mandatory=doc.mandatory,
            optional_flag=doc.optional_flag,
            refundability=doc.refundability,
            tax_reference=doc.tax_reference,
            active=doc.active,
            updated_at=doc.updated_at,
        )


class FeeStructureComponentInput(BaseModel):
    component_id: str | None = None
    fee_category_code: str
    amount: float = Field(ge=0)
    due_date: date | None = None
    billing_frequency: BillingFrequency = BillingFrequency.ONE_TIME
    student_group: str | None = None
    mandatory: bool = True
    optional_flag: bool = False
    refundability: RefundabilityClass | None = None
    installment_eligible: bool = False
    effective_from: date | None = None
    effective_to: date | None = None

    @field_validator("amount")
    @classmethod
    def money_precision(cls, value: float) -> float:
        return round_money(value)


class FeeStructureCreate(BaseModel):
    structure_id: str = Field(min_length=2, max_length=64)
    template_key: str | None = None
    academic_year_label: str
    semester_label: str
    programme_code: str
    department_id: str | None = None
    batch_year: str | None = None
    student_category: str | None = None
    campus_id: str | None = None
    admission_type: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    installment_eligible: bool = False
    components: list[FeeStructureComponentInput] = Field(min_length=1)


class FeeStructureRead(BaseModel):
    structure_id: str
    template_key: str | None
    academic_year_label: str
    semester_label: str
    programme_code: str
    department_id: str | None
    batch_year: str | None
    student_category: str | None
    campus_id: str | None
    admission_type: str | None
    status: FeeStructureLifecycleStatus
    version: int
    effective_from: date | None
    effective_to: date | None
    total_amount: float
    installment_eligible: bool
    components: list[dict]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_parts(
        cls,
        doc: FinanceFeeStructure,
        components: list[FinanceFeeStructureComponent],
    ) -> "FeeStructureRead":
        return cls(
            structure_id=doc.structure_id,
            template_key=doc.template_key,
            academic_year_label=doc.academic_year_label,
            semester_label=doc.semester_label,
            programme_code=doc.programme_code,
            department_id=str(doc.department_id) if doc.department_id else None,
            batch_year=doc.batch_year,
            student_category=doc.student_category,
            campus_id=str(doc.campus_id) if doc.campus_id else None,
            admission_type=doc.admission_type,
            status=doc.status,
            version=doc.version,
            effective_from=doc.effective_from,
            effective_to=doc.effective_to,
            total_amount=doc.total_amount,
            installment_eligible=doc.installment_eligible,
            components=[
                {
                    "component_id": c.component_id,
                    "fee_category_code": c.fee_category_code,
                    "amount": c.amount,
                    "due_date": c.due_date.isoformat() if c.due_date else None,
                    "billing_frequency": c.billing_frequency.value,
                    "mandatory": c.mandatory,
                    "installment_eligible": c.installment_eligible,
                }
                for c in components
            ],
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class FeeStructureRevision(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    effective_date: date
    components: list[FeeStructureComponentInput] = Field(min_length=1)
    effective_from: date | None = None
    effective_to: date | None = None
    installment_eligible: bool | None = None


class FeeStructureTransition(BaseModel):
    action: FeeStructureApprovalAction
    note: str | None = Field(default=None, max_length=500)
    scheduled_activate_at: date | None = None


class FeeStructureTemplateCreate(BaseModel):
    template_key: str = Field(min_length=2, max_length=64)
    structure_id: str = Field(min_length=2, max_length=64)
    academic_year_label: str
    semester_label: str
    programme_code: str
    components: list[FeeStructureComponentInput] = Field(min_length=1)