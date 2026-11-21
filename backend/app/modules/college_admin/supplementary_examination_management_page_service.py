"""Supplementary examination management page (CA 09.10)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.department_resource_management_page_service import _format_inr
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_revaluation_supplementary_nav import examination_revaluation_supplementary_sub_nav
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    SupplementaryArrearSubjectRow,
    SupplementaryExaminationCreateSessionPayload,
    SupplementaryExaminationManagementPageRead,
    UserDashboardKpi,
)
from app.modules.examinations.exam_cell_enums import ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamRegistration, ExamRegistrationSubject
from app.modules.examinations.exam_cell_revaluation_enums import ExamSupplementaryRegistrationStatus
from app.modules.examinations.exam_cell_revaluation_models import ExamRevaluationApplication, ExamSupplementaryAttempt, ExamSupplementaryRegistration
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate
from app.modules.examinations.exam_cell_session_service import create_exam_session
from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableEntryStatus, ExamTimetableStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable, ExamTimetableEntry
from app.modules.students.arrear_backlog_models import BacklogStatus, StudentArrearReference
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationSubjectType

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 8
_REG_ACTIVE = [ExamRegistrationStatus.SUBMITTED.value, ExamRegistrationStatus.CONFIRMED.value]


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _pick_supplementary_session(
    sessions: list[ExamSession],
    session_id: str | None,
    now,
) -> ExamSession | None:
    if session_id:
        return _select_session(sessions, session_id, now)
    for session in sessions:
        if session.examination_type in {ExamSessionType.SUPPLEMENTARY, ExamSessionType.ARREAR}:
            return session
    return sessions[0] if sessions else None


def _subtitle(session: ExamSession | None) -> str:
    if session is None:
        return "Supplementary and arrear examinations"
    return session.name or session.session_code


def _month_label(dt) -> str:
    local = as_utc_aware(dt).astimezone(_IST)
    return local.strftime("%b %Y")


def _hall_label(entry: ExamTimetableEntry | None) -> str:
    if entry is None:
        return "—"
    if entry.room_label:
        return entry.room_label
    if entry.centre_code:
        return entry.centre_code
    return "—"


async def _timetable_map(
    tenant_id: PydanticObjectId,
    session: ExamSession,
) -> dict[str, ExamTimetableEntry]:
    timetable = await ExamTimetable.find_one(
        Eq(ExamTimetable.tenant_id, tenant_id),
        Eq(ExamTimetable.exam_session_id, session.id),
        Eq(ExamTimetable.status, ExamTimetableStatus.PUBLISHED.value),
    )
    if timetable is None:
        timetable = await ExamTimetable.find_one(
            Eq(ExamTimetable.tenant_id, tenant_id),
            Eq(ExamTimetable.exam_session_id, session.id),
        )
    if timetable is None:
        return {}
    entries = await ExamTimetableEntry.find(
        Eq(ExamTimetableEntry.tenant_id, tenant_id),
        Eq(ExamTimetableEntry.timetable_id, timetable.id),
        Eq(ExamTimetableEntry.status, ExamTimetableEntryStatus.ACTIVE.value),
    ).to_list()
    by_course: dict[str, ExamTimetableEntry] = {}
    for entry in entries:
        code = entry.course_code.upper()
        if code not in by_course:
            by_course[code] = entry
    return by_course


async def _arrear_subject_rows(
    tenant_id: PydanticObjectId,
    session: ExamSession | None,
) -> tuple[list[tuple[str, int]], int]:
    """Return sorted (course_code, student_count) and total paper count."""
    counts: dict[str, set[PydanticObjectId]] = defaultdict(set)

    if session is not None:
        active_regs = await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.exam_session_id, session.id),
            In(ExamRegistration.status, _REG_ACTIVE),
        ).to_list()
        active_reg_ids = {r.registration_id for r in active_regs}
        subjects = await ExamRegistrationSubject.find(
            Eq(ExamRegistrationSubject.tenant_id, tenant_id),
            Eq(ExamRegistrationSubject.exam_session_id, session.id),
            Eq(ExamRegistrationSubject.subject_type, ExamRegistrationSubjectType.SUPPLEMENTARY),
        ).to_list()
        for sub in subjects:
            if active_reg_ids and sub.registration_id not in active_reg_ids:
                continue
            counts[sub.course_code.upper()].add(sub.student_user_id)

        attempts = await ExamSupplementaryAttempt.find(
            Eq(ExamSupplementaryAttempt.tenant_id, tenant_id),
            Eq(ExamSupplementaryAttempt.exam_session_id, session.id),
        ).to_list()
        for att in attempts:
            counts[att.course_code.upper()].add(att.student_user_id)

    if not counts:
        arrears = await StudentArrearReference.find(
            Eq(StudentArrearReference.tenant_id, tenant_id),
            Eq(StudentArrearReference.backlog_status, BacklogStatus.PENDING),
        ).to_list()
        for row in arrears:
            counts[row.course_code.upper()].add(row.user_id)

    ranked = sorted(
        ((code, len(students)) for code, students in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return ranked, len(ranked)


async def _fee_collected_inr(
    tenant_id: PydanticObjectId,
    session: ExamSession | None,
) -> float:
    regs = await ExamSupplementaryRegistration.find(Eq(ExamSupplementaryRegistration.tenant_id, tenant_id)).to_list()
    if session is not None:
        regs = [
            r
            for r in regs
            if r.exam_session_id == session.id
            or (session.season_id and r.supplementary_season_id == session.season_id)
        ]
    verified = [r for r in regs if r.fee_verified]
    if not verified:
        return 0.0

    fee_samples = await ExamRevaluationApplication.find(
        Eq(ExamRevaluationApplication.tenant_id, tenant_id),
    ).to_list()
    unit_fees = [a.fee_amount for a in fee_samples if a.fee_amount > 0]
    unit = sum(unit_fees) / len(unit_fees) if unit_fees else 0.0
    if unit <= 0:
        return 0.0
    return sum(len(r.course_codes) * unit for r in verified)


async def get_supplementary_examination_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> SupplementaryExaminationManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
    session = _pick_supplementary_session(sessions, session_id, now)

    arrears_pending = await StudentArrearReference.find(
        Eq(StudentArrearReference.tenant_id, tenant_id),
        Eq(StudentArrearReference.backlog_status, BacklogStatus.PENDING),
    ).to_list()
    eligible_students = len({a.user_id for a in arrears_pending})

    supp_regs = await ExamSupplementaryRegistration.find(Eq(ExamSupplementaryRegistration.tenant_id, tenant_id)).to_list()
    if session is not None:
        supp_regs = [
            r
            for r in supp_regs
            if r.exam_session_id == session.id
            or (session.season_id and r.supplementary_season_id == session.season_id)
        ]
    registered = len(
        {
            r.student_user_id
            for r in supp_regs
            if r.status in {ExamSupplementaryRegistrationStatus.CONFIRMED, ExamSupplementaryRegistrationStatus.FEE_VERIFIED}
        }
    )

    subject_ranked, paper_total = await _arrear_subject_rows(tenant_id, session)
    fee_total = await _fee_collected_inr(tenant_id, session)

    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    course_titles = {(c.course_code or "").upper(): c.name for c in courses}

    timetable_by_course = await _timetable_map(tenant_id, session) if session else {}

    total = len(subject_ranked)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages) if total_pages else 1
    start = (page - 1) * _PAGE_SIZE
    page_subjects = subject_ranked[start : start + _PAGE_SIZE]

    rows: list[SupplementaryArrearSubjectRow] = []
    default_date = _month_label(session.examination_start_at) if session else "—"
    for code, students_count in page_subjects:
        entry = timetable_by_course.get(code)
        date_label = _month_label(entry.scheduled_start) if entry else default_date
        rows.append(
            SupplementaryArrearSubjectRow(
                course_code=code,
                subject_label=course_titles.get(code) or code,
                students_count=students_count,
                date_label=date_label,
                hall_label=_hall_label(entry),
            )
        )

    create_href = "/college-admin/examinations/examination-configuration?mode=new&examination_type=supplementary"
    if session:
        create_href = f"{create_href}&academic_year_label={session.academic_year_label}&semester_label={session.semester_label}"

    return SupplementaryExaminationManagementPageRead(
        page_title="Supplementary Examination Management",
        page_subtitle=_subtitle(session),
        create_session_label="Create session",
        create_session_href=create_href,
        sub_nav=examination_revaluation_supplementary_sub_nav("supplementary-examination-management"),
        eligible_hint_label="Arrears",
        arrear_subjects_section_title="Arrear subjects",
        table_headers=["Subject", "Code", "Students", "Date", "Hall"],
        arrear_subject_rows=rows,
        kpis=[
            UserDashboardKpi(
                key="eligible",
                label="Eligible students",
                value=f"{eligible_students:,}",
                hint_line="Arrears",
                hint_tone="info",
            ),
            UserDashboardKpi(key="registered", label="Registered", value=f"{registered:,}", hint_line="—", hint_tone="info"),
            UserDashboardKpi(key="papers", label="Papers", value=f"{paper_total:,}", hint_line="—", hint_tone="info"),
            UserDashboardKpi(
                key="fee_collected",
                label="Fee collected",
                value=_format_inr(fee_total) if fee_total > 0 else "₹0",
                hint_line="Verified payments",
                hint_tone="success" if fee_total > 0 else "muted",
            ),
        ],
        showing_label=f"{len(page_subjects)} of {paper_total:,}" if paper_total else "0 of 0",
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
        footer_disclaimer="Live institutional data · Supplementary examinations · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def create_supplementary_examination_session_page(
    scope: AccessScope,
    payload: SupplementaryExaminationCreateSessionPayload,
) -> SupplementaryExaminationManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    actor = await User.get(scope.user_id)
    if actor is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    local = as_utc_aware(now).astimezone(_IST)
    session_name = f"Arrear {local.strftime('%b %Y')}"

    base_session: ExamSession | None = None
    if payload.session_id:
        base_session = await ExamSession.find_one(
            Eq(ExamSession.tenant_id, tenant_id),
            Eq(ExamSession.session_id, payload.session_id),
        )
    else:
        sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
        base_session = sessions[0] if sessions else None

    ay_label = base_session.academic_year_label if base_session else f"{local.year}-{local.year + 1}"
    sem_label = base_session.semester_label if base_session else "Odd"
    season_id = base_session.season_id if base_session else None

    registration_end = now + timedelta(days=21)
    registration_start = now - timedelta(days=7)
    exam_start = registration_end + timedelta(days=14)
    exam_end = exam_start + timedelta(days=7)

    create_payload = ExamSessionCreate(
        session_code=f"SUPP-{uuid4().hex[:6].upper()}",
        name=session_name,
        examination_type=ExamSessionType.SUPPLEMENTARY,
        academic_year_label=ay_label,
        semester_label=sem_label,
        season_id=season_id,
        registration_start_at=registration_start,
        registration_end_at=registration_end,
        examination_start_at=exam_start,
        examination_end_at=exam_end,
        academic_scope=ExamSessionAcademicScopeInput(),
    )
    created = await create_exam_session(scope, actor, create_payload)
    return await get_supplementary_examination_management_page(
        scope,
        page=payload.page,
        session_id=created.session_id,
    )