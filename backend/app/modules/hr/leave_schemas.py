"""Leave management API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import LeaveDayPortion, LeaveRequestStatus
from app.modules.hr.leave_models import HrLeaveBalance, HrLeaveTypeConfig
from app.modules.hr.models import LeaveRequest


class LeaveOverviewStats(BaseModel):
    total_requests: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    cancelled: int = 0
    currently_on_leave: int = 0
    upcoming_approved: int = 0
    immediate_action: int = 0
    department_usage: dict[str, int] = Field(default_factory=dict)


class LeavePolicyUpsert(BaseModel):
    leave_type: str
    annual_quota_days: float = Field(ge=0)
    requires_approval: bool = True
    rules: dict[str, Any] = Field(default_factory=dict)


class LeaveReports(BaseModel):
    period_year: int
    pending_approvals: int = 0
    approved_count: int = 0
    upcoming_leaves: int = 0
    leave_type_distribution: dict[str, int] = Field(default_factory=dict)
    department_usage: dict[str, float] = Field(default_factory=dict)
    balance_snapshots: list["LeaveBalanceRead"] = Field(default_factory=list)


class LeaveTypeConfigUpsert(BaseModel):
    leave_type_code: str = Field(min_length=1, max_length=64)
    title: str
    rules: dict[str, Any] = Field(default_factory=dict)
    employee_categories: list[str] = Field(default_factory=list)
    effective_from: date | None = None


class LeaveTypeConfigRead(BaseModel):
    id: str
    leave_type_code: str
    title: str

    @classmethod
    def from_document(cls, doc: HrLeaveTypeConfig) -> "LeaveTypeConfigRead":
        return cls(id=str(doc.id), leave_type_code=doc.leave_type_code, title=doc.title)


class LeaveApplicationCreate(BaseModel):
    employee_user_id: str
    leave_type: str
    start_date: date
    end_date: date
    day_portion: LeaveDayPortion = LeaveDayPortion.FULL
    reason: str = Field(min_length=1, max_length=500)
    document_refs: list[str] = Field(default_factory=list)
    contact_during_leave: str | None = None
    alternate_arrangement: str | None = None


class LeaveApplicationReview(BaseModel):
    decision: str = Field(pattern="^(manager_approve|hr_approve|reject|request_clarification|approve|cancel)$")
    note: str | None = None


class LeaveAdjustmentCreate(BaseModel):
    employee_user_id: str
    leave_type: str
    period_year: int
    amount_days: float
    reason: str = Field(min_length=1, max_length=2000)


class LeaveBalanceRead(BaseModel):
    employee_user_id: str
    leave_type: str
    period_year: int
    available: float
    used: float
    pending: float

    @classmethod
    def from_document(cls, doc: HrLeaveBalance) -> "LeaveBalanceRead":
        return cls(
            employee_user_id=str(doc.employee_user_id),
            leave_type=doc.leave_type,
            period_year=doc.period_year,
            available=doc.available,
            used=doc.used,
            pending=doc.pending,
        )


class LeaveRequestRead(BaseModel):
    id: str
    employee_user_id: str
    leave_type: str
    start_date: date
    end_date: date
    working_days: float
    status: LeaveRequestStatus

    @classmethod
    def from_document(cls, doc: LeaveRequest) -> "LeaveRequestRead":
        return cls(
            id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            leave_type=doc.leave_type,
            start_date=doc.start_date,
            end_date=doc.end_date,
            working_days=doc.working_days,
            status=doc.status,
        )