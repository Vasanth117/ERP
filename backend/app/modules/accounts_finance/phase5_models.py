"""Phase 5 scholarship and concession collections."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase5_enums import ConcessionApplicationStatus, ScholarshipAwardStatus


class ScholarshipEligibilityRule(Document):
    tenant_id: PydanticObjectId
    rule_id: str
    programme_id: str
    rule_name: str
    field_path: str
    operator: str
    value: Any = None
    required: bool = True
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "scholarship_eligibility_rules"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("rule_id", ASCENDING)], unique=True, name="unique_scholarship_rule"),
            IndexModel([("tenant_id", ASCENDING), ("programme_id", ASCENDING)], name="rules_by_program"),
        ]


class ScholarshipApplicationReview(Document):
    tenant_id: PydanticObjectId
    review_id: str
    application_id: str
    reviewer_role: str
    reviewer_id: PydanticObjectId
    recommendation: str
    comments: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "scholarship_application_reviews"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("review_id", ASCENDING)], unique=True, name="unique_scholarship_review"),
        ]


class StudentScholarshipAward(Document):
    tenant_id: PydanticObjectId
    award_id: str
    student_user_id: PydanticObjectId
    programme_id: str
    application_id: str | None = None
    award_type: str = "fixed"
    approved_amount: float = Field(ge=0)
    funding_source: str | None = None
    fee_categories: list[str] = Field(default_factory=list)
    academic_year_label: str | None = None
    semester_label: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    invoice_id: str | None = None
    assessment_id: str | None = None
    status: ScholarshipAwardStatus = ScholarshipAwardStatus.PENDING
    disbursement_status: str = "pending"
    approval_reference: str | None = None
    approved_by: PydanticObjectId | None = None
    ledger_posted: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_scholarship_awards"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("award_id", ASCENDING)], unique=True, name="unique_scholarship_award"),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)], name="awards_by_student"),
        ]


class ScholarshipAwardHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    award_id: str
    action: str
    from_status: str | None = None
    to_status: str | None = None
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "scholarship_award_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_award_history"),
        ]


class ScholarshipFundingAllocation(Document):
    tenant_id: PydanticObjectId
    allocation_id: str
    programme_id: str
    funding_source: str
    total_fund: float = Field(ge=0)
    approved_total: float = 0.0
    committed_total: float = 0.0
    pending_total: float = 0.0
    academic_year_label: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "scholarship_funding_allocations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("programme_id", ASCENDING), ("funding_source", ASCENDING)],
                unique=True,
                name="unique_scholarship_funding",
            ),
        ]


class ScholarshipRenewalRecord(Document):
    tenant_id: PydanticObjectId
    renewal_id: str
    award_id: str
    student_user_id: PydanticObjectId
    status: str = "submitted"
    academic_year_label: str | None = None
    approved_amount: float | None = None
    decision: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "scholarship_renewal_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("renewal_id", ASCENDING)], unique=True, name="unique_scholarship_renewal"),
        ]


class FeeConcessionCategory(Document):
    tenant_id: PydanticObjectId
    category_id: str
    code: str
    name: str
    description: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_concession_categories"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("category_id", ASCENDING)], unique=True, name="unique_concession_category"),
            IndexModel([("tenant_id", ASCENDING), ("code", ASCENDING)], unique=True, name="unique_concession_category_code"),
        ]


class FeeConcessionPolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    policy_code: str
    name: str
    description: str | None = None
    category_id: str | None = None
    applicable_programmes: list[str] = Field(default_factory=list)
    applicable_fee_categories: list[str] = Field(default_factory=list)
    concession_type: str = "fixed"
    fixed_amount: float | None = Field(default=None, ge=0)
    percent_amount: float | None = Field(default=None, ge=0, le=100)
    max_limit: float | None = Field(default=None, ge=0)
    academic_year_label: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    document_required: bool = False
    approval_hierarchy: list[str] = Field(default_factory=list)
    stacking_rules: dict = Field(default_factory=dict)
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_concession_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_id", ASCENDING)], unique=True, name="unique_concession_policy"),
            IndexModel([("tenant_id", ASCENDING), ("policy_code", ASCENDING)], unique=True, name="unique_concession_policy_code"),
        ]


class StudentFeeConcessionApplication(Document):
    tenant_id: PydanticObjectId
    application_id: str
    student_user_id: PydanticObjectId
    policy_id: str
    category_id: str | None = None
    assessment_id: str | None = None
    invoice_id: str | None = None
    reason: str
    requested_amount: float | None = None
    requested_percent: float | None = Field(default=None, ge=0, le=100)
    document_refs: list[str] = Field(default_factory=list)
    academic_year_label: str | None = None
    semester_label: str | None = None
    status: ConcessionApplicationStatus = ConcessionApplicationStatus.SUBMITTED
    requested_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_concession_applications"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("application_id", ASCENDING)], unique=True, name="unique_concession_application"),
        ]


class StudentFeeConcessionAward(Document):
    tenant_id: PydanticObjectId
    award_id: str
    application_id: str | None = None
    student_user_id: PydanticObjectId
    policy_id: str
    approved_amount: float = Field(ge=0)
    invoice_id: str | None = None
    assessment_id: str | None = None
    status: ConcessionApplicationStatus = ConcessionApplicationStatus.APPROVED
    approved_by: PydanticObjectId | None = None
    ledger_posted: bool = False
    effective_from: date | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_concession_awards"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("award_id", ASCENDING)], unique=True, name="unique_concession_award"),
        ]


class StudentFeeWaiver(Document):
    tenant_id: PydanticObjectId
    waiver_id: str
    student_user_id: PydanticObjectId
    waiver_type: str
    original_amount: float = Field(ge=0)
    waived_amount: float = Field(ge=0)
    remaining_amount: float = Field(ge=0)
    invoice_id: str | None = None
    assessment_id: str | None = None
    reason: str
    document_refs: list[str] = Field(default_factory=list)
    requested_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    status: str = "approved"
    effective_date: date | None = None
    ledger_posted: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_waivers"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("waiver_id", ASCENDING)], unique=True, name="unique_fee_waiver"),
        ]


class FeeConcessionApprovalHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    target_type: str
    target_id: str
    action: str
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_concession_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_concession_approval_hist"),
        ]


class FeeConcessionAdjustmentHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    student_user_id: PydanticObjectId
    source_type: str
    source_id: str
    invoice_id: str | None = None
    amount: float = Field(ge=0)
    ledger_entry_id: str | None = None
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_concession_adjustment_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_concession_adjust_hist"),
        ]