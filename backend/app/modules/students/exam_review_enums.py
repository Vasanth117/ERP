"""Revaluation, rechecking, and correction request enumerations."""

from enum import Enum


class ExamReviewRequestType(str, Enum):
    REVALUATION = "revaluation"
    RECHECKING = "rechecking"
    MARKS_CORRECTION = "marks_correction"


class ExamReviewRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    PAYMENT_PENDING = "payment_pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class ExamReviewHistoryAction(str, Enum):
    SUBMITTED = "submitted"
    WITHDRAWN = "withdrawn"
    STATUS_CHANGED = "status_changed"
    OUTCOME_PUBLISHED = "outcome_published"
