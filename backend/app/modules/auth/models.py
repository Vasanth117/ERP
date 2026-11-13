"""User accounts."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.roles import Role
from app.common.time import utcnow


class User(Document):
    email: str
    hashed_password: str
    full_name: str
    role: Role
    tenant_id: PydanticObjectId | None = None
    department_id: PydanticObjectId | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True, name="unique_user_email"),
            IndexModel([("tenant_id", ASCENDING)], name="users_by_tenant"),
        ]
