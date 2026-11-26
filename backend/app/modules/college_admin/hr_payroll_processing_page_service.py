"""HR payroll processing dashboard (CA 11 — Payroll Processing)."""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.hr_admin_models import PayrollConfiguration
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.hr_payroll_shared import HR_PAYROLL_SUB_NAV, format_inr_compact, humanize_payroll_exception
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrPayrollExceptionRow,
    HrPayrollProcessingPageRead,
    HrPayrollWorkflowStep,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.hr.enums import HrPayrollEmployeeStatus, HrPayrollRunStatus
from app.modules.hr.payroll_models import HrEmployeePayrollRecord, HrPayrollPeriod, HrPayrollRun

_IST = ZoneInfo("Asia/Kolkata")
_EXCEPTION_PAGE_SIZE = 5
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

_WORKFLOW_STEPS = [
    ("attendance_lock", "Attendance lock"),
    ("calculate", "Calculate"),
    ("validate", "Validate"),
    ("approve", "Approve"),
    ("process", "Process"),
    ("slips", "Slips"),
]


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _period_subtitle(period: HrPayrollPeriod | None, now: datetime) -> str:
    if period:
        month_name = date(period.period_year, period.period_month, 1).strftime("%B %Y")
        return f"{month_name} payroll"
    return f"{now.astimezone(_IST).strftime('%B %Y')} payroll"


def _workflow_index(status: HrPayrollRunStatus | None, *, attendance_locked: bool) -> int:
    if status is None:
        return 0 if attendance_locked else 0
    if status in {HrPayrollRunStatus.DRAFT, HrPayrollRunStatus.REOPENED}:
        return 1 if attendance_locked else 0
    if status == HrPayrollRunStatus.CALCULATING:
        return 1
    if status == HrPayrollRunStatus.VALIDATION_REQUIRED:
        return 2
    if status in {HrPayrollRunStatus.READY_FOR_REVIEW, HrPayrollRunStatus.UNDER_REVIEW}:
        return 3
    if status == HrPayrollRunStatus.APPROVED:
        return 4
    if status in {HrPayrollRunStatus.PAYMENT_PROCESSING, HrPayrollRunStatus.PAID}:
        return 5
    return 1


def _build_workflow_steps(current_index: int) -> list[HrPayrollWorkflowStep]:
    steps: list[HrPayrollWorkflowStep] = []
    for idx, (key, label) in enumerate(_WORKFLOW_STEPS):
        if idx < current_index:
            state = "complete"
        elif idx == current_index:
            state = "current"
        else:
            state = "upcoming"
        steps.append(HrPayrollWorkflowStep(key=key, label=label, state=state))
    return steps


async def _resolve_current_period(tenant_id: PydanticObjectId, anchor: date) -> HrPayrollPeriod | None:
    return await HrPayrollPeriod.find_one(
        Eq(HrPayrollPeriod.tenant_id, tenant_id),
        Eq(HrPayrollPeriod.period_year, anchor.year),
        Eq(HrPayrollPeriod.period_month, anchor.month),
    )


async def _resolve_latest_run(tenant_id: PydanticObjectId, period_id: PydanticObjectId | None) -> HrPayrollRun | None:
    if period_id is None:
        return None
    runs = await HrPayrollRun.find(
        Eq(HrPayrollRun.tenant_id, tenant_id),
        Eq(HrPayrollRun.payroll_period_id, period_id),
    ).sort("-revision").to_list()
    return runs[0] if runs else None


def _can_validate(run: HrPayrollRun | None) -> bool:
    if run is None:
        return False
    return run.status in {
        HrPayrollRunStatus.VALIDATION_REQUIRED,
        HrPayrollRunStatus.READY_FOR_REVIEW,
        HrPayrollRunStatus.UNDER_REVIEW,
    }


def _can_process(run: HrPayrollRun | None) -> bool:
    if run is None:
        return True
    return run.status in {
        HrPayrollRunStatus.DRAFT,
        HrPayrollRunStatus.REOPENED,
        HrPayrollRunStatus.READY_FOR_REVIEW,
        HrPayrollRunStatus.UNDER_REVIEW,
        HrPayrollRunStatus.APPROVED,
        HrPayrollRunStatus.VALIDATION_REQUIRED,
    }


