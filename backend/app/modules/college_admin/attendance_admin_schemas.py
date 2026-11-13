"""Attendance administration API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.attendance.enums import AttendanceCorrectionStatus
from app.modules.attendance.models import AttendancePolicyRules
from app.modules.college_admin.attendance_admin_models import (
    AttendancePolicyAudience,
    InstitutionAttendancePolicy,
)


class AttendancePolicyUpsert(BaseModel):
    policy_code: str = Field(max_length=64)
    audience: AttendancePolicyAudience = AttendancePolicyAudience.STUDENT
    title: str = Field(max_length=200)
    rules: AttendancePolicyRules = Field(default_factory=AttendancePolicyRules)
    submission_deadline_hours: int = Field(default=24, ge=0, le=168)


class AttendancePolicyRead(BaseModel):
    policy_id: str
    policy_code: str
    audience: AttendancePolicyAudience
    title: str
    rules: AttendancePolicyRules
    submission_deadline_hours: int
    is_active: bool
    version: int

    @classmethod
    def from_document(cls, doc: InstitutionAttendancePolicy) -> "AttendancePolicyRead":
        return cls(
            policy_id=str(doc.id),
            policy_code=doc.policy_code,
            audience=doc.audience,
            title=doc.title,
            rules=doc.rules,
            submission_deadline_hours=doc.submission_deadline_hours,
            is_active=doc.is_active,
            version=doc.version,
        )


class DepartmentAttendanceSummary(BaseModel):
    department_id: str | None
    sessions_submitted: int
    pending_submissions: int
    pending_corrections: int


class CorrectionRequestRead(BaseModel):
    request_id: str
    faculty_user_id: str
    session_id: str
    student_user_id: str | None
    status: str
    reason: str
    created_at: datetime
    resolved_at: datetime | None


class CorrectionDecision(BaseModel):
    request_id: str
    decision: AttendanceCorrectionStatus
    reviewer_note: str | None = Field(default=None, max_length=2000)


class AttendanceReportGenerate(BaseModel):
    department_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None


class ComplianceSnapshotRead(BaseModel):
    snapshot_id: str
    department_id: str | None
    pending_submissions: int
    pending_corrections: int
    sessions_submitted: int
    students_below_threshold: int
    metrics: dict[str, Any]
    generated_at: datetime
