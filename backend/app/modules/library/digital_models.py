"""Digital library satellite collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class LibraryDigitalAccessLog(Document):
    tenant_id: PydanticObjectId
    resource_id: str
    user_id: PydanticObjectId
    action: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_digital_access_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("resource_id", ASCENDING), ("created_at", ASCENDING)],
                name="digital_access_by_resource",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("resource_id", ASCENDING), ("action", ASCENDING)],
                name="digital_access_by_user",
            ),
        ]