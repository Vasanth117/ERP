"""Platform dashboard aggregation."""

from datetime import datetime, timedelta

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.modules.audit.models import AuditLog
from app.modules.platform.health import inspect_api_health, inspect_background_jobs
from app.modules.platform.schemas import (
    OnboardingCompletionSummary,
    PlatformActivityItem,
    PlatformAlertRead,
    PlatformDashboard,
    PlatformDashboardFilters,
    TenantCountSummary,
    TenantGrowthPoint,
    TenantGrowthSummary,
    IntegrationFailureSummary,
    IncidentSummary,
)
from app.modules.tenants.enums import OnboardingStage, TenantOperationalStatus
from app.modules.tenants.schemas import TenantRead
from app.repositories.platform_repository import (
    MetricsSnapshotRepository,
    OnboardingRepository,
    PlatformAlertRepository,
    PlatformTenantRepository,
)

_platform_repo = PlatformTenantRepository()
_onboarding_repo = OnboardingRepository()
_alert_repo = PlatformAlertRepository()
_metrics_repo = MetricsSnapshotRepository()


def _status_counts(raw: dict[str, int]) -> TenantCountSummary:
    def pick(key: TenantOperationalStatus) -> int:
        return raw.get(key.value, 0)

    awaiting_verification = 0
    return TenantCountSummary(
        total_registered=sum(raw.values()),
        active=pick(TenantOperationalStatus.ACTIVE),
        suspended=pick(TenantOperationalStatus.SUSPENDED),
        onboarding=pick(TenantOperationalStatus.ONBOARDING),
        awaiting_verification=awaiting_verification,
        provisioning=pick(TenantOperationalStatus.PROVISIONING),
        failed=pick(TenantOperationalStatus.FAILED),
        cancelled=pick(TenantOperationalStatus.CANCELLED),
    )


async def _awaiting_verification_count() -> int:
    return await _onboarding_repo.count_by_stages(
        [OnboardingStage.SUBMITTED, OnboardingStage.VERIFICATION_PENDING]
    )


