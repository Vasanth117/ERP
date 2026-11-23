"""Attendance administration overview dashboard (CA 08.01)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, In, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceCorrectionRequest, AttendanceSession
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.attendance_overview_service import (
    _ACTIVE_EMPLOYMENT,
    _FACULTY_PRESENT,
    _is_teaching_employee,
    get_attendance_overview,
)
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyRecord
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AttendanceDashboardDepartmentRow,
    AttendanceDashboardPageRead,
    AttendanceDashboardTrendPoint,
    StudentAdminDashboardFilterOption,
    StudentAdminWorkQueueItem,
    UserDashboardKpi,
)
from app.modules.faculty.models import FacultyProfile
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceRecord
from app.modules.hr.enums import EmployeeAttendanceDayStatus, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_FACULTY_LOOKBACK_DAYS = 30


def _fmt_time_label(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _fmt_snapshot(now: datetime) -> str:
    local = now.astimezone(_IST)
    return local.strftime("Snapshot · %d %b %Y, %H:%M IST")


def _term_label(semester_label: str | None, academic_year_label: str | None) -> str:
    ay = (academic_year_label or "—").replace("-", "–")
    sem = semester_label or "Current term"
    return f"{sem} {ay}"


def _page_subtitle(semester_label: str | None, academic_year_label: str | None, anchor: date) -> str:
    return f"{_term_label(semester_label, academic_year_label)} · to {anchor.strftime('%d %b %Y')}"


def _trend_from_today_semester(today_pct: float | None, semester_pct: float | None) -> tuple[str, str, str]:
    if today_pct is None or semester_pct is None:
        return "flat", "—", "muted"
    delta = round(today_pct - semester_pct, 1)
    if delta >= 0.3:
        return "up", f"Up {abs(delta):g}%", "success"
    if delta <= -0.3:
        return "down", f"Down {abs(delta):g}%", "warning"
    return "flat", "Stable", "muted"


def _parse_term_key(term_key: str | None) -> tuple[str | None, str | None]:
    if not term_key or "|" not in term_key:
        return None, None
    ay, sem = term_key.split("|", 1)
    return ay.strip() or None, sem.strip() or None


def _term_key(ay: str | None, sem: str | None) -> str:
    return f"{ay or ''}|{sem or ''}"


async def _faculty_period_attendance_pct(
    tenant_id: PydanticObjectId,
    *,
    anchor: date,
    department_id: PydanticObjectId | None,
    lookback_days: int,
) -> float | None:
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    faculty_profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).to_list()
    profile_by_faculty = {p.user_id: p for p in faculty_profiles}
    workforce: set[PydanticObjectId] = set()
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        profile = profile_by_faculty.get(rec.user_id)
        dept_id = rec.department_id or (profile.department_id if profile else None)
        if department_id and dept_id != department_id:
            continue
        workforce.add(rec.user_id)
    for emp in employee_records:
        if emp.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        if not _is_teaching_employee(emp.employment_type, emp.designation):
            continue
        if department_id and emp.department_id != department_id:
            continue
        workforce.add(emp.user_id)
    if not workforce:
        return None

    start = anchor - timedelta(days=lookback_days - 1)
    rows = await HrEmployeeAttendanceRecord.find(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        GTE(HrEmployeeAttendanceRecord.attendance_date, start),
        LTE(HrEmployeeAttendanceRecord.attendance_date, anchor),
        In(HrEmployeeAttendanceRecord.employee_user_id, list(workforce)),
    ).to_list()
    if not rows:
        return None

    on_leave: set[tuple[PydanticObjectId, date]] = set()
    for req in await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
    ).to_list():
        if req.employee_user_id not in workforce:
            continue
        d = max(start, req.start_date)
        while d <= min(anchor, req.end_date):
            on_leave.add((req.employee_user_id, d))
            d += timedelta(days=1)

    present = 0
    total = 0
    for row in rows:
        if (row.employee_user_id, row.attendance_date) in on_leave:
            continue
        if row.status in _FACULTY_PRESENT:
            present += 1
            total += 1
        elif row.status in (
            EmployeeAttendanceDayStatus.ABSENT,
            EmployeeAttendanceDayStatus.MISSING,
            EmployeeAttendanceDayStatus.INCOMPLETE,
            EmployeeAttendanceDayStatus.MISSING_PUNCH,
        ):
            total += 1
        elif row.status == EmployeeAttendanceDayStatus.ON_LEAVE:
            continue
        else:
            present += 1
            total += 1
    return round((present / total) * 100, 1) if total else None


async def get_attendance_dashboard_page(
    scope: AccessScope,
    *,
    term_key: str | None = None,
    department_id: str | None = None,
) -> AttendanceDashboardPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    anchor = now.date()

    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    ay_override, sem_override = _parse_term_key(term_key)
    current_ay, current_sem = await _reader.current_academic_term(tenant_id)
    ay_label = ay_override or current_ay
    sem_label = sem_override or current_sem

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    if not years and ay_label:
        years = [AcademicYear(tenant_id=tenant_id, year_code=ay_label, label=ay_label, is_current=True)]

    term_options: list[StudentAdminDashboardFilterOption] = []
    for y in years:
        label = _term_label(sem_label if y.is_current else current_sem, y.year_code)
        term_options.append(
            StudentAdminDashboardFilterOption(
                value=_term_key(y.year_code, sem_label if y.is_current else current_sem),
                label=label,
            ),
        )
    if not term_options and ay_label:
        term_options = [
            StudentAdminDashboardFilterOption(value=_term_key(ay_label, sem_label), label=_term_label(sem_label, ay_label))
        ]

    selected_term = (term_key or "").strip() or _term_key(ay_label, sem_label)

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    department_options = [StudentAdminDashboardFilterOption(value="", label="All departments")]
    for dept in sorted(departments, key=lambda d: d.name or ""):
        department_options.append(
            StudentAdminDashboardFilterOption(value=str(dept.id), label=dept.name or dept.department_code or "—"),
        )

    overview = await get_attendance_overview(
        scope,
        anchor_date=anchor,
        date_range=DashboardDateRange.MONTH,
        department_id=department_id,
        academic_year_label=ay_label,
        semester_label=sem_label,
    )

    minimum_pct = overview.kpis.semester_minimum_pct
    faculty_period_pct = await _faculty_period_attendance_pct(
        tenant_id,
        anchor=anchor,
        department_id=dept_oid,
        lookback_days=_FACULTY_LOOKBACK_DAYS,
    )
    if faculty_period_pct is None:
        faculty_period_pct = overview.kpis.today_faculty_attendance_pct

    pending_corrections = await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
    ).count()

    shortage_notices = sum(item.count for item in overview.shortage_alerts)

    session_q = [
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.session_date, anchor),
        Eq(AttendanceSession.status, AttendanceSessionStatus.DRAFT),
    ]
    sessions = await AttendanceSession.find(*session_q).to_list()
    if ay_label:
        sessions = [s for s in sessions if s.academic_year_label == ay_label]
    if sem_label:
        sessions = [s for s in sessions if s.semester_label == sem_label]
    classes_not_marked = len(sessions)

    student_pct = overview.kpis.semester_average_pct
    kpis = [
        UserDashboardKpi(
            key="student_attendance",
            label="Student attendance",
            value=f"{student_pct:g}%" if student_pct is not None else "—",
            hint_line=f"Policy {minimum_pct:g}%",
            hint_tone="success" if student_pct is not None and student_pct >= minimum_pct else "warning",
        ),
        UserDashboardKpi(
            key="faculty_attendance",
            label="Faculty attendance",
            value=f"{faculty_period_pct:g}%" if faculty_period_pct is not None else "—",
            hint_line="Last 30 days",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="below_minimum",
            label=f"Below {minimum_pct:g}%",
            value=str(overview.kpis.students_below_minimum),
            hint_line="Students",
            hint_tone="error",
        ),
        UserDashboardKpi(
            key="pending_corrections",
            label="Pending corrections",
            value=str(pending_corrections),
            hint_line="Awaiting approval",
            hint_tone="warning",
        ),
    ]

    dept_rows: list[AttendanceDashboardDepartmentRow] = []
    for row in overview.department_rows:
        direction, trend_label, tone = _trend_from_today_semester(row.today_pct, row.semester_avg_pct)
        dept_rows.append(
            AttendanceDashboardDepartmentRow(
                department_id=row.department_id,
                department_name=row.department_name,
                student_count=row.student_count,
                average_pct=row.semester_avg_pct,
                below_minimum_count=row.below_minimum_count,
                trend_direction=direction,
                trend_label=trend_label,
                trend_tone=tone,
            ),
        )

    trend_series = [
        AttendanceDashboardTrendPoint(date_label=point.label, attendance_pct=point.attendance_pct)
        for point in overview.daily_student_attendance
    ]

    needs_attention = [
        StudentAdminWorkQueueItem(
            key="shortage_notices",
            title="Shortage notices due",
            subtitle="students",
            count=shortage_notices,
            href="/college-admin/attendance/attendance-shortage-report",
            action_label="Open →",
            icon_slug="triangle-alert",
        ),
        StudentAdminWorkQueueItem(
            key="corrections_waiting",
            title="Corrections waiting",
            subtitle="requests",
            count=pending_corrections,
            href="/college-admin/attendance/attendance-correction-requests",
            action_label="Open →",
            icon_slug="clock",
        ),
        StudentAdminWorkQueueItem(
            key="classes_not_marked",
            title="Classes not marked",
            subtitle="today",
            count=classes_not_marked,
            href="/college-admin/attendance/missing-submissions",
            action_label="Open →",
            icon_slug="triangle-alert",
        ),
    ]

    visible = len(dept_rows)
    total = overview.department_rows_total

    return AttendanceDashboardPageRead(
        page_title="Attendance Dashboard",
        page_subtitle=_page_subtitle(sem_label, ay_label, anchor),
        export_label="Export",
        open_reports_label="Open reports",
        open_reports_href="/college-admin/attendance/attendance-reports",
        term_filter_label="Academic term",
        department_filter_label="Department",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        term_options=term_options,
        department_options=department_options,
        selected_term_key=selected_term,
        selected_department_id=department_id or "",
        kpis=kpis,
        department_table_title="Department-wise attendance",
        department_table_headers=["Department", "Students", "Average", f"Below {minimum_pct:g}%", "Trend"],
        department_rows=dept_rows,
        department_table_footer_label=f"{visible} of {total} departments",
        trend_chart_title="Attendance trend",
        trend_series=trend_series,
        needs_attention_title="Needs attention",
        needs_attention_items=needs_attention,
        footer_disclaimer="Live institutional data · Student and faculty attendance · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )