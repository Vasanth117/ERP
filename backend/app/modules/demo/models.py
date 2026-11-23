"""Demo environment lifecycle metadata."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class DemoGenerationRun(Document):
    """Tracks deterministic demo dataset builds for a tenant."""

    tenant_id: PydanticObjectId
    tenant_code: str
    profile: str
    generator_version: str
    status: str = "initializing"
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
    record_counts: dict[str, int] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None

    class Settings:
        name = "demo_generation_runs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("started_at", DESCENDING)],
                name="demo_runs_by_tenant",
            ),
        ]