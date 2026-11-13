"""Platform dependency health probes (dashboard-compatible)."""

from app.modules.platform.schemas import (
    BackgroundJobHealthSummary,
    ServiceHealthComponent,
    ServiceHealthSummary,
)
from app.modules.platform_ops.probes import probe_celery, probe_mongodb, probe_rabbitmq, probe_redis
from app.modules.tenants.enums import ProvisioningJobStatus
from app.repositories.platform_repository import ProvisioningRepository

_provisioning_repo = ProvisioningRepository()


async def inspect_api_health() -> ServiceHealthSummary:
    probes = [
        await probe_mongodb(),
        await probe_redis(),
        await probe_rabbitmq(),
        await probe_celery(),
    ]
    components = [
        ServiceHealthComponent(
            name=item["name"],
            status=item["status"],
            detail=item.get("detail"),
        )
        for item in probes
    ]
    statuses = {component.status for component in components}
    if "unavailable" in statuses:
        overall = "unavailable"
    elif "unknown" in statuses or "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"
    return ServiceHealthSummary(overall=overall, components=components)


async def inspect_background_jobs() -> BackgroundJobHealthSummary:
    pending = await _provisioning_repo.count_by_status(ProvisioningJobStatus.PENDING)
    failed = await _provisioning_repo.count_by_status(ProvisioningJobStatus.FAILED)
    return BackgroundJobHealthSummary(
        monitored=True,
        status="degraded" if failed else "healthy",
        detail=None if not failed else "failed_provisioning_jobs_present",
        pending_provisioning_jobs=pending,
        failed_provisioning_jobs=failed,
    )
