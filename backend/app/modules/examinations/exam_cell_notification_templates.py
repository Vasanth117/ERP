"""Default examination notification copy (tenant templates may override)."""

from app.modules.examinations.exam_cell_notification_enums import ExamNotificationEvent

_DEFAULTS: dict[ExamNotificationEvent, tuple[str, str]] = {
    ExamNotificationEvent.SESSION_ANNOUNCEMENT: ("Examination session", "{message}"),
    ExamNotificationEvent.REGISTRATION_OPEN: ("Registration open", "Registration for {session_name} is now open until {closes_at}."),
    ExamNotificationEvent.REGISTRATION_CLOSE: ("Registration closing", "Registration for {session_name} closes on {closes_at}."),
    ExamNotificationEvent.ELIGIBILITY_PUBLISHED: ("Eligibility published", "Your eligibility for {session_name} has been published."),
    ExamNotificationEvent.REGISTRATION_CONFIRMED: ("Registration confirmed", "You are registered for {session_name} ({subject_count} subjects)."),
    ExamNotificationEvent.HALL_TICKET_AVAILABLE: ("Hall ticket available", "Your hall ticket for {session_name} is available."),
    ExamNotificationEvent.TIMETABLE_PUBLISHED: ("Timetable published", "The examination timetable for {session_name} has been published."),
    ExamNotificationEvent.SCHEDULE_CHANGE: ("Schedule change", "{summary}"),
    ExamNotificationEvent.EXAM_REMINDER: ("Examination reminder", "Upcoming exam: {course_code} on {exam_at} at {venue}."),
    ExamNotificationEvent.MARKS_SUBMISSION_REMINDER: ("Marks submission reminder", "Please submit marks for {course_code} ({session_name})."),
    ExamNotificationEvent.RESULT_PUBLISHED: ("Results published", "Results for {session_name} have been published."),
    ExamNotificationEvent.REVALUATION_UPDATE: ("Revaluation update", "{status_message}"),
    ExamNotificationEvent.SUPPLEMENTARY_NOTICE: ("Supplementary examination", "{message}"),
    ExamNotificationEvent.INCIDENT_WORKFLOW: ("Examination incident update", "{summary}"),
    ExamNotificationEvent.CELL_ANNOUNCEMENT: ("{title}", "{body}"),
}


def render_exam_notification(event: ExamNotificationEvent, **kwargs: str) -> tuple[str, str]:
    title_t, body_t = _DEFAULTS[event]
    safe = {k: (v or "") for k, v in kwargs.items()}
    return title_t.format(**safe), body_t.format(**safe)