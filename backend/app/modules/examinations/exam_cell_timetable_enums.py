"""Examination cell — exam timetable enumerations."""

from enum import Enum


class ExamTimetableStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ExamTimetableEntryStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class ExamScheduleApprovalDecision(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExamTimetableRevisionType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    ENTRY_ADDED = "entry_added"
    ENTRY_CANCELLED = "entry_cancelled"
    ENTRY_RESCHEDULED = "entry_rescheduled"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    REVISED = "revised"


_TIMETABLE_TRANSITIONS: dict[ExamTimetableStatus, frozenset[ExamTimetableStatus]] = {
    ExamTimetableStatus.DRAFT: frozenset({ExamTimetableStatus.IN_REVIEW, ExamTimetableStatus.CANCELLED}),
    ExamTimetableStatus.IN_REVIEW: frozenset({ExamTimetableStatus.APPROVED, ExamTimetableStatus.DRAFT}),
    ExamTimetableStatus.APPROVED: frozenset({ExamTimetableStatus.PUBLISHED, ExamTimetableStatus.DRAFT}),
    ExamTimetableStatus.PUBLISHED: frozenset({ExamTimetableStatus.DRAFT, ExamTimetableStatus.ARCHIVED}),
    ExamTimetableStatus.CANCELLED: frozenset({ExamTimetableStatus.ARCHIVED}),
    ExamTimetableStatus.ARCHIVED: frozenset(),
}


def assert_timetable_transition(current: ExamTimetableStatus, target: ExamTimetableStatus) -> None:
    allowed = _TIMETABLE_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition exam timetable from {current.value} to {target.value}")