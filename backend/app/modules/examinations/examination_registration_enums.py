"""Examination registration and fee enumerations."""

from enum import Enum


class ExaminationFeePaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    WAIVED = "waived"


class HallTicketPublicationStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    REVOKED = "revoked"


class SemesterResultPublicationStatus(str, Enum):
    PROCESSING = "processing"
    PUBLISHED = "published"
    WITHHELD = "withheld"
