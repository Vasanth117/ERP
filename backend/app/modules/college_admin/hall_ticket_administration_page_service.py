"""Hall ticket administration page (CA 09.04)."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.all_students_list_page_service import _register_number
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.examination_registration_nav import examination_registration_sub_nav
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HallTicketAdministrationActionPayload,
    HallTicketAdministrationPageRead,
    HallTicketAdministrationRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.examinations.exam_cell_hall_ticket_models import ExamHallTicket, ExamHallTicketHistory, ExamHallTicketSubject
from app.modules.examinations.exam_cell_hall_ticket_schemas import ExamHallTicketBulkGenerateRequest
from app.modules.examinations.exam_cell_hall_ticket_service import bulk_generate_hall_tickets, publish_hall_ticket
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import (
    ExamHallTicketHistoryAction,
    ExamHallTicketStatus,
    ExamRegistrationStatus,
)
from app.modules.examinations.exam_cell_registration_models import ExamEligibilityRecord, ExamRegistration
from app.modules.students.models import StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 8


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


def _ticket_status(ticket: ExamHallTicket | None, *, eligible: bool) -> tuple[str, str]:
    if ticket is None:
        return ("Withheld", "error") if not eligible else ("—", "muted")
    if ticket.status == ExamHallTicketStatus.PUBLISHED:
        return "Released", "success"
    if ticket.status == ExamHallTicketStatus.GENERATED:
        return "Generated", "info"
    if ticket.status == ExamHallTicketStatus.REVOKED:
        return "Withheld", "error"
    return "Withheld", "error"


async def get_hall_ticket_administration_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> HallTicketAdministrationPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-registration_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )
    if session is None:
        return HallTicketAdministrationPageRead(
            page_title="Hall Ticket Administration",
            page_subtitle="Generate and release hall tickets",
            generate_all_label="Generate all",
            release_label="Release",
            sub_nav=examination_registration_sub_nav("hall-ticket-administration"),
            scope_indicator_label="College scope",
            updated_at_label=_fmt_time_label(now),
            kpis=[
                UserDashboardKpi(key="generated", label="Generated", value="0", hint_line="—", hint_tone="info"),
                UserDashboardKpi(key="pending", label="Pending", value="0", hint_line="Awaiting fee clearance", hint_tone="warning"),
                UserDashboardKpi(key="withheld", label="Withheld", value="0", hint_line="Not eligible", hint_tone="error"),
                UserDashboardKpi(key="downloaded", label="Downloaded", value="0", hint_line="By students", hint_tone="info"),
            ],
            hall_tickets_section_title="Hall tickets",
            hall_tickets_count_label="0 tickets",
            table_headers=["Student", "Register no.", "Papers", "Generated", "Released", "Status"],
            ticket_rows=[],
            showing_label="Showing 0 of 0",
            pagination=empty_pagination,
            selected_session_id="",
            footer_disclaimer="Live institutional data · Hall tickets · All times IST",
            footer_snapshot_label="Sample snapshot",
            generated_at=now,
        )

    tickets = await ExamHallTicket.find(
        Eq(ExamHallTicket.tenant_id, tenant_id),
        Eq(ExamHallTicket.exam_session_id, session.id),
    ).to_list()
    generated = len([t for t in tickets if t.status != ExamHallTicketStatus.DRAFT])
    pending = len([t for t in tickets if t.status == ExamHallTicketStatus.GENERATED])
    withheld = len([t for t in tickets if t.status == ExamHallTicketStatus.REVOKED])

    elig = await ExamEligibilityRecord.find(
        Eq(ExamEligibilityRecord.tenant_id, tenant_id),
        Eq(ExamEligibilityRecord.exam_session_id, session.id),
        Eq(ExamEligibilityRecord.overall_eligible, False),
    ).count()
    regs_total = await ExamRegistration.find(
        Eq(ExamRegistration.tenant_id, tenant_id),
        Eq(ExamRegistration.exam_session_id, session.id),
        In(ExamRegistration.status, [ExamRegistrationStatus.CONFIRMED.value]),
    ).count()
    withheld += max(0, elig - withheld)

    histories = await ExamHallTicketHistory.find(
        Eq(ExamHallTicketHistory.tenant_id, tenant_id),
        Eq(ExamHallTicketHistory.action, ExamHallTicketHistoryAction.DOWNLOADED),
    ).to_list()
    ticket_ids = {t.hall_ticket_id for t in tickets}
    downloaded = sum(1 for h in histories if h.hall_ticket_id in ticket_ids)

    total = len(tickets)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_tickets = sorted(tickets, key=lambda t: t.created_at or now, reverse=True)[start : start + _PAGE_SIZE]

    user_ids = [t.student_user_id for t in page_tickets]
    records = (
        await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id), In(StudentRecord.user_id, user_ids)).to_list()
        if user_ids
        else []
    )
    record_map = {r.user_id: r for r in records}
    profiles = (
        await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id), In(StudentProfile.user_id, user_ids)).to_list()
        if user_ids
        else []
    )
    profile_map = {p.user_id: p for p in profiles}
    eligibility = await ExamEligibilityRecord.find(
        Eq(ExamEligibilityRecord.tenant_id, tenant_id),
        Eq(ExamEligibilityRecord.exam_session_id, session.id),
        In(ExamEligibilityRecord.student_user_id, user_ids),
    ).to_list()
    elig_map = {e.student_user_id: e.overall_eligible for e in eligibility}

    rows: list[HallTicketAdministrationRow] = []
    for ticket in page_tickets:
        rec = record_map.get(ticket.student_user_id)
        profile = profile_map.get(ticket.student_user_id)
        register_no = ticket.roll_number or (_register_number(rec, profile) if rec else "—")
        name = ticket.student_name or "—"
        papers = await ExamHallTicketSubject.find(
            Eq(ExamHallTicketSubject.tenant_id, tenant_id),
            Eq(ExamHallTicketSubject.hall_ticket_id, ticket.hall_ticket_id),
        ).count()
        status_label, status_tone = _ticket_status(ticket, eligible=elig_map.get(ticket.student_user_id, True))
        rows.append(
            HallTicketAdministrationRow(
                hall_ticket_id=ticket.hall_ticket_id,
                student_name=name,
                register_number=register_no,
                papers_count=papers,
                generated_at_label=_short_date(ticket.created_at),
                released_at_label=_short_date(ticket.published_at) if ticket.published_at else "Pending",
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return HallTicketAdministrationPageRead(
        page_title="Hall Ticket Administration",
        page_subtitle="Generate and release hall tickets",
        generate_all_label="Generate all",
        release_label="Release",
        sub_nav=examination_registration_sub_nav("hall-ticket-administration"),
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        kpis=[
            UserDashboardKpi(key="generated", label="Generated", value=f"{generated:,}", hint_line="—", hint_tone="info"),
            UserDashboardKpi(
                key="pending",
                label="Pending",
                value=f"{pending:,}",
                hint_line="Awaiting fee clearance" if pending else "—",
                hint_tone="warning",
            ),
            UserDashboardKpi(
                key="withheld",
                label="Withheld",
                value=f"{withheld:,}",
                hint_line="Not eligible" if withheld else "—",
                hint_tone="error",
            ),
            UserDashboardKpi(
                key="downloaded",
                label="Downloaded",
                value=f"{downloaded:,}",
                hint_line="By students" if downloaded else "—",
                hint_tone="info",
            ),
        ],
        hall_tickets_section_title="Hall tickets",
        hall_tickets_count_label=f"{total:,} tickets" if total else "0 tickets",
        table_headers=["Student", "Register no.", "Papers", "Generated", "Released", "Status"],
        ticket_rows=rows,
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
        selected_session_id=session.session_id,
        footer_disclaimer="Live institutional data · Hall tickets · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def generate_all_hall_tickets_page(
    scope: AccessScope,
    payload: HallTicketAdministrationActionPayload,
) -> HallTicketAdministrationPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    user = await User.get(scope.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    registrations = await ExamRegistration.find(
        Eq(ExamRegistration.tenant_id, tenant_id),
        Eq(ExamRegistration.exam_session_id, session.id),
        Eq(ExamRegistration.status, ExamRegistrationStatus.CONFIRMED.value),
        Eq(ExamRegistration.fee_verified, True),
    ).to_list()
    student_ids = [str(r.student_user_id) for r in registrations]
    if student_ids:
        await bulk_generate_hall_tickets(
            scope,
            user,
            ExamHallTicketBulkGenerateRequest(exam_session_id=str(session.id), student_user_ids=student_ids, publish=False),
        )
    return await get_hall_ticket_administration_page(scope, page=payload.page, session_id=payload.session_id)


async def release_hall_tickets_page(
    scope: AccessScope,
    payload: HallTicketAdministrationActionPayload,
) -> HallTicketAdministrationPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_PUBLISH)
    user = await User.get(scope.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    tickets = await ExamHallTicket.find(
        Eq(ExamHallTicket.tenant_id, tenant_id),
        Eq(ExamHallTicket.exam_session_id, session.id),
        Eq(ExamHallTicket.status, ExamHallTicketStatus.GENERATED),
    ).to_list()
    for ticket in tickets:
        await publish_hall_ticket(scope, user, ticket.hall_ticket_id)
    return await get_hall_ticket_administration_page(scope, page=payload.page, session_id=payload.session_id)