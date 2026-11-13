"""Library domain enumerations."""

from enum import Enum


class LibraryCopyStatus(str, Enum):
    AVAILABLE = "available"
    ISSUED = "issued"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    LOST = "lost"


class LibraryCirculationStatus(str, Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


class LibraryReservationStatus(str, Enum):
    QUEUED = "queued"
    READY = "ready"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class LibraryFineStatus(str, Enum):
    OPEN = "open"
    PAID = "paid"
    WAIVED = "waived"
