"""College admin audit and security collections (tenant-scoped)."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class SecurityIncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class InstitutionAuditLog(Document):
    """Append-only institutional audit mirror with integrity chain."""

    tenant_id: PydanticObjectId
    actor_id: PydanticObjectId | None = None
    action: str
    module: str
    resource_type: str
    resource_id: str | None = None
    outcome: str = "success"
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_audit_id: str | None = None
    entry_hash: str
    previous_entry_hash: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_audit_logs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="inst_audit_by_time"),
            IndexModel([("tenant_id", ASCENDING), ("module", ASCENDING), ("created_at", DESCENDING)], name="inst_audit_by_module"),
            IndexModel([("tenant_id", ASCENDING), ("actor_id", ASCENDING), ("created_at", DESCENDING)], name="inst_audit_by_actor"),
        ]


class InstitutionSecurityEvent(Document):
    tenant_id: PydanticObjectId
    event_id: str
    code: str
    category: str
    severity: str = "medium"
    title: str
    description: str
    actor_id: PydanticObjectId | None = None
    status: SecurityIncidentStatus = SecurityIncidentStatus.OPEN
    metadata: dict[str, Any] = Field(default_factory=dict)
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_security_events"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("event_id", ASCENDING)], unique=True, name="unique_security_event"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], name="security_events_open"),
        ]


class InstitutionLoginActivity(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId | None = None
    email: str | None = None
    success: bool
    ip_address: str | None = None
    user_agent: str | None = None
    failure_reason: str | None = None
    login_method: str | None = Field(default=None, max_length=32)
    device_label: str | None = Field(default=None, max_length=120)
    location_label: str | None = Field(default=None, max_length=120)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_login_activity"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="login_activity_recent"),
            IndexModel([("tenant_id", ASCENDING), ("success", ASCENDING), ("created_at", DESCENDING)], name="login_failures"),
        ]


class InstitutionAccessReview(Document):
    tenant_id: PydanticObjectId
    review_id: str
    subject_user_id: PydanticObjectId
    reviewer_id: PydanticObjectId
    decision: str
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_access_reviews"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("review_id", ASCENDING)], unique=True, name="unique_access_review"),
        ]


class InstitutionSecurityPolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str = "default"
    max_failed_logins: int = Field(default=5, ge=1)
    session_max_idle_minutes: int = Field(default=60, ge=5)
    require_mfa_privileged: bool = False
    audit_retention_days: int = Field(default=365, ge=30)
    block_self_approval: bool = True
    alert_on_privileged_access: bool = True
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_security_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_id", ASCENDING)], unique=True, name="unique_security_policy"),
        ]


class InstitutionAuditExport(Document):
    tenant_id: PydanticObjectId
    export_id: str
    actor_id: PydanticObjectId
    filter_summary: dict[str, Any] = Field(default_factory=dict)
    record_count: int = 0
    download_token_hash: str | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_audit_exports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("export_id", ASCENDING)], unique=True, name="unique_audit_export"),
        ]


class InstitutionAuditDataAccessLog(Document):
    """Meta-audit: who viewed institutional audit data."""

    tenant_id: PydanticObjectId
    actor_id: PydanticObjectId
    action: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_audit_data_access_logs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="audit_data_access"),
        ]