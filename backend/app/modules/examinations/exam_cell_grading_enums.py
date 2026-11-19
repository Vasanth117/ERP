"""Examination cell — grading policy and GPA enumerations."""

from enum import Enum


class ExamGradingPolicyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ExamGradeSystem(str, Enum):
    LETTER = "letter"
    POINTS = "points"


class ExamSubjectResultOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ABSENT = "absent"
    WITHHELD = "withheld"
    MALPRACTICE = "malpractice"
    EXEMPTED = "exempted"
    INCOMPLETE = "incomplete"


class ExamSubjectResultStatus(str, Enum):
    PROVISIONAL = "provisional"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    LOCKED = "locked"


class ExamResultReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    DEPARTMENT_VERIFIED = "department_verified"
    EXAM_CELL_VERIFIED = "exam_cell_verified"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExamResultApprovalStage(str, Enum):
    PROVISIONAL = "provisional"
    DEPARTMENT_REVIEW = "department_review"
    EXAM_CELL_VERIFICATION = "exam_cell_verification"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExamResultReviewAction(str, Enum):
    GENERATED = "generated"
    DEPARTMENT_REVIEW_STARTED = "department_review_started"
    DEPARTMENT_COMMENT = "department_comment"
    EXAM_CELL_VERIFIED = "exam_cell_verified"
    APPROVED = "approved"
    REJECTED = "rejected"
    RESUBMITTED = "resubmitted"
    RECALCULATED = "recalculated"