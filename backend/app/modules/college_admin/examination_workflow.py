"""Shared examination administration workflow (CA 09)."""

from __future__ import annotations

from app.modules.college_admin.schemas import ExaminationWorkflowEmptyState, FacultyAssignmentWorkflowStep

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


def workflow_back_href(step_key: str, session_id: str | None) -> str:
    index = next((i for i, (key, *_) in enumerate(WORKFLOW_DEF) if key == step_key), 0)
    if index <= 0:
        return "/college-admin/examinations/examination-session-management"
    href = WORKFLOW_DEF[index - 1][3]
    if session_id:
        sep = "&" if "?" in href else "?"
        return f"{href}{sep}session_id={session_id}"
    return href


def workflow_chrome(step_key: str, session_id: str | None) -> dict[str, object]:
    step_index = next((i for i, (key, *_) in enumerate(WORKFLOW_DEF) if key == step_key), 0)
    _key, step_label, step_number, _href = WORKFLOW_DEF[step_index]
    next_href = workflow_href_after(step_key, session_id) or ""
    return {
        "workflow_steps": workflow_steps(step_key),
        "workflow_active_key": step_key,
        "step_progress_label": f"Step {step_number} of {len(WORKFLOW_DEF)} · {step_label}",
        "back_href": workflow_back_href(step_key, session_id),
        "save_draft_label": "Save draft",
        "continue_label": "Continue",
        "continue_href": next_href,
        "continue_enabled": bool(next_href),
    }


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


def with_session_id(href: str, session_id: str | None) -> str:
    if not session_id:
        return href
    sep = "&" if "?" in href else "?"
    return f"{href}{sep}session_id={session_id}"


def empty_state_for_step(step_key: str, session_id: str | None) -> ExaminationWorkflowEmptyState:
    next_href = workflow_href_after(step_key, session_id)
    registrations_href = with_session_id("/college-admin/examinations/exam-registration-management", session_id)
    eligibility_href = with_session_id("/college-admin/examinations/student-exam-eligibility", session_id)
    marks_href = with_session_id("/college-admin/examinations/marks-entry-management", session_id)
    processing_href = with_session_id("/college-admin/examinations/result-processing", session_id)

    if step_key == "configure_subjects":
        return ExaminationWorkflowEmptyState(
            icon_slug="book-open",
            title="No assessment pattern yet",
            description="Create an assessment pattern for this academic year and semester. It applies to all programmes in scope—individual student registration is not required here.",
            primary_action_label="Create assessment pattern",
            primary_action_key="create_assessment_pattern",
        )
    if step_key == "generate_timetable":
        return ExaminationWorkflowEmptyState(
            icon_slug="calendar",
            title="No timetable entries yet",
            description="Generate papers from the curriculum mapped to this academic year and semester. Regenerate any time until you publish.",
            primary_action_label="Generate timetable",
            primary_action_key="regenerate_timetable",
            secondary_action_label="Open course curriculum",
            secondary_action_href="/college-admin/academics/curriculum-management",
        )
    if step_key == "assign_halls":
        return ExaminationWorkflowEmptyState(
            icon_slug="layout-grid",
            title="No exam halls configured",
            description="Create or assign halls for this session, then auto-allocate seating from the timetable.",
            primary_action_label="Auto-allocate seating",
            primary_action_key="auto_allocate_seating",
            secondary_action_label="Review timetable",
            secondary_action_href=with_session_id("/college-admin/examinations/exam-timetable-management", session_id),
        )
    if step_key == "marks_entry":
        return ExaminationWorkflowEmptyState(
            icon_slug="file-text",
            title="No scripts for marks entry",
            description="Students need confirmed registrations (and hall allocation) before marks can be entered.",
            primary_action_label="Open exam registration",
            primary_action_href=registrations_href,
            secondary_action_label="Check eligibility",
            secondary_action_href=eligibility_href,
        )
    if step_key == "result_approval":
        return ExaminationWorkflowEmptyState(
            icon_slug="check",
            title="No programme summaries yet",
            description="Process results and complete marks entry before this approval step is available.",
            primary_action_label="Open result processing",
            primary_action_href=processing_href,
            secondary_action_label="Go to marks entry",
            secondary_action_href=marks_href,
        )
    return ExaminationWorkflowEmptyState(
        icon_slug="inbox",
        title="Nothing to show yet",
        description="Complete earlier steps in the creation flow.",
        primary_action_label="Back to sessions",
        primary_action_href="/college-admin/examinations/examination-session-management",
    )