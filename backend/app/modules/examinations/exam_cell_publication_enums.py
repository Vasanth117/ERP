"""Examination cell — result publication enumerations."""

from enum import Enum


class ExamPublicationScopeType(str, Enum):
    SESSION = "session"
    PROGRAMME = "programme"
    SEMESTER = "semester"
    STUDENT_GROUP = "student_group"


class ExamPublicationStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REVISED = "revised"
    WITHHELD = "withheld"


class ExamPublicationHistoryAction(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    WITHHELD = "withheld"
    RELEASED = "released"
    REVISED = "revised"
    VISIBILITY_CHANGED = "visibility_changed"


class ExamResultDocumentType(str, Enum):
    GRADE_CARD = "grade_card"
    MARKSHEET = "marksheet"
    TRANSCRIPT = "transcript"
    ACADEMIC_STATEMENT = "academic_statement"
    PROVISIONAL_STATEMENT = "provisional_statement"