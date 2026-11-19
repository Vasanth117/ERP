"""Digital library enumerations."""

from enum import StrEnum


class DigitalResourceType(StrEnum):
    EBOOK = "ebook"
    JOURNAL = "journal"
    RESEARCH_PAPER = "research_paper"
    REFERENCE = "reference"


class DigitalAvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class DigitalAccessAction(StrEnum):
    VIEW = "view"
    DOWNLOAD = "download"
    EXTERNAL_LINK = "external_link"