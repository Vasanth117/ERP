"""Library domain enumerations."""

from enum import Enum


class LibraryCopyStatus(str, Enum):
    AVAILABLE = "available"
    ISSUED = "issued"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    DAMAGED = "damaged"
    LOST = "lost"
    WITHDRAWN = "withdrawn"


class LibraryCopyCondition(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNUSABLE = "unusable"


class LibraryCirculationStatus(str, Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


class LibraryReservationStatus(str, Enum):
    QUEUED = "queued"
    READY = "ready"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class LibraryFineStatus(str, Enum):
    OPEN = "open"
    PENDING_WAIVER = "pending_waiver"
    PENDING_WRITEOFF = "pending_writeoff"
    PAID = "paid"
    WAIVED = "waived"
    WRITTEN_OFF = "written_off"


class LibraryDashboardDateRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    SEMESTER = "semester"
