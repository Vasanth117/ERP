"""Phase 5 scholarship and concession enumerations."""

from enum import Enum


class ScholarshipProgramStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class ScholarshipWorkflowStatus(str, Enum):
    DRAFT = "draft"
    APPLICATION_SUBMITTED = "application_submitted"
    UNDER_REVIEW = "under_review"
    ADDITIONAL_INFO = "additional_information_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    AWARDED = "awarded"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    RENEWED = "renewed"
    CANCELLED = "cancelled"


class ScholarshipAwardStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class ScholarshipAwardType(str, Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    COMPONENT = "fee_component"
    RECURRING = "recurring"
    ONE_TIME = "one_time"


class EligibilityRuleOperator(str, Enum):
    GTE = "gte"
    LTE = "lte"
    EQ = "eq"
    IN = "in"
    NOT_IN = "not_in"


class ConcessionApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class WaiverType(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    COMPONENT = "component"
    ONE_TIME = "one_time"
    SEMESTER = "semester"
    ACADEMIC_YEAR = "academic_year"