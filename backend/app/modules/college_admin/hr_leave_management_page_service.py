"""HR leave management dashboard (CA 11 — Leave Management)."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, GTE, In, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyRecord
from app.modules.college_admin.hr_attendance_leave_shared import HR_ATTENDANCE_LEAVE_SUB_NAV
from app.modules.college_admin.hr_dashboard_page_service import (
    _PENDING_LEAVE,
    _approver_label,
    _format_leave_dates,
    _leave_days,
    _leave_status,
    _leave_type_label,
    _page_numbers,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrDashboardLeaveRow,
    HrLeaveManagementPageRead,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.leave_models import HrLeaveBalance
from app.modules.hr.models import LeaveRequest

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Employee", "Leave type", "Dates", "Days", "Approver", "Status"]
_LOW_BALANCE_DAYS = 3.0


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _month_bounds(today: date) -> tuple[date, date]:
    start = date(today.year, today.month, 1)
    if today.month == 12:
        end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    return start, end


def _week_bounds(today: date) -> tuple[date, date]:
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end


async def get_hr_leave_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HrLeaveManagementPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    period_year = today.year

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    employee_by_user = {e.user_id: e for e in employee_records}

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

    application_rows: list[HrDashboardLeaveRow] = []
    for req in all_leave:
        user = user_by_id.get(req.employee_user_id)
        emp = employee_by_user.get(req.employee_user_id)
        faculty = next((f for f in faculty_records if f.user_id == req.employee_user_id), None)
        dept_id = emp.department_id if emp and emp.department_id else (faculty.department_id if faculty else None)
        dept = dept_by_id.get(dept_id) if dept_id else None
        status_label, status_tone = _leave_status(req.status)
        name = user.full_name if user else "—"
        application_rows.append(
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
            ),
        )

    pending_count = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        In(LeaveRequest.status, list(_PENDING_LEAVE)),
    ).count()

    month_start, month_end = _month_bounds(today)
    approved_month = sum(
        1
        for r in all_leave
        if r.status == LeaveRequestStatus.APPROVED and month_start <= r.updated_at.date() <= month_end
    )

    week_start, week_end = _week_bounds(today)
    on_leave_week = len(
        {
            r.employee_user_id
            for r in all_leave
            if r.status == LeaveRequestStatus.APPROVED
            and r.start_date <= week_end
            and r.end_date >= week_start
        },
    )

    balances = await HrLeaveBalance.find(
        Eq(HrLeaveBalance.tenant_id, tenant_id),
        Eq(HrLeaveBalance.period_year, period_year),
    ).to_list()
    low_balance_users = {
        b.employee_user_id for b in balances if b.available is not None and b.available < _LOW_BALANCE_DAYS
    }

    kpis = [
        UserDashboardKpi(
            key="applications",
            label="Applications",
            value=f"{pending_count:,}",
            hint_line="Pending",
            hint_tone="warning" if pending_count else "neutral",
        ),
        UserDashboardKpi(
            key="approved_month",
            label="Approved this month",
            value=f"{approved_month:,}",
            hint_line=now.astimezone(_IST).strftime("%b %Y"),
            hint_tone="success" if approved_month else "neutral",
        ),
        UserDashboardKpi(
            key="on_leave_week",
            label="On leave this week",
            value=f"{on_leave_week:,}",
            hint_line=f"{week_start.strftime('%d %b')} – {week_end.strftime('%d %b')}",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="low_balance",
            label="Balance below 3 days",
            value=f"{len(low_balance_users):,}",
            hint_line="Employees",
            hint_tone="warning" if low_balance_users else "neutral",
        ),
    ]

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_rows = len(application_rows)
    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    start = (page - 1) * page_size
    paged_rows = application_rows[start : start + page_size]
    showing_end = min(total_rows, start + len(paged_rows)) if total_rows else 0
    showing_label = f"Showing {showing_end} of {total_rows}"

    return HrLeaveManagementPageRead(
        page_title="Leave Management",
        page_subtitle="Leave balances, applications and calendar",
        leave_policy_label="Leave policy",
        leave_policy_href="/college-admin/hr/hr-settings-policies",
        sub_nav=HR_ATTENDANCE_LEAVE_SUB_NAV,
        kpis=kpis,
        applications_section_title="Leave applications",
        table_headers=_TABLE_HEADERS,
        application_rows=paged_rows,
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_rows,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages) if total_pages else [],
            has_previous=page > 1,
            has_next=page < total_pages if total_pages else False,
        ),
        footer_disclaimer="Live institutional data · Leave applications · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )