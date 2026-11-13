"""Student timetable and attendance portal enumerations."""

from enum import Enum


class DiscrepancyRequestStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AttendanceNotificationType(str, Enum):
    SHORTAGE_WARNING = "shortage_warning"
    TIMETABLE_CHANGE = "timetable_change"
    GENERAL = "general"


class AttendanceDataStatus(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    NOT_AVAILABLE = "not_available"
