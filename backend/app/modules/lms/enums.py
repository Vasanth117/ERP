"""LMS enumerations."""

from enum import Enum


class MaterialPublishState(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class LmsAssignmentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class SubmissionStatus(str, Enum):
    MISSING = "missing"
    SUBMITTED = "submitted"
    LATE = "late"
    EVALUATED = "evaluated"
