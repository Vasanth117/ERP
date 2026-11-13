"""Course registration enumerations."""

from enum import Enum


class CourseRegistrationType(str, Enum):
    CORE = "core"
    ELECTIVE = "elective"
    OPEN = "open"


class CourseRegistrationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RegistrationRequestStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
