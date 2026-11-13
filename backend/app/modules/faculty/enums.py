"""Faculty domain enumerations."""

from enum import Enum


class AssignmentRole(str, Enum):
    PRIMARY = "primary"
    CO_TEACHER = "co_teacher"
    GUEST = "guest"


class AssignmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FacultyActivityType(str, Enum):
    PROFILE_UPDATED = "profile_updated"
    COVERAGE_UPDATED = "coverage_updated"
    SESSION_UPDATE_REQUESTED = "session_update_requested"
    ASSIGNMENT_CHANGED = "assignment_changed"
    ATTENDANCE_SUBMITTED = "attendance_submitted"
    ASSESSMENT_PUBLISHED = "assessment_published"
    ASSIGNMENT_GRADED = "assignment_graded"
    NOTIFICATION = "notification"
    OTHER = "other"


class FacultyNotificationCategory(str, Enum):
    ACADEMIC = "academic"
    DEPARTMENT = "department"
    EXAMINATION = "examination"
    GENERAL = "general"


class DashboardDateRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"


class SessionUpdateRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SessionUpdateRequestType(str, Enum):
    TOPIC_UPDATE = "topic_update"
    CANCELLATION_REQUEST = "cancellation_request"
    RESCHEDULE_REQUEST = "reschedule_request"
