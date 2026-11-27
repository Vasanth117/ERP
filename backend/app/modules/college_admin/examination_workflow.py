"""Shared examination administration workflow (CA 09)."""

from __future__ import annotations

from app.modules.college_admin.schemas import FacultyAssignmentWorkflowStep

WORKFLOW_DEF: list[tuple[str, str, int, str]] = [
    ("create_examination", "Create examination", 1, "/college-admin/examinations/examination-configuration"),
    ("configure_subjects", "Configure subjects", 2, "/college-admin/examinations/internal-external-assessment"),
    ("generate_timetable", "Generate timetable", 3, "/college-admin/examinations/exam-timetable-management"),
    ("assign_halls", "Assign halls", 4, "/college-admin/examinations/examination-hall-seating-management"),
    ("marks_entry", "Marks entry", 5, "/college-admin/examinations/marks-entry-management"),
    (
        "result_approval",
        "Result approval and publication",
        6,
        "/college-admin/examinations/result-approval",
    ),
]


def workflow_steps(active_key: str) -> list[FacultyAssignmentWorkflowStep]:
    active_index = next((i for i, (key, *_) in enumerate(WORKFLOW_DEF) if key == active_key), 0)
    steps: list[FacultyAssignmentWorkflowStep] = []
    for index, (key, label, number, href) in enumerate(WORKFLOW_DEF):
        if index < active_index:
            status = "done"
        elif index == active_index:
            status = "active"
        else:
            status = "pending"
        steps.append(FacultyAssignmentWorkflowStep(key=key, label=label, step_number=number, status=status, href=href))
    return steps


def workflow_href_after(step_key: str, session_id: str | None) -> str | None:
    for index, (key, *_rest, href) in enumerate(WORKFLOW_DEF):
        if key != step_key:
            continue
        if index + 1 >= len(WORKFLOW_DEF):
            return None
        next_href = WORKFLOW_DEF[index + 1][3]
        if session_id:
            sep = "&" if "?" in next_href else "?"
            return f"{next_href}{sep}session_id={session_id}"
        return next_href
    return None