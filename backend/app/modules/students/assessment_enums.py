"""Student CIA and continuous assessment enumerations."""

from enum import Enum


class AssessmentNotificationKind(str, Enum):
    MARKS_PUBLISHED = "marks_published"
    FEEDBACK_PUBLISHED = "feedback_published"
    ASSIGNMENT_DUE = "assignment_due"
    EVALUATION_PENDING = "evaluation_pending"


class MarkVisibility(str, Enum):
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    MISSING = "missing"


CIA_COMPONENT_TYPES = frozenset({"internal", "assignment", "practical"})
