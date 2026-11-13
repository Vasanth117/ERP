"""Security events and platform audit store."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class SecurityEvent(Document):
    code: str
    category: str
    severity: str = "medium"
    title: str
    description: str
    actor_id: PydanticObjectId | None = None
    tenant_id: PydanticObjectId | None = None
    status: str = "open"
    investigation_notes: list[dict[str, Any]] = Field(default_factory=list)
    incident_reference: str | None = None
    escalated_to: PydanticObjectId | None = None
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "security_events"
        indexes = [
            IndexModel([("status", ASCENDING), ("severity", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("category", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)]),
        ]


class PlatformAuditLog(Document):
    """Append-only platform audit (distinct from tenant audit_logs)."""

    actor_id: PydanticObjectId | None = None
    action: str
    module: str
    resource_type: str
    resource_id: str | None = None
    tenant_id: PydanticObjectId | None = None
    outcome: str = "success"
    request_id: str | None = None
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "platform_audit_logs"
        indexes = [
            IndexModel([("actor_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("module", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("action", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("created_at", DESCENDING)], name="platform_audit_by_time"),
        ]
