"""Student grade and academic document enumerations."""

from enum import Enum


class AcademicDocumentRequestType(str, Enum):
    TRANSCRIPT = "transcript"
    CONSOLIDATED_MARKSHEET = "consolidated_marksheet"
    MARKSHEET = "marksheet"
    GRADE_CARD = "grade_card"
    REISSUE = "reissue"


class AcademicDocumentRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FULFILLED = "fulfilled"


class DocumentReferenceKind(str, Enum):
    MARKSHEET = "marksheet"
    GRADE_CARD = "grade_card"
    TRANSCRIPT = "transcript"
