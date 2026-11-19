"""HR operational records (attendance, recruitment applications, activity)."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import (
    EmployeeAttendanceCorrectionStatus,
    EmployeeAttendanceDayStatus,
    HrRecruitmentApplicationStatus,
    HrStaffActivityType,
)


class EmployeeDayAttendance(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    attendance_date: date
    status: EmployeeAttendanceDayStatus
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    remarks: str | None = Field(default=None, max_length=500)
    recorded_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_day_attendance"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("attendance_date", ASCENDING)],
                unique=True,
                name="unique_employee_day_attendance",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("attendance_date", ASCENDING), ("status", ASCENDING)],
                name="employee_attendance_by_date_status",
            ),
        ]


class EmployeeAttendanceCorrection(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    attendance_date: date
    requested_status: EmployeeAttendanceDayStatus
    reason: str = Field(max_length=2000)
    status: EmployeeAttendanceCorrectionStatus = EmployeeAttendanceCorrectionStatus.PENDING
    manager_reviewer_id: PydanticObjectId | None = None
    hr_reviewer_id: PydanticObjectId | None = None
    reviewer_id: PydanticObjectId | None = None
    reviewer_note: str | None = Field(default=None, max_length=2000)
    previous_snapshot: dict[str, Any] = Field(default_factory=dict)
    proposed_snapshot: dict[str, Any] = Field(default_factory=dict)
    applied: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_attendance_corrections"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="attendance_corrections_pending",
            ),
        ]


class HrRecruitmentApplication(Document):
    tenant_id: PydanticObjectId
    recruitment_record_id: PydanticObjectId
    requisition_id: str
    applicant_name: str = Field(max_length=200)
    applicant_email: str = Field(max_length=254)
    status: HrRecruitmentApplicationStatus = HrRecruitmentApplicationStatus.NEW
    interview_scheduled_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_recruitment_applications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("requisition_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_applications_by_requisition",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING)],
                name="hr_applications_by_status",
            ),
        ]


class HrStaffActivityLog(Document):
    tenant_id: PydanticObjectId
    activity_type: HrStaffActivityType
    summary: str = Field(max_length=500)
    employee_user_id: PydanticObjectId | None = None
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    resource_type: str | None = Field(default=None, max_length=64)
    resource_id: str | None = None
    status_label: str | None = Field(default=None, max_length=64)
    actor_id: PydanticObjectId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_staff_activity_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_activity_by_tenant",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("activity_type", ASCENDING), ("created_at", DESCENDING)],
                name="hr_activity_by_type",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("department_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_activity_by_department",
            ),
        ]