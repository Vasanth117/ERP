"""Colleges and departments."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class Tenant(Document):
    name: str
    code: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenants"
        indexes = [
            IndexModel([("code", ASCENDING)], unique=True, name="unique_tenant_code"),
        ]


class Department(Document):
    tenant_id: PydanticObjectId
    name: str
    code: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "departments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("code", ASCENDING)],
                unique=True,
                name="unique_department_code_per_tenant",
            ),
        ]
