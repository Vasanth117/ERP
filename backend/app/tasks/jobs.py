"""Background jobs executed by Celery workers."""

import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="erp.jobs.ping")
def ping() -> str:
    logger.info("Celery heartbeat")
    return "ok"
