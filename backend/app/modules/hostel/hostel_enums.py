"""Hostel domain enumerations."""

from enum import Enum


class HostelApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"


class HostelRequestType(str, Enum):
    MAINTENANCE = "maintenance"
    ROOM_CHANGE = "room_change"
    LEAVE = "leave"
    OUTPASS = "outpass"
    OTHER = "other"


class HostelRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
