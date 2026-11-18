"""Library acquisition workflow enums."""

from enum import Enum


class LibraryAcquisitionType(str, Enum):
    SUGGESTION = "suggestion"
    PURCHASE = "purchase"


class LibraryAcquisitionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    QUOTED = "quoted"
    ORDERED = "ordered"
    PARTIAL_RECEIVED = "partial_received"
    RECEIVED = "received"
    REGISTERED = "registered"
    CANCELLED = "cancelled"