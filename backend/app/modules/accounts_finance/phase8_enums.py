"""Phase 8 reporting and period closing enumerations."""

from enum import Enum


class PeriodLifecycleStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PROCESSING = "processing"
    UNDER_REVIEW = "under_review"
    PENDING_APPROVAL = "pending_approval"
    CLOSED = "closed"
    REOPENED = "reopened"
    LOCKED = "locked"
    ARCHIVED = "archived"


class ClosingRunStatus(str, Enum):
    VALIDATION = "validation"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    CLOSED = "closed"
    REJECTED = "rejected"


class ReportExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"