"""Library & branch facility enumerations."""

from enum import Enum


class LibraryOperatingStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    TEMPORARILY_CLOSED = "temporarily_closed"


class LibraryStaffRole(str, Enum):
    HEAD_LIBRARIAN = "head_librarian"
    LIBRARIAN = "librarian"
    ASSISTANT = "assistant"
    CIRCULATION_DESK = "circulation_desk"
    CATALOGUER = "cataloguer"


class LibraryStaffAssignmentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ENDED = "ended"


class LibraryLocationLevel(str, Enum):
    FLOOR = "floor"
    ROOM = "room"
    RACK = "rack"
    SHELF = "shelf"


class LibraryConfigEntityType(str, Enum):
    LIBRARY = "library"
    BRANCH = "branch"
    OPERATING_HOURS = "operating_hours"
    HOLIDAY = "holiday"
    STAFF_ASSIGNMENT = "staff_assignment"
    SECTION = "section"
    SHELF_LOCATION = "shelf_location"