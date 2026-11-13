"""Authoritative course, curriculum, and enrollment records (institutional writes)."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class TeachingMaterialRef(BaseModel):
    title: str
    file_id: str | None = None
    url: str | None = None
    material_type: str = "document"


class SyllabusUnit(BaseModel):
    unit_no: int = Field(ge=1)
    title: str
    topics: list[str] = Field(default_factory=list)
    planned_hours: float = Field(default=0, ge=0)


class CourseRecord(Document):
    tenant_id: PydanticObjectId
    course_id: str
    course_code: str
    name: str
    description: str | None = None
    department_id: PydanticObjectId | None = None
    credit_units: float = Field(default=0, ge=0)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "courses"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_code", ASCENDING)],
                unique=True,
                name="unique_course_code_per_tenant",
            ),
            IndexModel([("tenant_id", ASCENDING), ("course_id", ASCENDING)], unique=True, name="unique_course_id"),
        ]


class SubjectRecord(Document):
    tenant_id: PydanticObjectId
    subject_id: str
    subject_code: str
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "subjects"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("subject_code", ASCENDING)],
                unique=True,
                name="unique_subject_code_per_tenant",
            ),
        ]


class CourseSubjectMapping(Document):
    tenant_id: PydanticObjectId
    course_id: str
    subject_id: str
    sequence_order: int = Field(default=1, ge=1)

    class Settings:
        name = "course_subject_mappings"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_id", ASCENDING), ("subject_id", ASCENDING)],
                unique=True,
                name="unique_course_subject_map",
            ),
        ]


class CurriculumRecord(Document):
    tenant_id: PydanticObjectId
    course_id: str
    academic_year_label: str
    semester_label: str
    version: str
    approved: bool = True
    locked: bool = True
    approved_at: datetime | None = None
    summary: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "curriculum_records"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("course_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                ],
                name="curriculum_by_course_term",
            ),
        ]


class SyllabusRecord(Document):
    tenant_id: PydanticObjectId
    course_id: str
    subject_id: str | None = None
    curriculum_id: str | None = None
    academic_year_label: str
    semester_label: str
    units: list[SyllabusUnit] = Field(default_factory=list)
    approved: bool = True
    locked: bool = True
    teaching_materials: list[TeachingMaterialRef] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "syllabus_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_id", ASCENDING), ("subject_id", ASCENDING)],
                name="syllabus_by_course_subject",
            ),
        ]


class CourseLearningOutcome(Document):
    tenant_id: PydanticObjectId
    course_id: str
    academic_year_label: str
    semester_label: str
    outcomes: list[str] = Field(default_factory=list)
    locked: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "course_learning_outcomes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_id", ASCENDING), ("academic_year_label", ASCENDING)],
                name="outcomes_by_course_year",
            ),
        ]


class SectionOffering(Document):
    tenant_id: PydanticObjectId
    section_id: str
    course_id: str
    course_code: str
    section_code: str
    batch_label: str | None = None
    academic_year_label: str
    semester_label: str

    class Settings:
        name = "section_offerings"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_id", ASCENDING), ("section_code", ASCENDING)],
                name="section_by_course",
            ),
        ]


class EnrollmentRosterEntry(Document):
    """Minimal roster fields permitted for faculty visibility."""

    tenant_id: PydanticObjectId
    course_id: str
    course_code: str
    section_code: str
    subject_id: str | None = None
    student_user_id: PydanticObjectId
    roll_number: str
    display_name: str
    academic_year_label: str
    semester_label: str

    class Settings:
        name = "enrollment_rosters"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_id", ASCENDING), ("section_code", ASCENDING)],
                name="roster_by_course_section",
            ),
        ]
