"""Library settings and policy enumerations."""

from enum import StrEnum


class LibraryPolicyStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class LibraryResourceType(StrEnum):
    ANY = "any"
    PHYSICAL = "physical"
    EBOOK = "ebook"
    REFERENCE = "reference"
    JOURNAL = "journal"


class LibraryPolicyType(StrEnum):
    BORROWING = "borrowing"
    FINE = "fine"
    RESERVATION = "reservation"