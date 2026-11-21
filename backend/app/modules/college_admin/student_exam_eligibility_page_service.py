"""Student exam eligibility page (CA 09.04)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.attendance.enums import AttendanceMarkStatus
from app.modules.attendance.models import AttendanceRecord
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.auth.models import User
from app.modules.college_admin.all_students_list_page_service import _register_number
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.examination_registration_nav import examination_registration_sub_nav
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    StudentExamEligibilityPageRead,
    StudentExamEligibilityRerunPayload,
    StudentExamEligibilityTableRow,
    UserDashboardKpi,
)
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.examinations.exam_cell_eligibility_service import evaluate_student_eligibility
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamEligibilityRecord, ExamEligibilityRuleResult, ExamRegistration
from app.modules.examinations.exam_cell_registration_schemas import ExamEligibilityEvaluateRequest
from app.modules.students.models import StudentProfile

_PAGE_SIZE = 8


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _attendance_pct(rows: list[AttendanceRecord]) -> float | None:
    marked = [r for r in rows if r.status != AttendanceMarkStatus.UNMARKED]
    if not marked:
        return None
    return calculate_percentage(marked)


async def get_student_exam_eligibility_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> StudentExamEligibilityPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-registration_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )
    if session is None:
        return StudentExamEligibilityPageRead(
            page_title="Student Exam Eligibility",
            page_subtitle="Eligibility rules and exceptions",
            rerun_check_label="Re-run check",
            sub_nav=examination_registration_sub_nav("student-exam-eligibility"),
            scope_indicator_label="College scope",
            updated_at_label=_fmt_time_label(now),
            kpis=[
                UserDashboardKpi(key="eligible", label="Eligible", value="0", hint_line="—", hint_tone="success"),
                UserDashboardKpi(key="not_eligible", label="Not eligible", value="0", hint_line="—", hint_tone="error"),
                UserDashboardKpi(key="condoned", label="Condoned", value="0", hint_line="Medical cases", hint_tone="info"),
                UserDashboardKpi(key="under_review", label="Under review", value="0", hint_line="—", hint_tone="warning"),
            ],
            ineligible_section_title="Ineligible students",
            ineligible_count_label="0 students",
            table_headers=["Student", "Register no.", "Reason", "Attendance", "Fee", "Decision"],
            ineligible_rows=[],
            showing_label="Showing 0 of 0",
            pagination=empty_pagination,
            selected_session_id="",
            footer_disclaimer="Live institutional data · Exam eligibility · All times IST",
            footer_snapshot_label="Sample snapshot",
            generated_at=now,
        )

    records = await ExamEligibilityRecord.find(
        Eq(ExamEligibilityRecord.tenant_id, tenant_id),
        Eq(ExamEligibilityRecord.exam_session_id, session.id),
    ).to_list()
    total_students = len(records)
    eligible = sum(1 for r in records if r.overall_eligible)
    not_eligible = sum(1 for r in records if not r.overall_eligible)
    condoned = sum(1 for r in records if any("condon" in s.lower() or "medical" in s.lower() for s in r.summary_reasons))
    under_review = sum(1 for r in records if not r.published and not r.overall_eligible)

    pct = f"{(eligible / total_students * 100):.1f}%" if total_students else "—"

    ineligible_docs = [r for r in records if not r.overall_eligible]
    total = len(ineligible_docs)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_docs = ineligible_docs[start : start + _PAGE_SIZE]

    user_ids = [r.student_user_id for r in page_docs]
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    user_map = {u.id: u for u in users if u.id}
    student_records = (
        await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id), In(StudentRecord.user_id, user_ids)).to_list()
        if user_ids
        else []
    )
    record_map = {r.user_id: r for r in student_records}
    profiles = (
        await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id), In(StudentProfile.user_id, user_ids)).to_list()
        if user_ids
        else []
    )
    profile_map = {p.user_id: p for p in profiles}

    attendance_rows = (
        await AttendanceRecord.find(Eq(AttendanceRecord.tenant_id, tenant_id), In(AttendanceRecord.student_user_id, user_ids)).to_list()
        if user_ids
        else []
    )
    att_by_user: dict[PydanticObjectId, list[AttendanceRecord]] = {}
    for row in attendance_rows:
        att_by_user.setdefault(row.student_user_id, []).append(row)

    regs = (
        await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.exam_session_id, session.id),
            In(ExamRegistration.student_user_id, user_ids),
        ).to_list()
        if user_ids
        else []
    )
    reg_by_user = {r.student_user_id: r for r in regs}

    rows: list[StudentExamEligibilityTableRow] = []
    for doc in page_docs:
        user = user_map.get(doc.student_user_id)
        rec = record_map.get(doc.student_user_id)
        profile = profile_map.get(doc.student_user_id)
        name = user.full_name.strip() if user and user.full_name else "—"
        register_no = _register_number(rec, profile) if rec else "—"
        rules = await ExamEligibilityRuleResult.find(
            Eq(ExamEligibilityRuleResult.tenant_id, tenant_id),
            Eq(ExamEligibilityRuleResult.eligibility_id, doc.eligibility_id),
        ).to_list()
        reason = "—"
        for rule in rules:
            if not rule.passed:
                reason = rule.rule_code.value.replace("_", " ").title()
                if "attendance" in rule.rule_code.value:
                    reason = "Attendance"
                elif "fee" in rule.rule_code.value:
                    reason = "Dues"
                break
        att_pct = _attendance_pct(att_by_user.get(doc.student_user_id, []))
        att_label = f"{att_pct:g}%" if att_pct is not None else "—"
        reg = reg_by_user.get(doc.student_user_id)
        fee_label, fee_tone = ("Paid", "success") if reg and reg.fee_verified else ("Due", "error")
        if doc.published:
            decision, decision_tone = ("Blocked", "error")
        else:
            decision, decision_tone = ("Review", "warning")
        rows.append(
            StudentExamEligibilityTableRow(
                student_name=name,
                register_number=register_no,
                reason_label=reason,
                attendance_label=att_label,
                fee_status_label=fee_label,
                fee_status_tone=fee_tone,
                decision_label=decision,
                decision_tone=decision_tone,
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return StudentExamEligibilityPageRead(
        page_title="Student Exam Eligibility",
        page_subtitle="Eligibility rules and exceptions",
        rerun_check_label="Re-run check",
        sub_nav=examination_registration_sub_nav("student-exam-eligibility"),
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        kpis=[
            UserDashboardKpi(key="eligible", label="Eligible", value=f"{eligible:,}", hint_line=pct, hint_tone="success"),
            UserDashboardKpi(key="not_eligible", label="Not eligible", value=f"{not_eligible:,}", hint_line="—", hint_tone="error"),
            UserDashboardKpi(
                key="condoned",
                label="Condoned",
                value=f"{condoned:,}",
                hint_line="Medical cases" if condoned else "—",
                hint_tone="info",
            ),
            UserDashboardKpi(key="under_review", label="Under review", value=f"{under_review:,}", hint_line="—", hint_tone="warning"),
        ],
        ineligible_section_title="Ineligible students",
        ineligible_count_label=f"{total:,} students" if total else "0 students",
        table_headers=["Student", "Register no.", "Reason", "Attendance", "Fee", "Decision"],
        ineligible_rows=rows,
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
        footer_disclaimer="Live institutional data · Exam eligibility · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def rerun_student_exam_eligibility_page(
    scope: AccessScope,
    payload: StudentExamEligibilityRerunPayload,
) -> StudentExamEligibilityPageRead:
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
        In(
            ExamRegistration.status,
            [ExamRegistrationStatus.SUBMITTED.value, ExamRegistrationStatus.CONFIRMED.value],
        ),
    ).to_list()
    for reg in registrations:
        try:
            await evaluate_student_eligibility(
                scope,
                user,
                ExamEligibilityEvaluateRequest(
                    student_user_id=str(reg.student_user_id),
                    exam_session_id=str(session.id),
                    publish=True,
                ),
            )
        except AppError:
            continue
    return await get_student_exam_eligibility_page(scope, page=payload.page, session_id=payload.session_id)