"""Faculty-owned MongoDB collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.faculty.enums import (
    AssignmentRole,
    AssignmentStatus,
    DashboardDateRange,
    FacultyActivityType,
    FacultyNotificationCategory,
    SessionUpdateRequestStatus,
    SessionUpdateRequestType,
)


class QualificationRecord(BaseModel):
    degree: str
    institution: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2100)


class ProfileDocumentRef(BaseModel):
    label: str
    file_id: str
    document_type: str = "other"


class FacultyProfile(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    employee_id: str | None = None
    faculty_code: str | None = None
    designation: str | None = None
    department_id: PydanticObjectId | None = None
    qualifications: list[QualificationRecord] = Field(default_factory=list)
    specialization: str | None = None
    contact_phone: str | None = None
    office_location: str | None = None
    bio: str | None = Field(default=None, max_length=4000)
    document_refs: list[ProfileDocumentRef] = Field(default_factory=list)
    employment_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Read-only HR fields copied for faculty display",
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_profiles"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_faculty_profile_per_user",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_code", ASCENDING)],
                unique=True,
                name="unique_faculty_code_per_tenant",
                partialFilterExpression={"faculty_code": {"$type": "string"}},
            ),
            IndexModel([("tenant_id", ASCENDING), ("department_id", ASCENDING)], name="faculty_by_department"),
        ]


class FacultyAssignment(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    course_id: str | None = None
    course_code: str
    course_name: str
    subject_id: str | None = None
    subject_code: str | None = None
    subject_name: str | None = None
    class_id: str | None = None
    section: str
    assignment_role: AssignmentRole = AssignmentRole.PRIMARY
    status: AssignmentStatus = AssignmentStatus.ACTIVE
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    allocation_locked: bool = True
    change_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("status", ASCENDING)],
                name="assignments_by_faculty_status",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                ],
                name="assignments_by_faculty_term",
            ),
        ]


class FacultyWorkload(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    lecture_hours: float = Field(default=0, ge=0)
    lab_hours: float = Field(default=0, ge=0)
    tutorial_hours: float = Field(default=0, ge=0)
    total_hours: float = Field(default=0, ge=0)
    credit_units: float = Field(default=0, ge=0)
    active_course_count: int = Field(default=0, ge=0)
    computed_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_workloads"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                ],
                unique=True,
                name="unique_workload_per_faculty_term",
            ),
        ]


class FacultyDashboardPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    default_date_range: DashboardDateRange = DashboardDateRange.WEEK
    pinned_widgets: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_dashboard_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_dashboard_prefs_per_user",
            ),
        ]


class FacultyActivityLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    activity_type: FacultyActivityType
    title: str
    description: str | None = None
    occurred_at: datetime = Field(default_factory=utcnow)
    source_module: str = "faculty"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_activity_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("occurred_at", DESCENDING)],
                name="faculty_activity_by_user",
            ),
        ]


class TeachingProgressNote(BaseModel):
    recorded_at: datetime = Field(default_factory=utcnow)
    unit_no: int | None = Field(default=None, ge=1)
    notes: str = Field(max_length=2000)
    percent_complete: float | None = Field(default=None, ge=0, le=100)


class CourseCoverage(Document):
    """Faculty-maintained coverage; does not alter approved syllabus."""

    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    course_id: str
    course_code: str
    section: str
    subject_id: str | None = None
    academic_year_label: str
    semester_label: str
    units_completed: list[int] = Field(default_factory=list)
    percent_complete: float = Field(default=0, ge=0, le=100)
    progress_log: list[TeachingProgressNote] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "course_coverage"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("faculty_user_id", ASCENDING),
                    ("course_id", ASCENDING),
                    ("section", ASCENDING),
                ],
                unique=True,
                name="unique_coverage_per_faculty_course_section",
            ),
        ]


class FacultyTimetableNotification(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    title: str
    body: str
    change_log_id: PydanticObjectId | None = None
    class_session_id: PydanticObjectId | None = None
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_timetable_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="timetable_notifications_by_user",
            ),
        ]


class ClassSessionUpdateRequest(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    class_session_id: PydanticObjectId
    request_type: SessionUpdateRequestType
    status: SessionUpdateRequestStatus = SessionUpdateRequestStatus.PENDING
    payload: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    class Settings:
        name = "class_session_update_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("status", ASCENDING)],
                name="session_requests_by_faculty",
            ),
        ]


class FacultyNotification(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    title: str
    body: str
    category: FacultyNotificationCategory = FacultyNotificationCategory.GENERAL
    read_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    @field_validator("title", "body")
    @classmethod
    def non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    class Settings:
        name = "faculty_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="faculty_notifications_by_user",
            ),
            IndexModel(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="faculty_notifications_ttl",
                partialFilterExpression={"expires_at": {"$type": "date"}},
            ),
        ]
