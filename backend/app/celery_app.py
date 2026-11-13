"""Celery application.

RabbitMQ is the broker for background jobs such as mail, exports, and reminders.
Kafka is an optional later path for high-volume business events and is not wired
into this release. Celery's Kafka transport is experimental, so it is not used.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("erp", broker=settings.rabbitmq_url)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_default_queue="erp",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=["app.tasks.jobs"],
)

if settings.app_env == "development":
    celery_app.conf.beat_schedule = {
        "heartbeat": {
            "task": "erp.jobs.ping",
            "schedule": 300.0,
        }
    }
