"""Benefits & claims API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.benefits_models import EmployeeBenefitClaim, EmployeeBenefitEnrollment, HrBenefitProgram
from app.modules.hr.enums import HrBenefitClaimStatus, HrBenefitEnrollmentStatus, HrBenefitProgramStatus


class BenefitsDashboard(BaseModel):
    total_programs: int = 0
    active_programs: int = 0
    eligible_employees: int = 0
    enrolled_employees: int = 0
    pending_enrollments: int = 0
    claims_awaiting_review: int = 0
    approved_claims: int = 0
    rejected_claims: int = 0
    claims_awaiting_payment: int = 0
    paid_claims: int = 0
    failed_claims: int = 0


class BenefitProgramUpsert(BaseModel):
    program_code: str = Field(min_length=1, max_length=64)
    name: str
    description: str | None = None
    category: str
    eligibility_rules: dict[str, Any] = Field(default_factory=dict)
    applicable_categories: list[str] = Field(default_factory=list)
    applicable_departments: list[str] = Field(default_factory=list)
    min_service_days: int = 0
    coverage_limit: str = "0"
    employee_contribution: str = "0"
    employer_contribution: str = "0"
    enrollment_start: date | None = None
    enrollment_end: date | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    required_documents: list[str] = Field(default_factory=list)
    requires_approval: bool = True
    renewal_rules: dict[str, Any] = Field(default_factory=dict)
    claim_rules: dict[str, Any] = Field(default_factory=dict)
    status: HrBenefitProgramStatus = HrBenefitProgramStatus.DRAFT


class BenefitProgramRead(BaseModel):
    id: str
    program_code: str
    name: str
    category: str
    status: str

    @classmethod
    def from_doc(cls, doc: HrBenefitProgram) -> "BenefitProgramRead":
        return cls(id=str(doc.id), program_code=doc.program_code, name=doc.name, category=doc.category, status=doc.status.value)


class BenefitEligibilityRead(BaseModel):
    eligible: bool
    reason: str | None = None
    program_id: str


class BenefitEnrollmentCreate(BaseModel):
    benefit_program_id: str
    employee_user_id: str
    enrollment_source: str = "employee"
    dependents: list[dict[str, Any]] = Field(default_factory=list)
    document_refs: list[str] = Field(default_factory=list)


class BenefitEnrollmentReview(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    reviewer_note: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class BenefitEnrollmentRead(BaseModel):
    id: str
    program_code: str
    employee_user_id: str
    status: HrBenefitEnrollmentStatus

    @classmethod
    def from_doc(cls, doc: EmployeeBenefitEnrollment) -> "BenefitEnrollmentRead":
        return cls(id=str(doc.id), program_code=doc.program_code, employee_user_id=str(doc.employee_user_id), status=doc.status)


class BenefitClaimCreate(BaseModel):
    benefit_program_id: str
    enrollment_id: str | None = None
    employee_user_id: str
    claim_category: str
    claim_date: date
    description: str
    expense_amount: str
    requested_amount: str
    document_refs: list[str] = Field(default_factory=list)


class BenefitClaimReview(BaseModel):
    action: str = Field(pattern="^(approve|partial|reject|return)$")
    approved_amount: str | None = None
    reviewer_note: str | None = None
    stage: str = "hr"


class BenefitClaimPaymentConfirm(BaseModel):
    payment_reference: str = Field(min_length=1, max_length=128)


class BenefitClaimRead(BaseModel):
    id: str
    claim_code: str
    employee_user_id: str
    status: HrBenefitClaimStatus
    requested_amount: str
    approved_amount: str
    payment_status: str

    @classmethod
    def from_doc(cls, doc: EmployeeBenefitClaim) -> "BenefitClaimRead":
        return cls(
            id=str(doc.id),
            claim_code=doc.claim_code,
            employee_user_id=str(doc.employee_user_id),
            status=doc.status,
            requested_amount=doc.requested_amount,
            approved_amount=doc.approved_amount,
            payment_status=doc.payment_status,
        )


class BenefitsReports(BaseModel):
    enrollments_by_program: dict[str, int] = Field(default_factory=dict)
    claims_by_category: dict[str, int] = Field(default_factory=dict)
    pending_claims: int = 0
    approved_claims: int = 0
    rejected_claims: int = 0
    awaiting_payment: int = 0
    paid_claims: int = 0
    utilization_total: str = "0"