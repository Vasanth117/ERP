"""Security and platform audit schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.platform_security.models import PlatformAuditLog, SecurityEvent


class SecurityEventRead(BaseModel):
    id: str
    code: str
    category: str
    severity: str
    title: str
    description: str
    status: str
    actor_id: str | None
    tenant_id: str | None
    incident_reference: str | None
    investigation_notes: list[dict[str, Any]]
    created_at: datetime
    resolved_at: datetime | None

    @classmethod
    def from_document(cls, event: SecurityEvent) -> "SecurityEventRead":
        return cls(
            id=str(event.id),
            code=event.code,
            category=event.category,
            severity=event.severity,
            title=event.title,
            description=event.description,
            status=event.status,
            actor_id=str(event.actor_id) if event.actor_id else None,
            tenant_id=str(event.tenant_id) if event.tenant_id else None,
            incident_reference=event.incident_reference,
            investigation_notes=event.investigation_notes,
            created_at=event.created_at,
            resolved_at=event.resolved_at,
        )


class SecurityEventUpdate(BaseModel):
    status: str | None = None
    incident_reference: str | None = Field(default=None, max_length=128)
    escalated_to: str | None = None


class SecurityInvestigationNote(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    note: str = Field(min_length=3, max_length=2000)


class PlatformAuditLogRead(BaseModel):
    id: str
    actor_id: str | None
    action: str
    module: str
    resource_type: str
    resource_id: str | None
    tenant_id: str | None
    outcome: str
    request_id: str | None
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def from_document(cls, row: PlatformAuditLog) -> "PlatformAuditLogRead":
        return cls(
            id=str(row.id),
            actor_id=str(row.actor_id) if row.actor_id else None,
            action=row.action,
            module=row.module,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            tenant_id=str(row.tenant_id) if row.tenant_id else None,
            outcome=row.outcome,
            request_id=row.request_id,
            before_state=row.before_state,
            after_state=row.after_state,
            metadata=row.metadata,
            created_at=row.created_at,
        )


class PlatformAuditExportRow(BaseModel):
    id: str
    action: str
    module: str
    actor_id: str | None
    created_at: datetime
    outcome: str
