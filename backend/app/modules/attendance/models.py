"""Central attendance collections (authoritative)."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow
from app.modules.attendance.enums import (
    AttendanceCorrectionStatus,
    AttendanceMarkStatus,
    AttendanceSessionStatus,
)


class AttendancePolicyRules(BaseModel):
    min_percentage_required: float = Field(default=75.0, ge=0, le=100)
    late_weight: float = Field(default=0.75, ge=0, le=1)
    present_weight: float = Field(default=1.0, ge=0, le=1)
    absent_weight: float = Field(default=0.0, ge=0, le=1)
    excused_weight: float = Field(default=1.0, ge=0, le=1)


class AttendancePolicyReference(Document):
    tenant_id: PydanticObjectId
    policy_code: str = "default"
    rules: AttendancePolicyRules = Field(default_factory=AttendancePolicyRules)
    is_active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "attendance_policy_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_code", ASCENDING)],
                unique=True,
                name="unique_attendance_policy_per_tenant",
            ),
        ]


class AttendanceSession(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    course_id: str
    course_code: str
    section: str
    subject_id: str | None = None
    class_session_id: PydanticObjectId | None = None
    session_date: date
    academic_year_label: str
    semester_label: str
    status: AttendanceSessionStatus = AttendanceSessionStatus.DRAFT
    submitted_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "attendance_sessions"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("course_code", ASCENDING),
                    ("section", ASCENDING),
                    ("session_date", ASCENDING),
                    ("faculty_user_id", ASCENDING),
                ],
                unique=True,
                name="unique_attendance_session_per_class_day",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("session_date", ASCENDING)],
                name="sessions_by_faculty_date",
            ),
        ]


class AttendanceRecord(Document):
    tenant_id: PydanticObjectId
    session_id: PydanticObjectId
    student_user_id: PydanticObjectId
    status: AttendanceMarkStatus
    remarks: str | None = Field(default=None, max_length=256)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "attendance_records"
        indexes = [
            IndexModel(
                [("session_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_record_per_student_session",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING)],
                name="records_by_student",
            ),
        ]


class AttendanceCorrectionRequest(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    session_id: PydanticObjectId
    student_user_id: PydanticObjectId | None = None
    requested_status: AttendanceMarkStatus | None = None
    reason: str = Field(max_length=1000)
    status: AttendanceCorrectionStatus = AttendanceCorrectionStatus.PENDING
    reviewer_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None

    class Settings:
        name = "attendance_correction_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("status", ASCENDING)],
                name="corrections_by_faculty",
            ),
        ]


class AttendanceReportSnapshot(BaseModel):
    """Embedded in service responses; not persisted separately in Phase 3."""

    course_code: str
    section: str
    generated_at: datetime
    summary: dict[str, Any]
