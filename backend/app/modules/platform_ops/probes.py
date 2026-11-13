"""Infrastructure health probes (no credential exposure)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.celery_app import celery_app
from app.core.database import ping_mongo
from app.core.redis import ping_redis

logger = logging.getLogger(__name__)


async def probe_mongodb() -> dict[str, Any]:
    try:
        await ping_mongo()
        return {"name": "mongodb", "status": "healthy"}
    except Exception as exc:
        logger.warning("MongoDB probe failed: %s", exc)
        return {"name": "mongodb", "status": "unavailable", "detail": "ping_failed"}


async def probe_redis() -> dict[str, Any]:
    try:
        await ping_redis()
        return {"name": "redis", "status": "healthy"}
    except Exception as exc:
        logger.warning("Redis probe failed: %s", exc)
        return {"name": "redis", "status": "unavailable", "detail": "ping_failed"}


def _probe_rabbitmq_sync() -> dict[str, Any]:
    try:
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=1)
        return {"name": "rabbitmq", "status": "healthy"}
    except Exception as exc:
        logger.warning("RabbitMQ probe failed: %s", exc)
        return {"name": "rabbitmq", "status": "unavailable", "detail": "broker_unreachable"}


async def probe_rabbitmq() -> dict[str, Any]:
    return await asyncio.to_thread(_probe_rabbitmq_sync)


def _probe_celery_sync() -> dict[str, Any]:
    try:
        inspect = celery_app.control.inspect(timeout=2.0)
        if inspect is None:
            return {"name": "celery_workers", "status": "unknown", "detail": "inspect_unavailable"}
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        if not stats:
            return {
                "name": "celery_workers",
                "status": "unavailable",
                "detail": "no_workers_reporting",
                "worker_count": 0,
            }
        return {
            "name": "celery_workers",
            "status": "healthy",
            "worker_count": len(stats),
            "active_tasks": sum(len(v) for v in active.values()),
        }
    except Exception as exc:
        logger.warning("Celery probe failed: %s", exc)
        return {"name": "celery_workers", "status": "unknown", "detail": "inspect_failed"}


async def probe_celery() -> dict[str, Any]:
    return await asyncio.to_thread(_probe_celery_sync)


async def probe_application() -> dict[str, Any]:
    return {"name": "api_application", "status": "healthy"}
