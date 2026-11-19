"""Physical copy inventory enumerations."""

from enum import Enum


class InventoryAdjustmentType(str, Enum):
    STATUS_CHANGE = "status_change"
    CONDITION_CHANGE = "condition_change"
    LOCATION_CHANGE = "location_change"
    FOUND = "found"
    WRITE_OFF = "write_off"
    CORRECTION = "correction"


class StockVerificationStatus(str, Enum):
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StockVerificationItemOutcome(str, Enum):
    FOUND = "found"
    MISSING = "missing"
    UNEXPECTED = "unexpected"