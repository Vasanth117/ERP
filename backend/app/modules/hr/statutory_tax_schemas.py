"""Statutory payroll and tax API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import (
    HrStatutoryCalcBasis,
    HrStatutoryComponentKind,
    HrTaxDeclarationStatus,
    HrTaxFinancialYearStatus,
    HrTaxProofStatus,
)
from app.modules.hr.statutory_tax_models import (
    EmployeeTaxDeclaration,
    EmployeeTaxProfile,
    EmployeeTaxProof,
    HrStatutoryComponent,
    HrStatutoryRuleVersion,
    HrTaxFinancialYear,
    HrTaxRegimeConfiguration,
    HrTaxSlab,
)


class StatutoryComponentUpsert(BaseModel):
    component_code: str = Field(min_length=1, max_length=64)
    display_name: str
    component_kind: HrStatutoryComponentKind
    statutory_ref: str = Field(min_length=1, max_length=128)
    employee_categories: list[str] = Field(default_factory=list)
    calculation_basis: HrStatutoryCalcBasis = HrStatutoryCalcBasis.BASIC
    eligible_salary_components: list[str] = Field(default_factory=list)
    is_active: bool = True


class StatutoryComponentRead(BaseModel):
    id: str
    component_code: str
    display_name: str
    component_kind: str
    statutory_ref: str
    is_active: bool
    active_rule_version: int

    @classmethod
    def from_doc(cls, doc: HrStatutoryComponent) -> "StatutoryComponentRead":
        return cls(
            id=str(doc.id),
            component_code=doc.component_code,
            display_name=doc.display_name,
            component_kind=doc.component_kind.value,
            statutory_ref=doc.statutory_ref,
            is_active=doc.is_active,
            active_rule_version=doc.active_rule_version,
        )


class StatutoryRuleVersionCreate(BaseModel):
    component_id: str
    effective_from: date
    effective_to: date | None = None
    employee_rate_percent: str = "0"
    employer_rate_percent: str = "0"
    fixed_amount: str | None = None
    threshold_min: str | None = None
    threshold_max: str | None = None
    exemptions: dict[str, Any] = Field(default_factory=dict)
    rounding_rule: str = "half_up_2dp"


class StatutoryRuleVersionRead(BaseModel):
    id: str
    component_code: str
    version_number: int
    effective_from: date
    effective_to: date | None
    employee_rate_percent: str
    employer_rate_percent: str

    @classmethod
    def from_doc(cls, doc: HrStatutoryRuleVersion) -> "StatutoryRuleVersionRead":
        return cls(
            id=str(doc.id),
            component_code=doc.component_code,
            version_number=doc.version_number,
            effective_from=doc.effective_from,
            effective_to=doc.effective_to,
            employee_rate_percent=doc.employee_rate_percent,
            employer_rate_percent=doc.employer_rate_percent,
        )


class TaxFinancialYearUpsert(BaseModel):
    fy_code: str
    label: str
    start_date: date
    end_date: date
    assessment_year: str
    status: HrTaxFinancialYearStatus = HrTaxFinancialYearStatus.DRAFT


class TaxFinancialYearRead(BaseModel):
    id: str
    fy_code: str
    label: str
    start_date: date
    end_date: date
    assessment_year: str
    status: str
    version: int

    @classmethod
    def from_doc(cls, doc: HrTaxFinancialYear) -> "TaxFinancialYearRead":
        return cls(
            id=str(doc.id),
            fy_code=doc.fy_code,
            label=doc.label,
            start_date=doc.start_date,
            end_date=doc.end_date,
            assessment_year=doc.assessment_year,
            status=doc.status.value,
            version=doc.version,
        )


class TaxRegimeUpsert(BaseModel):
    financial_year_id: str
    regime_code: str
    display_name: str
    is_default: bool = False
    effective_from: date
    effective_to: date | None = None
    rules: dict[str, Any] = Field(default_factory=dict)


class TaxRegimeRead(BaseModel):
    id: str
    financial_year_id: str
    regime_code: str
    display_name: str
    version: int

    @classmethod
    def from_doc(cls, doc: HrTaxRegimeConfiguration) -> "TaxRegimeRead":
        return cls(
            id=str(doc.id),
            financial_year_id=str(doc.financial_year_id),
            regime_code=doc.regime_code,
            display_name=doc.display_name,
            version=doc.version,
        )


class TaxSlabUpsert(BaseModel):
    regime_configuration_id: str
    slab_order: int
    income_from: str
    income_to: str | None = None
    rate_percent: str
    rebate_amount: str | None = None
    effective_from: date
    effective_to: date | None = None


class TaxSlabRead(BaseModel):
    id: str
    slab_order: int
    income_from: str
    income_to: str | None
    rate_percent: str

    @classmethod
    def from_doc(cls, doc: HrTaxSlab) -> "TaxSlabRead":
        return cls(
            id=str(doc.id),
            slab_order=doc.slab_order,
            income_from=doc.income_from,
            income_to=doc.income_to,
            rate_percent=doc.rate_percent,
        )


class EmployeeTaxProfileUpsert(BaseModel):
    employee_user_id: str
    pan_number: str | None = None
    aadhaar_masked: str | None = None
    uan_number: str | None = None
    esi_number: str | None = None
    preferred_regime_code: str | None = None


class EmployeeTaxProfileRead(BaseModel):
    employee_user_id: str
    pan_number: str | None
    preferred_regime_code: str | None

    @classmethod
    def from_doc(cls, doc: EmployeeTaxProfile) -> "EmployeeTaxProfileRead":
        return cls(
            employee_user_id=str(doc.employee_user_id),
            pan_number=doc.pan_number,
            preferred_regime_code=doc.preferred_regime_code,
        )


class TaxDeclarationUpsert(BaseModel):
    financial_year_id: str
    regime_code: str
    declaration_lines: dict[str, Any] = Field(default_factory=dict)
    employee_note: str | None = None


class TaxDeclarationReview(BaseModel):
    action: str = Field(pattern="^(approve|reject|return)$")
    reviewer_note: str | None = None
    approved_snapshot: dict[str, Any] = Field(default_factory=dict)


class TaxDeclarationRead(BaseModel):
    id: str
    employee_user_id: str
    fy_code: str
    regime_code: str
    status: HrTaxDeclarationStatus
    total_declared_deductions: str
    submitted_at: datetime | None

    @classmethod
    def from_doc(cls, doc: EmployeeTaxDeclaration) -> "TaxDeclarationRead":
        return cls(
            id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            fy_code=doc.fy_code,
            regime_code=doc.regime_code,
            status=doc.status,
            total_declared_deductions=doc.total_declared_deductions,
            submitted_at=doc.submitted_at,
        )


class TaxProofUpsert(BaseModel):
    proof_category: str
    claimed_amount: str
    document_ref: str | None = None
    storage_key: str | None = None


class TaxProofReview(BaseModel):
    action: str = Field(pattern="^(verify|reject|return)$")
    verified_amount: str | None = None
    reviewer_note: str | None = None


class TaxProofRead(BaseModel):
    id: str
    proof_category: str
    claimed_amount: str
    status: HrTaxProofStatus
    verified_amount: str | None

    @classmethod
    def from_doc(cls, doc: EmployeeTaxProof) -> "TaxProofRead":
        return cls(
            id=str(doc.id),
            proof_category=doc.proof_category,
            claimed_amount=doc.claimed_amount,
            status=doc.status,
            verified_amount=doc.verified_amount,
        )


class ComplianceReport(BaseModel):
    missing_tax_declarations: int = 0
    pending_proofs: int = 0
    rejected_proofs: int = 0
    open_financial_years: list[str] = Field(default_factory=list)
    employee_statutory_summary: dict[str, int] = Field(default_factory=dict)