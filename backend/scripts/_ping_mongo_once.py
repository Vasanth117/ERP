import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings


async def main() -> None:
    s = get_settings()
    c = AsyncIOMotorClient(s.mongodb_url, serverSelectionTimeoutMS=20000)
    try:
        r = await c.admin.command("ping")
        print("MongoDB ping OK:", r.get("ok"))
    finally:
        c.close()


if __name__ == "__main__":
    asyncio.run(main())