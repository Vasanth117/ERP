"""Pytest fixtures."""

import os

import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017/erp_test?replicaSet=rs0&directConnection=true")
os.environ.setdefault("MONGODB_DB_NAME", "erp_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters-long")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
