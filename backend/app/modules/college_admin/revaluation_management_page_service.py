"""Revaluation management page (CA 09.10)."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.department_resource_management_page_service import _format_inr
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.examination_revaluation_supplementary_nav import examination_revaluation_supplementary_sub_nav
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    RevaluationManagementPageRead,
    RevaluationManagementTableRow,
)
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_revaluation_enums import ExamRevaluationApplicationStatus
from app.modules.examinations.exam_cell_revaluation_models import ExamRevaluationApplication, ExamRevaluationEvaluation
from app.modules.academics.curriculum_models import CourseRecord

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10

_STATUS_ACTIVE = {
    ExamRevaluationApplicationStatus.UNDER_EVALUATION,
    ExamRevaluationApplicationStatus.ASSIGNED,
    ExamRevaluationApplicationStatus.PENDING_APPROVAL,
    ExamRevaluationApplicationStatus.FEE_VERIFIED,
}


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _result_and_status(
    app: ExamRevaluationApplication,
    evaluation: ExamRevaluationEvaluation | None,
) -> tuple[str, str, str]:
    result_label = "—"
    if evaluation and evaluation.original_marks is not None and evaluation.revised_marks is not None:
        delta = round(evaluation.revised_marks - evaluation.original_marks)
        if delta > 0:
            result_label = f"Marks +{delta}"
        elif delta < 0:
            result_label = f"Marks {delta}"
        else:
            result_label = "No change"
    elif app.status == ExamRevaluationApplicationStatus.APPROVED:
        result_label = "No change"
    elif app.status == ExamRevaluationApplicationStatus.REJECTED:
        result_label = "—"

    if app.status in {ExamRevaluationApplicationStatus.APPROVED, ExamRevaluationApplicationStatus.REJECTED}:
        status_label = "Completed"
        tone = "info" if result_label in {"—", "No change"} else "success"
    elif app.status in _STATUS_ACTIVE:
        status_label = "Under evaluation"
        tone = "warning"
    else:
        status_label = "Submitted"
        tone = "muted"

    return result_label, status_label, tone


async def get_revaluation_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> RevaluationManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)

    apps = await ExamRevaluationApplication.find(Eq(ExamRevaluationApplication.tenant_id, tenant_id)).sort(
        "-updated_at"
    ).to_list()
    if session is not None:
        apps = [a for a in apps if a.exam_session_id == session.id]

    if not apps and session is None:
        return RevaluationManagementPageRead(
            page_title="Revaluation Management",
            page_subtitle="Revaluation and re-totalling requests",
            export_label="Export",
            sub_nav=examination_revaluation_supplementary_sub_nav("revaluation-management"),
            requests_section_title="Requests",
            table_headers=["Request", "Student", "Subject", "Fee", "Result", "Status"],
            request_rows=[],
            showing_label="Showing 0 of 0",
            pagination=empty_pagination,
            selected_session_id="",
            footer_disclaimer="Live institutional data · Revaluation management · All times IST",
            footer_snapshot_label="Sample snapshot",
            generated_at=now,
        )

    student_ids = list({a.student_user_id for a in apps})
    users = await User.find(In(User.id, student_ids)).to_list() if student_ids else []
    user_names = {u.id: (u.full_name or "").strip() for u in users}

    evals = await ExamRevaluationEvaluation.find(Eq(ExamRevaluationEvaluation.tenant_id, tenant_id)).to_list()
    eval_by_app = {e.application_id: e for e in evals}

    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    course_titles = {(c.course_code or "").upper(): c.name for c in courses}

    total = len(apps)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages) if total_pages else 1
    start = (page - 1) * _PAGE_SIZE
    page_apps = apps[start : start + _PAGE_SIZE]

    rows: list[RevaluationManagementTableRow] = []
    for app in page_apps:
        evaluation = eval_by_app.get(app.application_id)
        result_label, status_label, tone = _result_and_status(app, evaluation)
        fee_label = _format_inr(app.fee_amount) if app.fee_amount > 0 else "—"
        code = (app.course_code or "").upper()
        rows.append(
            RevaluationManagementTableRow(
                application_id=app.application_id,
                request_label=app.application_id,
                student_label=user_names.get(app.student_user_id) or "—",
                subject_label=course_titles.get(code) or app.course_code or "—",
                fee_label=fee_label,
                result_label=result_label,
                status_label=status_label,
                status_tone=tone,
            )
        )

    return RevaluationManagementPageRead(
        page_title="Revaluation Management",
        page_subtitle="Revaluation and re-totalling requests",
        export_label="Export",
        sub_nav=examination_revaluation_supplementary_sub_nav("revaluation-management"),
        requests_section_title="Requests",
        table_headers=["Request", "Student", "Subject", "Fee", "Result", "Status"],
        request_rows=rows,
        showing_label=f"Showing {len(page_apps)} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        selected_session_id=session.session_id if session else "",
        footer_disclaimer="Live institutional data · Revaluation management · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )