"""Library audit and inventory-control enumerations."""

from enum import Enum


class LibraryAuditDomain(str, Enum):
    ACTIVITY = "activity"
    CATALOGUE = "catalogue"
    INVENTORY = "inventory"
    CIRCULATION = "circulation"
    RESERVATION = "reservation"
    FINE = "fine"
    MEMBER = "member"
    FACILITY = "facility"
    SETTINGS = "settings"
    ACQUISITION = "acquisition"
    DIGITAL = "digital"
    STAFF = "staff"


class StockDiscrepancyKind(str, Enum):
    MISSING = "missing"
    UNEXPECTED = "unexpected"
    EXCESS = "excess"


class StockDiscrepancyStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class StockAdjustmentRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"