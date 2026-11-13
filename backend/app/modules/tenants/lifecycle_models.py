"""Tenant lifecycle operations and offboarding records."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow
from app.modules.tenants.enums import (
    LifecycleOperationStatus,
    LifecycleOperationType,
    OffboardingApprovalStatus,
)


class OffboardingDetails(BaseModel):
    """Embedded offboarding request metadata (no deletion in Phase 2)."""

    reason: str
    effective_date: datetime
    approval_status: OffboardingApprovalStatus = OffboardingApprovalStatus.PENDING
    data_retention_policy: str
    export_required: bool = False
    subscription_status: str = "unknown"
    billing_status: str = "unknown"
    outstanding_dependencies: list[str] = Field(default_factory=list)
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None


class TenantLifecycleOperation(Document):
    tenant_id: PydanticObjectId
    operation_type: LifecycleOperationType
    status: LifecycleOperationStatus = LifecycleOperationStatus.PENDING
    scheduled_for: datetime | None = None
    reason: str | None = None
    actor_id: PydanticObjectId
    confirmation_phrase_ok: bool = False
    approval_status: OffboardingApprovalStatus = OffboardingApprovalStatus.NOT_REQUIRED
    idempotency_key: str
    progress_steps: list[dict[str, Any]] = Field(default_factory=list)
    last_error: str | None = None
    offboarding: OffboardingDetails | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Settings:
        name = "tenant_lifecycle_operations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_lifecycle_idempotency",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING)],
                name="lifecycle_ops_by_tenant_status",
            ),
            IndexModel([("scheduled_for", ASCENDING)], name="lifecycle_scheduled"),
        ]


class DomainVerificationRecord(Document):
    tenant_id: PydanticObjectId
    domain_id: PydanticObjectId
    normalized_domain: str
    token_hash: str
    dns_record_name: str
    dns_record_value: str
    status: str = "pending"
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime

    class Settings:
        name = "domain_verification_records"
        indexes = [
            IndexModel([("token_hash", ASCENDING)], unique=True, name="unique_domain_verification_hash"),
            IndexModel([("tenant_id", ASCENDING), ("domain_id", ASCENDING)], name="domain_verification_by_domain"),
        ]
