"""LMS assessments administration pages (CA 15.06–08)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import timedelta

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.academics.models import UpcomingAssessment
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.lms_courses_shared import load_course_context
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LmsAssignmentManagementPageRead,
    LmsAssignmentManagementRow,
    LmsAssessmentManagementPageRead,
    LmsAssessmentManagementRow,
    LmsQuizManagementPageRead,
    LmsQuizManagementRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.examinations.enums import StudentMarkStatus
from app.modules.examinations.models import AssessmentComponent, StudentAssessmentMark
from app.modules.lms.enums import LmsAssignmentStatus, SubmissionStatus
from app.modules.lms.models import AssignmentEvaluation, AssignmentSubmission, CourseAssignment
from app.modules.students.student_lms_models import StudentLearningProgress

_PAGE_SIZE = 3
_PUBLISHED_MARK_STATUSES = frozenset({StudentMarkStatus.APPROVED, StudentMarkStatus.LOCKED})


def _paginate(rows: list, page: int, page_size: int):
    total = len(rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    paged = rows[offset : offset + page_size]
    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(paged))
    footer = f"Showing {showing_end:,} of {total:,}"
    short_footer = f"{showing_end:,} of {total:,}"
    return paged, total, total_pages, footer, short_footer


def _due_label(deadline) -> str:
    return deadline.strftime("%d %b")


def _is_quiz_assessment(assessment_type: str) -> bool:
    key = (assessment_type or "").strip().lower()
    if not key:
        return False
    if "quiz" in key:
        return True
    return key in {"test", "ia", "mcq"}


async def _roster_sizes(tenant_id) -> dict[tuple[str, str], int]:
    sizes: dict[tuple[str, str], set] = defaultdict(set)
    progress = await StudentLearningProgress.find(Eq(StudentLearningProgress.tenant_id, tenant_id)).to_list()
    for row in progress:
        sizes[(row.course_code.upper(), "")].add(row.user_id)
    return {k: len(v) for k, v in sizes.items()}


async def get_lms_assignment_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LmsAssignmentManagementPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    assignments = await CourseAssignment.find(Eq(CourseAssignment.tenant_id, tenant_id)).sort("-deadline_at").to_list()
    table_assignments = [a for a in assignments if a.status == LmsAssignmentStatus.PUBLISHED]

    assignment_ids = [a.id for a in assignments]
    submissions: list[AssignmentSubmission] = []
    if assignment_ids:
        submissions = await AssignmentSubmission.find(
            Eq(AssignmentSubmission.tenant_id, tenant_id),
            In(AssignmentSubmission.assignment_id, assignment_ids),
        ).to_list()

    submission_ids = [s.id for s in submissions]
    evaluations: set = set()
    if submission_ids:
        for ev in await AssignmentEvaluation.find(
            Eq(AssignmentEvaluation.tenant_id, tenant_id),
            In(AssignmentEvaluation.submission_id, submission_ids),
        ).to_list():
            evaluations.add(ev.submission_id)

    subs_by_assignment: dict[str, list[AssignmentSubmission]] = defaultdict(list)
    for sub in submissions:
        subs_by_assignment[str(sub.assignment_id)].append(sub)

    roster_by_course = await _roster_sizes(tenant_id)

    published_open = 0
    overdue_count = 0
    pending_eval = 0
    for a in assignments:
        if a.status == LmsAssignmentStatus.PUBLISHED:
            if a.deadline_at >= now:
                published_open += 1
        aid = str(a.id)
        subs = subs_by_assignment.get(aid, [])
        for sub in subs:
            if sub.id not in evaluations and sub.status in {
                SubmissionStatus.SUBMITTED,
                SubmissionStatus.LATE,
            }:
                pending_eval += 1
            if sub.status == SubmissionStatus.LATE:
                overdue_count += 1

    ctx = await load_course_context(tenant_id)
    rows: list[LmsAssignmentManagementRow] = []
    for assign in table_assignments:
        aid = str(assign.id)
        subs = subs_by_assignment.get(aid, [])
        evaluated = sum(1 for s in subs if s.id in evaluations)
        roster = roster_by_course.get((assign.course_code.upper(), ""), 0) or len(
            ctx["students_by_code"].get(assign.course_code.upper(), set())
        )
        submitted = len(subs)
        if assign.status == LmsAssignmentStatus.PUBLISHED and assign.deadline_at >= now:
            status_label, status_tone = "Open", "info"
        elif assign.status == LmsAssignmentStatus.PUBLISHED:
            status_label, status_tone = "Closed", "success"
        else:
            status_label, status_tone = "Draft", "muted"
        rows.append(
            LmsAssignmentManagementRow(
                row_key=aid,
                assignment_label=assign.title,
                course_code=assign.course_code.upper(),
                due_label=_due_label(assign.deadline_at),
                submitted_label=f"{submitted:,} of {roster:,}" if roster else f"{submitted:,} of —",
                evaluated_count=evaluated,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/assignment-management?assignment_id={aid}",
            )
        )

    paged, total, total_pages, footer, short_footer = _paginate(rows, page, page_size)

    return LmsAssignmentManagementPageRead(
        page_title="Assignment Management",
        page_subtitle="Assignments across courses",
        export_label="Export",
        primary_action_href="/college-admin/lms/assignment-management?export=1",
        assignments_section_title="Assignments",
        table_headers=["Assignment", "Course", "Due", "Submitted", "Evaluated", "Status"],
        kpis=[
            UserDashboardKpi(
                key="active",
                label="Active",
                value=f"{published_open:,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="submissions",
                label="Submissions",
                value=f"{len(submissions):,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="pending_evaluation",
                label="Pending evaluation",
                value=f"{pending_eval:,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="overdue",
                label="Overdue submissions",
                value=f"{overdue_count:,}",
                hint_line="",
                hint_tone="muted",
            ),
        ],
        assignment_rows=paged,
        empty_table_message="No assignments to show yet.",
        showing_label=footer,
        count_footer_label=short_footer,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )


async def _quiz_metrics(tenant_id, quiz_rows: list[UpcomingAssessment]) -> dict[str, tuple[str, str]]:
    """Return attempts_label and average_label per upcoming assessment row_key."""
    if not quiz_rows:
        return {}
    component_ids = []
    key_by_component: dict[str, str] = {}
    for row in quiz_rows:
        meta = row.metadata or {}
        component_id = meta.get("component_id") or meta.get("quiz_id")
        row_key = str(row.id)
        if component_id:
            component_ids.append(str(component_id))
            key_by_component[str(component_id)] = row_key

    marks: list[StudentAssessmentMark] = []
    if component_ids:
        marks = await StudentAssessmentMark.find(
            Eq(StudentAssessmentMark.tenant_id, tenant_id),
            In(StudentAssessmentMark.component_id, component_ids),
            In(StudentAssessmentMark.status, list(_PUBLISHED_MARK_STATUSES)),
        ).to_list()

    by_key: dict[str, list[StudentAssessmentMark]] = defaultdict(list)
    for mark in marks:
        key = key_by_component.get(mark.component_id)
        if key:
            by_key[key].append(mark)

    out: dict[str, tuple[str, str]] = {}
    for row in quiz_rows:
        row_key = str(row.id)
        meta = row.metadata or {}
        if meta.get("attempt_count") is not None:
            attempts = f"{int(meta['attempt_count']):,}"
        else:
            attempts = f"{len(by_key.get(row_key, [])):,}" if by_key.get(row_key) else "—"
        if meta.get("average_percent") is not None:
            avg = f"{int(round(float(meta['average_percent'])))}%"
        else:
            group = by_key.get(row_key, [])
            if group and all(m.max_marks for m in group):
                pct = sum((m.marks_obtained or 0) / m.max_marks * 100 for m in group) / len(group)
                avg = f"{int(round(pct))}%"
            else:
                avg = "—"
        out[row_key] = (attempts, avg)
    return out


async def get_lms_quiz_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LmsQuizManagementPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    upcoming = await UpcomingAssessment.find(Eq(UpcomingAssessment.tenant_id, tenant_id)).sort("-scheduled_at").to_list()
    quizzes = [u for u in upcoming if _is_quiz_assessment(u.assessment_type)]

    metrics = await _quiz_metrics(tenant_id, quizzes)

    rows: list[LmsQuizManagementRow] = []
    for quiz in quizzes:
        row_key = str(quiz.id)
        meta = quiz.metadata or {}
        questions = meta.get("question_count")
        attempts, avg = metrics.get(row_key, ("—", "—"))
        if questions is not None:
            questions_label = f"{int(questions):,}"
        else:
            questions_label = str(meta.get("questions") or "—")
        if quiz.scheduled_at > now:
            status_label, status_tone = "Scheduled", "info"
        else:
            status_label, status_tone = "Closed", "success"
        rows.append(
            LmsQuizManagementRow(
                row_key=row_key,
                quiz_label=quiz.title,
                course_code=quiz.course_code.upper(),
                questions_label=questions_label,
                attempts_label=attempts,
                average_label=avg,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/quiz-management?quiz_id={row_key}",
            )
        )

    paged, total, total_pages, _, short_footer = _paginate(rows, page, page_size)

    return LmsQuizManagementPageRead(
        page_title="Quiz Management",
        page_subtitle="Quizzes and question banks",
        primary_action_label="Create quiz",
        primary_action_href="/college-admin/lms/quiz-management?mode=create",
        quizzes_section_title="Quizzes",
        table_headers=["Quiz", "Course", "Questions", "Attempts", "Average", "Status"],
        quiz_rows=paged,
        empty_table_message="No quizzes to show yet.",
        count_footer_label=short_footer,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )


def _assessment_type_label(assessment_type: str, meta: dict) -> str:
    if label := meta.get("assessment_kind") or meta.get("type_label"):
        return str(label).title()
    key = (assessment_type or "").strip().lower()
    if "project" in key:
        return "Project"
    if "practical" in key:
        return "Practical"
    if "written" in key or "internal" in key:
        return "Written"
    return (assessment_type or "Assessment").replace("_", " ").title()


async def get_lms_assessment_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LmsAssessmentManagementPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    upcoming = await UpcomingAssessment.find(Eq(UpcomingAssessment.tenant_id, tenant_id)).sort("scheduled_at").to_list()
    internal_rows = [u for u in upcoming if not _is_quiz_assessment(u.assessment_type)]

    # fallback from examination components without matching upcoming rows
    component_weights: dict[str, float] = {}
    for comp in await AssessmentComponent.find(Eq(AssessmentComponent.tenant_id, tenant_id)).to_list():
        if comp.code and comp.weight_percent:
            component_weights[comp.code.lower()] = comp.weight_percent

    rows: list[LmsAssessmentManagementRow] = []
    for item in internal_rows:
        meta = item.metadata or {}
        weight = meta.get("weight_percent")
        if weight is None and meta.get("component_code"):
            weight = component_weights.get(str(meta["component_code"]).lower())
        weight_label = f"{int(round(float(weight)))}%" if weight is not None else "—"
        if item.scheduled_at > now:
            status_label, status_tone = "Scheduled", "info"
        else:
            status_label, status_tone = "Closed", "success"
        rows.append(
            LmsAssessmentManagementRow(
                row_key=str(item.id),
                assessment_label=item.title,
                course_code=item.course_code.upper(),
                type_label=_assessment_type_label(item.assessment_type, meta),
                weight_label=weight_label,
                opens_label=item.scheduled_at.strftime("%d %b"),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/assessment-management?assessment_id={item.id}",
            )
        )

    if not rows:
        for comp in await AssessmentComponent.find(Eq(AssessmentComponent.tenant_id, tenant_id)).sort("-created_at").to_list():
            if comp.component_type.value not in {"internal", "practical", "assignment"}:
                continue
            rows.append(
                LmsAssessmentManagementRow(
                    row_key=f"{comp.assessment_id}:{comp.component_id}",
                    assessment_label=comp.name,
                    course_code=comp.code.upper() if comp.code else "—",
                    type_label=comp.component_type.value.replace("_", " ").title(),
                    weight_label=f"{int(comp.weight_percent)}%" if comp.weight_percent else "—",
                    opens_label="—",
                    status_label="Scheduled" if not comp.is_official_final else "Closed",
                    status_tone="info" if not comp.is_official_final else "success",
                    detail_href=f"/college-admin/lms/assessment-management?component_id={comp.component_id}",
                )
            )

    paged, total, total_pages, _, short_footer = _paginate(rows, page, page_size)

    return LmsAssessmentManagementPageRead(
        page_title="Assessment Management",
        page_subtitle="Internal assessments and rubrics",
        primary_action_label="Create assessment",
        primary_action_href="/college-admin/lms/assessment-management?mode=create",
        assessments_section_title="Assessments",
        table_headers=["Assessment", "Course", "Type", "Weight", "Opens", "Status"],
        assessment_rows=paged,
        empty_table_message="No assessments to show yet.",
        count_footer_label=short_footer,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )