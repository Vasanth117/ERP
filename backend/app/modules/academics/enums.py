"""Academic domain enumerations."""

from enum import Enum


class SessionType(str, Enum):
    LECTURE = "lecture"
    LABORATORY = "laboratory"
    TUTORIAL = "tutorial"


class TimetableEntryStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
