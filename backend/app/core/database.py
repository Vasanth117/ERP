"""MongoDB connection.

The ERP database is MongoDB. Beanie stores Pydantic documents through Motor.
SQLAlchemy and Alembic target relational databases, so they are not part of this
service. Tenant isolation is enforced on each request in the API.
"""

import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def document_models() -> list[type]:
    from app.modules.audit.models import AuditLog
    from app.modules.auth.models import User
    from app.modules.tenants.models import Department, Tenant

    return [User, Tenant, Department, AuditLog]


async def connect_to_mongo() -> None:
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    await _client.admin.command("ping")
    await init_beanie(
        database=_client[settings.mongodb_db_name],
        document_models=document_models(),
    )
    logger.info("Connected to MongoDB database %s", settings.mongodb_db_name)


async def close_mongo() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ping_mongo() -> None:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized")
    await _client.admin.command("ping")
