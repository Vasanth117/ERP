"""Platform dashboard response schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.tenants.schemas import TenantRead


class TenantCountSummary(BaseModel):
    total_registered: int
    active: int
    suspended: int
    onboarding: int
    awaiting_verification: int
    provisioning: int
    failed: int
    cancelled: int


class TenantGrowthPoint(BaseModel):
    date: str
    count: int


class TenantGrowthSummary(BaseModel):
    points: list[TenantGrowthPoint]
    window_days: int


class OnboardingCompletionSummary(BaseModel):
    total: int
    completed: int
    in_progress: int
    completion_rate: float


class ServiceHealthComponent(BaseModel):
    name: str
    status: Literal["healthy", "degraded", "unavailable", "unknown"]
    detail: str | None = None


class ServiceHealthSummary(BaseModel):
    overall: Literal["healthy", "degraded", "unavailable", "unknown"]
    components: list[ServiceHealthComponent]


class BackgroundJobHealthSummary(BaseModel):
    monitored: bool
    status: Literal["healthy", "degraded", "unavailable", "unknown"]
    detail: str | None = None
    pending_provisioning_jobs: int = 0
    failed_provisioning_jobs: int = 0


class PlatformAlertRead(BaseModel):
    id: str
    code: str
    title: str
    message: str
    severity: str
    source: str
    related_tenant_id: str | None
    created_at: datetime


class PlatformActivityItem(BaseModel):
    id: str
    action: str
    actor_id: str | None
    resource_type: str
    resource_id: str | None
    tenant_id: str | None
    created_at: datetime


class IntegrationFailureSummary(BaseModel):
    monitored: bool
    total_recent_failures: int = 0
    items: list[dict[str, Any]] = Field(default_factory=list)


class IncidentSummary(BaseModel):
    monitored: bool
    open_incidents: int = 0
    items: list[dict[str, Any]] = Field(default_factory=list)


class PlatformDashboardFilters(BaseModel):
    created_from: datetime | None = None
    created_to: datetime | None = None
    tenant_status: str | None = None


class PlatformDashboard(BaseModel):
    generated_at: datetime
    filters: PlatformDashboardFilters
    tenant_counts: TenantCountSummary
    recently_created_tenants: list[TenantRead]
    recently_activated_tenants: list[TenantRead]
    tenant_growth: TenantGrowthSummary
    tenant_status_distribution: dict[str, int]
    onboarding_stage_distribution: dict[str, int]
    onboarding_completion: OnboardingCompletionSummary
    api_health: ServiceHealthSummary
    background_jobs: BackgroundJobHealthSummary
    critical_alerts: list[PlatformAlertRead]
    recent_admin_activities: list[PlatformActivityItem]
    service_availability: IncidentSummary
    integration_failures: IntegrationFailureSummary
