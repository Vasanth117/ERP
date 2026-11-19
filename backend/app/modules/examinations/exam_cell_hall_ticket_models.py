"""Examination cell — hall ticket collections."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_registration_enums import ExamHallTicketHistoryAction, ExamHallTicketStatus


class ExamHallTicket(Document):
    tenant_id: PydanticObjectId
    hall_ticket_id: str
    ticket_number: str
    verification_code: str
    exam_session_id: PydanticObjectId
    season_id: str | None = None
    registration_id: str
    student_user_id: PydanticObjectId
    institution_name: str | None = None
    roll_number: str | None = None
    student_name: str | None = None
    status: ExamHallTicketStatus = ExamHallTicketStatus.DRAFT
    storage_key: str | None = None
    payload_checksum: str | None = None
    document_token: str | None = None
    published_at: datetime | None = None
    revoked_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_hall_tickets"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("ticket_number", ASCENDING)],
                unique=True,
                name="unique_exam_hall_ticket_number",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("hall_ticket_id", ASCENDING)],
                unique=True,
                name="unique_exam_hall_ticket_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("exam_session_id", ASCENDING)],
                name="exam_hall_tickets_by_student_session",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("verification_code", ASCENDING)],
                unique=True,
                name="unique_exam_hall_ticket_verification",
            ),
        ]


class ExamHallTicketSubject(Document):
    tenant_id: PydanticObjectId
    hall_ticket_id: str
    course_code: str
    subject_code: str | None = None
    paper_code: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    centre_code: str | None = None
    room_label: str | None = None
    facility_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_hall_ticket_subjects"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("hall_ticket_id", ASCENDING), ("course_code", ASCENDING)],
                name="exam_hall_ticket_subjects_by_ticket",
            ),
        ]


class ExamHallTicketHistory(Document):
    tenant_id: PydanticObjectId
    hall_ticket_id: str
    action: ExamHallTicketHistoryAction
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_hall_ticket_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("hall_ticket_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_hall_ticket_history_timeline",
            ),
        ]