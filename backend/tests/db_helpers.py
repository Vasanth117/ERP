"""Shared helpers for integration tests."""


async def drop_all_test_collections() -> None:
    """Drop every collection in the test database so Beanie can recreate indexes cleanly."""
    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import get_settings

    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    await client.admin.command("ping")
    db = client[settings.mongodb_db_name]
    for name in await db.list_collection_names():
        await db[name].drop()
    client.close()