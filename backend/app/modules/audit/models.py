"""Sensitive action history."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class AuditLog(Document):
  actor_id: PydanticObjectId | None = None
  action: str
  resource_type: str
  resource_id: str | None = None
  tenant_id: PydanticObjectId | None = None
  outcome: str = "success"
  request_id: str | None = None
  metadata: dict[str, Any] = Field(default_factory=dict)
  created_at: datetime = Field(default_factory=utcnow)

  class Settings:
    name = "audit_logs"
    indexes = [
      IndexModel([("tenant_id", ASCENDING), ("created_at", ASCENDING)], name="audit_by_tenant"),
      IndexModel([("created_at", ASCENDING)], name="audit_by_time"),
      IndexModel([("actor_id", ASCENDING), ("created_at", ASCENDING)], name="audit_by_actor"),
    ]
