"""Examination cell — marks entry enumerations."""

from enum import Enum


class ExamMarksSubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_MODERATION = "under_moderation"
    APPROVED = "approved"
    LOCKED = "locked"


class ExamMarksCandidateStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    MALPRACTICE = "malpractice"
    WITHHELD = "withheld"
    EXEMPTED = "exempted"


class ExamMarksComponentStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MODERATED = "moderated"
    LOCKED = "locked"


class ExamMarksCorrectionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExamMarksHistoryAction(str, Enum):
    ACCESS_GRANTED = "access_granted"
    DRAFT_SAVED = "draft_saved"
    SUBMITTED = "submitted"
    MODERATED = "moderated"
    CORRECTION_REQUESTED = "correction_requested"
    CORRECTION_APPLIED = "correction_applied"
    LOCKED = "locked"
    IMPORTED = "imported"
    BULK_SAVED = "bulk_saved"