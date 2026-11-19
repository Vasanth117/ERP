"""Examination cell — assessment configuration enumerations."""

from enum import Enum


class ExamAssessmentComponentKind(str, Enum):
    INTERNAL = "internal"
    CIA = "cia"
    MODEL_EXAM = "model_examination"
    PRACTICAL = "practical"
    LABORATORY = "laboratory"
    THEORY = "theory"
    END_SEMESTER = "end_semester"


class ExamAssessmentConfigStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ExamMarkRoundingMode(str, Enum):
    NEAREST = "nearest"
    HALF = "half"
    CEILING = "ceiling"
    FLOOR = "floor"