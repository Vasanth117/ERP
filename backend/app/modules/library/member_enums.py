"""Library membership enumerations."""

from enum import Enum


class LibraryMemberCategory(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    EMPLOYEE = "employee"
    EXTERNAL = "external"


class LibraryMemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"