"""Redis connection for cache, rate limits, and idempotency."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
  from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_client: Redis | None = None


async def connect_redis() -> None:
  global _client
  from redis.asyncio import Redis

  settings = get_settings()
  _client = Redis.from_url(settings.redis_url, decode_responses=True)
  await _client.ping()
  logger.info("Connected to Redis")


async def close_redis() -> None:
  global _client
  if _client is not None:
    await _client.aclose()
    _client = None


def get_redis() -> Redis:
  if _client is None:
    raise RuntimeError("Redis client is not initialized")
  return _client


async def ping_redis() -> None:
  redis = get_redis()
  await redis.ping()
