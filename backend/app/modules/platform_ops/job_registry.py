"""Register safe background jobs for operations visibility."""

from beanie import PydanticObjectId

from app.common.time import utcnow
from app.modules.platform_ops.enums import BackgroundJobStatus
from app.modules.platform_ops.models import BackgroundJobFailure, BackgroundJobRegistry


async def ensure_job_registry(
    *,
    job_type: str,
    job_key: str,
    safe_to_retry: bool,
    summary: str,
    tenant_id: PydanticObjectId | None = None,
    idempotency_key: str | None = None,
) -> BackgroundJobRegistry:
    existing = await BackgroundJobRegistry.find_one(
        BackgroundJobRegistry.job_type == job_type,
        BackgroundJobRegistry.job_key == job_key,
    )
    if existing is not None:
        return existing
    job = BackgroundJobRegistry(
        job_type=job_type,
        job_key=job_key,
        safe_to_retry=safe_to_retry,
        summary=summary,
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
        status=BackgroundJobStatus.PENDING,
    )
    await job.insert()
    return job


async def update_job_registry_status(
    *,
    job_type: str,
    job_key: str,
    status: BackgroundJobStatus,
    last_error: str | None = None,
) -> None:
    job = await BackgroundJobRegistry.find_one(
        BackgroundJobRegistry.job_type == job_type,
        BackgroundJobRegistry.job_key == job_key,
    )
    if job is None:
        return
    job.status = status
    job.updated_at = utcnow()
    if last_error:
        job.last_error = last_error[:500]
    await job.save()


async def record_job_failure(
    *,
    registry: BackgroundJobRegistry,
    error_code: str,
    error_message: str,
) -> None:
    await BackgroundJobFailure(
        registry_id=registry.id,
        job_type=registry.job_type,
        error_code=error_code,
        error_message=error_message[:500],
    ).insert()
    registry.status = BackgroundJobStatus.FAILED
    registry.last_error = error_message[:500]
    registry.updated_at = utcnow()
    await registry.save()
