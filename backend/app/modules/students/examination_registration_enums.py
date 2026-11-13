"""Student examination registration enumerations."""

from enum import Enum


class StudentExamRegistrationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class ExamRegistrationSubjectType(str, Enum):
    SEMESTER = "semester"
    ARREAR = "arrear"


class ExamRegistrationHistoryAction(str, Enum):
    CREATED = "created"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    UPDATED = "updated"


class ResultNotificationKind(str, Enum):
    PUBLISHED = "published"
    PROCESSING = "processing"
    WITHHELD = "withheld"
    GENERAL = "general"
