"""Background jobs executed by Celery workers."""

import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="erp.jobs.ping")
def ping() -> str:
    logger.info("Celery heartbeat")
    return "ok"


async def register_ping_job() -> None:
    from app.modules.platform_ops.job_registry import ensure_job_registry

    await ensure_job_registry(
        job_type="erp.jobs.ping",
        job_key="heartbeat",
        safe_to_retry=True,
        summary="Celery heartbeat probe",
    )
