"""Official semester result publication (examination cell)."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus


class SemesterResultPublication(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    season_id: str
    academic_year_label: str
    semester_label: str
    status: SemesterResultPublicationStatus = SemesterResultPublicationStatus.PROCESSING
    overall_pass: bool | None = None
    gpa: float | None = None
    grading_policy_version: str | None = None
    published_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "semester_result_publications"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("season_id", ASCENDING),
                ],
                unique=True,
                name="unique_result_publication_per_student",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("published_at", DESCENDING)],
                name="results_by_status",
            ),
        ]


class SemesterResultSubjectMark(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    season_id: str
    course_code: str
    course_name: str | None = None
    attempt_number: int = Field(default=1, ge=1)
    is_arrear: bool = False
    theory_obtained: float | None = Field(default=None, ge=0)
    theory_max: float | None = Field(default=None, ge=0)
    practical_obtained: float | None = Field(default=None, ge=0)
    practical_max: float | None = Field(default=None, ge=0)
    internal_obtained: float | None = Field(default=None, ge=0)
    internal_max: float | None = Field(default=None, ge=0)
    external_obtained: float | None = Field(default=None, ge=0)
    external_max: float | None = Field(default=None, ge=0)
    total_obtained: float | None = Field(default=None, ge=0)
    total_max: float | None = Field(default=None, ge=0)
    pass_fail: str | None = None
    grade_letter: str | None = None
    credit_units: float | None = Field(default=None, ge=0)
    grade_points: float | None = Field(default=None, ge=0)
    grading_policy_version: str | None = None
    published: bool = False
    published_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "semester_result_subject_marks"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("season_id", ASCENDING),
                    ("course_code", ASCENDING),
                    ("attempt_number", ASCENDING),
                ],
                unique=True,
                name="unique_result_line",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("is_arrear", ASCENDING)],
                name="arrear_results_by_student",
            ),
        ]
