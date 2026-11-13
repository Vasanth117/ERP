"""Authoritative hall tickets (examination cell publishes)."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.examination_registration_enums import HallTicketPublicationStatus


class ExaminationHallTicket(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    season_id: str
    ticket_number: str
    status: HallTicketPublicationStatus = HallTicketPublicationStatus.DRAFT
    roll_number: str | None = None
    student_name: str | None = None
    centre_code: str | None = None
    centre_name: str | None = None
    examination_sessions: list[dict[str, Any]] = Field(default_factory=list)
    instructions: str | None = None
    document_token: str | None = None
    payload_checksum: str | None = None
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_hall_tickets"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("ticket_number", ASCENDING)],
                unique=True,
                name="unique_hall_ticket_number",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("season_id", ASCENDING),
                ],
                unique=True,
                name="unique_hall_ticket_per_student_season",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING)],
                name="hall_tickets_by_status",
            ),
        ]
