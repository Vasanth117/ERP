"""Exam registration management page (CA 09.05)."""

from __future__ import annotations

import math
from collections import defaultdict
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.all_students_list_page_service import _programme_label, _register_number
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ExamRegistrationBulkConfirmPayload,
    ExamRegistrationManagementPageRead,
    ExamRegistrationManagementTableRow,
    PoliciesPagination,
    StudentAdminDashboardFilterOption,
    UserDashboardKpi,
)
from app.modules.college_admin.examination_registration_nav import examination_registration_sub_nav
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.examinations.exam_cell_registration_models import ExamEligibilityRecord
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.students.models import StudentProfile
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import (
    ExamRegistrationHistoryAction,
    ExamRegistrationStatus,
)
from app.modules.examinations.exam_cell_registration_models import (
    ExamRegistration,
    ExamRegistrationHistory,
    ExamRegistrationSubject,
)
from app.modules.examinations.exam_cell_policy import authorize_examination_cell_registration_manage

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10

_STATUS_LABELS: dict[ExamRegistrationStatus, tuple[str, str]] = {
    ExamRegistrationStatus.DRAFT: ("On hold", "warning"),
    ExamRegistrationStatus.SUBMITTED: ("On hold", "warning"),
    ExamRegistrationStatus.CONFIRMED: ("Registered", "success"),
    ExamRegistrationStatus.CORRECTION_PENDING: ("On hold", "warning"),
    ExamRegistrationStatus.CANCELLED: ("Not eligible", "error"),
    ExamRegistrationStatus.REJECTED: ("Not eligible", "error"),
}


def _fee_label(verified: bool) -> tuple[str, str]:
    return ("Paid", "success") if verified else ("Due", "error")


def _eligibility_label(record: ExamEligibilityRecord | None) -> tuple[str, str]:
    if record is None:
        return ("Review", "warning")
    if record.overall_eligible:
        return ("Eligible", "success")
    reasons = [r.lower() for r in record.summary_reasons]
    if any("attendance" in r for r in reasons):
        return ("Attendance", "error")
    if any("fee" in r for r in reasons):
        return ("Review", "warning")
    return ("Review", "warning")

_STATUS_FILTER_OPTIONS: list[tuple[str, str]] = [
    ("", "All statuses"),
    (ExamRegistrationStatus.SUBMITTED.value, "Submitted"),
    (ExamRegistrationStatus.CONFIRMED.value, "Confirmed"),
    (ExamRegistrationStatus.CORRECTION_PENDING.value, "Correction pending"),
    (ExamRegistrationStatus.CANCELLED.value, "Cancelled"),
]


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _fmt_window(when) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b %Y, %I:%M %p")


def _registration_window_status(session: ExamSession, now) -> tuple[str, str]:
    start = as_utc_aware(session.registration_start_at)
    end = as_utc_aware(session.registration_end_at)
    if now < start:
        return "Opens soon", "info"
    if start <= now <= end:
        return "Open", "success"
    return "Closed", "muted"


def _select_session(sessions: list[ExamSession], session_id: str | None, now) -> ExamSession | None:
    if session_id:
        for row in sessions:
            if row.session_id == session_id:
                return row
    for row in sessions:
        start = as_utc_aware(row.registration_start_at)
        end = as_utc_aware(row.registration_end_at)
        if start <= now <= end:
            return row
    return sessions[0] if sessions else None


