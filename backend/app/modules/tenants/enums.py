"""Tenant registry and onboarding lifecycle enums."""

from enum import Enum


class TenantOperationalStatus(str, Enum):
    """Runtime status stored on the tenant registry (not onboarding stage)."""

    ONBOARDING = "onboarding"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OnboardingStage(str, Enum):
    """Configurable onboarding workflow stages."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    VERIFICATION_PENDING = "verification_pending"
    VERIFIED = "verified"
    PROVISIONING = "provisioning"
    PROVISIONED = "provisioned"
    ADMIN_INVITATION_PENDING = "admin_invitation_pending"
    ADMIN_SETUP_PENDING = "admin_setup_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DomainVerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class ProvisioningJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProvisioningStep(str, Enum):
    REGISTRY = "registry"
    CONFIGURATION = "configuration"
    DOMAIN = "domain"
    ADMIN_INVITATION = "admin_invitation"
    FINALIZE = "finalize"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PlatformAlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# Default forward transitions; stages may skip optional steps via service rules.
ONBOARDING_TRANSITIONS: dict[OnboardingStage, frozenset[OnboardingStage]] = {
    OnboardingStage.DRAFT: frozenset({OnboardingStage.SUBMITTED, OnboardingStage.CANCELLED}),
    OnboardingStage.SUBMITTED: frozenset(
        {OnboardingStage.VERIFICATION_PENDING, OnboardingStage.CANCELLED}
    ),
    OnboardingStage.VERIFICATION_PENDING: frozenset(
        {OnboardingStage.VERIFIED, OnboardingStage.FAILED, OnboardingStage.CANCELLED}
    ),
    OnboardingStage.VERIFIED: frozenset({OnboardingStage.PROVISIONING, OnboardingStage.CANCELLED}),
    OnboardingStage.PROVISIONING: frozenset(
        {OnboardingStage.PROVISIONED, OnboardingStage.FAILED, OnboardingStage.CANCELLED}
    ),
    OnboardingStage.PROVISIONED: frozenset({OnboardingStage.ADMIN_INVITATION_PENDING}),
    OnboardingStage.ADMIN_INVITATION_PENDING: frozenset(
        {OnboardingStage.ADMIN_SETUP_PENDING, OnboardingStage.FAILED, OnboardingStage.CANCELLED}
    ),
    OnboardingStage.ADMIN_SETUP_PENDING: frozenset({OnboardingStage.COMPLETED, OnboardingStage.FAILED}),
    OnboardingStage.COMPLETED: frozenset(),
    OnboardingStage.FAILED: frozenset({OnboardingStage.PROVISIONING, OnboardingStage.CANCELLED}),
    OnboardingStage.CANCELLED: frozenset(),
}


def assert_onboarding_transition(current: OnboardingStage, target: OnboardingStage) -> None:
    allowed = ONBOARDING_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition onboarding from {current.value} to {target.value}")


class TenantLifecycleStatus(str, Enum):
    """Authoritative tenant lifecycle state (Phase 2)."""

    PENDING = "pending"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    OFFBOARDING_REQUESTED = "offboarding_requested"
    OFFBOARDING_APPROVED = "offboarding_approved"
    OFFBOARDING_IN_PROGRESS = "offboarding_in_progress"
    ARCHIVED = "archived"
    CLOSED = "closed"


class LifecycleOperationType(str, Enum):
    ACTIVATE = "activate"
    SUSPEND = "suspend"
    REACTIVATE = "reactivate"
    OFFBOARDING_INITIATE = "offboarding_initiate"
    OFFBOARDING_APPROVE = "offboarding_approve"
    OFFBOARDING_START = "offboarding_start"
    SCHEDULED_SUSPEND = "scheduled_suspend"
    SCHEDULED_ACTIVATE = "scheduled_activate"


class LifecycleOperationStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OffboardingApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


LIFECYCLE_TRANSITIONS: dict[TenantLifecycleStatus, frozenset[TenantLifecycleStatus]] = {
    TenantLifecycleStatus.PENDING: frozenset(
        {TenantLifecycleStatus.PROVISIONING, TenantLifecycleStatus.ACTIVE, TenantLifecycleStatus.CLOSED}
    ),
    TenantLifecycleStatus.PROVISIONING: frozenset(
        {TenantLifecycleStatus.ACTIVE, TenantLifecycleStatus.PENDING, TenantLifecycleStatus.CLOSED}
    ),
    TenantLifecycleStatus.ACTIVE: frozenset(
        {
            TenantLifecycleStatus.SUSPENDED,
            TenantLifecycleStatus.OFFBOARDING_REQUESTED,
        }
    ),
    TenantLifecycleStatus.SUSPENDED: frozenset(
        {TenantLifecycleStatus.ACTIVE, TenantLifecycleStatus.OFFBOARDING_REQUESTED}
    ),
    TenantLifecycleStatus.OFFBOARDING_REQUESTED: frozenset(
        {
            TenantLifecycleStatus.OFFBOARDING_APPROVED,
            TenantLifecycleStatus.ACTIVE,
            TenantLifecycleStatus.SUSPENDED,
        }
    ),
    TenantLifecycleStatus.OFFBOARDING_APPROVED: frozenset(
        {TenantLifecycleStatus.OFFBOARDING_IN_PROGRESS, TenantLifecycleStatus.ACTIVE}
    ),
    TenantLifecycleStatus.OFFBOARDING_IN_PROGRESS: frozenset(
        {TenantLifecycleStatus.ARCHIVED, TenantLifecycleStatus.CLOSED}
    ),
    TenantLifecycleStatus.ARCHIVED: frozenset({TenantLifecycleStatus.CLOSED}),
    TenantLifecycleStatus.CLOSED: frozenset(),
}


def assert_lifecycle_transition(
    current: TenantLifecycleStatus,
    target: TenantLifecycleStatus,
) -> None:
    allowed = LIFECYCLE_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition lifecycle from {current.value} to {target.value}")


def operational_status_for_lifecycle(
    lifecycle: TenantLifecycleStatus,
) -> TenantOperationalStatus:
    """Keep legacy `tenant.status` aligned for existing readers."""
    mapping = {
        TenantLifecycleStatus.PENDING: TenantOperationalStatus.ONBOARDING,
        TenantLifecycleStatus.PROVISIONING: TenantOperationalStatus.PROVISIONING,
        TenantLifecycleStatus.ACTIVE: TenantOperationalStatus.ACTIVE,
        TenantLifecycleStatus.SUSPENDED: TenantOperationalStatus.SUSPENDED,
        TenantLifecycleStatus.OFFBOARDING_REQUESTED: TenantOperationalStatus.SUSPENDED,
        TenantLifecycleStatus.OFFBOARDING_APPROVED: TenantOperationalStatus.SUSPENDED,
        TenantLifecycleStatus.OFFBOARDING_IN_PROGRESS: TenantOperationalStatus.SUSPENDED,
        TenantLifecycleStatus.ARCHIVED: TenantOperationalStatus.SUSPENDED,
        TenantLifecycleStatus.CLOSED: TenantOperationalStatus.CANCELLED,
    }
    return mapping[lifecycle]
