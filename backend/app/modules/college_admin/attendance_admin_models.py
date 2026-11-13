"""College admin attendance administration collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.attendance.enums import AttendanceCorrectionStatus
from app.modules.attendance.models import AttendancePolicyRules


class AttendancePolicyAudience(str, Enum):
    STUDENT = "student"
    EMPLOYEE = "employee"
    FACULTY = "faculty"


class InstitutionAttendancePolicy(Document):
    tenant_id: PydanticObjectId
    policy_code: str = Field(max_length=64)
    audience: AttendancePolicyAudience = AttendancePolicyAudience.STUDENT
    title: str = Field(max_length=200)
    rules: AttendancePolicyRules = Field(default_factory=AttendancePolicyRules)
    submission_deadline_hours: int = Field(default=24, ge=0, le=168)
    is_active: bool = True
    version: int = 1
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_attendance_policies"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_code", ASCENDING), ("audience", ASCENDING)],
                unique=True,
                name="unique_institution_attendance_policy",
            ),
        ]


class AttendanceSubmissionMonitoring(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    course_code: str | None = None
    section: str | None = None
    session_date: date
    due_at: datetime | None = None
    status: str = "pending"
    snapshot_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "attendance_submission_monitoring"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("session_date", ASCENDING)],
                name="attendance_monitoring_by_status",
            ),
        ]


class AttendanceCorrectionApproval(Document):
    tenant_id: PydanticObjectId
    correction_request_id: PydanticObjectId
    decision: AttendanceCorrectionStatus
    reviewer_id: PydanticObjectId
    reviewer_note: str | None = Field(default=None, max_length=2000)
    applied_to_record: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "attendance_correction_approvals"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("correction_request_id", ASCENDING)],
                unique=True,
                name="unique_correction_approval",
            ),
        ]


class AttendanceComplianceSnapshot(Document):
    tenant_id: PydanticObjectId
    department_id: PydanticObjectId | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    pending_submissions: int = 0
    pending_corrections: int = 0
    sessions_submitted: int = 0
    students_below_threshold: int = 0
    metrics: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utcnow)
    generated_by: PydanticObjectId | None = None

    class Settings:
        name = "attendance_compliance_snapshots"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("generated_at", DESCENDING)],
                name="compliance_snapshots_recent",
            ),
        ]
