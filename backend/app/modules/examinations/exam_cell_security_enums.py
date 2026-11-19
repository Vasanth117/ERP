"""Examination integration, security and audit enumerations."""

from enum import Enum


class ExamIntegrationTarget(str, Enum):
    STUDENT_MANAGEMENT = "student_management"
    ACADEMIC_MANAGEMENT = "academic_management"
    CURRICULUM = "curriculum"
    FACULTY = "faculty"
    ATTENDANCE = "attendance"
    FINANCE = "finance"
    CAMPUS = "campus"
    DOCUMENTS = "documents"
    NOTIFICATIONS = "notifications"
    REPORTING = "reporting"


class ExamIntegrationSyncStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ExamSecurityEventType(str, Enum):
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SEPARATION_OF_DUTIES = "separation_of_duties"
    RATE_LIMITED = "rate_limited"
    POLICY_VIOLATION = "policy_violation"


class ExamAccessReviewStatus(str, Enum):
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"