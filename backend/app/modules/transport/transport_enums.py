"""Transport domain enumerations."""

from enum import Enum


class TransportRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TransportRequestType(str, Enum):
    ROUTE_CHANGE = "route_change"
    PICKUP_CHANGE = "pickup_change"
    PASS_ISSUE = "pass_issue"
    OTHER = "other"
