"""Library membership history (authoritative membership in library_membership_references)."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class LibraryMembershipHistory(Document):
    tenant_id: PydanticObjectId
    member_user_id: PydanticObjectId
    membership_number: str | None = None
    action: str
    actor_id: PydanticObjectId | None = None
    changes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_membership_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("member_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="membership_history_by_member",
            ),
        ]