"""College admin HR administration collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import LeaveRequestStatus


class RecruitmentStatus(str, Enum):
    OPEN = "open"
    INTERVIEW = "interview"
    OFFERED = "offered"
    HIRED = "hired"
    CLOSED = "closed"


class HrPolicy(Document):
    tenant_id: PydanticObjectId
    policy_code: str
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    version: int = 1
    published: bool = False
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_code", ASCENDING)], unique=True, name="unique_hr_policy"),
        ]


class RecruitmentRecord(Document):
    tenant_id: PydanticObjectId
    requisition_id: str
    role_title: str
    department_id: PydanticObjectId | None = None
    status: RecruitmentStatus = RecruitmentStatus.OPEN
    applicant_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "recruitment_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("requisition_id", ASCENDING)], unique=True, name="unique_recruitment"),
        ]


class EmployeeOnboardingRecord(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    employee_record_id: PydanticObjectId | None = None
    checklist: list[dict[str, Any]] = Field(default_factory=list)
    completed: bool = False
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "employee_onboarding_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING)], unique=True, name="unique_onboarding_per_user"),
        ]


class EmployeeOffboardingRecord(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    reason: str = Field(max_length=1000)
    last_working_date: date | None = None
    clearance_checklist: list[dict[str, Any]] = Field(default_factory=list)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_offboarding_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)], name="offboarding_history"),
        ]


class EmployeeLeavePolicy(Document):
    tenant_id: PydanticObjectId
    leave_type: str
    annual_quota_days: float = Field(ge=0)
    requires_approval: bool = True
    rules: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_leave_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("leave_type", ASCENDING)], unique=True, name="unique_leave_policy"),
        ]


class EmployeeLeaveApproval(Document):
    tenant_id: PydanticObjectId
    leave_request_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    decision: LeaveRequestStatus
    reviewer_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_leave_approvals"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("leave_request_id", ASCENDING)], unique=True, name="unique_leave_approval"),
        ]


class PayrollConfiguration(Document):
    """Salary bands stored in `confidential_config` — never returned via admin read APIs."""

    tenant_id: PydanticObjectId
    config_id: str
    label: str
    pay_frequency: str = "monthly"
    confidential_config: dict[str, Any] = Field(default_factory=dict)
    integration_provider: str | None = None
    last_run_status: str | None = None
    version: int = 1
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payroll_configuration"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("config_id", ASCENDING)], unique=True, name="unique_payroll_config"),
        ]


class EmployeeBenefitRecord(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    benefit_code: str
    title: str
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_benefit_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING), ("benefit_code", ASCENDING)], name="benefits_by_user"),
        ]


class EmployeePerformanceRecord(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    review_period: str
    rating: float | None = Field(default=None, ge=0, le=5)
    summary: str | None = Field(default=None, max_length=4000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_performance_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING), ("review_period", ASCENDING)], name="performance_by_user"),
        ]
