"""Training programs, enrollments, attendance and assessments."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrTrainingAttendanceStatus, HrTrainingEnrollmentStatus, HrTrainingProgramStatus


class HrTrainingProgram(Document):
    tenant_id: PydanticObjectId
    program_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str = Field(max_length=64)
    objectives: list[str] = Field(default_factory=list)
    trainer_name: str | None = None
    provider: str | None = None
    venue: str | None = None
    mode: str = "in_person"
    duration_hours: int = 0
    schedule: dict[str, Any] = Field(default_factory=dict)
    capacity: int = 0
    eligibility_rules: dict[str, Any] = Field(default_factory=dict)
    completion_criteria: dict[str, Any] = Field(default_factory=dict)
    status: HrTrainingProgramStatus = HrTrainingProgramStatus.DRAFT
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_training_programs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("program_code", ASCENDING)], unique=True, name="unique_training_program"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="training_programs_status"),
        ]


class HrTrainingEnrollment(Document):
    tenant_id: PydanticObjectId
    training_program_id: PydanticObjectId
    program_code: str = Field(max_length=64)
    employee_user_id: PydanticObjectId
    enrollment_source: str = Field(default="self", max_length=32)
    nominator_user_id: PydanticObjectId | None = None
    status: HrTrainingEnrollmentStatus = HrTrainingEnrollmentStatus.PENDING_APPROVAL
    waitlist_position: int | None = None
    certificate_issued: bool = False
    certificate_code: str | None = None
    completed_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_training_enrollments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("training_program_id", ASCENDING), ("employee_user_id", ASCENDING)],
                name="training_enrollment_unique_lookup",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="training_enrollments_status"),
        ]


class HrTrainingAttendance(Document):
    tenant_id: PydanticObjectId
    enrollment_id: PydanticObjectId
    training_program_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    session_code: str = Field(max_length=64)
    session_date: date
    status: HrTrainingAttendanceStatus = HrTrainingAttendanceStatus.ABSENT
    attended_minutes: int = 0
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_training_attendance"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("enrollment_id", ASCENDING), ("session_code", ASCENDING)],
                unique=True,
                name="unique_training_session_attendance",
            ),
        ]


class HrTrainingAssessment(Document):
    tenant_id: PydanticObjectId
    enrollment_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    attempt_number: int = 1
    score: str | None = None
    max_score: str | None = None
    passed: bool = False
    feedback: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_training_assessments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("enrollment_id", ASCENDING), ("attempt_number", ASCENDING)],
                unique=True,
                name="unique_training_assessment_attempt",
            ),
        ]


class EmployeeTrainingHistory(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    training_program_id: PydanticObjectId
    enrollment_id: PydanticObjectId
    program_code: str
    title: str
    completed: bool = False
    certificate_code: str | None = None
    completed_at: datetime | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_training_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("created_at", DESCENDING)], name="training_history_employee"),
        ]