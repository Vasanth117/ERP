"""Attendance & work schedule API schemas."""

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.attendance_schedule_models import (
    HrEmployeeAttendanceRecord,
    HrEmployeeRosterAssignment,
    HrShift,
    HrWorkSchedule,
)
from app.modules.hr.enums import (
    EmployeeAttendanceCorrectionStatus,
    EmployeeAttendanceDayStatus,
    HrAttendanceEventSource,
    HrAttendanceEventType,
    HrMonthlyAttendanceStatus,
    HrRosterAssignmentStatus,
    HrShiftKind,
)


class WorkScheduleUpsert(BaseModel):
    schedule_code: str
    title: str
    employee_categories: list[str] = Field(default_factory=list)
    department_id: str | None = None
    campus_id: str | None = None
    working_days: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    weekly_offs: list[int] = Field(default_factory=lambda: [5, 6])
    start_time: time
    end_time: time
    break_minutes: int = Field(ge=0, default=60)
    expected_hours: float = Field(ge=0, default=8.0)
    grace_minutes: int = Field(ge=0, default=15)
    wfh_enabled: bool = False
    effective_from: date


class WorkScheduleRead(BaseModel):
    id: str
    schedule_code: str
    title: str
    version: int
    is_active: bool

    @classmethod
    def from_document(cls, doc: HrWorkSchedule) -> "WorkScheduleRead":
        return cls(id=str(doc.id), schedule_code=doc.schedule_code, title=doc.title, version=doc.version, is_active=doc.is_active)


class ShiftUpsert(BaseModel):
    shift_code: str
    title: str
    kind: HrShiftKind = HrShiftKind.GENERAL
    start_time: time
    end_time: time
    crosses_midnight: bool = False
    break_minutes: int = Field(ge=0, default=30)
    expected_hours: float = Field(ge=0, default=8.0)
    grace_minutes: int = Field(ge=0, default=10)


class ShiftRead(BaseModel):
    id: str
    shift_code: str
    title: str
    kind: HrShiftKind

    @classmethod
    def from_document(cls, doc: HrShift) -> "ShiftRead":
        return cls(id=str(doc.id), shift_code=doc.shift_code, title=doc.title, kind=doc.kind)


class RosterAssign(BaseModel):
    employee_user_id: str
    shift_id: str
    schedule_id: str | None = None
    department_id: str | None = None
    roster_date: date


class RosterRead(BaseModel):
    id: str
    employee_user_id: str
    roster_date: date
    status: HrRosterAssignmentStatus

    @classmethod
    def from_document(cls, doc: HrEmployeeRosterAssignment) -> "RosterRead":
        return cls(
            id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            roster_date=doc.roster_date,
            status=doc.status,
        )


class ShiftSwapCreate(BaseModel):
    from_assignment_id: str
    to_employee_user_id: str
    reason: str = Field(min_length=1, max_length=2000)


class AttendanceEventIngest(BaseModel):
    employee_user_id: str
    event_type: HrAttendanceEventType
    event_at: datetime
    source: HrAttendanceEventSource
    device_reference: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=128)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class AttendanceManualDay(BaseModel):
    employee_user_id: str
    attendance_date: date
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    status: EmployeeAttendanceDayStatus | None = None
    remarks: str | None = None


class AttendanceRecordRead(BaseModel):
    id: str
    employee_user_id: str
    attendance_date: date
    status: EmployeeAttendanceDayStatus
    working_minutes: int
    late_minutes: int
    missing_punch: bool

    @classmethod
    def from_document(cls, doc: HrEmployeeAttendanceRecord) -> "AttendanceRecordRead":
        return cls(
            id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            attendance_date=doc.attendance_date,
            status=doc.status,
            working_minutes=doc.working_minutes,
            late_minutes=doc.late_minutes,
            missing_punch=doc.missing_punch,
        )


class AttendanceCorrectionCreate(BaseModel):
    employee_user_id: str
    attendance_date: date
    requested_status: EmployeeAttendanceDayStatus
    reason: str = Field(min_length=1, max_length=2000)
    proposed_check_in: datetime | None = None
    proposed_check_out: datetime | None = None


class AttendanceCorrectionReview(BaseModel):
    decision: str = Field(pattern="^(manager_approve|hr_approve|approve|reject)$")
    note: str | None = None


class MonthlyAttendanceAction(BaseModel):
    period_year: int
    period_month: int = Field(ge=1, le=12)
    department_id: str | None = None
    reopen_reason: str | None = None


class MonthlySummaryRead(BaseModel):
    period_year: int
    period_month: int
    status: HrMonthlyAttendanceStatus
    present_days: int
    absent_days: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MonthlySummaryRead":
        return cls(
            period_year=data["period_year"],
            period_month=data["period_month"],
            status=data["status"],
            present_days=data.get("present_days", 0),
            absent_days=data.get("absent_days", 0),
        )


class AttendanceOverview(BaseModel):
    pending_corrections: int = 0
    missing_punch_today: int = 0
    locked_months: int = 0