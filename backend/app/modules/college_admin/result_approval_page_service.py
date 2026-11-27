"""Result approval page (CA 09.09)."""

from __future__ import annotations

import math
from collections import defaultdict
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
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
from app.modules.college_admin.examination_workflow import empty_state_for_step, workflow_chrome
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    ResultApprovalActionPayload,
    ResultApprovalPageRead,
    ResultApprovalProgrammeRow,
    ResultApprovalRouteStep,
)
from app.modules.examinations.exam_cell_grading_enums import ExamResultReviewStatus, ExamSubjectResultOutcome
from app.modules.examinations.exam_cell_grading_models import ExamSemesterResult
from app.modules.examinations.exam_cell_models import ExamSession, ExamSessionAcademicScope
from app.modules.examinations.exam_cell_result_models import ExamResultApprovalWorkflow
from app.modules.examinations.exam_cell_result_schemas import ExamResultReviewDecision, ExamResultReviewStart
from app.modules.examinations.exam_cell_result_service import approve_results, exam_cell_verify, start_result_review

_PAGE_SIZE = 8
_IST = ZoneInfo("Asia/Kolkata")


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _programme_display(code: str, programmes: dict[str, AcademicProgramme]) -> str:
    row = programmes.get(code.upper()) or programmes.get(code)
    if row and row.name:
        return row.name
    return code


def _route_steps(status: ExamResultReviewStatus | None) -> list[ResultApprovalRouteStep]:
    if status is None:
        status = ExamResultReviewStatus.PENDING

    def tone(done: bool, pending: bool) -> tuple[str, str]:
        if done:
            return "Done", "success"
        if pending:
            return "Pending", "warning"
        return "—", "muted"

    exam_done = status in {
        ExamResultReviewStatus.DEPARTMENT_VERIFIED,
        ExamResultReviewStatus.EXAM_CELL_VERIFIED,
        ExamResultReviewStatus.APPROVED,
        ExamResultReviewStatus.IN_REVIEW,
    }
    controller_done = status in {ExamResultReviewStatus.EXAM_CELL_VERIFIED, ExamResultReviewStatus.APPROVED}
    admin_done = status == ExamResultReviewStatus.APPROVED
    admin_pending = status == ExamResultReviewStatus.EXAM_CELL_VERIFIED

    exam_label, exam_tone = tone(exam_done, status == ExamResultReviewStatus.IN_REVIEW)
    ctrl_label, ctrl_tone = tone(controller_done, status == ExamResultReviewStatus.DEPARTMENT_VERIFIED)
    admin_label, admin_tone = tone(admin_done, admin_pending)

    return [
        ResultApprovalRouteStep(key="exam_cell", title="Exam Cell", status_label=exam_label, status_tone=exam_tone),
        ResultApprovalRouteStep(
            key="controller",
            title="Controller of Examinations",
            status_label=ctrl_label,
            status_tone=ctrl_tone,
        ),
        ResultApprovalRouteStep(key="college_admin", title="College Admin", status_label=admin_label, status_tone=admin_tone),
    ]


async def _programme_summary(
    tenant_id: PydanticObjectId,
    session: ExamSession,
    programmes: dict[str, AcademicProgramme],
) -> list[ResultApprovalProgrammeRow]:
    rows = await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, session.id),
    ).to_list()
    if not rows:
        scope = await ExamSessionAcademicScope.find_one(
            Eq(ExamSessionAcademicScope.tenant_id, tenant_id),
            Eq(ExamSessionAcademicScope.exam_session_id, session.id),
        )
        codes = scope.programme_codes if scope and scope.programme_codes else []
        return [
            ResultApprovalProgrammeRow(
                programme_code=code,
                programme_label=_programme_display(code, programmes),
                students_count=0,
                pass_count=0,
                pass_percent_label="—",
            )
            for code in codes
        ]

    grouped: dict[str, list[ExamSemesterResult]] = defaultdict(list)
    for row in rows:
        grouped[(row.programme_code or "UNASSIGNED").upper()].append(row)

    result: list[ResultApprovalProgrammeRow] = []
    for code in sorted(grouped.keys()):
        group = grouped[code]
        students = len(group)
        passed = sum(1 for r in group if r.overall_outcome == ExamSubjectResultOutcome.PASS)
        pct = round(100.0 * passed / students, 1) if students else 0.0
        result.append(
            ResultApprovalProgrammeRow(
                programme_code=code,
                programme_label=_programme_display(code if code != "UNASSIGNED" else "ALL", programmes),
                students_count=students,
                pass_count=passed,
                pass_percent_label=f"{pct:.0f}%",
            )
        )
    return result


