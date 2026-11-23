"""Chart series for the college admin main dashboard overview."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.modules.college_admin.attendance_overview_service import get_attendance_overview
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.finance_overview_service import get_finance_overview
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CollegeDashboardAttendanceTrendPoint,
    CollegeDashboardFeeMonthPoint,
)
from app.modules.faculty.models import FacultyProfile
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceRecord
from app.modules.hr.enums import EmployeeAttendanceDayStatus, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest

_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
)

_FACULTY_PRESENT = frozenset(
    {
        EmployeeAttendanceDayStatus.PRESENT,
        EmployeeAttendanceDayStatus.LATE,
        EmployeeAttendanceDayStatus.WORK_FROM_HOME,
        EmployeeAttendanceDayStatus.HALF_DAY,
        EmployeeAttendanceDayStatus.EARLY_DEPARTURE,
    }
)


def _is_teaching_employee(employment_type: str | None, designation: str | None) -> bool:
    blob = f"{employment_type or ''} {designation or ''}".lower()
    if not blob.strip():
        return True
    return any(k in blob for k in ("faculty", "professor", "lecturer", "teaching", "academic"))


def _faculty_counts_for_day(
    workforce: set[PydanticObjectId],
    att_by_user: dict[PydanticObjectId, HrEmployeeAttendanceRecord],
    on_leave_users: set[PydanticObjectId],
) -> tuple[int, int]:
    if not workforce:
        return 0, 0
    present = 0
    for uid in workforce:
        if uid in on_leave_users:
            continue
        row = att_by_user.get(uid)
        if row and row.status in _FACULTY_PRESENT:
            present += 1
        elif row and row.status == EmployeeAttendanceDayStatus.ON_LEAVE:
            continue
        elif row is None:
            continue
        elif row.status not in (
            EmployeeAttendanceDayStatus.ABSENT,
            EmployeeAttendanceDayStatus.MISSING,
            EmployeeAttendanceDayStatus.INCOMPLETE,
            EmployeeAttendanceDayStatus.MISSING_PUNCH,
        ):
            present += 1
    return present, len(workforce)


async def _faculty_pct_by_dates(
    tenant_id: PydanticObjectId,
    dates: list[date],
    *,
    department_id: str | None,
) -> dict[date, float | None]:
    if not dates:
        return {}
    dept_oid = to_object_id(department_id, "department_id") if department_id else None

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    faculty_profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).to_list()
    profile_by_faculty = {p.user_id: p for p in faculty_profiles}

    workforce: set[PydanticObjectId] = set()
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        profile = profile_by_faculty.get(rec.user_id)
        if dept_oid and profile and profile.department_id != dept_oid:
            continue
        workforce.add(rec.user_id)
    for emp in employee_records:
        if emp.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        if not _is_teaching_employee(emp.employment_type, emp.designation):
            continue
        if dept_oid and emp.department_id != dept_oid:
            continue
        workforce.add(emp.user_id)

    if not workforce:
        return {day: None for day in dates}

    attendance_rows = await HrEmployeeAttendanceRecord.find(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        In(HrEmployeeAttendanceRecord.attendance_date, dates),
        In(HrEmployeeAttendanceRecord.employee_user_id, list(workforce)),
    ).to_list()
    att_by_date_user: dict[tuple[date, PydanticObjectId], HrEmployeeAttendanceRecord] = {}
    for row in attendance_rows:
        att_by_date_user[(row.attendance_date, row.employee_user_id)] = row

    leave_rows = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
    ).to_list()

    out: dict[date, float | None] = {}
    for day in dates:
        on_leave_users = {
            req.employee_user_id
            for req in leave_rows
            if req.start_date <= day <= req.end_date and req.employee_user_id in workforce
        }
        att_by_user = {
            uid: row
            for (d, uid), row in att_by_date_user.items()
            if d == day
        }
        present, total = _faculty_counts_for_day(workforce, att_by_user, on_leave_users)
        out[day] = round((present / total) * 100, 1) if total else None
    return out


_OVERVIEW_TREND_MAX_POINTS = 8


def _monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _compress_attendance_trend_for_overview(
    daily: list[tuple[date, float | None, float | None]],
    *,
    max_points: int = _OVERVIEW_TREND_MAX_POINTS,
) -> list[CollegeDashboardAttendanceTrendPoint]:
    """Roll up many session days into weekly averages for a readable overview chart."""
    if not daily:
        return []
    if len(daily) <= max_points:
        return [
            CollegeDashboardAttendanceTrendPoint(
                label=day.strftime("%d %b"),
                students_pct=student,
                faculty_pct=faculty,
            )
            for day, student, faculty in daily
        ]

    by_week: dict[date, list[tuple[float | None, float | None]]] = defaultdict(list)
    for day, student, faculty in daily:
        by_week[_monday_of_week(day)].append((student, faculty))

    week_starts = sorted(by_week.keys())
    if len(week_starts) > max_points:
        week_starts = week_starts[-max_points:]

    out: list[CollegeDashboardAttendanceTrendPoint] = []
    for week_start in week_starts:
        bucket = by_week[week_start]
        student_vals = [s for s, _ in bucket if s is not None]
        faculty_vals = [f for _, f in bucket if f is not None]
        week_end = week_start + timedelta(days=6)
        if week_start.month == week_end.month:
            label = f"{week_start.day}–{week_end.day} {week_start.strftime('%b')}"
        else:
            label = f"{week_start.strftime('%d %b')}–{week_end.strftime('%d %b')}"
        out.append(
            CollegeDashboardAttendanceTrendPoint(
                label=label,
                students_pct=round(mean(student_vals), 1) if student_vals else None,
                faculty_pct=round(mean(faculty_vals), 1) if faculty_vals else None,
            )
        )
    return out


async def load_college_dashboard_chart_series(
    scope: AccessScope,
    *,
    anchor_date: date,
    date_range: DashboardDateRange,
    department_id: str | None,
    campus_id: str | None,
    academic_year_label: str | None,
) -> tuple[list[CollegeDashboardAttendanceTrendPoint], list[CollegeDashboardFeeMonthPoint]]:
    tenant_id = require_college_tenant_scope(scope)

    attendance_read = await get_attendance_overview(
        scope,
        anchor_date=anchor_date,
        date_range=date_range,
        department_id=department_id,
        campus_id=campus_id,
        academic_year_label=academic_year_label,
    )
    session_dates = [point.session_date for point in attendance_read.daily_student_attendance]
    faculty_by_date = await _faculty_pct_by_dates(
        tenant_id,
        session_dates,
        department_id=department_id,
    )

    daily_rows = [
        (
            point.session_date,
            point.attendance_pct,
            faculty_by_date.get(point.session_date),
        )
        for point in attendance_read.daily_student_attendance
    ]
    attendance_trend = _compress_attendance_trend_for_overview(daily_rows)

    finance_read = await get_finance_overview(scope, academic_year_label=academic_year_label)
    fee_monthly_collection = [
        CollegeDashboardFeeMonthPoint(
            year=point.year,
            month=point.month,
            label=point.label,
            amount_inr=point.amount_inr,
            is_month_to_date=point.is_month_to_date,
        )
        for point in finance_read.monthly_collection
    ]

    return attendance_trend, fee_monthly_collection