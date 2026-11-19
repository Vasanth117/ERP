"""Reservation policy, history and notifications."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class LibraryReservationPolicy(Document):
    tenant_id: PydanticObjectId
    branch_code: str | None = None
    hold_hours: int = Field(default=72, ge=1, le=168)
    max_active_per_member: int = Field(default=5, ge=1)
    reserve_only_when_unavailable: bool = True
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_reservation_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING)], unique=True, name="unique_reservation_policy"),
        ]


class LibraryReservationHistory(Document):
    tenant_id: PydanticObjectId
    reservation_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    changes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_reservation_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("reservation_id", ASCENDING), ("created_at", DESCENDING)],
                name="reservation_history_by_id",
            ),
        ]


class LibraryReservationNotification(Document):
    tenant_id: PydanticObjectId
    notification_id: str
    reservation_id: str
    member_user_id: PydanticObjectId
    channel: str = "in_app"
    title: str = Field(max_length=200)
    body: str = Field(max_length=2000)
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_reservation_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("notification_id", ASCENDING)],
                unique=True,
                name="unique_reservation_notification",
            ),
            IndexModel([("tenant_id", ASCENDING), ("member_user_id", ASCENDING), ("created_at", DESCENDING)], name="reservation_notifications_member"),
        ]