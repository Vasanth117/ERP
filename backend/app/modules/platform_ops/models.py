"""Platform health, incidents, and job registry."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.platform_ops.enums import BackgroundJobStatus, IncidentSeverity, IncidentStatus


class PlatformService(Document):
    code: str
    name: str
    service_type: str
    description: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "platform_services"
        indexes = [IndexModel([("code", ASCENDING)], unique=True, name="unique_platform_service_code")]


class ServiceHealthSnapshot(Document):
    captured_at: datetime = Field(default_factory=utcnow)
    overall_status: str
    components: dict[str, Any] = Field(default_factory=dict)
    queue_stats: dict[str, Any] = Field(default_factory=dict)
    worker_stats: dict[str, Any] = Field(default_factory=dict)
    integration_failure_count: int = 0

    class Settings:
        name = "service_health_snapshots"
        indexes = [IndexModel([("captured_at", DESCENDING)], name="health_snapshots_by_time")]


class PlatformIncident(Document):
    title: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN
    priority: int = Field(default=3, ge=1, le=5)
    assignee_id: PydanticObjectId | None = None
    created_by: PydanticObjectId
    related_service: str | None = None
    related_tenant_id: PydanticObjectId | None = None
    investigation_notes: list[dict[str, Any]] = Field(default_factory=list)
    escalated_to: PydanticObjectId | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "platform_incidents"
        indexes = [
            IndexModel([("status", ASCENDING), ("severity", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("assignee_id", ASCENDING), ("status", ASCENDING)]),
        ]


class IncidentAssignment(Document):
    incident_id: PydanticObjectId
    assignee_id: PydanticObjectId
    assigned_by: PydanticObjectId
    assigned_at: datetime = Field(default_factory=utcnow)
    unassigned_at: datetime | None = None

    class Settings:
        name = "incident_assignments"
        indexes = [IndexModel([("incident_id", ASCENDING), ("assigned_at", DESCENDING)])]


class IncidentHistory(Document):
    incident_id: PydanticObjectId
    from_status: str | None
    to_status: str
    actor_id: PydanticObjectId | None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "incident_history"
        indexes = [IndexModel([("incident_id", ASCENDING), ("created_at", DESCENDING)])]


class BackgroundJobRegistry(Document):
    job_type: str
    job_key: str
    status: BackgroundJobStatus = BackgroundJobStatus.PENDING
    safe_to_retry: bool = False
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: str | None = None
    tenant_id: PydanticObjectId | None = None
    summary: str = ""
    last_error: str | None = None
    scheduled_for: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None

    class Settings:
        name = "background_job_registry"
        indexes = [
            IndexModel([("job_type", ASCENDING), ("job_key", ASCENDING)], unique=True, name="unique_job_registry"),
            IndexModel([("status", ASCENDING), ("updated_at", DESCENDING)]),
        ]


class BackgroundJobFailure(Document):
    registry_id: PydanticObjectId
    job_type: str
    error_code: str
    error_message: str
    occurred_at: datetime = Field(default_factory=utcnow)
    retried: bool = False

    class Settings:
        name = "background_job_failures"
        indexes = [IndexModel([("registry_id", ASCENDING), ("occurred_at", DESCENDING)])]
