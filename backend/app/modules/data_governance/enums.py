"""Data export, retention and offboarding enums."""

from enum import Enum


class ExportRequestStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    ZIP = "zip"


class ExportJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OffboardingWorkflowStage(str, Enum):
    OFFBOARDING_REQUESTED = "offboarding_requested"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXPORT_PREPARATION = "export_preparation"
    EXPORT_IN_PROGRESS = "export_in_progress"
    EXPORT_AVAILABLE = "export_available"
    RETENTION_PERIOD = "retention_period"
    ARCHIVAL_IN_PROGRESS = "archival_in_progress"
    ARCHIVED = "archived"
    DELETION_REVIEW = "deletion_review"
    DELETION_APPROVED = "deletion_approved"
    DELETION_IN_PROGRESS = "deletion_in_progress"
    CLOSED = "closed"


OFFBOARDING_TRANSITIONS: dict[OffboardingWorkflowStage, frozenset[OffboardingWorkflowStage]] = {
    OffboardingWorkflowStage.OFFBOARDING_REQUESTED: frozenset(
        {OffboardingWorkflowStage.PENDING_APPROVAL, OffboardingWorkflowStage.CLOSED}
    ),
    OffboardingWorkflowStage.PENDING_APPROVAL: frozenset(
        {OffboardingWorkflowStage.APPROVED, OffboardingWorkflowStage.CLOSED, OffboardingWorkflowStage.OFFBOARDING_REQUESTED}
    ),
    OffboardingWorkflowStage.APPROVED: frozenset({OffboardingWorkflowStage.EXPORT_PREPARATION}),
    OffboardingWorkflowStage.EXPORT_PREPARATION: frozenset({OffboardingWorkflowStage.EXPORT_IN_PROGRESS}),
    OffboardingWorkflowStage.EXPORT_IN_PROGRESS: frozenset(
        {OffboardingWorkflowStage.EXPORT_AVAILABLE, OffboardingWorkflowStage.EXPORT_PREPARATION}
    ),
    OffboardingWorkflowStage.EXPORT_AVAILABLE: frozenset({OffboardingWorkflowStage.RETENTION_PERIOD}),
    OffboardingWorkflowStage.RETENTION_PERIOD: frozenset({OffboardingWorkflowStage.ARCHIVAL_IN_PROGRESS}),
    OffboardingWorkflowStage.ARCHIVAL_IN_PROGRESS: frozenset({OffboardingWorkflowStage.ARCHIVED}),
    OffboardingWorkflowStage.ARCHIVED: frozenset({OffboardingWorkflowStage.DELETION_REVIEW}),
    OffboardingWorkflowStage.DELETION_REVIEW: frozenset(
        {OffboardingWorkflowStage.DELETION_APPROVED, OffboardingWorkflowStage.ARCHIVED}
    ),
    OffboardingWorkflowStage.DELETION_APPROVED: frozenset({OffboardingWorkflowStage.DELETION_IN_PROGRESS}),
    OffboardingWorkflowStage.DELETION_IN_PROGRESS: frozenset({OffboardingWorkflowStage.CLOSED}),
    OffboardingWorkflowStage.CLOSED: frozenset(),
}


def assert_offboarding_transition(
    current: OffboardingWorkflowStage,
    target: OffboardingWorkflowStage,
) -> None:
    allowed = OFFBOARDING_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition offboarding from {current.value} to {target.value}")


class RetentionExecutionStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED_HOLD = "skipped_hold"


class DeletionRequestStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED_HOLD = "blocked_hold"


class ArchivalStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class LegalHoldStatus(str, Enum):
    ACTIVE = "active"
    RELEASED = "released"


ALLOWED_EXPORT_MODULES = frozenset(
    {
        "tenant_registry",
        "configuration",
        "users_metadata",
        "audit_logs",
        "departments",
        "documents_metadata",
    }
)
