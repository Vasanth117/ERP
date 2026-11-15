"""Department helpdesk categories and status transitions."""

from app.modules.department_admin.models import DepartmentHelpdeskStatus

HELPDESK_CATEGORIES = frozenset(
    {
        "academic",
        "faculty",
        "student_administration",
        "attendance",
        "timetable",
        "examination_coordination",
        "department_resources",
        "classroom_laboratory",
        "equipment",
        "document_management",
        "erp_technical",
        "other",
    }
)

STATUS_TRANSITIONS: dict[DepartmentHelpdeskStatus, frozenset[DepartmentHelpdeskStatus]] = {
    DepartmentHelpdeskStatus.OPEN: frozenset(
        {
            DepartmentHelpdeskStatus.ASSIGNED,
            DepartmentHelpdeskStatus.IN_PROGRESS,
            DepartmentHelpdeskStatus.WAITING_FOR_INFORMATION,
            DepartmentHelpdeskStatus.ESCALATED,
            DepartmentHelpdeskStatus.CLOSED,
        }
    ),
    DepartmentHelpdeskStatus.REOPENED: frozenset(
        {
            DepartmentHelpdeskStatus.ASSIGNED,
            DepartmentHelpdeskStatus.IN_PROGRESS,
            DepartmentHelpdeskStatus.ESCALATED,
        }
    ),
    DepartmentHelpdeskStatus.ASSIGNED: frozenset(
        {
            DepartmentHelpdeskStatus.IN_PROGRESS,
            DepartmentHelpdeskStatus.WAITING_FOR_INFORMATION,
            DepartmentHelpdeskStatus.ESCALATED,
            DepartmentHelpdeskStatus.RESOLVED,
        }
    ),
    DepartmentHelpdeskStatus.IN_PROGRESS: frozenset(
        {
            DepartmentHelpdeskStatus.WAITING_FOR_INFORMATION,
            DepartmentHelpdeskStatus.ESCALATED,
            DepartmentHelpdeskStatus.RESOLVED,
            DepartmentHelpdeskStatus.ASSIGNED,
        }
    ),
    DepartmentHelpdeskStatus.WAITING_FOR_INFORMATION: frozenset(
        {
            DepartmentHelpdeskStatus.IN_PROGRESS,
            DepartmentHelpdeskStatus.ASSIGNED,
            DepartmentHelpdeskStatus.ESCALATED,
        }
    ),
    DepartmentHelpdeskStatus.ESCALATED: frozenset(
        {
            DepartmentHelpdeskStatus.IN_PROGRESS,
            DepartmentHelpdeskStatus.RESOLVED,
            DepartmentHelpdeskStatus.ASSIGNED,
        }
    ),
    DepartmentHelpdeskStatus.RESOLVED: frozenset({DepartmentHelpdeskStatus.CLOSED, DepartmentHelpdeskStatus.REOPENED}),
    DepartmentHelpdeskStatus.CLOSED: frozenset({DepartmentHelpdeskStatus.REOPENED}),
}

PLACEMENT_ACTIVITY_TYPES = frozenset(
    {
        "mock_interview",
        "resume_workshop",
        "career_guidance",
        "technical_training",
        "dept_placement_meeting",
        "recruiter_event",
        "other",
    }
)

PROJECT_TYPES = frozenset({"academic", "capstone", "mini_project", "industry", "research_linked", "other"})

RESEARCH_EVENT_CATEGORIES = frozenset({"research_seminar", "project_review", "workshop"})