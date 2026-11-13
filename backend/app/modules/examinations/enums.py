"""Examination and assessment enumerations."""

from enum import Enum


class AssessmentComponentType(str, Enum):
    INTERNAL = "internal"
    PRACTICAL = "practical"
    ASSIGNMENT = "assignment"
    FINAL_EXAM = "final_exam"


class MarksBatchStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class StudentMarkStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    LOCKED = "locked"


class MarksCorrectionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class GradingLetterScale(str, Enum):
    LETTER = "letter"
    PASS_FAIL = "pass_fail"


class ExaminationEligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    CONDITIONAL = "conditional"
    PENDING_REVIEW = "pending_review"


class ExaminationAnnouncementAudience(str, Enum):
    STUDENTS = "students"
    FACULTY = "faculty"
    ALL = "all"
