"""Controlled tenant support access."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


from enum import Enum


class SupportAccessScope(str, Enum):
    VIEW_TENANT_CONFIG = "view_tenant_config"
    VIEW_INTEGRATION_DIAGNOSTICS = "view_integration_diagnostics"
    VIEW_OPERATIONAL_ERRORS = "view_operational_errors"
    VIEW_SYSTEM_METADATA = "view_system_metadata"


SUPPORT_ACCESS_SCOPES = frozenset(scope.value for scope in SupportAccessScope)


class SupportAccessRequest(Document):
    requester_id: PydanticObjectId
    tenant_id: PydanticObjectId
    reason: str
    scopes: list[str]
    duration_minutes: int
    status: str = "pending"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "support_access_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("requester_id", ASCENDING), ("created_at", DESCENDING)]),
        ]


class SupportAccessApproval(Document):
    request_id: PydanticObjectId
    approver_id: PydanticObjectId
    decision: str
    notes: str | None = None
    decided_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "support_access_approvals"
        indexes = [
            IndexModel([("request_id", ASCENDING)], unique=True, name="unique_support_approval_per_request"),
        ]


class SupportAccessSession(Document):
    request_id: PydanticObjectId
    operator_id: PydanticObjectId
    tenant_id: PydanticObjectId
    token_hash: str
    scopes: list[str]
    expires_at: datetime
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_by: PydanticObjectId | None = None

    class Settings:
        name = "support_access_sessions"
        indexes = [
            IndexModel([("token_hash", ASCENDING)], unique=True, name="unique_support_session_token"),
            IndexModel([("operator_id", ASCENDING), ("ended_at", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)]),
        ]


class SupportAccessActivity(Document):
    session_id: PydanticObjectId
    operator_id: PydanticObjectId
    tenant_id: PydanticObjectId
    action: str
    resource_type: str
    resource_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "support_access_activity"
        indexes = [
            IndexModel([("session_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)]),
        ]
