"""College admin enumerations."""

from enum import Enum


class InstitutionActivityKind(str, Enum):
    PROFILE_UPDATED = "profile_updated"
    CAMPUS_CREATED = "campus_created"
    CAMPUS_UPDATED = "campus_updated"
    SETTINGS_UPDATED = "settings_updated"
    BRANDING_UPDATED = "branding_updated"
    DASHBOARD_VIEW = "dashboard_view"


class DashboardDateRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    SEMESTER = "semester"


class PendingApprovalCategory(str, Enum):
    ATTENDANCE = "attendance"
    ASSESSMENT = "assessment"
    LEAVE = "leave"
    STUDENT_REQUEST = "student_request"
    ENROLLMENT = "enrollment"
    PROFILE_CORRECTION = "profile_correction"
    HOSTEL = "hostel"
    SCHOLARSHIP = "scholarship"
    OTHER = "other"
