"""HR salary slip management (CA 11 — Salary Slip Management)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.hr_payroll_shared import HR_PAYROLL_SUB_NAV
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrSalarySlipManagementPageRead,
    HrSalarySlipMonthRow,
    PoliciesPagination,
)
from app.modules.hr.enums import HrPayslipStatus, HrPayrollRunStatus
from app.modules.hr.payroll_models import HrEmployeePayrollRecord, HrEmployeePayslip, HrPayrollPeriod, HrPayrollRun

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
        FacultyEmploymentStatus.NOTICE_PERIOD,
    },
)


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _month_label(year: int, month: int) -> str:
    return datetime(year, month, 1).strftime("%b %Y")


def _period_label(period: HrPayrollPeriod) -> str:
    return f"{period.period_year}-{period.period_month:02d}"


def _slip_status(
    *,
    run: HrPayrollRun | None,
    employee_count: int | None,
    generated: int,
    published: int,
    failed: int,
) -> tuple[str, str]:
    if run is None or run.status not in {
        HrPayrollRunStatus.APPROVED,
        HrPayrollRunStatus.PAYMENT_PROCESSING,
        HrPayrollRunStatus.PAID,
    }:
        return "Not generated", "muted"
    if failed:
        return "Failed", "error"
    if employee_count and published >= employee_count:
        return "Published", "success"
    if generated > 0:
        return "Generated", "info"
    return "Not generated", "muted"


async def get_hr_salary_slip_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HrSalarySlipManagementPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    periods = await HrPayrollPeriod.find(Eq(HrPayrollPeriod.tenant_id, tenant_id)).sort(-HrPayrollPeriod.period_year, -HrPayrollPeriod.period_month).to_list()
    period_ids = [p.id for p in periods]
    runs_by_period: dict[str, HrPayrollRun] = {}
    if period_ids:
        runs = await HrPayrollRun.find(
            Eq(HrPayrollRun.tenant_id, tenant_id),
            In(HrPayrollRun.payroll_period_id, period_ids),
        ).sort("-revision").to_list()
        for run in runs:
            key = str(run.payroll_period_id)
            if key not in runs_by_period:
                runs_by_period[key] = run

    payslips_by_period: dict[str, list[HrEmployeePayslip]] = defaultdict(list)
    slips = await HrEmployeePayslip.find(Eq(HrEmployeePayslip.tenant_id, tenant_id)).to_list()
    for slip in slips:
        payslips_by_period[slip.period_label].append(slip)

    default_employees = await EmployeeRecord.find(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        In(EmployeeRecord.employment_status, list(_ACTIVE_EMPLOYMENT)),
    ).count()

    table_rows: list[HrSalarySlipMonthRow] = []
    for period in periods:
        run = runs_by_period.get(str(period.id))
        label = _period_label(period)
        month_slips = payslips_by_period.get(label, [])
        generated = sum(1 for s in month_slips if s.status in {HrPayslipStatus.GENERATED, HrPayslipStatus.PUBLISHED, HrPayslipStatus.UNDER_REVIEW})
        published = sum(1 for s in month_slips if s.status == HrPayslipStatus.PUBLISHED)
        failed = sum(1 for s in month_slips if s.status == HrPayslipStatus.FAILED)

        employee_count: int | None = None
        if run:
            employee_count = await HrEmployeePayrollRecord.find(
                Eq(HrEmployeePayrollRecord.tenant_id, tenant_id),
                Eq(HrEmployeePayrollRecord.payroll_run_id, run.id),
            ).count()
        elif month_slips:
            employee_count = len({s.employee_user_id for s in month_slips})

        status_label, status_tone = _slip_status(
            run=run,
            employee_count=employee_count,
            generated=generated,
            published=published,
            failed=failed,
        )

        def _count_display(value: int | None) -> str | None:
            if status_label == "Not generated" and value == 0:
                return None
            return str(value) if value is not None else None

        table_rows.append(
            HrSalarySlipMonthRow(
                period_id=str(period.id),
                month_label=_month_label(period.period_year, period.period_month),
                payroll_run_id=str(run.id) if run else None,
                employees_count=employee_count if employee_count is not None else (default_employees if run is None else 0),
                generated_count=generated if generated or status_label != "Not generated" else None,
                published_count=published if published or status_label not in ("Not generated",) else None,
                failed_count=failed if failed else (0 if status_label == "Published" else None),
                status_label=status_label,
                status_tone=status_tone,
            ),
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total = len(table_rows)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    visible = table_rows[start : start + page_size]
    showing_end = min(total, start + len(visible)) if total else 0

    latest_run = None
    if periods:
        latest_run = runs_by_period.get(str(periods[0].id))

    can_generate = bool(latest_run and latest_run.status in {HrPayrollRunStatus.APPROVED, HrPayrollRunStatus.PAYMENT_PROCESSING, HrPayrollRunStatus.PAID})
    generated_for_run = 0
    if latest_run:
        generated_for_run = sum(
            1 for s in slips if s.payroll_run_id == latest_run.id and s.status == HrPayslipStatus.GENERATED
        )
    can_publish = generated_for_run > 0

    return HrSalarySlipManagementPageRead(
        page_title="Salary Slip Management",
        page_subtitle="Generate and publish salary slips",
        generate_label="Generate",
        publish_label="Publish",
        can_generate=can_generate,
        can_publish=can_publish > 0,
        generate_blocked_message=None if can_generate else "Approve payroll for a period before generating slips.",
        publish_blocked_message=None if can_publish else "Generate slips for the latest approved payroll run first.",
        selected_payroll_run_id=str(latest_run.id) if latest_run else None,
        sub_nav=HR_PAYROLL_SUB_NAV,
        slips_section_title="Salary slips",
        table_headers=["Month", "Employees", "Generated", "Published", "Failed", "Status"],
        slip_rows=visible,
        showing_label=f"Showing {showing_end} of {total}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages) if total_pages else [],
            has_previous=page > 1,
            has_next=page < total_pages if total_pages else False,
        ),
        footer_disclaimer="Live institutional data · Salary slips · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )