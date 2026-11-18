"""Reliable post-commit domain events (notifications processed outside transactions)."""

from datetime import datetime
from enum import Enum

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class OutboxEventStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DomainOutboxEvent(Document):
    tenant_id: PydanticObjectId
    event_type: str = Field(max_length=64)
    aggregate_type: str = Field(max_length=64)
    aggregate_id: str = Field(max_length=64)
    payload: dict = Field(default_factory=dict)
    status: OutboxEventStatus = OutboxEventStatus.PENDING
    idempotency_key: str = Field(max_length=128)
    created_at: datetime = Field(default_factory=utcnow)
    processed_at: datetime | None = None

    class Settings:
        name = "domain_outbox_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_outbox_idempotency",
            ),
            IndexModel([("status", ASCENDING), ("created_at", ASCENDING)], name="outbox_pending"),
        ]