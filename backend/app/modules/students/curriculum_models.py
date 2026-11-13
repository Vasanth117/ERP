"""Student portal curriculum and registration reference collections.

These documents point at central academic records (`courses`, `syllabus_records`, …) and hold
programme-specific registration configuration. Students never write official curriculum data.
"""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.registration_enums import (
    CourseRegistrationStatus,
    CourseRegistrationType,
    RegistrationRequestStatus,
)


class SyllabusRevisionEvent(BaseModel):
    version: str
    effective_at: datetime
    summary: str | None = None


class CourseCatalogReference(Document):
    """Programme-term course offering pointer for student catalogue and registration."""

    tenant_id: PydanticObjectId
    programme_code: str
    academic_year_label: str
    semester_label: str
    course_id: str
    course_code: str
    registration_type: CourseRegistrationType = CourseRegistrationType.CORE
    is_open_for_registration: bool = True
    show_faculty: bool = True
    credit_units: float = Field(default=0, ge=0)
    max_capacity: int | None = Field(default=None, ge=1)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "course_catalog_references"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                    ("course_code", ASCENDING),
                ],
                unique=True,
                name="unique_course_catalog_entry",
            ),
        ]


class SubjectCatalogReference(Document):
    tenant_id: PydanticObjectId
    programme_code: str
    academic_year_label: str
    semester_label: str
    course_id: str
    subject_id: str
    subject_code: str
    credit_units: float = Field(default=0, ge=0)
    sequence_order: int = Field(default=1, ge=1)

    class Settings:
        name = "subject_catalog_references"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("course_id", ASCENDING),
                    ("subject_id", ASCENDING),
                ],
                unique=True,
                name="unique_subject_catalog_ref",
            ),
        ]


class CurriculumReference(Document):
    """Approved curriculum pointer plus student-visible regulations."""

    tenant_id: PydanticObjectId
    programme_code: str
    academic_year_label: str
    semester_label: str
    primary_course_id: str
    central_version: str | None = None
    academic_regulations: list[str] = Field(default_factory=list)
    locked: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "curriculum_references"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                ],
                unique=True,
                name="unique_curriculum_ref_per_term",
            ),
        ]


class SyllabusReference(Document):
    tenant_id: PydanticObjectId
    course_id: str
    subject_id: str | None = None
    academic_year_label: str
    semester_label: str
    revision_history: list[SyllabusRevisionEvent] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "syllabus_references"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("course_id", ASCENDING),
                    ("subject_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                ],
                name="syllabus_ref_lookup",
            ),
        ]


class CoursePrerequisite(Document):
    tenant_id: PydanticObjectId
    course_id: str
    course_code: str
    prerequisite_course_ids: list[str] = Field(default_factory=list)
    corequisite_course_ids: list[str] = Field(default_factory=list)
    min_cgpa: float | None = Field(default=None, ge=0, le=10)
    notes: str | None = Field(default=None, max_length=1000)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "course_prerequisites"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_id", ASCENDING)],
                unique=True,
                name="unique_prereq_per_course",
            ),
        ]


class ElectiveGroup(Document):
    tenant_id: PydanticObjectId
    programme_code: str
    academic_year_label: str
    semester_label: str
    group_code: str
    title: str
    description: str | None = None
    min_selections: int = Field(default=1, ge=0)
    max_selections: int = Field(default=1, ge=1)
    min_credits: float = Field(default=0, ge=0)
    max_credits: float = Field(default=99, ge=0)
    is_active: bool = True

    class Settings:
        name = "elective_groups"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                    ("group_code", ASCENDING),
                ],
                unique=True,
                name="unique_elective_group",
            ),
        ]


class ElectiveOption(Document):
    tenant_id: PydanticObjectId
    elective_group_id: PydanticObjectId
    course_id: str
    course_code: str
    course_name: str
    credit_units: float = Field(ge=0)
    max_seats: int | None = Field(default=None, ge=1)
    seats_taken: int = Field(default=0, ge=0)
    is_active: bool = True

    class Settings:
        name = "elective_options"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("elective_group_id", ASCENDING), ("course_id", ASCENDING)],
                unique=True,
                name="unique_elective_option",
            ),
        ]


class RegistrationPolicyReference(Document):
    tenant_id: PydanticObjectId
    programme_code: str
    academic_year_label: str
    semester_label: str
    min_credits: float = Field(default=12, ge=0)
    max_credits: float = Field(default=26, ge=0)
    registration_open_at: datetime
    registration_close_at: datetime
    modification_deadline: datetime
    allow_self_registration: bool = True
    require_admin_approval: bool = True
    check_timetable_conflicts: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "registration_policy_references"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                ],
                unique=True,
                name="unique_registration_policy",
            ),
        ]


class StudentCourseRegistration(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    programme_code: str
    course_id: str
    course_code: str
    section_code: str | None = None
    registration_type: CourseRegistrationType
    credit_units: float = Field(ge=0)
    status: CourseRegistrationStatus = CourseRegistrationStatus.DRAFT
    approved_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_course_registrations"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                    ("course_id", ASCENDING),
                ],
                unique=True,
                name="unique_student_course_registration",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("status", ASCENDING)],
                name="registrations_by_student_status",
            ),
        ]


class StudentElectiveSelection(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    elective_group_id: PydanticObjectId
    course_id: str
    course_code: str
    status: CourseRegistrationStatus = CourseRegistrationStatus.DRAFT
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_elective_selections"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("elective_group_id", ASCENDING),
                    ("course_id", ASCENDING),
                ],
                unique=True,
                name="unique_elective_selection",
            ),
        ]


class RegistrationSelectionItem(BaseModel):
    course_id: str
    course_code: str
    section_code: str | None = None
    registration_type: CourseRegistrationType = CourseRegistrationType.ELECTIVE
    elective_group_id: str | None = None


class CourseRegistrationRequest(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    programme_code: str
    status: RegistrationRequestStatus = RegistrationRequestStatus.DRAFT
    selections: list[RegistrationSelectionItem] = Field(default_factory=list)
    validation_snapshot: dict[str, Any] = Field(default_factory=dict)
    reviewer_note: str | None = None
    submitted_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "course_registration_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("status", ASCENDING)],
                name="registration_requests_by_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("submitted_at", DESCENDING)],
                name="registration_requests_by_time",
            ),
        ]


class RegistrationHistoryEntry(Document):
    """Immutable audit trail of registration lifecycle events."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    course_id: str
    course_code: str
    action: str
    previous_status: str | None = None
    new_status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_registration_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("occurred_at", DESCENDING)],
                name="registration_history_by_student",
            ),
        ]
