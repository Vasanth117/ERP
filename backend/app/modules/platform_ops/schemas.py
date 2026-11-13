"""Platform operations API schemas."""

from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.modules.platform_ops.enums import IncidentSeverity, IncidentStatus
from app.modules.platform_ops.models import PlatformIncident


class QueueStatistics(BaseModel):
    pending: int
    failed: int
    retrying: int
    scheduled: int


class WorkerStatistics(BaseModel):
    status: str
    worker_count: int
    active_tasks: int
    detail: str | None = None


class BackgroundJobSummary(BaseModel):
    pending: int
    failed: int
    retrying: int
    scheduled: int
    integration_degraded: int


class PlatformHealthOverview(BaseModel):
    generated_at: datetime
    overall_status: str
    components: list[dict]
    queue_statistics: QueueStatistics
    worker_statistics: WorkerStatistics
    background_jobs: BackgroundJobSummary
    integration_failure_count: int
    open_alerts: int


class IncidentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=2000)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    priority: int = Field(default=3, ge=1, le=5)
    related_service: str | None = Field(default=None, max_length=64)
    related_tenant_id: PydanticObjectId | None = None


class IncidentAssignRequest(BaseModel):
    assignee_id: PydanticObjectId


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus
    priority: int | None = Field(default=None, ge=1, le=5)
    note: str | None = Field(default=None, max_length=500)


class IncidentNote(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    note: str = Field(min_length=3, max_length=2000)


class IncidentRead(BaseModel):
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    priority: int
    assignee_id: str | None
    related_service: str | None
    related_tenant_id: str | None
    investigation_notes: list[dict]
    created_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None

    @classmethod
    def from_document(cls, doc: PlatformIncident) -> "IncidentRead":
        return cls(
            id=str(doc.id),
            title=doc.title,
            description=doc.description,
            severity=doc.severity,
            status=doc.status,
            priority=doc.priority,
            assignee_id=str(doc.assignee_id) if doc.assignee_id else None,
            related_service=doc.related_service,
            related_tenant_id=str(doc.related_tenant_id) if doc.related_tenant_id else None,
            investigation_notes=doc.investigation_notes,
            created_at=doc.created_at,
            resolved_at=doc.resolved_at,
            closed_at=doc.closed_at,
        )