async def get_hr_payroll_processing_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _EXCEPTION_PAGE_SIZE,
) -> HrPayrollProcessingPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    period = await _resolve_current_period(tenant_id, today)
    run = await _resolve_latest_run(tenant_id, period.id if period else None)

    payroll_config = await PayrollConfiguration.find_one(Eq(PayrollConfiguration.tenant_id, tenant_id))
    owner_label = payroll_config.label if payroll_config and payroll_config.label else "HR Officer"

    attendance_locked = bool(period and (period.is_closed or today > period.attendance_cutoff))

    employee_count = await EmployeeRecord.find(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        In(EmployeeRecord.employment_status, list(_ACTIVE_EMPLOYMENT)),
    ).count()

    gross = Decimal("0")
    deductions = Decimal("0")
    net = Decimal("0")
    exception_rows_raw: list[HrEmployeePayrollRecord] = []

    if run:
        records = await HrEmployeePayrollRecord.find(
            Eq(HrEmployeePayrollRecord.tenant_id, tenant_id),
            Eq(HrEmployeePayrollRecord.payroll_run_id, run.id),
        ).to_list()
        for rec in records:
            if rec.status == HrPayrollEmployeeStatus.EXCLUDED:
                continue
            gross += Decimal(rec.gross_salary or "0")
            deductions += Decimal(rec.total_employee_deductions or "0")
            net += Decimal(rec.net_payable or "0")
            if rec.exceptions or rec.status == HrPayrollEmployeeStatus.EXCEPTION:
                exception_rows_raw.append(rec)
        if run.summary:
            gross = Decimal(run.summary.get("gross_total", gross))
            net = Decimal(run.summary.get("net_total", net))
            deductions = gross - net if gross >= net else deductions

    users: dict[PydanticObjectId, User] = {}
    if exception_rows_raw:
        uids = {r.employee_user_id for r in exception_rows_raw}
        for user in await User.find(In(User.id, list(uids))).to_list():
            users[user.id] = user

    exception_table: list[HrPayrollExceptionRow] = []
    for rec in exception_rows_raw:
        user = users.get(rec.employee_user_id)
        name = user.full_name if user and user.full_name else "—"
        issue = humanize_payroll_exception(rec.exceptions[0] if rec.exceptions else "payroll_exception")
        impact = format_inr_compact(Decimal(rec.net_payable or "0")) if rec.net_payable else "—"
        if rec.exceptions and "probation" in rec.exceptions[0]:
            impact = "Grade change"
        exception_table.append(
            HrPayrollExceptionRow(
                row_key=str(rec.id),
                employee_label=name,
                issue_label=issue,
                impact_label=impact,
                owner_label=owner_label,
                status_label="Open",
                status_tone="warning",
            ),
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_exc = len(exception_table)
    total_pages = math.ceil(total_exc / page_size) if total_exc else 0
    start = (page - 1) * page_size
    visible_exc = exception_table[start : start + page_size]
    showing_end = min(total_exc, start + len(visible_exc)) if total_exc else 0

    workflow_idx = _workflow_index(run.status if run else None, attendance_locked=attendance_locked)

    blocked: str | None = None
    if run and run.status == HrPayrollRunStatus.VALIDATION_REQUIRED and run.exception_count:
        blocked = f"{run.exception_count} exception(s) must be resolved before validation can complete."

    kpis = [
        UserDashboardKpi(key="employees", label="Employees", value=f"{employee_count:,}", hint_line="In payroll scope", hint_tone="neutral"),
        UserDashboardKpi(key="gross", label="Gross", value=format_inr_compact(gross), hint_line="Current run", hint_tone="neutral"),
        UserDashboardKpi(key="deductions", label="Deductions", value=format_inr_compact(deductions), hint_line="Employee deductions", hint_tone="neutral"),
        UserDashboardKpi(
            key="net_payable",
            label="Net payable",
            value=format_inr_compact(net),
            hint_line="After deductions",
            hint_tone="success" if net > 0 else "neutral",
        ),
    ]

    return HrPayrollProcessingPageRead(
        page_title="Payroll Processing",
        page_subtitle=_period_subtitle(period, now),
        validate_label="Validate",
        process_payroll_label="Process payroll",
        can_validate=_can_validate(run),
        can_process=_can_process(run),
        action_blocked_message=blocked,
        payroll_period_id=str(period.id) if period else None,
        payroll_run_id=str(run.id) if run else None,
        sub_nav=HR_PAYROLL_SUB_NAV,
        workflow_steps=_build_workflow_steps(workflow_idx),
        kpis=kpis,
        exceptions_section_title="Exceptions",
        exception_table_headers=["Employee", "Issue", "Impact", "Owner", "Status"],
        exception_rows=visible_exc,
        exceptions_showing_label=f"{showing_end} of {total_exc}" if total_exc else "0 of 0",
        exceptions_pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_exc,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages) if total_pages else [],
            has_previous=page > 1,
            has_next=page < total_pages if total_pages else False,
        ),
        footer_disclaimer="Live institutional data · Payroll processing · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )