"""HR administration API schemas."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.hr_admin_models import HrPolicy, PayrollConfiguration, RecruitmentStatus
from app.modules.hr.enums import LeaveRequestStatus


class HrPolicyUpsert(BaseModel):
    policy_code: str
    title: str
    body: str


class HrPolicyRead(BaseModel):
    policy_code: str
    title: str
    version: int
    published: bool

    @classmethod
    def from_document(cls, doc: HrPolicy) -> "HrPolicyRead":
        return cls(policy_code=doc.policy_code, title=doc.title, version=doc.version, published=doc.published)


class RecruitmentCreate(BaseModel):
    requisition_id: str
    role_title: str
    department_id: str | None = None


class OnboardingCreate(BaseModel):
    user_id: str
    checklist: list[dict[str, Any]] = Field(default_factory=list)


class OffboardingCreate(BaseModel):
    user_id: str
    reason: str
    last_working_date: date | None = None


class LeavePolicyUpsert(BaseModel):
    leave_type: str
    annual_quota_days: float = Field(ge=0)
    requires_approval: bool = True
    rules: dict[str, Any] = Field(default_factory=dict)


class LeaveDecision(BaseModel):
    leave_request_id: str
    decision: LeaveRequestStatus
    note: str | None = None


class PayrollConfigUpsert(BaseModel):
    config_id: str
    label: str
    pay_frequency: str = "monthly"
    integration_provider: str | None = None


class PayrollConfigRead(BaseModel):
    config_id: str
    label: str
    pay_frequency: str
    last_run_status: str | None
    version: int

    @classmethod
    def from_document(cls, doc: PayrollConfiguration) -> "PayrollConfigRead":
        return cls(
            config_id=doc.config_id,
            label=doc.label,
            pay_frequency=doc.pay_frequency,
            last_run_status=doc.last_run_status,
            version=doc.version,
        )
