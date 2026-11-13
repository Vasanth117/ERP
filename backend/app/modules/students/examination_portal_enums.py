"""Student practical and semester examination portal enumerations."""

from enum import Enum


class ExaminationNotificationKind(str, Enum):
    SCHEDULE_CHANGE = "schedule_change"
    ELIGIBILITY = "eligibility"
    MARKS_PUBLISHED = "marks_published"
    ANNOUNCEMENT = "announcement"
    GENERAL = "general"


PRACTICAL_EXAM_TYPES = frozenset(
    {
        "practical",
        "laboratory",
        "lab",
        "lab_exam",
        "laboratory_exam",
        "practical_exam",
    }
)

MODEL_EXAM_TYPES = frozenset(
    {
        "model",
        "model_exam",
        "model_examination",
    }
)

SEMESTER_EXAM_TYPES = frozenset(
    {
        "semester",
        "end_semester",
        "final",
        "final_exam",
        "university",
        "semester_examination",
    }
)
