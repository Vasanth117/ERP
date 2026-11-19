"""Accounts / Finance Staff domain enumerations."""

from enum import Enum


class FeeCategoryClassification(str, Enum):
    TUITION = "tuition"
    ADMISSION = "admission"
    REGISTRATION = "registration"
    EXAMINATION = "examination"
    LABORATORY = "laboratory"
    LIBRARY = "library"
    DEVELOPMENT = "development"
    INFRASTRUCTURE = "infrastructure"
    CAUTION_DEPOSIT = "caution_deposit"
    HOSTEL = "hostel"
    TRANSPORT = "transport"
    OTHER = "other"


class RefundabilityClass(str, Enum):
    FULLY_REFUNDABLE = "fully_refundable"
    PARTIALLY_REFUNDABLE = "partially_refundable"
    NON_REFUNDABLE = "non_refundable"


class BillingFrequency(str, Enum):
    ONE_TIME = "one_time"
    PER_SEMESTER = "per_semester"
    PER_YEAR = "per_year"
    MONTHLY = "monthly"
    INSTALLMENT = "installment"


class FeeStructureLifecycleStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class FeeStructureApprovalAction(str, Enum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    SCHEDULE = "schedule"
    ACTIVATE = "activate"
    SUSPEND = "suspend"
    EXPIRE = "expire"
    SUPERSEDE = "supersede"
    ARCHIVE = "archive"
    REVISION_REQUEST = "revision_request"