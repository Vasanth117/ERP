"""Phase 6 payment plans, installments and late fees."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase6_enums import AssignmentStatus, InstallmentStatus, LateFeeAssessmentStatus, PaymentPlanStatus


class StudentPaymentPlan(Document):
    tenant_id: PydanticObjectId
    plan_id: str
    plan_code: str
    plan_name: str
    description: str | None = None
    academic_year_label: str | None = None
    applicable_programmes: list[str] = Field(default_factory=list)
    applicable_fee_categories: list[str] = Field(default_factory=list)
    applicable_student_categories: list[str] = Field(default_factory=list)
    number_of_installments: int = Field(default=1, ge=1)
    installment_definitions: list[dict[str, Any]] = Field(default_factory=list)
    initial_payment_percent: float = Field(default=0, ge=0, le=100)
    requires_approval: bool = False
    effective_from: date | None = None
    effective_to: date | None = None
    plan_status: PaymentPlanStatus = PaymentPlanStatus.DRAFT
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_payment_plans"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("plan_id", ASCENDING)], unique=True, name="unique_payment_plan"),
            IndexModel([("tenant_id", ASCENDING), ("plan_code", ASCENDING)], unique=True, name="unique_plan_code"),
        ]


class StudentPaymentPlanAssignment(Document):
    tenant_id: PydanticObjectId
    assignment_id: str
    plan_id: str
    student_user_id: PydanticObjectId
    invoice_id: str | None = None
    demand_id: str | None = None
    total_obligation: float = Field(ge=0)
    academic_year_label: str | None = None
    semester_label: str | None = None
    status: AssignmentStatus = AssignmentStatus.PENDING_APPROVAL
    effective_from: date | None = None
    approved_by: PydanticObjectId | None = None
    special_arrangement: bool = False
    special_reason: str | None = None
    schedule_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_payment_plan_assignments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("assignment_id", ASCENDING)], unique=True, name="unique_plan_assignment"),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)], name="assignments_by_student"),
        ]


class StudentInstallmentSchedule(Document):
    tenant_id: PydanticObjectId
    schedule_id: str
    assignment_id: str
    student_user_id: PydanticObjectId
    invoice_id: str | None = None
    demand_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    installments: list[dict[str, Any]] = Field(default_factory=list)
    version: int = 1
    active: bool = True
    published: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_installment_schedules"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("schedule_id", ASCENDING)], unique=True, name="unique_installment_schedule_phase6"),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("active", ASCENDING)], name="schedules_by_student"),
        ]


class StudentInstallmentPayment(Document):
    tenant_id: PydanticObjectId
    allocation_id: str
    schedule_id: str
    installment_id: str
    transaction_id: str
    amount: float = Field(ge=0)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_installment_payments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("allocation_id", ASCENDING)], unique=True, name="unique_installment_payment"),
            IndexModel([("tenant_id", ASCENDING), ("transaction_id", ASCENDING)], name="inst_pay_by_tx"),
        ]


class StudentInstallmentHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    schedule_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    previous_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_installment_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_installment_history"),
        ]


class StudentInstallmentRescheduleRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str
    schedule_id: str
    student_user_id: PydanticObjectId
    reason: str
    proposed_installments: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "submitted"
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_installment_reschedule_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_reschedule_request"),
        ]


class LateFeePolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    policy_code: str
    name: str
    calc_type: str = "fixed"
    fixed_amount: float = Field(default=0, ge=0)
    percent_rate: float = Field(default=0, ge=0)
    daily_rate: float = Field(default=0, ge=0)
    max_late_fee: float | None = Field(default=None, ge=0)
    grace_days: int = Field(default=0, ge=0)
    fee_categories: list[str] = Field(default_factory=list)
    academic_year_label: str | None = None
    student_categories: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    rounding_rule: str = "round_half_up"
    ageing_buckets: list[dict[str, Any]] = Field(default_factory=list)
    effective_from: date | None = None
    effective_to: date | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "late_fee_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_id", ASCENDING)], unique=True, name="unique_late_fee_policy"),
            IndexModel([("tenant_id", ASCENDING), ("policy_code", ASCENDING)], unique=True, name="unique_late_fee_policy_code"),
        ]


class StudentLateFeeAssessment(Document):
    tenant_id: PydanticObjectId
    assessment_id: str
    student_user_id: PydanticObjectId
    invoice_id: str | None = None
    demand_id: str | None = None
    installment_id: str | None = None
    policy_id: str
    principal_outstanding: float = Field(ge=0)
    overdue_days: int = Field(ge=0)
    calculated_fee: float = Field(ge=0)
    period_key: str
    status: LateFeeAssessmentStatus = LateFeeAssessmentStatus.PENDING
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_late_fee_assessments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("assessment_id", ASCENDING)], unique=True, name="unique_late_fee_assessment"),
            IndexModel(
                [("tenant_id", ASCENDING), ("period_key", ASCENDING), ("demand_id", ASCENDING)],
                unique=True,
                name="unique_late_fee_period",
                partialFilterExpression={"demand_id": {"$type": "string"}},
            ),
        ]


class StudentLateFeeTransaction(Document):
    tenant_id: PydanticObjectId
    transaction_ref: str
    assessment_id: str
    student_user_id: PydanticObjectId
    demand_id: str | None = None
    amount: float = Field(ge=0)
    posting_key: str
    ledger_entry_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_late_fee_transactions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("transaction_ref", ASCENDING)], unique=True, name="unique_late_fee_tx"),
            IndexModel([("tenant_id", ASCENDING), ("posting_key", ASCENDING)], unique=True, name="unique_late_fee_posting"),
        ]


class StudentLateFeeWaiver(Document):
    tenant_id: PydanticObjectId
    waiver_id: str
    assessment_id: str | None = None
    transaction_ref: str | None = None
    student_user_id: PydanticObjectId
    original_late_fee: float = Field(ge=0)
    waived_amount: float = Field(ge=0)
    reason: str
    requested_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    effective_date: date | None = None
    ledger_entry_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_late_fee_waivers"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("waiver_id", ASCENDING)], unique=True, name="unique_late_fee_waiver"),
        ]