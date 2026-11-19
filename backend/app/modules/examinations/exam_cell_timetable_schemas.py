"""Examination cell — timetable schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_timetable_enums import (
    ExamScheduleApprovalDecision,
    ExamTimetableEntryStatus,
    ExamTimetableStatus,
)
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable, ExamTimetableEntry, ExamTimetableRevision


class ExamTimetableCreate(BaseModel):
    exam_session_id: str
    title: str = Field(min_length=2, max_length=200)
    shift_labels: list[str] = Field(default_factory=list, max_length=20)


class ExamTimetableEntryCreate(BaseModel):
    entry_code: str = Field(min_length=2, max_length=32)
    course_code: str = Field(min_length=2, max_length=32)
    subject_code: str | None = Field(default=None, max_length=32)
    paper_code: str | None = Field(default=None, max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=32)
    section: str | None = Field(default=None, max_length=16)
    scheduled_start: datetime
    scheduled_end: datetime
    shift_label: str | None = Field(default=None, max_length=32)
    session_label: str | None = Field(default=None, max_length=32)
    centre_code: str | None = Field(default=None, max_length=32)
    facility_id: str | None = Field(default=None, max_length=64)
    room_label: str | None = Field(default=None, max_length=64)
    campus_id: str | None = None
    metadata: dict = Field(default_factory=dict)

    @field_validator("entry_code", "course_code")
    @classmethod
    def normalize_upper(cls, value: str) -> str:
        return value.strip().upper()


class ExamTimetableEntryReschedule(BaseModel):
    scheduled_start: datetime
    scheduled_end: datetime
    centre_code: str | None = None
    facility_id: str | None = None
    room_label: str | None = None
    note: str | None = Field(default=None, max_length=500)


class ExamTimetableApprovalRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ExamTimetableValidationResult(BaseModel):
    conflict_count: int
    conflicts: list[dict] = Field(default_factory=list)


class ExamTimetableRead(BaseModel):
    id: str
    timetable_id: str
    exam_session_id: str
    title: str
    status: ExamTimetableStatus
    revision_number: int
    published_version: int
    shift_labels: list[str]
    entry_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    @classmethod
    def from_document(cls, doc: ExamTimetable, *, entry_count: int = 0) -> "ExamTimetableRead":
        return cls(
            id=str(doc.id),
            timetable_id=doc.timetable_id,
            exam_session_id=str(doc.exam_session_id),
            title=doc.title,
            status=doc.status,
            revision_number=doc.revision_number,
            published_version=doc.published_version,
            shift_labels=list(doc.shift_labels),
            entry_count=entry_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            published_at=doc.published_at,
        )


class ExamTimetableEntryRead(BaseModel):
    id: str
    entry_code: str
    course_code: str
    subject_code: str | None
    paper_code: str | None
    programme_code: str | None
    batch_label: str | None
    section: str | None
    student_group_label: str
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int
    shift_label: str | None
    session_label: str | None
    centre_code: str | None
    facility_id: str | None
    room_label: str | None
    campus_id: str | None
    status: ExamTimetableEntryStatus

    @classmethod
    def from_document(cls, doc: ExamTimetableEntry) -> "ExamTimetableEntryRead":
        return cls(
            id=str(doc.id),
            entry_code=doc.entry_code,
            course_code=doc.course_code,
            subject_code=doc.subject_code,
            paper_code=doc.paper_code,
            programme_code=doc.programme_code,
            batch_label=doc.batch_label,
            section=doc.section,
            student_group_label=doc.student_group_label,
            scheduled_start=doc.scheduled_start,
            scheduled_end=doc.scheduled_end,
            duration_minutes=doc.duration_minutes,
            shift_label=doc.shift_label,
            session_label=doc.session_label,
            centre_code=doc.centre_code,
            facility_id=doc.facility_id,
            room_label=doc.room_label,
            campus_id=str(doc.campus_id) if doc.campus_id else None,
            status=doc.status,
        )


class ExamTimetableRevisionRead(BaseModel):
    revision_number: int
    change_type: str
    summary: str
    actor_id: str | None
    created_at: datetime

    @classmethod
    def from_document(cls, doc: ExamTimetableRevision) -> "ExamTimetableRevisionRead":
        return cls(
            revision_number=doc.revision_number,
            change_type=doc.change_type.value,
            summary=doc.summary,
            actor_id=str(doc.actor_id) if doc.actor_id else None,
            created_at=doc.created_at,
        )


class ExamScheduleApprovalRead(BaseModel):
    approval_id: str
    decision: ExamScheduleApprovalDecision
    actor_id: str | None
    note: str | None
    created_at: datetime