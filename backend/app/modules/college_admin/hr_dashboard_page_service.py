"""HR administration overview dashboard (CA 11.01)."""

from __future__ import annotations

import calendar
import math
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, In, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyEmploymentStatus,
    FacultyRecord,
)
from app.modules.college_admin.hr_admin_models import EmployeeBenefitRecord, EmployeeOnboardingRecord, PayrollConfiguration, RecruitmentRecord, RecruitmentStatus
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrDashboardLeaveRow,
    HrDashboardPageRead,
    PoliciesPagination,
    StudentAdminWorkQueueItem,
    UserDashboardKpi,
)
from app.modules.hr.employment_change_models import HrContractRecord
from app.modules.hr.enums import HrJobOpeningStatus, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest
from app.modules.hr.onboarding_models import HrOnboardingTask
from app.modules.hr.recruitment_models import HrJobOpening
from app.modules.hr.enums import HrOnboardingTaskStatus

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_CONTRACT_WARNING_DAYS = 60
_ONBOARDING_OVERDUE_DAYS = 7

_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
)

_PENDING_LEAVE = frozenset(
    {
        LeaveRequestStatus.SUBMITTED,
        LeaveRequestStatus.PENDING_MANAGER,
        LeaveRequestStatus.PENDING_HR,
        LeaveRequestStatus.CLARIFICATION_REQUESTED,
    }
)

_TABLE_HEADERS = ["Employee", "Leave type", "Dates", "Days", "Approver", "Status"]


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _employee_active(status: FacultyEmploymentStatus) -> bool:
    return status in _ACTIVE_EMPLOYMENT


def _is_teaching_employee(emp: EmployeeRecord) -> bool:
    if emp.is_faculty:
        return True
    blob = f"{emp.employment_type or ''} {emp.designation or ''}".lower()
    if any(k in blob for k in ("non-teaching", "admin", "accounts", "support staff", "clerical")):
        return False
    return any(k in blob for k in ("faculty", "professor", "lecturer", "teaching", "academic"))


def _format_short_date(d: date) -> str:
    return d.strftime("%d %b %Y")


def _format_leave_dates(start: date, end: date) -> str:
    if start == end:
        return _format_short_date(start)
    if start.year == end.year and start.month == end.month:
        return f"{start.day:02d}–{end.day:02d} {end.strftime('%b %Y')}"
    return f"{_format_short_date(start)} – {_format_short_date(end)}"


def _leave_days(req: LeaveRequest) -> int:
    if req.working_days and req.working_days > 0:
        return max(1, int(round(req.working_days)))
    return max(1, (req.end_date - req.start_date).days + 1)


def _leave_type_label(raw: str) -> str:
    cleaned = (raw or "leave").replace("_", " ").strip()
    return cleaned.title()


def _leave_status(status: LeaveRequestStatus) -> tuple[str, str]:
    if status == LeaveRequestStatus.APPROVED:
        return "Approved", "success"
    if status == LeaveRequestStatus.REJECTED:
        return "Rejected", "error"
    if status in _PENDING_LEAVE:
        return "Pending", "warning"
    if status == LeaveRequestStatus.CANCELLED:
        return "Cancelled", "muted"
    return status.value.replace("_", " ").title(), "muted"


def _approver_label(dept: InstitutionDepartment | None) -> str:
    if dept is None:
        return "—"
    code = (dept.department_code or dept.name or "Dept").strip()
    if len(code) > 12:
        code = code[:10] + "…"
    return f"HOD, {code}"


