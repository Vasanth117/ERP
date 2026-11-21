"""Examination session management list (CA 09.02)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.examination_dashboard_page_service import (
    _PAGE_SIZE,
    _page_numbers,
    _period_label,
    _programmes_label,
    _TYPE_LABELS,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ExaminationDashboardSessionRow,
    ExaminationSessionManagementPageRead,
    PoliciesPagination,
)
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamRegistration

_SESSION_LIST_STATUS: dict[ExamSessionStatus, tuple[str, str]] = {
    ExamSessionStatus.DRAFT: ("Draft", "muted"),
    ExamSessionStatus.SCHEDULED: ("Scheduled", "info"),
    ExamSessionStatus.REGISTRATION_OPEN: ("Scheduled", "info"),
    ExamSessionStatus.REGISTRATION_CLOSED: ("Scheduled", "info"),
    ExamSessionStatus.ONGOING: ("Ongoing", "warning"),
    ExamSessionStatus.COMPLETED: ("Completed", "success"),
    ExamSessionStatus.RESULTS_PROCESSING: ("Processing", "warning"),
    ExamSessionStatus.PUBLISHED: ("Published", "success"),
    ExamSessionStatus.ARCHIVED: ("Archived", "muted"),
    ExamSessionStatus.CANCELLED: ("Cancelled", "error"),
}

_REG_STATUSES = [ExamRegistrationStatus.SUBMITTED.value, ExamRegistrationStatus.CONFIRMED.value]


async def get_examination_session_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> ExaminationSessionManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
    total = len(sessions)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_sessions = sessions[start : start + _PAGE_SIZE]

    session_rows: list[ExaminationDashboardSessionRow] = []
    for session in page_sessions:
        students = await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.exam_session_id, session.id),
            In(ExamRegistration.status, _REG_STATUSES),
        ).count()
        status_label, status_tone = _SESSION_LIST_STATUS.get(session.status, ("—", "muted"))
        config_href = (
            f"/college-admin/examinations/examination-configuration?session_id={session.session_id}"
        )
        session_rows.append(
            ExaminationDashboardSessionRow(
                session_id=session.session_id,
                session_label=session.name or session.session_code,
                type_label=_TYPE_LABELS.get(session.examination_type, session.examination_type.value.title()),
                period_label=_period_label(session),
                programmes_label=await _programmes_label(tenant_id, session.id),
                students_count=students,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=config_href,
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return ExaminationSessionManagementPageRead(
        page_title="Examination Session Management",
        page_subtitle="Create and manage examination sessions",
        create_session_label="Create session",
        create_session_href="/college-admin/examinations/examination-configuration?mode=new",
        sessions_section_title="Examination sessions",
        sessions_count_label=f"{total:,} sessions" if total else "0 sessions",
        table_headers=["Session", "Type", "Period", "Programmes", "Students", "Status"],
        session_rows=session_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · Examination sessions · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )