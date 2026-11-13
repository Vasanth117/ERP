"""Student portal enumerations."""

from enum import Enum


class StudentActivityType(str, Enum):
    PROFILE_UPDATED = "profile_updated"
    ENROLLMENT_REQUEST = "enrollment_request"
    DASHBOARD_VIEW = "dashboard_view"
    DOCUMENT_VIEWED = "document_viewed"
    OTHER = "other"


class StudentEnrollmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    ON_LEAVE = "on_leave"
    PROVISIONAL = "provisional"


class AcademicStanding(str, Enum):
    GOOD = "good_standing"
    PROBATION = "probation"
    SUSPENDED = "suspended"
    GRADUATED = "graduated"
    UNKNOWN = "unknown"


class ProgressionStatus(str, Enum):
    PROMOTED = "promoted"
    HELD = "held"
    REPEAT = "repeat"
    PENDING = "pending_review"
    NOT_APPLICABLE = "not_applicable"


class StudentAcademicRequestType(str, Enum):
    SECTION_CHANGE = "section_change"
    COURSE_ADD = "course_add"
    COURSE_DROP = "course_drop"
    LEAVE_OF_ABSENCE = "leave_of_absence"
    REINSTATEMENT = "reinstatement"
    OTHER = "other"


class StudentAcademicRequestStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DashboardDateRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"


class StudentNotificationCategory(str, Enum):
    ACADEMIC = "academic"
    FINANCE = "finance"
    EXAMINATION = "examination"
    GENERAL = "general"
