"""Student portal phase 10 enumerations."""

from enum import Enum


class StudentServiceCategory(str, Enum):
    LIBRARY = "library"
    HOSTEL = "hostel"
    TRANSPORT = "transport"
    ACADEMIC = "academic"
    GENERAL = "general"


class StudentServiceRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class StudentDocumentPortalType(str, Enum):
    BONAFIDE = "bonafide"
    CHARACTER = "character"
    TRANSFER = "transfer"
    OTHER = "other"


class StudentDocumentRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class StudentReportType(str, Enum):
    ACADEMIC_SUMMARY = "academic_summary"
    ATTENDANCE = "attendance"
    EXAMINATION_PERFORMANCE = "examination_performance"
    FEE_SUMMARY = "fee_summary"
    COURSE_REGISTRATION = "course_registration"


class StudentReportExportStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    EXPIRED = "expired"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
