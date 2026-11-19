"""Examination cell — exam timetable collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_timetable_enums import (
    ExamScheduleApprovalDecision,
    ExamTimetableEntryStatus,
    ExamTimetableRevisionType,
    ExamTimetableStatus,
)


class ExamTimetable(Document):
    tenant_id: PydanticObjectId
    timetable_id: str
    exam_session_id: PydanticObjectId
    title: str
    status: ExamTimetableStatus = ExamTimetableStatus.DRAFT
    revision_number: int = 1
    published_version: int = 0
    shift_labels: list[str] = Field(default_factory=list)
    created_by: PydanticObjectId | None = None
    approved_by: PydanticObjectId | None = None
    published_by: PydanticObjectId | None = None
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_timetables"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("timetable_id", ASCENDING)],
                unique=True,
                name="unique_exam_timetable_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("status", ASCENDING)],
                name="exam_timetables_by_session",
            ),
        ]


class ExamTimetableEntry(Document):
    tenant_id: PydanticObjectId
    timetable_id: PydanticObjectId
    entry_code: str
    course_code: str
    subject_code: str | None = None
    paper_code: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section: str | None = None
    student_group_label: str
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int = Field(ge=1)
    shift_label: str | None = None
    session_label: str | None = None
    centre_code: str | None = None
    facility_id: str | None = None
    room_label: str | None = None
    campus_id: PydanticObjectId | None = None
    status: ExamTimetableEntryStatus = ExamTimetableEntryStatus.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_timetable_entries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("timetable_id", ASCENDING), ("entry_code", ASCENDING)],
                unique=True,
                name="unique_exam_timetable_entry",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("scheduled_start", ASCENDING)],
                name="exam_timetable_entries_schedule",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("centre_code", ASCENDING), ("room_label", ASCENDING), ("scheduled_start", ASCENDING)],
                name="exam_timetable_room_schedule",
                sparse=True,
            ),
        ]


class ExamTimetableRevision(Document):
    tenant_id: PydanticObjectId
    timetable_id: PydanticObjectId
    revision_number: int
    change_type: ExamTimetableRevisionType
    summary: str
    previous_values: dict[str, Any] = Field(default_factory=dict)
    new_values: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_timetable_revisions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("timetable_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_timetable_revision_timeline",
            ),
        ]


class ExamScheduleApproval(Document):
    tenant_id: PydanticObjectId
    timetable_id: PydanticObjectId
    approval_id: str
    decision: ExamScheduleApprovalDecision = ExamScheduleApprovalDecision.PENDING
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_schedule_approvals"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("approval_id", ASCENDING)],
                unique=True,
                name="unique_exam_schedule_approval",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("timetable_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_schedule_approvals_by_timetable",
            ),
        ]