"""Result publication page (CA 09.09)."""

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
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    ResultPublicationActionPayload,
    ResultPublicationPageRead,
    ResultPublicationProgrammeRow,
)
from app.modules.examinations.exam_cell_grading_enums import ExamResultReviewStatus, ExamSubjectResultStatus
from app.modules.examinations.exam_cell_grading_models import ExamSemesterResult
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_publication_enums import ExamPublicationScopeType, ExamPublicationStatus
from app.modules.examinations.exam_cell_publication_models import ExamResultPublication
from app.modules.examinations.exam_cell_publication_schemas import ExamPublicationCreate
from app.modules.examinations.exam_cell_publication_service import create_publication, publish_results
from app.modules.examinations.exam_cell_result_models import ExamResultApprovalWorkflow

_PAGE_SIZE = 8
_IST = ZoneInfo("Asia/Kolkata")


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _short_date(dt) -> str:
    if dt is None:
        return "—"
    local = as_utc_aware(dt).astimezone(_IST)
    return f"{local.day} {local.strftime('%b')}"


def _programme_display(code: str, programmes: dict[str, AcademicProgramme]) -> str:
    row = programmes.get(code.upper()) or programmes.get(code)
    if row and row.name:
        return row.name
    return code


async def _publication_rows(
    tenant_id: PydanticObjectId,
    session: ExamSession,
    workflow: ExamResultApprovalWorkflow | None,
    programmes: dict[str, AcademicProgramme],
) -> list[ResultPublicationProgrammeRow]:
    semester_rows = await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, session.id),
        Eq(ExamSemesterResult.status, ExamSubjectResultStatus.APPROVED.value),
    ).to_list()
    grouped: dict[str, int] = defaultdict(int)
    for row in semester_rows:
        grouped[(row.programme_code or "UNASSIGNED").upper()] += 1

    publications = await ExamResultPublication.find(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.exam_session_id, session.id),
    ).to_list()
    pub_by_code = {p.programme_code.upper(): p for p in publications if p.programme_code}

    approved_label = _short_date(workflow.approved_at) if workflow and workflow.approved_at else "Pending"
    workflow_ready = workflow is not None and workflow.status == ExamResultReviewStatus.APPROVED

    rows: list[ResultPublicationProgrammeRow] = []
    for code in sorted(grouped.keys()):
        pub = pub_by_code.get(code)
        students = grouped[code]
        if pub and pub.status == ExamPublicationStatus.PUBLISHED:
            publish_label = _short_date(pub.published_at)
            notify_label, notify_tone = "Yes", "success"
            ready = True
        elif workflow_ready:
            publish_label = "Immediately" if pub is None or not pub.publish_at else _short_date(pub.publish_at)
            notify_label, notify_tone = ("Yes", "success") if (pub is None or pub.visibility_default) else ("No", "muted")
            ready = True
        else:
            publish_label = "Pending"
            notify_label, notify_tone = "No", "muted"
            ready = False
        rows.append(
            ResultPublicationProgrammeRow(
                programme_code=code,
                programme_label=_programme_display(code if code != "UNASSIGNED" else "ALL", programmes),
                students_count=students,
                approved_label=approved_label,
                publish_at_label=publish_label,
                notify_label=notify_label,
                notify_tone=notify_tone,
                ready_to_publish=ready and (pub is None or pub.status != ExamPublicationStatus.PUBLISHED),
                publication_id=pub.publication_id if pub else "",
            )
        )
    return rows


