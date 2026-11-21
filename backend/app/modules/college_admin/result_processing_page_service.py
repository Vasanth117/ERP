"""Result processing page (CA 09.09)."""

from __future__ import annotations

from collections import defaultdict
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.examination_results_nav import examination_results_sub_nav
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ResultProcessingActionPayload,
    ResultProcessingPageRead,
    ResultProcessingPassBarRow,
    UserDashboardKpi,
)
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultOutcome, ExamSubjectResultStatus
from app.modules.examinations.exam_cell_grading_models import ExamSemesterResult
from app.modules.examinations.exam_cell_grading_schemas import ExamProvisionalCalculateRequest
from app.modules.examinations.exam_cell_grading_service import calculate_provisional_results
from app.modules.examinations.exam_cell_models import ExamSession

_IST = ZoneInfo("Asia/Kolkata")


def _session_period_subtitle(session: ExamSession) -> str:
    if session.examination_start_at:
        local = as_utc_aware(session.examination_start_at).astimezone(_IST)
        return f"Process results for {local.strftime('%b %Y')}"
    return f"Process results for {session.name or session.session_code}"


def _programme_display(code: str | None, programmes: dict[str, AcademicProgramme]) -> str:
    if not code:
        return "Unassigned"
    row = programmes.get(code.upper()) or programmes.get(code)
    if row and row.name:
        return row.name
    return code


def _kpi_stats(rows: list[ExamSemesterResult]) -> tuple[int, int, int, int]:
    total = len(rows)
    processed = sum(1 for r in rows if r.overall_outcome is not None and r.overall_outcome != ExamSubjectResultOutcome.INCOMPLETE)
    passed = sum(1 for r in rows if r.overall_outcome == ExamSubjectResultOutcome.PASS)
    arrears = sum(1 for r in rows if r.overall_outcome == ExamSubjectResultOutcome.FAIL)
    return total, processed, passed, arrears


async def get_result_processing_page(
    scope: AccessScope,
    *,
    session_id: str | None = None,
) -> ResultProcessingPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty = ResultProcessingPageRead(
        page_title="Result Processing",
        page_subtitle="Process results for the active session",
        process_label="Process",
        sub_nav=examination_results_sub_nav("result-processing"),
        pass_chart_section_title="Pass percentage by programme",
        kpis=[
            UserDashboardKpi(key="students", label="Students", value="0", hint_line="—", hint_tone="info"),
            UserDashboardKpi(key="processed", label="Processed", value="0", hint_line="—", hint_tone="success"),
            UserDashboardKpi(key="pass", label="Pass", value="0", hint_line="—", hint_tone="success"),
            UserDashboardKpi(key="arrears", label="Arrears", value="0", hint_line="—", hint_tone="error"),
        ],
        pass_by_programme=[],
        selected_session_id="",
        footer_disclaimer="Live institutional data · Result processing · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )
    if session is None:
        return empty

    semester_rows = await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, session.id),
    ).to_list()
    programmes = {
        p.programme_code.upper(): p
        for p in await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    }

    total, processed, passed, arrears = _kpi_stats(semester_rows)
    processed_pct = round(100.0 * processed / total, 1) if total else None
    pass_pct = round(100.0 * passed / total, 1) if total else None

    by_programme: dict[str, list[ExamSemesterResult]] = defaultdict(list)
    for row in semester_rows:
        key = (row.programme_code or "UNASSIGNED").upper()
        by_programme[key].append(row)

    pass_rows: list[ResultProcessingPassBarRow] = []
    for code in sorted(by_programme.keys()):
        group = by_programme[code]
        g_total = len(group)
        g_pass = sum(1 for r in group if r.overall_outcome == ExamSubjectResultOutcome.PASS)
        pct = round(100.0 * g_pass / g_total, 1) if g_total else 0.0
        pass_rows.append(
            ResultProcessingPassBarRow(
                programme_code=code,
                programme_label=_programme_display(code if code != "UNASSIGNED" else None, programmes),
                pass_percent=pct,
                pass_percent_label=f"{pct:.0f}%",
                bar_tone="success" if pct >= 90 else "info",
            )
        )

    return ResultProcessingPageRead(
        page_title="Result Processing",
        page_subtitle=_session_period_subtitle(session),
        process_label="Process",
        sub_nav=examination_results_sub_nav("result-processing"),
        pass_chart_section_title="Pass percentage by programme",
        kpis=[
            UserDashboardKpi(key="students", label="Students", value=f"{total:,}", hint_line="Registered", hint_tone="info"),
            UserDashboardKpi(
                key="processed",
                label="Processed",
                value=f"{processed:,}",
                hint_line=f"{processed_pct:.1f}%" if processed_pct is not None else "—",
                hint_tone="success",
            ),
            UserDashboardKpi(
                key="pass",
                label="Pass",
                value=f"{passed:,}",
                hint_line=f"{pass_pct:.1f}%" if pass_pct is not None else "—",
                hint_tone="success",
            ),
            UserDashboardKpi(key="arrears", label="Arrears", value=f"{arrears:,}", hint_line="Students", hint_tone="error" if arrears else "success"),
        ],
        pass_by_programme=pass_rows,
        selected_session_id=session.session_id,
        footer_disclaimer="Live institutional data · Result processing · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def process_results_page(
    scope: AccessScope,
    payload: ResultProcessingActionPayload,
) -> ResultProcessingPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    actor = await User.get(scope.user_id)
    if actor is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)

    await calculate_provisional_results(
        scope,
        actor,
        ExamProvisionalCalculateRequest(exam_session_id=str(session.id)),
    )

    await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, session.id),
        Eq(ExamSemesterResult.status, ExamSubjectResultStatus.PROVISIONAL.value),
    ).update({"$set": {"status": ExamSubjectResultStatus.UNDER_REVIEW.value}})

    return await get_result_processing_page(scope, session_id=payload.session_id)