def _empty_page(now, subtitle: str = "Exam registrations for active sessions") -> ExamRegistrationManagementPageRead:
    empty_pagination = PoliciesPagination(
        page=1,
        page_size=_PAGE_SIZE,
        total=0,
        total_pages=0,
        page_numbers=[],
        has_previous=False,
        has_next=False,
    )
    return ExamRegistrationManagementPageRead(
        page_title="Exam Registration Management",
        page_subtitle="Student registrations for the session",
        export_label="Export",
        confirm_selected_label="Confirm selected",
        search_placeholder="Search student or register number",
        sub_nav=examination_registration_sub_nav("exam-registration-management"),
        session_filter_label="Exam session",
        status_filter_label="Status",
        programme_filter_label="Programme",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        session_options=[],
        status_options=[StudentAdminDashboardFilterOption(value=k, label=v) for k, v in _STATUS_FILTER_OPTIONS],
        programme_options=[StudentAdminDashboardFilterOption(value="", label="All programmes")],
        selected_session_id="",
        selected_status="",
        selected_programme_code="",
        registration_window_title="Registration window",
        registration_window_open_label="Opens —",
        registration_window_close_label="Closes —",
        registration_window_status_label="No session",
        registration_window_status_tone="muted",
        kpis=[
            UserDashboardKpi(key="total", label="Total", value="0", hint_line="All registrations", hint_tone="info"),
            UserDashboardKpi(key="confirmed", label="Confirmed", value="0", hint_line="—", hint_tone="success"),
            UserDashboardKpi(key="submitted", label="Submitted", value="0", hint_line="Awaiting review", hint_tone="info"),
            UserDashboardKpi(
                key="pending_fee", label="Fee pending", value="0", hint_line="Fee not verified", hint_tone="warning"
            ),
            UserDashboardKpi(key="cancelled", label="Cancelled", value="0", hint_line="—", hint_tone="muted"),
        ],
        registrations_section_title="Registrations",
        registration_count_label="0 registrations",
        table_headers=["Student", "Register no.", "Subjects", "Fee", "Eligibility", "Status"],
        registration_rows=[],
        showing_label="Showing 0 of 0",
        pagination=empty_pagination,
        footer_disclaimer="Live institutional data · Exam registrations and fee verification · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_exam_registration_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
    status: str | None = None,
    programme_code: str | None = None,
    search: str | None = None,
) -> ExamRegistrationManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-registration_start_at").to_list()
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_by_code = {p.programme_code.upper(): p for p in programmes}

    session = _select_session(sessions, session_id, now)
    if not session:
        return _empty_page(now, "Create an exam session to manage registrations")

    programme_filter = (programme_code or "").strip().upper()
    status_filter = (status or "").strip().lower()
    search_term = (search or "").strip().lower()

    session_options = [
        StudentAdminDashboardFilterOption(
            value=row.session_id,
            label=f"{row.name or row.session_code} · {row.semester_label} {row.academic_year_label}",
        )
        for row in sessions
    ]
    programme_options = [
        StudentAdminDashboardFilterOption(value="", label="All programmes"),
        *[
            StudentAdminDashboardFilterOption(value=p.programme_code, label=p.name or p.programme_code)
            for p in programmes
        ],
    ]

    window_status, window_tone = _registration_window_status(session, now)

    base = {"tenant_id": tenant_id, "exam_session_id": session.id}
    total_regs = await ExamRegistration.find(base).count()
    confirmed = await ExamRegistration.find({**base, "status": ExamRegistrationStatus.CONFIRMED.value}).count()
    submitted = await ExamRegistration.find({**base, "status": ExamRegistrationStatus.SUBMITTED.value}).count()
    cancelled = await ExamRegistration.find({**base, "status": ExamRegistrationStatus.CANCELLED.value}).count()
    pending_fee = await ExamRegistration.find(
        {**base, "fee_verified": False, "status": {"$nin": [ExamRegistrationStatus.CANCELLED.value]}}
    ).count()

    registrations = await ExamRegistration.find(
        Eq(ExamRegistration.tenant_id, tenant_id),
        Eq(ExamRegistration.exam_session_id, session.id),
    ).sort("-created_at").to_list()

    student_user_ids = list({r.student_user_id for r in registrations})
    users = await User.find(In(User.id, student_user_ids)).to_list() if student_user_ids else []
    user_by_id = {u.id: u for u in users if u.id}

    records = (
        await StudentRecord.find(
            Eq(StudentRecord.tenant_id, tenant_id),
            In(StudentRecord.user_id, student_user_ids),
        ).to_list()
        if student_user_ids
        else []
    )
    record_by_user = {r.user_id: r for r in records}

    profiles = (
        await StudentProfile.find(
            Eq(StudentProfile.tenant_id, tenant_id),
            In(StudentProfile.user_id, student_user_ids),
        ).to_list()
        if student_user_ids
        else []
    )
    profiles_map = {p.user_id: p for p in profiles}

    reg_ids = [r.registration_id for r in registrations]
    subjects = (
        await ExamRegistrationSubject.find(
            Eq(ExamRegistrationSubject.tenant_id, tenant_id),
            In(ExamRegistrationSubject.registration_id, reg_ids),
        ).to_list()
        if reg_ids
        else []
    )
    subject_counts: dict[str, int] = defaultdict(int)
    for subj in subjects:
        subject_counts[subj.registration_id] += 1

    eligibility_rows = await ExamEligibilityRecord.find(
        Eq(ExamEligibilityRecord.tenant_id, tenant_id),
        Eq(ExamEligibilityRecord.exam_session_id, session.id),
    ).to_list()
    eligibility_by_user = {row.student_user_id: row for row in eligibility_rows}

    filtered: list[ExamRegistration] = []
    for reg in registrations:
        if status_filter and reg.status.value != status_filter:
            continue
        record = record_by_user.get(reg.student_user_id)
        code = (record.programme_code if record else "").upper()
        if programme_filter and code != programme_filter:
            continue
        if search_term:
            user = user_by_id.get(reg.student_user_id)
            profile = profiles_map.get(reg.student_user_id)
            register_no = _register_number(record, profile) if record else ""
            name = (user.full_name if user else "").lower()
            if search_term not in name and search_term not in register_no.lower():
                continue
        filtered.append(reg)

    total = len(filtered)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_regs = filtered[start : start + _PAGE_SIZE]

    rows: list[ExamRegistrationManagementTableRow] = []
    for reg in page_regs:
        user = user_by_id.get(reg.student_user_id)
        record = record_by_user.get(reg.student_user_id)
        profile = profiles_map.get(reg.student_user_id)
        status_label, status_tone = _STATUS_LABELS.get(reg.status, ("—", "muted"))
        fee_label, fee_tone = _fee_label(reg.fee_verified)
        elig_label, elig_tone = _eligibility_label(eligibility_by_user.get(reg.student_user_id))
        student_name = user.full_name.strip() if user and user.full_name else "—"
        register_no = _register_number(record, profile) if record else "—"
        programme = _programme_label(record.programme_code if record else None, profile, programme_by_code)
        submitted_label = _fmt_window(reg.submitted_at) if reg.submitted_at else "—"
        detail_href = f"/college-admin/students/student-details?id={record.id}" if record else "/college-admin/students/all-students-list"
        is_selectable = reg.status == ExamRegistrationStatus.SUBMITTED and reg.fee_verified
        rows.append(
            ExamRegistrationManagementTableRow(
                registration_id=reg.registration_id,
                student_name=student_name,
                register_number=register_no,
                programme_label=programme,
                subjects_count=subject_counts.get(reg.registration_id, 0),
                fee_status_label=fee_label,
                fee_status_tone=fee_tone,
                eligibility_status_label=elig_label,
                eligibility_status_tone=elig_tone,
                registration_status_label=status_label,
                registration_status_tone=status_tone,
                submitted_at_label=submitted_label,
                detail_href=detail_href,
                is_selectable=is_selectable,
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return ExamRegistrationManagementPageRead(
        page_title="Exam Registration Management",
        page_subtitle="Student registrations for the session",
        export_label="Export",
        confirm_selected_label="Confirm selected",
        search_placeholder="Search student or register number",
        sub_nav=examination_registration_sub_nav("exam-registration-management"),
        session_filter_label="Exam session",
        status_filter_label="Status",
        programme_filter_label="Programme",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        session_options=session_options,
        status_options=[StudentAdminDashboardFilterOption(value=k, label=v) for k, v in _STATUS_FILTER_OPTIONS],
        programme_options=programme_options,
        selected_session_id=session.session_id,
        selected_status=status_filter,
        selected_programme_code=programme_filter,
        registration_window_title="Registration window",
        registration_window_open_label=f"Opens {_fmt_window(session.registration_start_at)}",
        registration_window_close_label=f"Closes {_fmt_window(session.registration_end_at)}",
        registration_window_status_label=window_status,
        registration_window_status_tone=window_tone,
        kpis=[
            UserDashboardKpi(
                key="total",
                label="Total",
                value=f"{total_regs:,}",
                hint_line="All registrations",
                hint_tone="info",
            ),
            UserDashboardKpi(
                key="confirmed",
                label="Confirmed",
                value=f"{confirmed:,}",
                hint_line="Ready for hall tickets",
                hint_tone="success",
            ),
            UserDashboardKpi(
                key="submitted",
                label="Submitted",
                value=f"{submitted:,}",
                hint_line="Awaiting confirmation",
                hint_tone="info",
            ),
            UserDashboardKpi(
                key="pending_fee",
                label="Fee pending",
                value=f"{pending_fee:,}",
                hint_line="Fee not verified",
                hint_tone="warning",
            ),
            UserDashboardKpi(
                key="cancelled",
                label="Cancelled",
                value=f"{cancelled:,}",
                hint_line="—",
                hint_tone="muted",
            ),
        ],
        registrations_section_title="Registrations",
        registration_count_label=f"{total:,} registrations" if total else "0 registrations",
        table_headers=["Student", "Register no.", "Subjects", "Fee", "Eligibility", "Status"],
        registration_rows=rows,
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
        footer_disclaimer="Live institutional data · Exam registrations and fee verification · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def bulk_confirm_exam_registrations(
    scope: AccessScope,
    actor: User,
    payload: ExamRegistrationBulkConfirmPayload,
) -> ExamRegistrationManagementPageRead:
    authorize_examination_cell_registration_manage(scope)
    tenant_id = require_college_tenant_scope(scope)
    if not payload.registration_ids:
        raise AppError(code="VALIDATION_ERROR", message="Select at least one submitted registration", status_code=422)

    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)

    now = utcnow()
    for registration_id in payload.registration_ids:
        reg = await ExamRegistration.find_one(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.registration_id, registration_id),
            Eq(ExamRegistration.exam_session_id, session.id),
        )
        if reg is None:
            continue
        if reg.status != ExamRegistrationStatus.SUBMITTED or not reg.fee_verified:
            continue
        reg.status = ExamRegistrationStatus.CONFIRMED
        reg.confirmed_at = now
        reg.updated_at = now
        await reg.save()
        await ExamRegistrationHistory(
            tenant_id=tenant_id,
            registration_id=reg.registration_id,
            exam_session_id=session.id,
            student_user_id=reg.student_user_id,
            action=ExamRegistrationHistoryAction.CONFIRMED,
            actor_id=actor.id,
            note="Confirmed from registration management",
        ).insert()

    return await get_exam_registration_management_page(
        scope,
        page=payload.page,
        session_id=payload.session_id,
        status=payload.status,
        programme_code=payload.programme_code,
    )