async def get_result_publication_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> ResultPublicationPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )
    if session is None:
        return ResultPublicationPageRead(
            page_title="Result Publication",
            page_subtitle="Publish approved results",
            schedule_label="Schedule",
            publish_now_label="Publish now",
            warning_title="Publishing is final",
            warning_message="Students and parents are notified. Changes after publication need a revaluation or correction request.",
            sub_nav=examination_results_sub_nav("result-publication"),
            ready_section_title="Ready to publish",
            table_headers=["Programme", "Students", "Approved", "Publish at", "Notify"],
            programme_rows=[],
            ready_count_label="0 of 0 ready",
            showing_label="0 of 0 programmes",
            pagination=empty_pagination,
            selected_session_id="",
            selected_workflow_id="",
            footer_disclaimer="Live institutional data · Result publication · All times IST",
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
    all_rows = await _publication_rows(tenant_id, session, workflow, programmes)
    ready_count = sum(1 for r in all_rows if r.ready_to_publish)
    total = len(all_rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages) if total_pages else 1
    start = (page - 1) * _PAGE_SIZE
    page_rows = all_rows[start : start + _PAGE_SIZE]

    return ResultPublicationPageRead(
        page_title="Result Publication",
        page_subtitle="Publish approved results",
        schedule_label="Schedule",
        publish_now_label="Publish now",
        warning_title="Publishing is final",
        warning_message="Students and parents are notified. Changes after publication need a revaluation or correction request.",
        sub_nav=examination_results_sub_nav("result-publication"),
        ready_section_title="Ready to publish",
        table_headers=["Programme", "Students", "Approved", "Publish at", "Notify"],
        programme_rows=page_rows,
        ready_count_label=f"{ready_count} of {total:,} ready" if total else "0 of 0 ready",
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
        footer_disclaimer="Live institutional data · Result publication · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def publish_results_now_page(
    scope: AccessScope,
    payload: ResultPublicationActionPayload,
) -> ResultPublicationPageRead:
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
    if workflow is None or workflow.status != ExamResultReviewStatus.APPROVED:
        raise AppError(code="VALIDATION_ERROR", message="Results must be approved before publication", status_code=422)

    page_data = await get_result_publication_page(scope, page=payload.page, session_id=payload.session_id)
    for row in page_data.programme_rows:
        if not row.ready_to_publish:
            continue
        pub_id = row.publication_id
        if not pub_id:
            created = await create_publication(
                scope,
                actor,
                ExamPublicationCreate(
                    exam_session_id=str(session.id),
                    workflow_id=workflow.workflow_id,
                    scope_type=ExamPublicationScopeType.PROGRAMME,
                    programme_code=row.programme_code if row.programme_code != "UNASSIGNED" else None,
                ),
            )
            pub_id = created.publication_id
        await publish_results(scope, actor, pub_id)

    return await get_result_publication_page(scope, page=payload.page, session_id=payload.session_id)


async def schedule_result_publication_page(
    scope: AccessScope,
    payload: ResultPublicationActionPayload,
) -> ResultPublicationPageRead:
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

    workflow = await ExamResultApprovalWorkflow.find_one(
        Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
        Eq(ExamResultApprovalWorkflow.exam_session_id, session.id),
    )
    if workflow is None or workflow.status != ExamResultReviewStatus.APPROVED:
        raise AppError(code="VALIDATION_ERROR", message="Results must be approved before scheduling", status_code=422)

    publish_at = payload.publish_at or session.result_processing_deadline_at or (utcnow())
    page_data = await get_result_publication_page(scope, page=payload.page, session_id=payload.session_id)
    for row in page_data.programme_rows:
        if row.publication_id:
            pub = await ExamResultPublication.find_one(
                Eq(ExamResultPublication.tenant_id, tenant_id),
                Eq(ExamResultPublication.publication_id, row.publication_id),
            )
            if pub and pub.status != ExamPublicationStatus.PUBLISHED:
                pub.publish_at = publish_at
                pub.status = ExamPublicationStatus.SCHEDULED
                pub.updated_at = utcnow()
                await pub.save()
            continue
        await create_publication(
            scope,
            actor,
            ExamPublicationCreate(
                exam_session_id=str(session.id),
                workflow_id=workflow.workflow_id,
                scope_type=ExamPublicationScopeType.PROGRAMME,
                programme_code=row.programme_code if row.programme_code != "UNASSIGNED" else None,
                publish_at=publish_at,
            ),
        )

    return await get_result_publication_page(scope, page=payload.page, session_id=payload.session_id)