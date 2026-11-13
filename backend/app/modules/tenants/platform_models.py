"""Platform-owned tenant lifecycle collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.tenants.enums import (
    DomainVerificationStatus,
    InvitationStatus,
    OnboardingStage,
    PlatformAlertSeverity,
    ProvisioningJobStatus,
    ProvisioningStep,
)


class InstitutionAddress(BaseModel):
    line1: str = ""
    line2: str | None = None
    city: str = ""
    state: str = ""
    country: str = ""
    postal_code: str | None = None


class AcademicSettings(BaseModel):
    default_academic_year_label: str | None = None
    grading_scheme: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TenantOnboarding(Document):
    tenant_id: PydanticObjectId
    stage: OnboardingStage = OnboardingStage.DRAFT
    stage_history: list[dict[str, Any]] = Field(default_factory=list)
    requirements: dict[str, bool] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_onboarding"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_onboarding_per_tenant"),
            IndexModel([("stage", ASCENDING), ("updated_at", DESCENDING)], name="onboarding_by_stage"),
        ]


class TenantDomain(Document):
    tenant_id: PydanticObjectId
    domain: str
    normalized_domain: str
    is_primary: bool = True
    verification_status: DomainVerificationStatus = DomainVerificationStatus.PENDING
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_domains"
        indexes = [
            IndexModel(
                [("normalized_domain", ASCENDING)],
                unique=True,
                name="unique_normalized_domain",
            ),
            IndexModel([("tenant_id", ASCENDING)], name="domains_by_tenant"),
        ]


class TenantAdminInvitation(Document):
    tenant_id: PydanticObjectId
    email: str
    full_name: str
    token_hash: str
    status: InvitationStatus = InvitationStatus.PENDING
    expires_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None
    sent_count: int = 1
    last_sent_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_admin_invitations"
        indexes = [
            IndexModel([("token_hash", ASCENDING)], unique=True, name="unique_invitation_token_hash"),
            IndexModel(
                [("tenant_id", ASCENDING), ("email", ASCENDING)],
                name="invitation_by_tenant_email",
            ),
            IndexModel([("expires_at", ASCENDING)], name="invitation_expiry"),
        ]


class TenantProvisioningJob(Document):
    tenant_id: PydanticObjectId
    idempotency_key: str
    status: ProvisioningJobStatus = ProvisioningJobStatus.PENDING
    steps_completed: list[ProvisioningStep] = Field(default_factory=list)
    last_error: str | None = None
    attempt_count: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_provisioning_jobs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_provisioning_idempotency",
            ),
            IndexModel([("status", ASCENDING), ("updated_at", DESCENDING)], name="provisioning_by_status"),
        ]


class TenantStatusHistory(Document):
    tenant_id: PydanticObjectId
    from_status: str | None = None
    to_status: str
    from_lifecycle: str | None = None
    to_lifecycle: str | None = None
    operation_id: str | None = None
    reason: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_status_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("created_at", DESCENDING)],
                name="tenant_status_history_by_tenant",
            ),
        ]


class PlatformMetricsSnapshot(Document):
    captured_at: datetime = Field(default_factory=utcnow)
    metrics: dict[str, Any] = Field(default_factory=dict)
    source: str = "dashboard_aggregator"

    class Settings:
        name = "platform_metrics_snapshots"
        indexes = [
            IndexModel([("captured_at", DESCENDING)], name="metrics_by_time"),
        ]


class PlatformAlert(Document):
    code: str
    title: str
    message: str
    severity: PlatformAlertSeverity = PlatformAlertSeverity.INFO
    source: str = "platform"
    related_tenant_id: PydanticObjectId | None = None
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime | None = None

    class Settings:
        name = "platform_alerts"
        indexes = [
            IndexModel(
                [("acknowledged", ASCENDING), ("severity", ASCENDING), ("created_at", DESCENDING)],
                name="alerts_open_by_severity",
            ),
        ]
