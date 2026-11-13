"""Arrear and supplementary examination enumerations."""

from enum import Enum


class BacklogStatus(str, Enum):
    PENDING = "pending"
    CLEARED = "cleared"
    REGISTERED = "registered"


class SupplementaryRegistrationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