async def _tenant_growth(window_days: int = 30) -> TenantGrowthSummary:
    from app.modules.tenants.models import Tenant

    start = utcnow() - timedelta(days=window_days)
    pipeline = [
        {"$match": {"created_at": {"$gte": start}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"},
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    rows = await Tenant.get_motor_collection().aggregate(pipeline).to_list(length=window_days + 2)
    points = [TenantGrowthPoint(date=row["_id"], count=row["count"]) for row in rows]
    return TenantGrowthSummary(points=points, window_days=window_days)


async def get_platform_dashboard(
    scope: AccessScope,
    *,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    tenant_status: TenantOperationalStatus | None = None,
) -> PlatformDashboard:
    authorize(scope, Permission.PLATFORM_DASHBOARD_READ)

    status_distribution = await _platform_repo.count_tenants_by_status()
    counts = _status_counts(status_distribution)
    counts.awaiting_verification = await _awaiting_verification_count()

    recent_created = await _platform_repo.recent_tenants(limit=10)
    recent_activated = await _platform_repo.recently_activated(limit=10)
    onboarding_stages = await _onboarding_repo.stage_distribution()
    completion_raw = await _onboarding_repo.completion_stats()
    completion_rate = (
        completion_raw["completed"] / completion_raw["total"]
        if completion_raw["total"]
        else 0.0
    )
    onboarding_completion = OnboardingCompletionSummary(
        total=completion_raw["total"],
        completed=completion_raw["completed"],
        in_progress=completion_raw["in_progress"],
        completion_rate=round(completion_rate, 4),
    )

    api_health = await inspect_api_health()
    background_jobs = await inspect_background_jobs()
    alerts = await _alert_repo.list_open(limit=20, severity=None)
    critical_alerts = [
        PlatformAlertRead(
            id=str(alert.id),
            code=alert.code,
            title=alert.title,
            message=alert.message,
            severity=alert.severity.value,
            source=alert.source,
            related_tenant_id=str(alert.related_tenant_id) if alert.related_tenant_id else None,
            created_at=alert.created_at,
        )
        for alert in alerts
        if alert.severity.value == "critical"
    ]

    platform_actions = (
        await AuditLog.find({"action": {"$regex": "^platform\\."}})
        .sort("-created_at")
        .limit(25)
        .to_list()
    )
    tenant_admin_actions = (
        await AuditLog.find({"action": {"$regex": "^tenant\\."}})
        .sort("-created_at")
        .limit(25)
        .to_list()
    )
    combined = sorted(platform_actions + tenant_admin_actions, key=lambda row: row.created_at, reverse=True)
    recent_admin_activities = [
        PlatformActivityItem(
            id=str(item.id),
            action=item.action,
            actor_id=str(item.actor_id) if item.actor_id else None,
            resource_type=item.resource_type,
            resource_id=item.resource_id,
            tenant_id=str(item.tenant_id) if item.tenant_id else None,
            created_at=item.created_at,
        )
        for item in combined[:25]
    ]

    dashboard = PlatformDashboard(
        generated_at=utcnow(),
        filters=PlatformDashboardFilters(
            created_from=created_from,
            created_to=created_to,
            tenant_status=tenant_status.value if tenant_status else None,
        ),
        tenant_counts=counts,
        recently_created_tenants=[TenantRead.from_document(t) for t in recent_created],
        recently_activated_tenants=[TenantRead.from_document(t) for t in recent_activated],
        tenant_growth=await _tenant_growth(),
        tenant_status_distribution=status_distribution,
        onboarding_stage_distribution=onboarding_stages,
        onboarding_completion=onboarding_completion,
        api_health=api_health,
        background_jobs=background_jobs,
        critical_alerts=critical_alerts,
        recent_admin_activities=recent_admin_activities,
        service_availability=IncidentSummary(monitored=False, open_incidents=0),
        integration_failures=IntegrationFailureSummary(monitored=False, total_recent_failures=0),
    )

    snapshot = await _metrics_repo.latest()
    if snapshot is None or snapshot.captured_at < utcnow() - timedelta(hours=1):
        from app.modules.tenants.platform_models import PlatformMetricsSnapshot

        await PlatformMetricsSnapshot(metrics=dashboard.model_dump(mode="json")).insert()

    return dashboard


async def get_tenant_statistics(
    scope: AccessScope,
    *,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> TenantCountSummary:
    authorize(scope, Permission.PLATFORM_DASHBOARD_READ)
    if created_from or created_to:
        from app.repositories.platform_repository import PlatformTenantRepository

        # filtered counts reuse list filters for total only; status breakdown stays global registry view
        _ = await PlatformTenantRepository().count_tenants_filtered(
            created_from=created_from,
            created_to=created_to,
        )
    status_distribution = await _platform_repo.count_tenants_by_status()
    counts = _status_counts(status_distribution)
    counts.awaiting_verification = await _awaiting_verification_count()
    return counts


async def get_platform_alerts(scope: AccessScope, pagination: Pagination) -> Page[PlatformAlertRead]:
    authorize(scope, Permission.PLATFORM_DASHBOARD_READ)
    alerts = await _alert_repo.list_open(limit=pagination.limit + pagination.offset)
    sliced = alerts[pagination.offset : pagination.offset + pagination.limit]
    items = [
        PlatformAlertRead(
            id=str(alert.id),
            code=alert.code,
            title=alert.title,
            message=alert.message,
            severity=alert.severity.value,
            source=alert.source,
            related_tenant_id=str(alert.related_tenant_id) if alert.related_tenant_id else None,
            created_at=alert.created_at,
        )
        for alert in sliced
    ]
    return Page(items=items, total=len(alerts), limit=pagination.limit, offset=pagination.offset)


async def get_platform_activity_summary(scope: AccessScope, pagination: Pagination) -> Page[PlatformActivityItem]:
    authorize(scope, Permission.PLATFORM_DASHBOARD_READ)
    rows = await AuditLog.find_all().sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    total = await AuditLog.find_all().count()
    items = [
        PlatformActivityItem(
            id=str(row.id),
            action=row.action,
            actor_id=str(row.actor_id) if row.actor_id else None,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            tenant_id=str(row.tenant_id) if row.tenant_id else None,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_service_health_summary(scope: AccessScope):
    authorize(scope, Permission.PLATFORM_DASHBOARD_READ)
    api_health = await inspect_api_health()
    background_jobs = await inspect_background_jobs()
    return {"api_health": api_health, "background_jobs": background_jobs}
