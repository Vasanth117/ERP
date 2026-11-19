"""Statutory payroll, tax configuration and employee tax declarations."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import (
    HrSelfServiceRequestStatus,
    HrSelfServiceRequestType,
    HrStatutoryCalcBasis,
    HrStatutoryComponentKind,
    HrTaxDeclarationStatus,
    HrTaxFinancialYearStatus,
    HrTaxProofStatus,
)


class HrStatutoryComponent(Document):
    tenant_id: PydanticObjectId
    component_code: str = Field(max_length=64)
    display_name: str = Field(max_length=200)
    component_kind: HrStatutoryComponentKind = HrStatutoryComponentKind.EMPLOYEE_DEDUCTION
    statutory_ref: str = Field(max_length=128)
    employee_categories: list[str] = Field(default_factory=list)
    calculation_basis: HrStatutoryCalcBasis = HrStatutoryCalcBasis.BASIC
    eligible_salary_components: list[str] = Field(default_factory=list)
    is_active: bool = True
    active_rule_version: int = 1
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_statutory_components"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("component_code", ASCENDING)],
                unique=True,
                name="unique_statutory_component",
            ),
            IndexModel([("tenant_id", ASCENDING), ("statutory_ref", ASCENDING)], name="statutory_by_ref"),
        ]


class HrStatutoryRuleVersion(Document):
    tenant_id: PydanticObjectId
    component_id: PydanticObjectId
    component_code: str = Field(max_length=64)
    version_number: int = 1
    effective_from: date
    effective_to: date | None = None
    employee_rate_percent: str = "0"
    employer_rate_percent: str = "0"
    fixed_amount: str | None = None
    threshold_min: str | None = None
    threshold_max: str | None = None
    exemptions: dict[str, Any] = Field(default_factory=dict)
    rounding_rule: str = "half_up_2dp"
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_statutory_rule_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("component_id", ASCENDING), ("version_number", ASCENDING)],
                unique=True,
                name="unique_statutory_rule_version",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("component_code", ASCENDING), ("effective_from", DESCENDING)],
                name="statutory_rules_by_effective",
            ),
        ]


class HrTaxFinancialYear(Document):
    tenant_id: PydanticObjectId
    fy_code: str = Field(max_length=32)
    label: str = Field(max_length=120)
    start_date: date
    end_date: date
    assessment_year: str = Field(max_length=32)
    status: HrTaxFinancialYearStatus = HrTaxFinancialYearStatus.DRAFT
    version: int = 1
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_tax_financial_years"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("fy_code", ASCENDING)], unique=True, name="unique_tax_fy"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="tax_fy_status"),
        ]


class HrTaxRegimeConfiguration(Document):
    tenant_id: PydanticObjectId
    financial_year_id: PydanticObjectId
    regime_code: str = Field(max_length=64)
    display_name: str = Field(max_length=120)
    is_default: bool = False
    effective_from: date
    effective_to: date | None = None
    rules: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_tax_regime_configurations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("financial_year_id", ASCENDING), ("regime_code", ASCENDING), ("version", ASCENDING)],
                unique=True,
                name="unique_tax_regime_version",
            ),
        ]


class HrTaxSlab(Document):
    tenant_id: PydanticObjectId
    regime_configuration_id: PydanticObjectId
    slab_order: int
    income_from: str
    income_to: str | None = None
    rate_percent: str
    rebate_amount: str | None = None
    effective_from: date
    effective_to: date | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_tax_slabs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("regime_configuration_id", ASCENDING), ("slab_order", ASCENDING)],
                name="tax_slabs_order",
            ),
        ]


class EmployeeTaxProfile(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    pan_number: str | None = Field(default=None, max_length=16)
    aadhaar_masked: str | None = Field(default=None, max_length=16)
    uan_number: str | None = Field(default=None, max_length=32)
    esi_number: str | None = Field(default=None, max_length=32)
    preferred_regime_code: str | None = Field(default=None, max_length=64)
    confidential_tax: dict[str, Any] = Field(default_factory=dict)
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_tax_profiles"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING)],
                unique=True,
                name="unique_employee_tax_profile",
            ),
        ]


class EmployeeTaxDeclaration(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    financial_year_id: PydanticObjectId
    fy_code: str = Field(max_length=32)
    regime_code: str = Field(max_length=64)
    status: HrTaxDeclarationStatus = HrTaxDeclarationStatus.DRAFT
    declaration_lines: dict[str, Any] = Field(default_factory=dict)
    total_declared_deductions: str = "0"
    employee_note: str | None = Field(default=None, max_length=2000)
    reviewer_id: PydanticObjectId | None = None
    reviewer_note: str | None = Field(default=None, max_length=2000)
    approved_snapshot: dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_tax_declarations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("financial_year_id", ASCENDING)],
                unique=True,
                name="unique_tax_declaration_per_fy",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="tax_declaration_status"),
        ]


class EmployeeTaxProof(Document):
    tenant_id: PydanticObjectId
    declaration_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    proof_category: str = Field(max_length=64)
    claimed_amount: str
    document_ref: str | None = None
    storage_key: str | None = None
    status: HrTaxProofStatus = HrTaxProofStatus.PENDING
    verified_amount: str | None = None
    reviewer_id: PydanticObjectId | None = None
    reviewer_note: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_tax_proofs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("declaration_id", ASCENDING), ("proof_category", ASCENDING)],
                name="tax_proofs_by_declaration",
            ),
        ]


class EmployeeTaxReviewHistory(Document):
    tenant_id: PydanticObjectId
    declaration_id: PydanticObjectId
    proof_id: PydanticObjectId | None = None
    action: str = Field(max_length=64)
    from_status: str | None = None
    to_status: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_tax_review_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("declaration_id", ASCENDING), ("created_at", DESCENDING)], name="tax_review_history"),
        ]


class EmployeeSelfServiceRequest(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    request_type: HrSelfServiceRequestType
    status: HrSelfServiceRequestStatus = HrSelfServiceRequestStatus.DRAFT
    title: str = Field(max_length=200)
    payload: dict[str, Any] = Field(default_factory=dict)
    employee_note: str | None = Field(default=None, max_length=2000)
    reviewer_id: PydanticObjectId | None = None
    reviewer_note: str | None = Field(default=None, max_length=2000)
    resolution: dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_self_service_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("status", ASCENDING)],
                name="self_service_requests_by_employee",
            ),
        ]


class EmployeeSelfServiceRequestHistory(Document):
    tenant_id: PydanticObjectId
    request_id: PydanticObjectId
    action: str = Field(max_length=64)
    from_status: str | None = None
    to_status: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_self_service_request_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING), ("created_at", DESCENDING)], name="self_service_request_history"),
        ]