"""Library notification enumerations."""

from enum import StrEnum


class LibraryNotificationEvent(StrEnum):
    ISSUE = "issue"
    RETURN_REMINDER = "return_reminder"
    DUE_UPCOMING = "due_upcoming"
    OVERDUE = "overdue"
    RESERVATION_READY = "reservation_ready"
    RESERVATION_EXPIRY = "reservation_expiry"
    FINE = "fine"
    MEMBERSHIP_EXPIRY = "membership_expiry"
    ANNOUNCEMENT = "announcement"


class LibraryNotificationChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"


class LibraryDeliveryStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"