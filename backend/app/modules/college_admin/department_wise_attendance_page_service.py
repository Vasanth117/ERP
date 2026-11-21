"""Department-wise student attendance (CA 08.05)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.attendance_dashboard_page_service import (
    _parse_term_key,
    _term_key,
    _term_label,
    _trend_from_today_semester,
)
from app.modules.college_admin.attendance_overview_service import get_attendance_overview
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AttendanceDashboardDepartmentRow,
    DepartmentWiseAttendanceBarItem,
    DepartmentWiseAttendancePageRead,
    StudentAdminDashboardFilterOption,
)

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_TABLE_LIMIT = 12


def _fmt_time_label(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


async def get_department_wise_attendance_page(
    scope: AccessScope,
    *,
    term_key: str | None = None,
) -> DepartmentWiseAttendancePageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    ay_override, sem_override = _parse_term_key(term_key)
    current_ay, current_sem = await _reader.current_academic_term(tenant_id)
    ay_label = ay_override or current_ay
    sem_label = sem_override or current_sem

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
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

    overview = await get_attendance_overview(
        scope,
        date_range=DashboardDateRange.SEMESTER,
        academic_year_label=ay_label,
        semester_label=sem_label,
    )
    minimum_pct = overview.kpis.semester_minimum_pct

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    code_by_id = {str(d.id): (d.department_code or d.name[:4].upper()) for d in departments}

    dept_rows: list[AttendanceDashboardDepartmentRow] = []
    bars: list[DepartmentWiseAttendanceBarItem] = []
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
        short = code_by_id.get(row.department_id, row.department_code or "—")
        bars.append(
            DepartmentWiseAttendanceBarItem(
                department_code=short,
                department_name=row.department_name,
                average_pct=row.semester_avg_pct,
            ),
        )

    total = overview.department_rows_total
    visible = len(dept_rows)

    return DepartmentWiseAttendancePageRead(
        page_title="Department-wise Attendance",
        page_subtitle="Compare departments",
        export_label="Export",
        term_filter_label="Academic term",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        term_options=term_options,
        selected_term_key=_term_key(ay_label, sem_label),
        department_table_title="Department-wise attendance",
        department_table_headers=["Department", "Students", "Average", f"Below {minimum_pct:g}%", "Trend"],
        department_rows=dept_rows[:_TABLE_LIMIT],
        department_table_footer_label=f"{min(visible, _TABLE_LIMIT)} of {total} departments",
        bars_section_title="Average by department",
        department_bars=bars[:_TABLE_LIMIT],
        footer_disclaimer="Live institutional data · Student attendance · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )