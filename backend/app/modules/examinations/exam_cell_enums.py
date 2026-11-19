"""Examination cell — session and dashboard enumerations."""

from enum import Enum


class ExamSessionStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    RESULTS_PROCESSING = "results_processing"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class ExamSessionType(str, Enum):
    REGULAR = "regular"
    ARREAR = "arrear"
    SUPPLEMENTARY = "supplementary"
    SPECIAL = "special"


class ExamSessionLifecycleAction(str, Enum):
    ACTIVATE = "activate"
    OPEN_REGISTRATION = "open_registration"
    CLOSE_REGISTRATION = "close_registration"
    START_EXAMINATIONS = "start_examinations"
    COMPLETE_EXAMINATIONS = "complete_examinations"
    BEGIN_RESULT_PROCESSING = "begin_result_processing"
    PUBLISH_RESULTS = "publish_results"
    ARCHIVE = "archive"
    CANCEL = "cancel"
    SCHEDULE = "schedule"


_EXAM_SESSION_TRANSITIONS: dict[ExamSessionStatus, frozenset[ExamSessionStatus]] = {
    ExamSessionStatus.DRAFT: frozenset(
        {ExamSessionStatus.SCHEDULED, ExamSessionStatus.CANCELLED, ExamSessionStatus.ARCHIVED}
    ),
    ExamSessionStatus.SCHEDULED: frozenset(
        {ExamSessionStatus.REGISTRATION_OPEN, ExamSessionStatus.CANCELLED, ExamSessionStatus.ARCHIVED}
    ),
    ExamSessionStatus.REGISTRATION_OPEN: frozenset(
        {ExamSessionStatus.REGISTRATION_CLOSED, ExamSessionStatus.CANCELLED}
    ),
    ExamSessionStatus.REGISTRATION_CLOSED: frozenset(
        {ExamSessionStatus.ONGOING, ExamSessionStatus.CANCELLED}
    ),
    ExamSessionStatus.ONGOING: frozenset({ExamSessionStatus.COMPLETED, ExamSessionStatus.CANCELLED}),
    ExamSessionStatus.COMPLETED: frozenset({ExamSessionStatus.RESULTS_PROCESSING}),
    ExamSessionStatus.RESULTS_PROCESSING: frozenset({ExamSessionStatus.PUBLISHED}),
    ExamSessionStatus.PUBLISHED: frozenset({ExamSessionStatus.ARCHIVED}),
    ExamSessionStatus.CANCELLED: frozenset({ExamSessionStatus.ARCHIVED}),
    ExamSessionStatus.ARCHIVED: frozenset(),
}


_ACTION_TO_STATUS: dict[ExamSessionLifecycleAction, ExamSessionStatus] = {
    ExamSessionLifecycleAction.SCHEDULE: ExamSessionStatus.SCHEDULED,
    ExamSessionLifecycleAction.ACTIVATE: ExamSessionStatus.SCHEDULED,
    ExamSessionLifecycleAction.OPEN_REGISTRATION: ExamSessionStatus.REGISTRATION_OPEN,
    ExamSessionLifecycleAction.CLOSE_REGISTRATION: ExamSessionStatus.REGISTRATION_CLOSED,
    ExamSessionLifecycleAction.START_EXAMINATIONS: ExamSessionStatus.ONGOING,
    ExamSessionLifecycleAction.COMPLETE_EXAMINATIONS: ExamSessionStatus.COMPLETED,
    ExamSessionLifecycleAction.BEGIN_RESULT_PROCESSING: ExamSessionStatus.RESULTS_PROCESSING,
    ExamSessionLifecycleAction.PUBLISH_RESULTS: ExamSessionStatus.PUBLISHED,
    ExamSessionLifecycleAction.ARCHIVE: ExamSessionStatus.ARCHIVED,
    ExamSessionLifecycleAction.CANCEL: ExamSessionStatus.CANCELLED,
}


def assert_exam_session_transition(current: ExamSessionStatus, target: ExamSessionStatus) -> None:
    allowed = _EXAM_SESSION_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition exam session from {current.value} to {target.value}")


def target_status_for_action(action: ExamSessionLifecycleAction) -> ExamSessionStatus:
    return _ACTION_TO_STATUS[action]