"""Student fee management list page (CA 10.03)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.all_students_list_page_service import _programme_label, _register_number
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    StudentFeeManagementPageRead,
    StudentFeeManagementTableRow,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.college_admin.student_statistics_overview_service import _ENROLLED_LIFECYCLE
from app.modules.students.models import StudentProfile

_PAGE_SIZE = 10


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _format_inr(amount: float) -> str:
    rupees = int(round(amount))
    s = str(rupees)
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    rest = s[:-3]
    groups: list[str] = []
    while rest:
        take = 2 if len(rest) > 2 else len(rest)
        groups.insert(0, rest[-take:])
        rest = rest[:-take]
    return f"₹{','.join(groups + [last3])}"


def _assessment_status(assessment: StudentFeeAssessment) -> tuple[str, str]:
    workflow = (assessment.workflow_status or "posted").lower()
    if workflow in {"exception", "error", "hold", "blocked"}:
        return "Exception", "error"
    if workflow in {"pending", "draft", "review", "submitted"}:
        return "Pending", "warning"
    if not assessment.demand_id:
        return "Pending", "warning"
    return "Finalised", "success"


def _adjustment_total(assessment: StudentFeeAssessment) -> float:
    return (
        (assessment.concession_amount or 0)
        + (assessment.scholarship_amount or 0)
        + (assessment.waiver_amount or 0)
        + (assessment.adjustment_amount or 0)
    )


async def get_student_fee_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> StudentFeeManagementPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    assessments = await StudentFeeAssessment.find(Eq(StudentFeeAssessment.tenant_id, tenant_id)).sort(
        "-updated_at"
    ).to_list()

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    enrolled_records = [r for r in records if r.lifecycle_status.value in _ENROLLED_LIFECYCLE]
    enrolled_count = len(enrolled_records) or len(records)

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}
    record_by_user = {r.user_id: r for r in records}

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}

    assessed_students = len({a.student_user_id for a in assessments})
    assessed_pct = round((assessed_students / enrolled_count) * 100, 1) if enrolled_count > 0 else 0.0

    pending_count = sum(1 for a in assessments if _assessment_status(a)[0] == "Pending")
    adjustment_count = sum(1 for a in assessments if _adjustment_total(a) > 0)
    exception_count = sum(1 for a in assessments if _assessment_status(a)[0] == "Exception")

    total = len(assessments)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_rows = assessments[start : start + _PAGE_SIZE]

    user_ids = {a.student_user_id for a in page_rows}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}

    rows: list[StudentFeeManagementTableRow] = []
    for assessment in page_rows:
        profile = profile_by_user.get(assessment.student_user_id)
        record = record_by_user.get(assessment.student_user_id)
        programme_code = assessment.programme_code or (profile.programme_code if profile else None)
        code_key = (programme_code or "").upper()
        if record:
            register = _register_number(record, profile)
        elif profile and profile.roll_number:
            register = profile.roll_number
        else:
            register = "—"
        status_label, status_tone = _assessment_status(assessment)
        rows.append(
            StudentFeeManagementTableRow(
                assessment_id=assessment.assessment_id,
                student_name=user_names.get(assessment.student_user_id, "—"),
                register_number=register,
                programme_label=_programme_label(code_key or None, profile, prog_by_code),
                assessed_label=_format_inr(assessment.assessed_amount),
                concession_label=_format_inr(assessment.concession_amount or 0),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/student-fee-management",
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    kpis = [
        UserDashboardKpi(
            key="assessed",
            label="Assessed",
            value=f"{total:,}",
            hint_line=f"{assessed_pct:g}%" if enrolled_count else "—",
            hint_tone="success" if assessed_pct >= 80 else "info",
        ),
        UserDashboardKpi(
            key="pending",
            label="Pending",
            value=f"{pending_count:,}",
            hint_line="Awaiting finalisation",
            hint_tone="warning" if pending_count else "success",
        ),
        UserDashboardKpi(
            key="adjustments",
            label="Adjustments",
            value=f"{adjustment_count:,}",
            hint_line="Scholarship or concession",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="exceptions",
            label="Exceptions",
            value=f"{exception_count:,}",
            hint_line="Needs review",
            hint_tone="error" if exception_count else "success",
        ),
    ]

    return StudentFeeManagementPageRead(
        page_title="Student Fee Management",
        page_subtitle="Assign fees to students after assessment",
        assign_student_label="Assign student",
        assign_group_label="Assign group",
        bulk_assign_label="Bulk import",
        bulk_assign_href="/college-admin/finance/student-fee-management?bulk=1",
        kpis=kpis,
        student_fees_section_title="Student fees",
        student_fees_count_label=f"{total:,} records" if total else "0 records",
        table_headers=["Student", "Register no.", "Programme", "Assessed", "Concession", "Status"],
        student_fees=rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )