"""Hostel policy and configuration versioning."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelConfigLifecycle(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ACTIVE = "active"
    SCHEDULED = "scheduled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class HostelConfiguration(Document):
    tenant_id: PydanticObjectId
    policy_section: str
    hostel_code: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    status: HostelConfigLifecycle = HostelConfigLifecycle.DRAFT
    effective_from: date | None = None
    effective_to: date | None = None
    change_reason: str | None = None
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_configuration"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_section", ASCENDING), ("hostel_code", ASCENDING)],
                unique=True,
                name="unique_hostel_config_section",
            ),
        ]


class HostelConfigurationVersion(Document):
    tenant_id: PydanticObjectId
    version_id: str
    policy_section: str
    hostel_code: str | None = None
    version: int
    payload_snapshot: dict[str, Any] = Field(default_factory=dict)
    status: HostelConfigLifecycle
    effective_from: date | None = None
    actor_id: PydanticObjectId | None = None
    change_reason: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_configuration_versions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("version_id", ASCENDING)], unique=True, name="unique_hostel_config_version"),
            IndexModel([("tenant_id", ASCENDING), ("policy_section", ASCENDING), ("version", DESCENDING)], name="hostel_config_versions"),
        ]


class HostelPolicyDefinition(Document):
    tenant_id: PydanticObjectId
    policy_code: str
    title: str
    category: str
    description: str | None = None
    severity: str = "medium"
    hostel_codes: list[str] = Field(default_factory=list)
    current_version: int = 1
    status: HostelConfigLifecycle = HostelConfigLifecycle.DRAFT
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_policy_definitions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_code", ASCENDING)], unique=True, name="unique_hostel_policy_def"),
        ]


class HostelPolicyVersion(Document):
    tenant_id: PydanticObjectId
    policy_code: str
    version: int
    rules: dict[str, Any] = Field(default_factory=dict)
    effective_from: date | None = None
    effective_to: date | None = None
    status: HostelConfigLifecycle = HostelConfigLifecycle.DRAFT
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_policy_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_code", ASCENDING), ("version", ASCENDING)],
                unique=True,
                name="unique_hostel_policy_version",
            ),
        ]


class HostelPolicyApproval(Document):
    tenant_id: PydanticObjectId
    approval_id: str
    policy_code: str
    version: int
    decision: str
    actor_id: PydanticObjectId | None = None
    comment: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_policy_approvals"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("approval_id", ASCENDING)], unique=True, name="unique_hostel_policy_approval"),
        ]