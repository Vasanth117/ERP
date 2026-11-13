"""Platform health aggregation and snapshots."""

from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.modules.integrations.models import IntegrationHealth, WebhookDeliveryEvent
from app.modules.platform_ops.enums import BackgroundJobStatus
from app.modules.platform_ops.models import BackgroundJobRegistry, ServiceHealthSnapshot
from app.modules.platform_ops.probes import (
    probe_application,
    probe_celery,
    probe_mongodb,
    probe_rabbitmq,
    probe_redis,
)
from app.modules.platform_ops.schemas import (
    BackgroundJobSummary,
    PlatformHealthOverview,
    QueueStatistics,
    WorkerStatistics,
)
from app.modules.platform_security.audit import record_platform_audit
from app.modules.tenants.platform_models import PlatformAlert
from app.repositories.platform_repository import PlatformAlertRepository

_alert_repo = PlatformAlertRepository()

SAFE_RETRY_JOB_TYPES = frozenset({"erp.jobs.ping", "tenant.provisioning"})


async def _compute_overall(components: list[dict]) -> str:
    statuses = {c["status"] for c in components}
    if "unavailable" in statuses:
        return "unavailable"
    if "unknown" in statuses or "degraded" in statuses:
        return "degraded"
    return "healthy"


async def get_platform_health(scope: AccessScope) -> PlatformHealthOverview:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    components = [
        await probe_application(),
        await probe_mongodb(),
        await probe_redis(),
        await probe_rabbitmq(),
        await probe_celery(),
    ]
    queue = await get_queue_statistics(scope)
    workers = await get_worker_statistics(scope)
    job_summary = await get_background_job_summary(scope)
    integration_failures = await WebhookDeliveryEvent.find(Eq(WebhookDeliveryEvent.status, "failed")).count()
    alerts = await _alert_repo.list_open(limit=10)

    overall = await _compute_overall(components)
    snapshot = ServiceHealthSnapshot(
        overall_status=overall,
        components={c["name"]: c for c in components},
        queue_stats=queue.model_dump(),
        worker_stats=workers.model_dump(),
        integration_failure_count=integration_failures,
    )
    await snapshot.insert()

    return PlatformHealthOverview(
        generated_at=utcnow(),
        overall_status=overall,
        components=components,
        queue_statistics=queue,
        worker_statistics=workers,
        background_jobs=job_summary,
        integration_failure_count=integration_failures,
        open_alerts=len(alerts),
    )


async def get_dependency_health(scope: AccessScope) -> list[dict]:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    return [
        await probe_mongodb(),
        await probe_redis(),
        await probe_rabbitmq(),
    ]


async def get_service_health(scope: AccessScope) -> dict:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    return {
        "application": await probe_application(),
        "dependencies": await get_dependency_health(scope),
    }


async def get_queue_statistics(scope: AccessScope) -> QueueStatistics:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    pending = await BackgroundJobRegistry.find(Eq(BackgroundJobRegistry.status, BackgroundJobStatus.PENDING)).count()
    failed = await BackgroundJobRegistry.find(Eq(BackgroundJobRegistry.status, BackgroundJobStatus.FAILED)).count()
    retrying = await BackgroundJobRegistry.find(Eq(BackgroundJobRegistry.status, BackgroundJobStatus.RETRYING)).count()
    scheduled = await BackgroundJobRegistry.find(Eq(BackgroundJobRegistry.status, BackgroundJobStatus.SCHEDULED)).count()
    return QueueStatistics(
        pending=pending,
        failed=failed,
        retrying=retrying,
        scheduled=scheduled,
    )


async def get_worker_statistics(scope: AccessScope) -> WorkerStatistics:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    celery = await probe_celery()
    return WorkerStatistics(
        status=celery.get("status", "unknown"),
        worker_count=celery.get("worker_count", 0),
        active_tasks=celery.get("active_tasks", 0),
        detail=celery.get("detail"),
    )


async def get_background_job_summary(scope: AccessScope) -> BackgroundJobSummary:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    stats = await get_queue_statistics(scope)
    integration_degraded = await IntegrationHealth.find(
        Eq(IntegrationHealth.status, "degraded")
    ).count()
    return BackgroundJobSummary(
        pending=stats.pending,
        failed=stats.failed,
        retrying=stats.retrying,
        scheduled=stats.scheduled,
        integration_degraded=integration_degraded,
    )


async def list_failed_jobs(scope: AccessScope, *, limit: int = 50) -> list[dict]:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    jobs = (
        await BackgroundJobRegistry.find(Eq(BackgroundJobRegistry.status, BackgroundJobStatus.FAILED))
        .sort("-updated_at")
        .limit(limit)
        .to_list()
    )
    return [
        {
            "id": str(job.id),
            "job_type": job.job_type,
            "status": job.status.value,
            "safe_to_retry": job.safe_to_retry,
            "summary": job.summary,
            "retry_count": job.retry_count,
            "last_error": job.last_error,
            "updated_at": job.updated_at.isoformat(),
        }
        for job in jobs
    ]


async def retry_background_job(scope: AccessScope, registry_id: str) -> dict:
    authorize(scope, Permission.PLATFORM_OPS_MANAGE)
    from beanie import PydanticObjectId

    job = await BackgroundJobRegistry.get(PydanticObjectId(registry_id))
    if job is None:
        from app.core.exceptions import AppError

        raise AppError(code="NOT_FOUND", message="Job not found", status_code=404)
    if not job.safe_to_retry or job.job_type not in SAFE_RETRY_JOB_TYPES:
        from app.core.exceptions import AppError

        raise AppError(code="JOB_NOT_RETRYABLE", message="This job type cannot be retried", status_code=409)
    if job.retry_count >= job.max_retries:
        from app.core.exceptions import AppError

        raise AppError(code="RETRY_LIMIT", message="Retry limit reached", status_code=409)

    job.status = BackgroundJobStatus.RETRYING
    job.retry_count += 1
    job.updated_at = utcnow()
    await job.save()

    if job.job_type == "erp.jobs.ping":
        from app.tasks.jobs import ping

        ping.delay()
    elif job.job_type == "tenant.provisioning":
        if job.tenant_id is None:
            from app.core.exceptions import AppError

            raise AppError(code="CONFLICT", message="Provisioning job missing tenant context", status_code=409)
        from app.repositories.platform_repository import InvitationRepository, OnboardingRepository
        from app.modules.tenants.provisioning_service import retry_failed_provisioning
        from app.repositories.tenant_repository import TenantRepository

        tenant = await TenantRepository().get_tenant(job.tenant_id)
        onboarding = await OnboardingRepository().get_by_tenant(job.tenant_id)
        if tenant is None or onboarding is None or tenant.primary_domain is None:
            from app.core.exceptions import AppError

            raise AppError(code="CONFLICT", message="Cannot retry provisioning: missing tenant metadata", status_code=409)
        invite = await InvitationRepository().get_active_for_tenant(tenant.id)
        email = invite.email if invite else (tenant.institution_email or "")
        name = invite.full_name if invite else "College Administrator"
        await retry_failed_provisioning(
            tenant=tenant,
            onboarding=onboarding,
            actor_id=scope.user_id,
            domain=tenant.primary_domain,
            admin_email=email,
            admin_full_name=name,
        )

    job.status = BackgroundJobStatus.PENDING
    await job.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="background_job.retry",
        module="platform_ops",
        resource_type="background_job_registry",
        resource_id=str(job.id),
        tenant_id=job.tenant_id,
        metadata={"job_type": job.job_type, "retry_count": job.retry_count},
    )
    return {"id": str(job.id), "status": job.status.value, "retry_count": job.retry_count}
