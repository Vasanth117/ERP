"""Sync MongoDB indexes from Beanie models.

Run after deploying schema changes:
  cd backend && python -m scripts.migrate_indexes
"""

import asyncio
import logging

from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        for model in document_models():
            await model.ensure_indexes()
            logger.info("Indexes synced for %s", model.Settings.name)
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
