"""Phase 11 tax and finance notification enumerations."""

from enum import Enum


class FinanceTaxCategory(str, Enum):
    INDIRECT = "indirect"
    OUTPUT_TAX = "output_tax"
    TDS = "tds"
    WITHHOLDING = "withholding"
    OTHER = "other"


class TaxReportingStatus(str, Enum):
    PENDING = "pending"
    REPORTED = "reported"
    ADJUSTED = "adjusted"
    EXEMPT = "exempt"


class RegulatoryReportStatus(str, Enum):
    DRAFT = "draft"
    VALIDATION = "validation"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    FILED_RECORDED = "filed_recorded"
    REJECTED = "rejected"


class FilingRecordStatus(str, Enum):
    PREPARED = "prepared"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    FILED = "filed"
    AMENDED = "amended"


class FinanceNotificationStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"