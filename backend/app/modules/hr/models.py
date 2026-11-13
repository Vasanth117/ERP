"""Central HR records (authoritative)."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import LeaveRequestStatus


class LeaveRequest(Document):
    """Owned by HR; faculty self-service creates rows scoped to employee user."""

    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    leave_type: str = "casual"
    start_date: date
    end_date: date
    reason: str = Field(max_length=500)
    status: LeaveRequestStatus = LeaveRequestStatus.SUBMITTED
    approver_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "leave_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("created_at", ASCENDING)],
                name="leave_by_employee",
            ),
        ]


class PayslipReference(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    period_label: str
    storage_key: str
    payroll_provider: str | None = None
    published_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payslip_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("period_label", ASCENDING)],
                unique=True,
                name="unique_payslip_period",
            ),
        ]


class EmployeeProfileSnapshot(Document):
    """Read-only HR snapshot exposed to employee self-service."""

    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    employee_id: str | None = None
    designation: str | None = None
    department_name: str | None = None
    joining_date: date | None = None
    employment_type: str | None = None
    permitted_fields: dict = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_profile_snapshots"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING)],
                unique=True,
                name="unique_employee_snapshot",
            ),
        ]
