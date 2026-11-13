"""Faculty student support and mentoring collections."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class StudentMentoringRecord(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    course_code: str | None = None
    notes: str = Field(max_length=4000)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_mentoring_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("student_user_id", ASCENDING)],
                name="mentoring_by_faculty_student",
            ),
        ]


class StudentCounsellingSession(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    session_at: datetime
    summary: str = Field(max_length=4000)
    confidentiality_level: str = "restricted"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_counselling_sessions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("session_at", DESCENDING)],
                name="counselling_by_faculty",
            ),
        ]


class StudentAcademicFollowup(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    title: str = Field(max_length=200)
    action_item: str = Field(max_length=1000)
    due_date: date | None = None
    status: str = "pending"
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_academic_followups"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("status", ASCENDING)],
                name="followups_by_status",
            ),
        ]


class StudentImprovementPlan(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    course_code: str
    goals: list[str] = Field(default_factory=list)
    start_date: date
    target_date: date
    status: str = "active"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_improvement_plans"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)],
                name="improvement_plans_by_student",
            ),
        ]


class AcademicPerformanceSnapshot(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    course_code: str
    attendance_percentage: float = Field(ge=0, le=100)
    assessment_average: float = Field(ge=0, le=100)
    incomplete_tasks: int = Field(default=0, ge=0)
    captured_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_performance_snapshots"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("faculty_user_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("course_code", ASCENDING),
                    ("captured_at", DESCENDING),
                ],
                name="performance_snapshots",
            ),
        ]


class FacultyAcademicReport(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    report_type: str
    course_code: str | None = None
    student_user_id: PydanticObjectId | None = None
    payload: dict = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_academic_reports"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("generated_at", DESCENDING)],
                name="faculty_reports",
            ),
        ]
