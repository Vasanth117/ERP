"""MongoDB multi-document transaction helpers (replica set required)."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TypeVar

from motor.motor_asyncio import AsyncIOMotorClientSession

from app.core.database import get_database_client
from app.core.exceptions import AppError

T = TypeVar("T")


async def assert_transactions_supported() -> None:
    client = get_database_client()
    hello = await client.admin.command("hello")
    if not hello.get("setName"):
        raise AppError(
            code="TRANSACTIONS_UNAVAILABLE",
            message="MongoDB deployment must be a replica set or sharded cluster to run section transfers",
            status_code=503,
        )


@asynccontextmanager
async def mongo_transaction() -> AsyncIterator[AsyncIOMotorClientSession]:
    await assert_transactions_supported()
    client = get_database_client()
    async with await client.start_session() as session:
        async with session.start_transaction():
            yield session


async def run_in_transaction(operation: Callable[[AsyncIOMotorClientSession], Awaitable[T]]) -> T:
    async with mongo_transaction() as session:
        return await operation(session)