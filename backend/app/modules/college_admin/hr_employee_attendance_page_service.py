"""HR employee attendance dashboard (CA 11 — Employee Attendance)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, In, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.attendance_overview_service import _ACTIVE_EMPLOYMENT, _FACULTY_PRESENT
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyRecord
from app.modules.college_admin.faculty_employee_dashboard_page_service import _page_numbers
from app.modules.college_admin.hr_attendance_leave_shared import HR_ATTENDANCE_LEAVE_SUB_NAV
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrEmployeeAttendancePageRead,
    HrEmployeeAttendanceTableRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceRecord, HrWorkSchedule
from app.modules.hr.enums import EmployeeAttendanceDayStatus, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest

_IST = ZoneInfo("Asia/Kolkata")
_LOOKBACK_DAYS = 30
_DEFAULT_PAGE_SIZE = 3

_PRESENT_STATUSES = frozenset(
    {
        EmployeeAttendanceDayStatus.PRESENT,
        EmployeeAttendanceDayStatus.LATE,
        EmployeeAttendanceDayStatus.WORK_FROM_HOME,
        EmployeeAttendanceDayStatus.HALF_DAY,
        EmployeeAttendanceDayStatus.EARLY_DEPARTURE,
    }
)
_ABSENT_STATUSES = frozenset(
    {
        EmployeeAttendanceDayStatus.ABSENT,
        EmployeeAttendanceDayStatus.MISSING,
        EmployeeAttendanceDayStatus.INCOMPLETE,
        EmployeeAttendanceDayStatus.MISSING_PUNCH,
    }
)


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _late_hint(schedule: HrWorkSchedule | None) -> str:
    if schedule and schedule.start_time:
        parts = schedule.start_time.split(":")
        if len(parts) >= 2:
            hour = int(parts[0])
            minute = parts[1]
            suffix = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            if display_hour == 0:
                display_hour = 12
            return f"After {display_hour:02d}:{minute} {suffix}".replace(" 0", " ").strip()
        return f"After {schedule.start_time}"
    return "After shift start"


async def _build_hr_workforce(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
) -> tuple[set[PydanticObjectId], dict[PydanticObjectId, PydanticObjectId | None]]:
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()

    workforce: set[PydanticObjectId] = set()
    dept_by_user: dict[PydanticObjectId, PydanticObjectId | None] = {}

    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        dept_id = rec.department_id
        if department_id and dept_id != department_id:
            continue
        workforce.add(rec.user_id)
        dept_by_user[rec.user_id] = dept_id

    for emp in employee_records:
        if emp.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        if department_id and emp.department_id != department_id:
            continue
        workforce.add(emp.user_id)
        if emp.user_id not in dept_by_user:
            dept_by_user[emp.user_id] = emp.department_id

    return workforce, dept_by_user


async def get_hr_employee_attendance_page(
    scope: AccessScope,
    *,
    department_id: str | None = None,
    page: int = 1,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> HrEmployeeAttendancePageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    anchor = now.astimezone(_IST).date()
    dept_oid = to_object_id(department_id, "department_id") if department_id else None

    workforce, dept_by_user = await _build_hr_workforce(tenant_id, dept_oid)
    total_staff = len(workforce)

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_labels = {d.id: d.name or d.department_code or "—" for d in departments}

    schedule = await HrWorkSchedule.find_one(
        Eq(HrWorkSchedule.tenant_id, tenant_id),
        Eq(HrWorkSchedule.is_active, True),
    )
    late_hint = _late_hint(schedule)

    on_leave_users: set[PydanticObjectId] = set()
    if workforce:
        for req in await LeaveRequest.find(
            Eq(LeaveRequest.tenant_id, tenant_id),
            Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
            LTE(LeaveRequest.start_date, anchor),
            GTE(LeaveRequest.end_date, anchor),
        ).to_list():
            if req.employee_user_id in workforce:
                on_leave_users.add(req.employee_user_id)

    today_rows = (
        await HrEmployeeAttendanceRecord.find(
            Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
            Eq(HrEmployeeAttendanceRecord.attendance_date, anchor),
            In(HrEmployeeAttendanceRecord.employee_user_id, list(workforce)),
        ).to_list()
        if workforce
        else []
    )
    today_by_user = {r.employee_user_id: r for r in today_rows}

    present_today = 0
    late_today = 0
    absent_today = 0
    for uid in workforce:
        if uid in on_leave_users:
            continue
        row = today_by_user.get(uid)
        if row is None:
            absent_today += 1
            continue
        if row.status == EmployeeAttendanceDayStatus.LATE:
            late_today += 1
            present_today += 1
        elif row.status in _FACULTY_PRESENT or row.status in _PRESENT_STATUSES:
            present_today += 1
        elif row.status in _ABSENT_STATUSES:
            absent_today += 1
        elif row.status == EmployeeAttendanceDayStatus.ON_LEAVE:
            on_leave_users.add(uid)

    period_start = anchor - timedelta(days=_LOOKBACK_DAYS - 1)
    period_rows = (
        await HrEmployeeAttendanceRecord.find(
            Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
            GTE(HrEmployeeAttendanceRecord.attendance_date, period_start),
            LTE(HrEmployeeAttendanceRecord.attendance_date, anchor),
            In(HrEmployeeAttendanceRecord.employee_user_id, list(workforce)),
        ).to_list()
        if workforce
        else []
    )
    counts: dict[PydanticObjectId, dict[str, int]] = defaultdict(lambda: {"present": 0, "leave": 0, "absent": 0})
    for row in period_rows:
        bucket = counts[row.employee_user_id]
        if row.status in _PRESENT_STATUSES:
            bucket["present"] += 1
        elif row.status == EmployeeAttendanceDayStatus.ON_LEAVE:
            bucket["leave"] += 1
        elif row.status in _ABSENT_STATUSES:
            bucket["absent"] += 1

    users: dict[PydanticObjectId, User] = {}
    if workforce:
        for user in await User.find(In(User.id, list(workforce))).to_list():
            users[user.id] = user

    table_rows: list[HrEmployeeAttendanceTableRow] = []
    for uid in sorted(workforce, key=lambda u: (users.get(u).full_name if users.get(u) else str(u))):
        user = users.get(uid)
        name = user.full_name if user and user.full_name else (user.email if user else str(uid))
        dept_id = dept_by_user.get(uid)
        dept_label = dept_labels.get(dept_id, "—") if dept_id else "—"
        c = counts[uid]
        denom = c["present"] + c["leave"] + c["absent"]
        rate = round((c["present"] / denom) * 100, 0) if denom else None
        table_rows.append(
            HrEmployeeAttendanceTableRow(
                employee_user_id=str(uid),
                employee_name=name,
                department_label=dept_label,
                present_count=c["present"],
                leave_count=c["leave"],
                absent_count=c["absent"],
                attendance_rate_pct=rate,
            ),
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total = len(table_rows)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 0
    start = (page - 1) * page_size
    visible = table_rows[start : start + page_size]

    present_pct = round((present_today / total_staff) * 100, 1) if total_staff else 0.0

    kpis = [
        UserDashboardKpi(
            key="present_today",
            label="Present today",
            value=f"{present_today:,}",
            hint_line=f"{present_pct}%",
            hint_tone="success" if present_pct >= 90 else "warning",
        ),
        UserDashboardKpi(
            key="on_leave",
            label="On leave",
            value=f"{len(on_leave_users):,}",
            hint_line="Approved today",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="absent",
            label="Absent",
            value=f"{absent_today:,}",
            hint_line="Unmarked",
            hint_tone="error" if absent_today else "neutral",
        ),
        UserDashboardKpi(
            key="late_arrivals",
            label="Late arrivals",
            value=f"{late_today:,}",
            hint_line=late_hint,
            hint_tone="warning" if late_today else "neutral",
        ),
    ]

    showing_end = min(total, start + len(visible)) if total else 0
    footer_label = f"Showing {showing_end} of {total}"

    return HrEmployeeAttendancePageRead(
        page_title="Employee Attendance",
        page_subtitle="Staff attendance and late arrivals",
        export_label="Export",
        sub_nav=HR_ATTENDANCE_LEAVE_SUB_NAV,
        kpis=kpis,
        attendance_table_title="Attendance",
        attendance_table_headers=["Employee", "Department", "Present", "Leave", "Absent", "Rate"],
        attendance_rows=visible,
        table_footer_label=footer_label,
        table_pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages) if total_pages else [],
            has_previous=page > 1,
            has_next=page < total_pages if total_pages else False,
        ),
        footer_disclaimer="Live institutional data · Employee attendance · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )