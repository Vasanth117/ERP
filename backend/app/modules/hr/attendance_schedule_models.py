"""Work schedules, shifts, roster, attendance records and monthly summaries."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import (
    EmployeeAttendanceCorrectionStatus,
    EmployeeAttendanceDayStatus,
    HrAttendanceEventSource,
    HrAttendanceEventType,
    HrMonthlyAttendanceStatus,
    HrRosterAssignmentStatus,
    HrShiftKind,
)


class HrWorkSchedule(Document):
    tenant_id: PydanticObjectId
    schedule_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    employee_categories: list[str] = Field(default_factory=list)
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    working_days: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    weekly_offs: list[int] = Field(default_factory=lambda: [5, 6])
    start_time: str = Field(max_length=8)
    end_time: str = Field(max_length=8)
    break_minutes: int = Field(ge=0, default=60)
    expected_hours: float = Field(ge=0, default=8.0)
    grace_minutes: int = Field(ge=0, default=15)
    wfh_enabled: bool = False
    effective_from: date
    effective_to: date | None = None
    version: int = 1
    is_active: bool = True
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_work_schedules"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("schedule_code", ASCENDING), ("version", DESCENDING)],
                unique=True,
                name="unique_work_schedule_version",
            ),
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], name="hr_schedules_active"),
        ]


class HrShift(Document):
    tenant_id: PydanticObjectId
    shift_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    kind: HrShiftKind = HrShiftKind.GENERAL
    start_time: str = Field(max_length=8)
    end_time: str = Field(max_length=8)
    crosses_midnight: bool = False
    break_minutes: int = Field(ge=0, default=30)
    expected_hours: float = Field(ge=0, default=8.0)
    grace_minutes: int = Field(ge=0, default=10)
    is_active: bool = True
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_shifts"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("shift_code", ASCENDING)], unique=True, name="unique_hr_shift"),
        ]


class HrEmployeeRosterAssignment(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    shift_id: PydanticObjectId
    schedule_id: PydanticObjectId | None = None
    department_id: PydanticObjectId | None = None
    roster_date: date
    status: HrRosterAssignmentStatus = HrRosterAssignmentStatus.SCHEDULED
    replaced_by_assignment_id: PydanticObjectId | None = None
    swap_request_id: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_roster_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("roster_date", ASCENDING)],
                unique=True,
                name="unique_roster_per_day",
            ),
            IndexModel([("tenant_id", ASCENDING), ("roster_date", ASCENDING)], name="roster_by_date"),
        ]


class HrShiftSwapRequest(Document):
    tenant_id: PydanticObjectId
    request_code: str = Field(max_length=64)
    from_assignment_id: PydanticObjectId
    to_employee_user_id: PydanticObjectId
    reason: str = Field(max_length=2000)
    status: str = Field(default="pending", max_length=32)
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_shift_swap_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_code", ASCENDING)], unique=True, name="unique_shift_swap"),
        ]


class HrEmployeeAttendanceEvent(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    event_type: HrAttendanceEventType
    event_at: datetime
    source: HrAttendanceEventSource
    device_reference: str | None = Field(default=None, max_length=128)
    idempotency_key: str = Field(max_length=128)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_attendance_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_attendance_event",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("event_at", ASCENDING)],
                name="attendance_events_by_employee",
            ),
        ]


class HrEmployeeAttendanceRecord(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    attendance_date: date
    status: EmployeeAttendanceDayStatus
    first_check_in: datetime | None = None
    last_check_out: datetime | None = None
    working_minutes: int = 0
    break_minutes: int = 0
    late_minutes: int = 0
    early_departure_minutes: int = 0
    overtime_minutes: int = 0
    missing_punch: bool = False
    shift_id: PydanticObjectId | None = None
    schedule_id: PydanticObjectId | None = None
    previous_snapshot: dict[str, Any] = Field(default_factory=dict)
    locked: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_attendance_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("attendance_date", ASCENDING)],
                unique=True,
                name="unique_attendance_record",
            ),
            IndexModel([("tenant_id", ASCENDING), ("attendance_date", ASCENDING), ("status", ASCENDING)], name="attendance_records_by_date"),
        ]


class HrEmployeeAttendanceMonthlySummary(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId | None = None
    department_id: PydanticObjectId | None = None
    period_year: int
    period_month: int
    status: HrMonthlyAttendanceStatus = HrMonthlyAttendanceStatus.OPEN
    present_days: int = 0
    absent_days: int = 0
    leave_days: float = 0
    late_days: int = 0
    missing_punch_days: int = 0
    total_working_minutes: int = 0
    overtime_minutes: int = 0
    locked_at: datetime | None = None
    locked_by: PydanticObjectId | None = None
    reopen_reason: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_attendance_monthly_summaries"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("period_year", ASCENDING),
                    ("period_month", ASCENDING),
                    ("employee_user_id", ASCENDING),
                ],
                unique=True,
                name="unique_monthly_employee_summary",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("period_year", ASCENDING), ("period_month", ASCENDING), ("department_id", ASCENDING)],
                name="monthly_dept_summary",
            ),
        ]