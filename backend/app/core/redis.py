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
  from redis.exceptions import ConnectionError as RedisConnectionError

  settings = get_settings()
  client = Redis.from_url(settings.redis_url, decode_responses=True)
  try:
    await client.ping()
  except (RedisConnectionError, OSError) as exc:
    if settings.app_env == "development" and settings.redis_allow_inmemory_fallback:
      import fakeredis.aioredis

      _client = fakeredis.aioredis.FakeRedis(decode_responses=True)
      logger.warning(
        "Redis unavailable at %s (%s). Using in-memory FakeRedis (REDIS_ALLOW_INMEMORY_FALLBACK). "
        "Start Redis via docker compose up redis -d when you need a real cache.",
        settings.redis_url,
        exc,
      )
      return
    await client.aclose()
    raise

  _client = client
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
