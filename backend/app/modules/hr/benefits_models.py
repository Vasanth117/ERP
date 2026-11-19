"""Benefit programs, enrollments, claims and payments."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrBenefitClaimStatus, HrBenefitEnrollmentStatus, HrBenefitProgramStatus


class HrBenefitProgram(Document):
    tenant_id: PydanticObjectId
    program_code: str = Field(max_length=64)
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str = Field(max_length=64)
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
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_benefit_programs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("program_code", ASCENDING)], unique=True, name="unique_benefit_program"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="benefit_programs_status"),
        ]


class EmployeeBenefitEnrollment(Document):
    tenant_id: PydanticObjectId
    benefit_program_id: PydanticObjectId
    program_code: str = Field(max_length=64)
    employee_user_id: PydanticObjectId
    enrollment_source: str = Field(default="employee", max_length=32)
    dependents: list[dict[str, Any]] = Field(default_factory=list)
    document_refs: list[str] = Field(default_factory=list)
    status: HrBenefitEnrollmentStatus = HrBenefitEnrollmentStatus.PENDING
    reviewer_id: PydanticObjectId | None = None
    reviewer_note: str | None = Field(default=None, max_length=2000)
    effective_from: date | None = None
    effective_to: date | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_benefit_enrollments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("benefit_program_id", ASCENDING)],
                name="benefit_enrollment_by_employee_program",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="benefit_enrollments_status"),
        ]


class EmployeeBenefitEnrollmentHistory(Document):
    tenant_id: PydanticObjectId
    enrollment_id: PydanticObjectId
    action: str = Field(max_length=64)
    from_status: str | None = None
    to_status: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_benefit_enrollment_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("enrollment_id", ASCENDING), ("created_at", DESCENDING)], name="enrollment_history"),
        ]


class EmployeeBenefitClaim(Document):
    tenant_id: PydanticObjectId
    claim_code: str = Field(max_length=64)
    benefit_program_id: PydanticObjectId
    enrollment_id: PydanticObjectId | None = None
    employee_user_id: PydanticObjectId
    claim_category: str = Field(max_length=64)
    claim_date: date
    description: str = Field(max_length=4000)
    expense_amount: str
    requested_amount: str
    approved_amount: str = "0"
    document_refs: list[str] = Field(default_factory=list)
    status: HrBenefitClaimStatus = HrBenefitClaimStatus.AWAITING_REVIEW
    duplicate_hash: str | None = Field(default=None, max_length=128)
    reviewer_id: PydanticObjectId | None = None
    reviewer_note: str | None = Field(default=None, max_length=2000)
    payment_status: str = "pending"
    payment_reference: str | None = None
    actor_id: PydanticObjectId | None = None
    submitted_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_benefit_claims"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("claim_code", ASCENDING)], unique=True, name="unique_benefit_claim"),
            IndexModel([("tenant_id", ASCENDING), ("duplicate_hash", ASCENDING)], name="benefit_claim_duplicates"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="benefit_claims_status"),
        ]


class EmployeeBenefitClaimReview(Document):
    tenant_id: PydanticObjectId
    claim_id: PydanticObjectId
    stage: str = Field(max_length=32)
    action: str = Field(max_length=32)
    approved_amount: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_benefit_claim_reviews"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("claim_id", ASCENDING), ("created_at", DESCENDING)], name="claim_reviews"),
        ]


class EmployeeBenefitClaimPayment(Document):
    tenant_id: PydanticObjectId
    claim_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    amount: str
    status: str = "submitted"
    idempotency_key: str = Field(max_length=128)
    payment_reference: str | None = None
    finance_batch_id: str | None = None
    reconciled_at: datetime | None = None
    failure_reason: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_benefit_claim_payments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)], unique=True, name="unique_benefit_claim_payment"),
            IndexModel([("tenant_id", ASCENDING), ("claim_id", ASCENDING)], name="benefit_payments_by_claim"),
        ]


def claim_duplicate_hash(employee_user_id: PydanticObjectId, program_id: PydanticObjectId, claim_date: date, amount: str) -> str:
    return f"{employee_user_id}:{program_id}:{claim_date.isoformat()}:{Decimal(amount)}"