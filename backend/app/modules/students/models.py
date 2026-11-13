"""Student-owned MongoDB collections (portal layer).

Official academic, attendance, marks and fee figures are snapshots or aggregated
reads — students cannot mutate authoritative institutional records through these documents.
"""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.enums import (
    AcademicStanding,
    DashboardDateRange,
    ProgressionStatus,
    StudentAcademicRequestStatus,
    StudentAcademicRequestType,
    StudentActivityType,
    StudentEnrollmentStatus,
)


class ProfileDocumentRef(BaseModel):
    label: str
    file_id: str
    document_type: str = "other"
    authorized: bool = True


class EmergencyContact(BaseModel):
    name: str = Field(max_length=120)
    phone: str = Field(max_length=32)
    relationship: str | None = Field(default=None, max_length=64)


class StudentProfile(Document):
    """Permitted self-service fields plus read-only admission identity."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    student_id: str | None = Field(default=None, description="Official student identifier")
    roll_number: str | None = None
    admission_number: str | None = None
    admission_date: date | None = None
    department_id: PydanticObjectId | None = None
    programme_code: str | None = None
    programme_name: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    alternate_email: str | None = Field(default=None, max_length=254)
    permanent_address: str | None = Field(default=None, max_length=1000)
    current_address: str | None = Field(default=None, max_length=1000)
    emergency_contacts: list[EmergencyContact] = Field(default_factory=list)
    bio: str | None = Field(default=None, max_length=2000)
    profile_photo_ref: str | None = None
    document_refs: list[ProfileDocumentRef] = Field(default_factory=list)
    official_locked: bool = Field(default=True, description="Admission fields managed by admins only")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_profiles"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_student_profile_per_user",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("roll_number", ASCENDING)],
                unique=True,
                name="unique_roll_per_tenant",
                partialFilterExpression={"roll_number": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_id", ASCENDING)],
                name="student_by_official_id",
            ),
        ]


class StudentAcademicRecord(Document):
    """Read-only academic standing snapshot for the active term."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    enrollment_status: StudentEnrollmentStatus = StudentEnrollmentStatus.ACTIVE
    academic_standing: AcademicStanding = AcademicStanding.UNKNOWN
    progression_status: ProgressionStatus = ProgressionStatus.PENDING
    promotion_eligible: bool | None = None
    eligibility_summary: dict[str, Any] = Field(default_factory=dict)
    credits_registered: float = Field(default=0, ge=0)
    credits_earned: float = Field(default=0, ge=0)
    cgpa: float | None = Field(default=None, ge=0, le=10)
    fee_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Outstanding fee summary; Finance module is source of truth",
    )
    record_locked: bool = True
    effective_from: date | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_academic_records"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                ],
                unique=True,
                name="unique_academic_record_per_term",
            ),
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING)], name="academic_record_by_student"),
        ]


class StudentEnrollment(Document):
    """Approved enrollment line for a term (mirrors roster with student-visible metadata)."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    course_id: str
    course_code: str
    course_name: str
    section_code: str
    department_id: PydanticObjectId | None = None
    status: StudentEnrollmentStatus = StudentEnrollmentStatus.ACTIVE
    approved_at: datetime | None = None
    is_official: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_enrollments"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                    ("course_code", ASCENDING),
                ],
                name="enrollment_by_student_term_course",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("status", ASCENDING)],
                name="enrollment_by_student_status",
            ),
        ]


class StudentEnrollmentHistory(Document):
    """Archived term-level enrollment summaries."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    programme_code: str | None = None
    section_code: str | None = None
    courses: list[dict[str, str]] = Field(default_factory=list)
    final_standing: AcademicStanding = AcademicStanding.UNKNOWN
    credits_earned: float = Field(default=0, ge=0)
    cgpa: float | None = Field(default=None, ge=0, le=10)
    closed_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_enrollment_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("closed_at", DESCENDING)],
                name="enrollment_history_by_student",
            ),
        ]


class StudentDashboardPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    default_date_range: DashboardDateRange = DashboardDateRange.WEEK
    show_finance_summary: bool = True
    show_attendance_summary: bool = True
    pinned_widgets: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_dashboard_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_student_dashboard_prefs",
            ),
        ]


class StudentAcademicRequest(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_type: StudentAcademicRequestType
    academic_year_label: str
    semester_label: str
    title: str = Field(max_length=200)
    description: str = Field(max_length=4000)
    payload: dict[str, Any] = Field(default_factory=dict)
    status: StudentAcademicRequestStatus = StudentAcademicRequestStatus.SUBMITTED
    reviewer_note: str | None = Field(default=None, max_length=2000)
    submitted_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        return value.strip()

    class Settings:
        name = "student_academic_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("status", ASCENDING)],
                name="academic_requests_by_student_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("submitted_at", DESCENDING)],
                name="academic_requests_by_student_time",
            ),
        ]


class StudentActivityLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    activity_type: StudentActivityType
    title: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_activity_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="student_activity_by_user",
            ),
        ]
