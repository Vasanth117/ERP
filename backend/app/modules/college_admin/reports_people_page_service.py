"""People reports module pages (CA 16 People)."""

from __future__ import annotations

import math
from datetime import date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyRecord
from app.modules.college_admin.hr_admin_models import RecruitmentRecord, RecruitmentStatus
from app.modules.college_admin.hr_dashboard_page_service import _employee_active, _is_teaching_employee
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.reports_academic_page_service import (
    _academic_year_label,
    _department_options,
    _fmt_last_run,
    _fmt_updated,
    _format_labels,
    _period_for,
    _sync_last_runs,
)
from app.modules.college_admin.reports_admin_models import InstitutionReportsAcademicDefinition
from app.modules.college_admin.reports_people_catalog import page_meta, page_rows
from app.modules.college_admin.schemas import (
    InstitutionFieldOption,
    PoliciesPagination,
    ReportsAcademicModulePageRead,
    ReportsAcademicTableRow,
    UserDashboardKpi,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.hr.employment_change_models import HrContractRecord, HrProbationReview
from app.modules.hr.enums import HrJobOpeningStatus, HrProbationReviewStatus, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest
from app.modules.hr.payroll_models import HrEmployeePayrollRecord, HrPayrollPeriod, HrPayrollRun
from app.modules.hr.recruitment_models import HrJobOpening

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"]
_CONTRACT_WARNING_DAYS = 60


async def _ensure_definitions(
    tenant_id: PydanticObjectId,
    page_key: str,
    ay_label: str,
) -> list[InstitutionReportsAcademicDefinition]:
    existing = await InstitutionReportsAcademicDefinition.find(
        Eq(InstitutionReportsAcademicDefinition.tenant_id, tenant_id),
        Eq(InstitutionReportsAcademicDefinition.page_key, page_key),
        Eq(InstitutionReportsAcademicDefinition.is_active, True),
    ).sort("+sort_order").to_list()
    if existing:
        changed = False
        for row in existing:
            seed = next((s for s in page_rows(page_key) if s.report_key == row.report_key), None)
            period = await _period_for(seed.period_kind if seed else "month", tenant_id, ay_label)
            if row.period_label != period:
                row.period_label = period
                row.updated_at = utcnow()
                changed = True
        if changed:
            for row in existing:
                await row.save()
        return existing

    seeds = page_rows(page_key)
    created: list[InstitutionReportsAcademicDefinition] = []
    for index, seed in enumerate(seeds):
        period = await _period_for(seed.period_kind, tenant_id, ay_label)
        doc = InstitutionReportsAcademicDefinition(
            tenant_id=tenant_id,
            page_key=page_key,
            report_key=seed.report_key,
            title=seed.title,
            period_label=period,
            export_formats=list(seed.export_formats),
            schedule_label=seed.schedule_label,
            last_run_at=None,
            sort_order=index,
        )
        await doc.insert()
        created.append(doc)
    return created


async def _workforce_counts(tenant_id: PydanticObjectId, department_id: PydanticObjectId | None) -> tuple[int, int, int]:
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    if department_id:
        faculty_records = [r for r in faculty_records if r.department_id == department_id]
        employee_records = [e for e in employee_records if e.department_id == department_id]

    active_faculty = [r for r in faculty_records if _employee_active(r.employment_status)]
    active_faculty_users = {r.user_id for r in active_faculty}
    faculty_count = len(active_faculty)
    staff_count = sum(
        1
        for emp in employee_records
        if _employee_active(emp.employment_status)
        and emp.user_id not in active_faculty_users
        and not _is_teaching_employee(emp)
    )
    total = faculty_count + staff_count
    return total, faculty_count, staff_count


async def _vacancy_count(tenant_id: PydanticObjectId) -> int:
    open_recruitment = await RecruitmentRecord.find(
        Eq(RecruitmentRecord.tenant_id, tenant_id),
        Eq(RecruitmentRecord.status, RecruitmentStatus.OPEN),
    ).count()
    openings = await HrJobOpening.find(
        Eq(HrJobOpening.tenant_id, tenant_id),
        Eq(HrJobOpening.status, HrJobOpeningStatus.PUBLISHED),
    ).to_list()
    slots = sum(max(0, o.vacancies - o.filled_count) for o in openings)
    return max(open_recruitment, slots)


async def _contracts_ending(tenant_id: PydanticObjectId) -> int:
    today = utcnow().astimezone(_IST).date()
    horizon = today + timedelta(days=_CONTRACT_WARNING_DAYS)
    contracts = await HrContractRecord.find(
        Eq(HrContractRecord.tenant_id, tenant_id),
        Eq(HrContractRecord.status, "active"),
    ).to_list()
    return sum(1 for c in contracts if c.end_date and today <= c.end_date <= horizon)


async def _faculty_employee_kpis(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
) -> list[UserDashboardKpi]:
    total, faculty, _staff = await _workforce_counts(tenant_id, department_id)
    vacancies = await _vacancy_count(tenant_id)
    contracts = await _contracts_ending(tenant_id)
    return [
        UserDashboardKpi(key="employees", label="Employees", value=f"{total:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(key="faculty", label="Faculty", value=f"{faculty:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(key="vacancies", label="Vacancies", value=f"{vacancies:,}", hint_line="", hint_tone="warning" if vacancies else "success"),
        UserDashboardKpi(
            key="contracts_ending",
            label="Contracts ending",
            value=f"{contracts:,}",
            hint_line=f"{_CONTRACT_WARNING_DAYS} days",
            hint_tone="warning" if contracts else "success",
        ),
    ]


def _fmt_inr_crores(amount: Decimal) -> str:
    crores = float(amount) / 10_000_000
    if crores >= 1:
        return f"₹{crores:.2f} Cr"
    lakhs = float(amount) / 100_000
    return f"₹{lakhs:.2f} L"


async def _payroll_month_total(tenant_id: PydanticObjectId, today: date) -> tuple[str, str]:
    period_label = today.strftime("%b")
    periods = await HrPayrollPeriod.find(Eq(HrPayrollPeriod.tenant_id, tenant_id)).sort("-period_year", "-period_month").to_list()
    period = next((p for p in periods if p.period_month == today.month and p.period_year == today.year), None)
    if period is None and periods:
        period = periods[0]
        period_label = date(period.period_year, period.period_month, 1).strftime("%b")
    if period is None:
        return "—", period_label
    runs = await HrPayrollRun.find(
        Eq(HrPayrollRun.tenant_id, tenant_id),
        Eq(HrPayrollRun.payroll_period_id, period.id),
    ).sort("-revision").to_list()
    if not runs:
        return "—", period_label
    records = await HrEmployeePayrollRecord.find(
        Eq(HrEmployeePayrollRecord.tenant_id, tenant_id),
        Eq(HrEmployeePayrollRecord.payroll_run_id, runs[0].id),
    ).to_list()
    total = sum(Decimal(str(r.net_payable or 0)) for r in records)
    return (_fmt_inr_crores(total) if records else "—"), period_label


async def _attrition_pct(tenant_id: PydanticObjectId, ay_label: str) -> float | None:
    total, _, _ = await _workforce_counts(tenant_id, None)
    if total <= 0:
        return None
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    exits = sum(1 for e in employees if not _employee_active(e.employment_status))
    return round((exits / total) * 100, 1) if total else None


_APPRAISAL_DONE_STATUSES = {
    HrProbationReviewStatus.CONFIRMED,
    HrProbationReviewStatus.EXTENDED,
    HrProbationReviewStatus.REJECTED,
    HrProbationReviewStatus.CONFIRMATION_RECOMMENDED,
    HrProbationReviewStatus.EXTENSION_RECOMMENDED,
}


async def _appraisal_completion_pct(tenant_id: PydanticObjectId) -> int:
    reviews = await HrProbationReview.find(Eq(HrProbationReview.tenant_id, tenant_id)).to_list()
    if not reviews:
        return 0
    done = sum(1 for r in reviews if r.status in _APPRAISAL_DONE_STATUSES)
    return int(round((done / len(reviews)) * 100))


async def _hr_kpis(tenant_id: PydanticObjectId, ay_label: str) -> list[UserDashboardKpi]:
    today = utcnow().astimezone(_IST).date()
    on_leave = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
        LTE(LeaveRequest.start_date, today),
        GTE(LeaveRequest.end_date, today),
    ).count()
    payroll_value, payroll_month = await _payroll_month_total(tenant_id, today)
    attrition = await _attrition_pct(tenant_id, ay_label)
    appraisal_pct = await _appraisal_completion_pct(tenant_id)
    return [
        UserDashboardKpi(key="on_leave", label="On leave today", value=f"{on_leave:,}", hint_line="", hint_tone="warning" if on_leave else "success"),
        UserDashboardKpi(
            key="payroll",
            label=f"Payroll {payroll_month}",
            value=payroll_value,
            hint_line="",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="attrition",
            label="Attrition",
            value=f"{attrition:.1f}%" if attrition is not None else "—",
            hint_line="FY to date",
            hint_tone="warning" if attrition and attrition > 5 else "success",
        ),
        UserDashboardKpi(
            key="appraisals",
            label="Appraisals done",
            value=f"{appraisal_pct}%",
            hint_line="",
            hint_tone="success" if appraisal_pct >= 50 else "warning",
        ),
    ]


async def _department_highlights_faculty(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
) -> list:
    from app.modules.college_admin.schemas import ReportsAcademicHighlightBar

    from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment

    depts = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    if department_id:
        depts = [d for d in depts if d.id == department_id]
    faculties = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    counts: dict[PydanticObjectId, int] = {}
    for fac in faculties:
        if fac.department_id and _employee_active(fac.employment_status):
            counts[fac.department_id] = counts.get(fac.department_id, 0) + 1
    max_count = max(counts.values()) if counts else 1
    metrics = [(d, round((counts.get(d.id, 0) / max_count) * 100)) for d in depts]
    metrics.sort(key=lambda x: x[1], reverse=True)
    tones = ("success", "success", "info", "warning")
    return [
        ReportsAcademicHighlightBar(
            bar_key=str(dept.id),
            department_label=dept.name or dept.code or "Department",
            percent_value=int(min(100, pct)),
            tone=tones[i % len(tones)],
        )
        for i, (dept, pct) in enumerate(metrics[:4])
    ]


async def _department_highlights_hr(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
) -> list:
    from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
    from app.modules.college_admin.schemas import ReportsAcademicHighlightBar

    depts = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    if department_id:
        depts = [d for d in depts if d.id == department_id]
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    active_employees = [e for e in employees if _employee_active(e.employment_status) and e.department_id]
    latest_review: dict[PydanticObjectId, HrProbationReview] = {}
    for review in await HrProbationReview.find(Eq(HrProbationReview.tenant_id, tenant_id)).to_list():
        prev = latest_review.get(review.employee_user_id)
        if prev is None or review.updated_at > prev.updated_at:
            latest_review[review.employee_user_id] = review

    metrics: list[tuple[InstitutionDepartment, int]] = []
    for dept in depts:
        dept_emps = [e for e in active_employees if e.department_id == dept.id]
        if not dept_emps:
            metrics.append((dept, 0))
            continue
        done = sum(
            1
            for emp in dept_emps
            if latest_review.get(emp.user_id) and latest_review[emp.user_id].status in _APPRAISAL_DONE_STATUSES
        )
        metrics.append((dept, int(round((done / len(dept_emps)) * 100))))

    metrics.sort(key=lambda x: x[1], reverse=True)
    tones = ("success", "success", "info", "warning")
    return [
        ReportsAcademicHighlightBar(
            bar_key=str(dept.id),
            department_label=dept.name or dept.code or "Department",
            percent_value=int(min(100, pct)),
            tone=tones[i % len(tones)],
        )
        for i, (dept, pct) in enumerate(metrics[:4])
    ]


async def get_reports_people_module_page(
    scope: AccessScope,
    *,
    page_key: str,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    academic_year: str | None = None,
    department_id: str | None = None,
) -> ReportsAcademicModulePageRead:
    meta = page_meta(page_key)
    if meta is None:
        raise AppError(code="NOT_FOUND", message="Unknown reports page", status_code=404)
    authorize(scope, meta.permission)
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    now = utcnow()
    ay_label = await _academic_year_label(tenant_id, academic_year)

    definitions = await _ensure_definitions(tenant_id, page_key, ay_label)
    await _sync_last_runs(tenant_id, definitions, meta.run_report_key)

    total = len(definitions)
    page = max(1, page)
    page_size = max(1, min(page_size, 20))
    start = (page - 1) * page_size
    visible = definitions[start : start + page_size]

    table_rows = [
        ReportsAcademicTableRow(
            row_key=row.report_key,
            report_label=row.title,
            period_label=row.period_label,
            format_label=_format_labels(row.export_formats),
            last_run_label=_fmt_last_run(row.last_run_at),
            schedule_label=row.schedule_label,
        )
        for row in visible
    ]

    if page_key == "faculty-employee":
        kpis = await _faculty_employee_kpis(tenant_id, dept_oid)
        highlights = await _department_highlights_faculty(tenant_id, dept_oid)
    else:
        kpis = await _hr_kpis(tenant_id, ay_label)
        highlights = await _department_highlights_hr(tenant_id, dept_oid)

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, start + len(table_rows))

    return ReportsAcademicModulePageRead(
        page_key=page_key,
        page_title=meta.page_title,
        page_subtitle=meta.page_subtitle,
        export_label="Export",
        run_report_label="Run report",
        academic_year_label=f"AY {ay_label}",
        academic_year_options=[InstitutionFieldOption(value=ay_label, label=f"AY {ay_label}")],
        department_filter_label="All departments",
        department_options=await _department_options(tenant_id),
        selected_department_id=department_id or "",
        scope_badge_label="College scope" if not dept_oid else "Department scope",
        updated_at_label=_fmt_updated(now),
        kpis=kpis,
        reports_section_title="Reports",
        highlights_section_title="Highlights",
        table_headers=_TABLE_HEADERS,
        report_rows=table_rows,
        highlight_bars=highlights,
        empty_table_message="No reports configured yet.",
        empty_highlights_message="No department highlights yet.",
        showing_label=f"Showing {showing_end} of {total}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        run_report_key=meta.run_report_key,
        generated_at=now,
    )