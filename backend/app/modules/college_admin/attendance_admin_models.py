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


class InstitutionAttendanceMarkingConfig(Document):
    """Session marking windows and operational toggles (CA 08.10)."""

    tenant_id: PydanticObjectId
    marking_window_key: str = "same_day_18"
    correction_window_key: str = "3_working_days"
    late_mark_after_key: str = "15_minutes"
    session_length_key: str = "60_minutes"
    allow_substitute_faculty: bool = True
    lock_after_approval: bool = True
    biometric_sync: bool = False
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_attendance_marking_config"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING)],
                unique=True,
                name="unique_attendance_marking_config_per_tenant",
            ),
        ]


class AttendanceInstitutionalPolicyRow(Document):
    """Display policy catalogue rows for rules & policies (CA 08.11)."""

    tenant_id: PydanticObjectId
    policy_key: str = Field(max_length=64)
    title: str = Field(max_length=200)
    value_label: str = Field(max_length=120)
    applies_to_label: str = Field(max_length=200)
    effective_from: date
    is_active: bool = True
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "attendance_institutional_policy_rows"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_key", ASCENDING)],
                unique=True,
                name="unique_attendance_policy_row_per_tenant",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("sort_order", ASCENDING)],
                name="attendance_policy_rows_by_sort",
            ),
        ]


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


class AttendanceReportDefinition(Document):
    """Saved / scheduled attendance report catalogue (CA 08.12)."""

    tenant_id: PydanticObjectId
    report_key: str = Field(max_length=64)
    title: str = Field(max_length=200)
    period_label: str = Field(max_length=120)
    export_formats: list[str] = Field(default_factory=list)
    schedule_label: str = Field(max_length=64)
    last_run_at: datetime | None = None
    sort_order: int = 0
    is_builtin: bool = True
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "attendance_report_definitions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("report_key", ASCENDING)],
                unique=True,
                name="unique_attendance_report_per_tenant",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("sort_order", ASCENDING)],
                name="attendance_reports_by_sort",
            ),
        ]


class AttendanceReportExecution(Document):
    tenant_id: PydanticObjectId
    report_key: str = Field(max_length=64)
    period_label: str = Field(max_length=120)
    run_at: datetime = Field(default_factory=utcnow)
    run_by: PydanticObjectId | None = None

    class Settings:
        name = "attendance_report_executions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("report_key", ASCENDING), ("run_at", DESCENDING)],
                name="attendance_report_runs",
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
