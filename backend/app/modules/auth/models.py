"""User accounts and refresh tokens."""

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
      IndexModel(
        [("tenant_id", ASCENDING), ("email", ASCENDING)],
        unique=True,
        name="unique_email_per_tenant",
        partialFilterExpression={"tenant_id": {"$type": "objectId"}},
      ),
      IndexModel(
        [("email", ASCENDING)],
        unique=True,
        name="unique_platform_email",
        partialFilterExpression={"tenant_id": None},
      ),
      IndexModel([("tenant_id", ASCENDING)], name="users_by_tenant"),
    ]


class RefreshToken(Document):
  user_id: PydanticObjectId
  token_hash: str
  family_id: str
  expires_at: datetime
  revoked_at: datetime | None = None
  created_at: datetime = Field(default_factory=utcnow)

  class Settings:
    name = "refresh_tokens"
    indexes = [
      IndexModel([("token_hash", ASCENDING)], unique=True, name="unique_refresh_hash"),
      IndexModel([("user_id", ASCENDING), ("created_at", ASCENDING)], name="refresh_by_user"),
      IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="refresh_ttl"),
    ]
