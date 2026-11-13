"""Seed platform service catalog for health monitoring."""

import asyncio

from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.modules.platform_ops.models import PlatformService

SERVICES = (
    ("api", "ERP API", "application"),
    ("mongodb", "MongoDB", "database"),
    ("redis", "Redis", "cache"),
    ("rabbitmq", "RabbitMQ", "queue"),
    ("celery", "Celery workers", "worker"),
)


async def main() -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        for code, name, kind in SERVICES:
            existing = await PlatformService.find_one(PlatformService.code == code)
            if existing is not None:
                continue
            await PlatformService(code=code, name=name, service_type=kind, is_active=True).insert()
            print(f"seeded service {code}")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
