"""Library fine and damage enumerations."""

from enum import Enum


class LibraryFineType(str, Enum):
    OVERDUE = "overdue"
    LOST = "lost"
    DAMAGED = "damaged"
    REPLACEMENT = "replacement"


class LibraryFineRecoveryStatus(str, Enum):
    OPEN = "open"
    PARTIAL = "partial"
    RECOVERED = "recovered"
    WRITTEN_OFF = "written_off"


class LibraryFineApprovalType(str, Enum):
    WAIVER = "waiver"
    WRITEOFF = "writeoff"


class LibraryFineApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"