async def get_result_approval_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> ResultApprovalPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )
    if session is None:
        return ResultApprovalPageRead(
            page_title="Result Approval",
            page_subtitle="Approve processed results before publishing",
            **workflow_chrome("result_approval", session_id),  # type: ignore[arg-type]
            return_label="Return",
            approve_label="Approve",
            sub_nav=examination_results_sub_nav("result-approval"),
            summary_section_title="Approval summary",
            route_section_title="Approval route",
            table_headers=["Programme", "Students", "Pass", "Pass %"],
            programme_rows=[],
            approval_route_steps=_route_steps(None),
            showing_label="0 of 0 programmes",
            pagination=empty_pagination,
            selected_session_id="",
            selected_workflow_id="",
            footer_disclaimer="Live institutional data · Result approval · All times IST",
            footer_snapshot_label="Sample snapshot",
            generated_at=now,
        )

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.exam_session_id, session.id),
    )
    programmes = {
        p.programme_code.upper(): p
        for p in await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    }
    all_rows = await _programme_summary(tenant_id, session, programmes)
    total = len(all_rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages) if total_pages else 1
    start = (page - 1) * _PAGE_SIZE
    page_rows = all_rows[start : start + _PAGE_SIZE]

    panel_empty = empty_state_for_step("result_approval", session.session_id) if total == 0 else None
    return ResultApprovalPageRead(
        page_title="Result Approval",
        page_subtitle=f"Result approval · {session.name}",
        panel_empty_state=panel_empty,
        **workflow_chrome("result_approval", session.session_id),  # type: ignore[arg-type]
        return_label="Return",
        approve_label="Approve",
        sub_nav=examination_results_sub_nav("result-approval"),
        summary_section_title="Approval summary",
        route_section_title="Approval route",
        table_headers=["Programme", "Students", "Pass", "Pass %"],
        programme_rows=page_rows,
        approval_route_steps=_route_steps(workflow.status if workflow else None),
        showing_label=f"{len(page_rows)} of {total:,} programmes" if total else "0 of 0 programmes",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        selected_session_id=session.session_id,
        selected_workflow_id=workflow.workflow_id if workflow else "",
        footer_disclaimer="Live institutional data · Result approval · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def _ensure_workflow(scope: AccessScope, actor: User, session: ExamSession) -> ExamResultApprovalWorkflow:
    tenant_id = require_college_tenant_scope(scope)
    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.exam_session_id, session.id),
    )
    if workflow is not None:
        return workflow
    read = await start_result_review(
        scope,
        actor,
        ExamResultReviewStart(exam_session_id=str(session.id), comment="College admin review"),
    )
    doc = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.workflow_id, read.workflow_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Workflow not found after start", status_code=500)
    return doc


async def approve_result_approval_page(
    scope: AccessScope,
    payload: ResultApprovalActionPayload,
) -> ResultApprovalPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_PUBLISH)
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

    workflow = await _ensure_workflow(scope, actor, session)
    if workflow.status == ExamResultReviewStatus.IN_REVIEW:
        workflow.status = ExamResultReviewStatus.DEPARTMENT_VERIFIED
        workflow.updated_at = utcnow()
        await workflow.save()
    if workflow.status == ExamResultReviewStatus.DEPARTMENT_VERIFIED:
        verified = await exam_cell_verify(scope, actor, workflow.workflow_id)
        workflow = await ExamResultApprovalWorkflow.find_one(
            Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
            Eq(ExamResultApprovalWorkflow.workflow_id, verified.workflow_id),
        )
        if workflow is None:
            raise AppError(code="NOT_FOUND", message="Workflow not found", status_code=404)

    await approve_results(
        scope,
        actor,
        workflow.workflow_id,
        ExamResultReviewDecision(approve=True, comment="Approved by college admin"),
    )
    return await get_result_approval_page(scope, page=payload.page, session_id=payload.session_id)


async def return_result_approval_page(
    scope: AccessScope,
    payload: ResultApprovalActionPayload,
) -> ResultApprovalPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_PUBLISH)
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

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.exam_session_id, session.id),
    )
    if workflow is None:
        raise AppError(code="VALIDATION_ERROR", message="No approval workflow to return", status_code=422)

    await approve_results(
        scope,
        actor,
        workflow.workflow_id,
        ExamResultReviewDecision(approve=False, comment="Returned for corrections"),
    )
    return await get_result_approval_page(scope, page=payload.page, session_id=payload.session_id)