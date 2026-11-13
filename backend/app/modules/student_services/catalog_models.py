"""Institutional service catalogue (central)."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class InstitutionalService(Document):
    tenant_id: PydanticObjectId
    service_id: str
    title: str = Field(max_length=200)
    category: str = Field(max_length=64)
    description: str | None = Field(default=None, max_length=2000)
    enabled: bool = True
    requires_approval: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institutional_services"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("service_id", ASCENDING)],
                unique=True,
                name="unique_institutional_service",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("category", ASCENDING), ("enabled", ASCENDING)],
                name="services_by_category",
            ),
        ]