async def get_hr_dashboard_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HrDashboardPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    employee_by_user = {e.user_id: e for e in employee_records}

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
    total_employees = faculty_count + staff_count

    open_recruitment = await RecruitmentRecord.find(
        Eq(RecruitmentRecord.tenant_id, tenant_id),
        Eq(RecruitmentRecord.status, RecruitmentStatus.OPEN),
    ).count()
    job_openings = await HrJobOpening.find(
        Eq(HrJobOpening.tenant_id, tenant_id),
        Eq(HrJobOpening.status, HrJobOpeningStatus.PUBLISHED),
    ).to_list()
    opening_slots = sum(max(0, o.vacancies - o.filled_count) for o in job_openings)
    vacancies = max(open_recruitment, opening_slots)

    on_leave_rows = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
        LTE(LeaveRequest.start_date, today),
        GTE(LeaveRequest.end_date, today),
    ).to_list()
    on_leave_today = len({r.employee_user_id for r in on_leave_rows})

    payroll_configs = await PayrollConfiguration.find(Eq(PayrollConfiguration.tenant_id, tenant_id)).to_list()
    payroll_status_label = "Draft"
    payroll_hint = "Configure payroll"
    if payroll_configs:
        status = (payroll_configs[0].last_run_status or "draft").replace("_", " ").title()
        payroll_status_label = status if status else "Draft"
        last_day = calendar.monthrange(today.year, today.month)[1]
        run_due = date(today.year, today.month, min(28, last_day))
        if run_due < today:
            if today.month == 12:
                run_due = date(today.year + 1, 1, 28)
            else:
                run_due = date(today.year, today.month + 1, 28)
        payroll_hint = f"Run due {run_due.strftime('%d %b')}"
    payroll_month = now.astimezone(_IST).strftime("%b %Y")

    departments = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
    dept_by_id = {d.id: d for d in departments}

    all_leave = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        In(
            LeaveRequest.status,
            [
                LeaveRequestStatus.SUBMITTED,
                LeaveRequestStatus.PENDING_MANAGER,
                LeaveRequestStatus.PENDING_HR,
                LeaveRequestStatus.CLARIFICATION_REQUESTED,
                LeaveRequestStatus.APPROVED,
                LeaveRequestStatus.REJECTED,
            ],
        ),
    ).sort("-updated_at").to_list()

    user_ids = {req.employee_user_id for req in all_leave}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    leave_table: list[HrDashboardLeaveRow] = []
    for req in all_leave:
        user = user_by_id.get(req.employee_user_id)
        emp = employee_by_user.get(req.employee_user_id)
        faculty = next((f for f in faculty_records if f.user_id == req.employee_user_id), None)
        dept_id = emp.department_id if emp and emp.department_id else (faculty.department_id if faculty else None)
        dept = dept_by_id.get(dept_id) if dept_id else None
        status_label, status_tone = _leave_status(req.status)
        name = user.full_name if user else "—"
        leave_table.append(
            HrDashboardLeaveRow(
                leave_request_id=str(req.id),
                employee_name=name,
                leave_type_label=_leave_type_label(req.leave_type),
                dates_label=_format_leave_dates(req.start_date, req.end_date),
                days_label=str(_leave_days(req)),
                approver_label=_approver_label(dept),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hr/leave-approval?id={req.id}",
            )
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_rows = len(leave_table)
    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    start = (page - 1) * page_size
    paged_rows = leave_table[start : start + page_size]
    showing_end = min(total_rows, start + len(paged_rows))
    showing_label = f"Showing {showing_end if total_rows else 0} of {total_rows}"

    pending_leave_count = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        In(LeaveRequest.status, list(_PENDING_LEAVE)),
    ).count()

    onboarding_overdue = await EmployeeOnboardingRecord.find(
        Eq(EmployeeOnboardingRecord.tenant_id, tenant_id),
        Eq(EmployeeOnboardingRecord.completed, False),
    ).to_list()
    overdue_cutoff = now - timedelta(days=_ONBOARDING_OVERDUE_DAYS)
    overdue_onboarding = sum(1 for row in onboarding_overdue if row.created_at <= overdue_cutoff)
    hr_tasks = await HrOnboardingTask.find(
        Eq(HrOnboardingTask.tenant_id, tenant_id),
        Eq(HrOnboardingTask.status, HrOnboardingTaskStatus.OVERDUE),
    ).count()
    onboarding_attention = max(overdue_onboarding, hr_tasks)

    contract_horizon = today + timedelta(days=_CONTRACT_WARNING_DAYS)
    contracts = await HrContractRecord.find(
        Eq(HrContractRecord.tenant_id, tenant_id),
        Eq(HrContractRecord.status, "active"),
    ).to_list()
    contracts_ending = sum(1 for c in contracts if c.end_date and today <= c.end_date <= contract_horizon)

    benefit_rows = await EmployeeBenefitRecord.find(Eq(EmployeeBenefitRecord.tenant_id, tenant_id)).to_list()
    claims_pending = sum(
        1 for b in benefit_rows if (b.status or "").lower() in {"pending", "submitted", "awaiting_review", "review"}
    )

    kpis = [
        UserDashboardKpi(
            key="employees",
            label="Employees",
            value=f"{total_employees:,}",
            hint_line=f"{faculty_count:,} faculty · {staff_count:,} staff",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="vacancies",
            label="Open vacancies",
            value=f"{vacancies:,}",
            hint_line="Approved posts",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="on_leave_today",
            label="On leave today",
            value=f"{on_leave_today:,}",
            hint_line="Approved leave today",
            hint_tone="warning" if on_leave_today else "success",
        ),
        UserDashboardKpi(
            key="payroll",
            label=f"Payroll {payroll_month}",
            value=payroll_status_label,
            hint_line=payroll_hint,
            hint_tone="neutral",
        ),
    ]

    needs_attention = [
        StudentAdminWorkQueueItem(
            key="leave_approvals",
            title="Leave approvals",
            subtitle="pending",
            count=pending_leave_count,
            href="/college-admin/hr/leave-approval",
            action_label="Review →",
            icon_slug="clock",
        ),
        StudentAdminWorkQueueItem(
            key="onboarding_tasks",
            title="Onboarding tasks",
            subtitle="overdue" if onboarding_attention else "in progress",
            count=onboarding_attention or len(onboarding_overdue),
            href="/college-admin/hr/employee-onboarding",
            action_label="Open →",
            icon_slug="info",
        ),
        StudentAdminWorkQueueItem(
            key="contracts_ending",
            title="Contracts ending in 60 days",
            subtitle="employees",
            count=contracts_ending,
            href="/college-admin/hr/employee-management",
            action_label="View →",
            icon_slug="calendar",
        ),
        StudentAdminWorkQueueItem(
            key="claims_review",
            title="Claims awaiting review",
            subtitle="benefit claims",
            count=claims_pending,
            href="/college-admin/hr/employee-benefits-claims",
            action_label="Review →",
            icon_slug="file-text",
        ),
    ]

    page_subtitle = f"Workforce overview • {today.strftime('%d %b %Y')}"

    return HrDashboardPageRead(
        page_title="HR Dashboard",
        page_subtitle=page_subtitle,
        export_label="Export",
        open_portal_label="Open HR portal",
        open_portal_href="/college-admin/hr/employee-management",
        kpis=kpis,
        leave_section_title="Leave applications",
        leave_view_all_href="/college-admin/hr/leave-management",
        leave_view_all_label="View all →",
        table_headers=_TABLE_HEADERS,
        leave_rows=paged_rows,
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_rows,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        needs_attention_title="Needs attention",
        needs_attention_items=needs_attention,
        generated_at=now,
    )