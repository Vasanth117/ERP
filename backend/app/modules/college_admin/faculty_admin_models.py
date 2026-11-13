"""College admin faculty and employee administration collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.faculty.enums import AssignmentRole, AssignmentStatus
from app.modules.faculty.models import QualificationRecord


class FacultyEmploymentStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TRANSFERRED = "transferred"
    RESIGNED = "resigned"
    TERMINATED = "terminated"
    RETIRED = "retired"


class EmployeeRecord(Document):
    """Authoritative HR employee row (salary and restricted fields stay in `confidential_hr`)."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    employee_id: str | None = Field(default=None, max_length=64)
    employment_type: str | None = Field(default=None, max_length=64)
    joining_date: date | None = None
    designation: str | None = Field(default=None, max_length=120)
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    employment_status: FacultyEmploymentStatus = FacultyEmploymentStatus.ACTIVE
    is_faculty: bool = False
    confidential_hr: dict[str, Any] = Field(default_factory=dict)
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_employee_per_user",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_id", ASCENDING)],
                unique=True,
                name="unique_employee_id_per_tenant",
                partialFilterExpression={"employee_id": {"$type": "string"}},
            ),
        ]


class FacultyRecord(Document):
    """Institutional faculty record; syncs `faculty_profiles`."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    employee_record_id: PydanticObjectId | None = None
    faculty_code: str | None = Field(default=None, max_length=64)
    designation: str | None = None
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    specialization: str | None = Field(default=None, max_length=256)
    qualifications: list[QualificationRecord] = Field(default_factory=list)
    experience_years: float | None = Field(default=None, ge=0)
    employment_status: FacultyEmploymentStatus = FacultyEmploymentStatus.ACTIVE
    official_locked: bool = True
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_faculty_record_per_user",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_code", ASCENDING)],
                unique=True,
                name="unique_faculty_record_code",
                partialFilterExpression={"faculty_code": {"$type": "string"}},
            ),
        ]


class FacultyEmploymentHistory(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    event_type: str = Field(max_length=64)
    from_status: str | None = None
    to_status: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    effective_date: date | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_employment_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="faculty_employment_history_by_user",
            ),
        ]


class FacultyDepartmentAssignment(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    department_id: PydanticObjectId
    campus_id: PydanticObjectId | None = None
    is_primary: bool = True
    effective_from: date | None = None
    effective_to: date | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_department_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("is_primary", ASCENDING)],
                name="faculty_dept_assignments_by_user",
            ),
        ]


class FacultyTeachingAssignment(Document):
    """Admin assignment log; authoritative teaching row is `faculty_assignments`."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    faculty_assignment_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    course_code: str
    section: str
    assignment_role: AssignmentRole = AssignmentRole.PRIMARY
    status: AssignmentStatus = AssignmentStatus.ACTIVE
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_teaching_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("academic_year_label", ASCENDING)],
                name="faculty_teaching_by_user_year",
            ),
        ]


class FacultyWorkloadRecord(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    lecture_hours: float = 0
    lab_hours: float = 0
    tutorial_hours: float = 0
    total_hours: float = 0
    credit_units: float = 0
    note: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_workload_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="faculty_workload_history",
            ),
        ]


class FacultyDocumentReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    label: str = Field(max_length=200)
    file_id: str
    document_type: str = "other"
    authorized: bool = True
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_document_references"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING)], name="faculty_documents_by_user"),
        ]
