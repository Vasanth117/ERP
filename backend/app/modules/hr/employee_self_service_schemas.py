"""Employee HR self-service API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrSelfServiceRequestStatus, HrSelfServiceRequestType, LeaveDayPortion


class SelfServiceProfileRead(BaseModel):
    employee_user_id: str
    employee_code: str | None = None
    full_name: str | None = None
    official_email: str | None = None
    personal_email: str | None = None
    mobile_number: str | None = None
    department_id: str | None = None
    designation: str | None = None
    employment_status: str | None = None
    joining_date: str | None = None
    reporting_manager_user_id: str | None = None
    current_address: dict[str, Any] | None = None
    permanent_address: dict[str, Any] | None = None
    emergency_contact: dict[str, Any] | None = None


class SelfServiceLeaveApply(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    day_portion: LeaveDayPortion = LeaveDayPortion.FULL
    reason: str = Field(min_length=1, max_length=2000)
    document_refs: list[str] = Field(default_factory=list)
    contact_during_leave: str | None = None
    alternate_arrangement: str | None = None


class SelfServiceRequestCreate(BaseModel):
    request_type: HrSelfServiceRequestType
    title: str = Field(min_length=1, max_length=200)
    payload: dict[str, Any] = Field(default_factory=dict)
    employee_note: str | None = None


class SelfServiceRequestRead(BaseModel):
    id: str
    request_type: str
    status: HrSelfServiceRequestStatus
    title: str
    submitted_at: datetime | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc) -> "SelfServiceRequestRead":
        return cls(
            id=str(doc.id),
            request_type=doc.request_type.value,
            status=doc.status,
            title=doc.title,
            submitted_at=doc.submitted_at,
            created_at=doc.created_at,
        )


class SelfServiceSalaryRead(BaseModel):
    has_assignment: bool = False
    template_title: str | None = None
    component_amounts: dict[str, str] = Field(default_factory=dict)
    effective_from: date | None = None


class SelfServiceBenefitsStub(BaseModel):
    available: bool = False
    message: str = "Benefits & Claims module is not enabled in this phase."


class SelfServiceNotificationRead(BaseModel):
    event_type: str
    title: str
    body: str
    created_at: datetime