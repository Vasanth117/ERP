"""Audit log payloads."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.modules.audit.models import AuditLog


class AuditLogRead(BaseModel):
    id: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    tenant_id: str | None
    outcome: str
    request_id: str | None
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def from_document(cls, entry: AuditLog) -> "AuditLogRead":
        return cls(
            id=str(entry.id),
            actor_id=str(entry.actor_id) if entry.actor_id else None,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            tenant_id=str(entry.tenant_id) if entry.tenant_id else None,
            outcome=entry.outcome,
            request_id=entry.request_id,
            metadata=entry.metadata,
            created_at=entry.created_at,
        )
