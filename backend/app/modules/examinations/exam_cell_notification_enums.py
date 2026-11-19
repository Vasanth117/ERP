"""Examination cell notification enumerations."""

from enum import Enum


class ExamNotificationEvent(str, Enum):
    SESSION_ANNOUNCEMENT = "session_announcement"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSE = "registration_close"
    ELIGIBILITY_PUBLISHED = "eligibility_published"
    REGISTRATION_CONFIRMED = "registration_confirmed"
    HALL_TICKET_AVAILABLE = "hall_ticket_available"
    TIMETABLE_PUBLISHED = "timetable_published"
    SCHEDULE_CHANGE = "schedule_change"
    EXAM_REMINDER = "exam_reminder"
    MARKS_SUBMISSION_REMINDER = "marks_submission_reminder"
    RESULT_PUBLISHED = "result_published"
    REVALUATION_UPDATE = "revaluation_update"
    SUPPLEMENTARY_NOTICE = "supplementary_notice"
    INCIDENT_WORKFLOW = "incident_workflow"
    CELL_ANNOUNCEMENT = "cell_announcement"


class ExamNotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"


class ExamNotificationDeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class ExamAnnouncementAudience(str, Enum):
    ALL_STUDENTS = "all_students"
    SESSION_STUDENTS = "session_students"
    FACULTY = "faculty"
    EXAMINATION_STAFF = "examination_staff"
    CUSTOM = "custom"