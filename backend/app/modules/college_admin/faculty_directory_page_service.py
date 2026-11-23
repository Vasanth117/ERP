"""Faculty directory list page (CA 07.02)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyEmploymentStatus,
    FacultyRecord,
    FacultyWorkloadRecord,
)
from app.modules.college_admin.faculty_employee_dashboard_page_service import (
    _OVERLOAD_HOURS,
    _employee_active,
    _page_numbers,
    _status_for_row,
    _workload_label,
)
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FacultyDirectoryPageRead,
    FacultyDirectoryTableRow,
    PoliciesPagination,
    UserListFilterOption,
)

_PAGE_SIZE = 5
_reader = OperationalDataReader()

_STATUS_FILTERS: list[tuple[str, str]] = [
    ("", "All statuses"),
    ("active", "Active"),
    ("probation", "Probation"),
    ("overloaded", "Overloaded"),
    ("on_leave", "On leave"),
]


def _status_filter_key(
    employment_status: FacultyEmploymentStatus,
    workload_hours: float | None,
) -> str:
    if workload_hours is not None and workload_hours > _OVERLOAD_HOURS:
        return "overloaded"
    if employment_status == FacultyEmploymentStatus.PROBATION:
        return "probation"
    if employment_status == FacultyEmploymentStatus.ON_LEAVE:
        return "on_leave"
    if employment_status in (FacultyEmploymentStatus.ACTIVE, FacultyEmploymentStatus.CONFIRMED):
        return "active"
    return employment_status.value


def _matches_search(
    *,
    query: str,
    user: User | None,
    employee_id: str,
    department_name: str,
    designation: str,
) -> bool:
    if not query:
        return True
    q = query.lower()
    blobs = [
        user.full_name if user else "",
        user.email if user else "",
        employee_id,
        department_name,
        designation,
    ]
    return any(q in (value or "").lower() for value in blobs)


def _empty_page(now) -> FacultyDirectoryPageRead:
    empty_pagination = PoliciesPagination(
        page=1,
        page_size=_PAGE_SIZE,
        total=0,
        total_pages=0,
        page_numbers=[],
        has_previous=False,
        has_next=False,
    )
    return FacultyDirectoryPageRead(
        page_title="Faculty Directory",
        page_subtitle="All teaching staff",
        export_label="Export",
        add_faculty_label="Add faculty",
        add_faculty_href="/college-admin/faculty/add-new-faculty-employee",
        search_placeholder="Search name, ID or department",
        department_filter_label="Department",
        designation_filter_label="Designation",
        status_filter_label="Status",
        department_options=[UserListFilterOption(value="", label="All departments")],
        designation_options=[UserListFilterOption(value="", label="All designations")],
        status_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS],
        faculty_section_title="Faculty",
        faculty_count_label="0 faculty",
        table_headers=["Faculty", "ID", "Department", "Designation", "Workload", "Status"],
        faculty_rows=[],
        showing_label="Showing 0 of 0",
        pagination=empty_pagination,
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_faculty_directory_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    department_id: str | None = None,
    designation: str | None = None,
    status_filter: str | None = None,
    academic_year_code: str | None = None,
) -> FacultyDirectoryPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    designation_filter = (designation or "").strip().lower() or None
    status_key_filter = (status_filter or "").strip().lower() or None
    search_q = (search or "").strip()

    current_year_label, _ = await _reader.current_academic_term(tenant_id)
    selected_ay = academic_year_code or current_year_label or ""

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_by_id = {d.id: d for d in departments}

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).sort("-updated_at").to_list()
    if not faculty_records:
        return _empty_page(now)

    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    employee_by_user = {e.user_id: e for e in employee_records}

    workload_rows = await FacultyWorkloadRecord.find(
        Eq(FacultyWorkloadRecord.tenant_id, tenant_id),
        Eq(FacultyWorkloadRecord.academic_year_label, selected_ay),
    ).to_list() if selected_ay else []
    workload_by_user: dict[PydanticObjectId, float] = {}
    for row in workload_rows:
        hours = row.total_hours or (row.lecture_hours + row.lab_hours + row.tutorial_hours)
        prev = workload_by_user.get(row.user_id)
        if prev is None or hours >= prev:
            workload_by_user[row.user_id] = hours

    user_ids = list({r.user_id for r in faculty_records})
    users = await User.find(In(User.id, user_ids)).to_list()
    user_by_id = {u.id: u for u in users}

    designation_values: set[str] = set()
    built_rows: list[tuple[FacultyDirectoryTableRow, str]] = []

    for rec in faculty_records:
        if not _employee_active(rec.employment_status):
            continue
        if dept_oid and rec.department_id != dept_oid:
            continue
        user = user_by_id.get(rec.user_id)
        emp = employee_by_user.get(rec.user_id)
        dept = dept_by_id.get(rec.department_id) if rec.department_id else None
        dept_name = dept.name if dept else "—"
        desig = rec.designation or "—"
        if designation_filter and desig.lower() != designation_filter:
            continue

        if desig and desig != "—":
            designation_values.add(desig)

        emp_id = (emp.employee_id if emp and emp.employee_id else None) or rec.faculty_code or "—"
        if not _matches_search(
            query=search_q,
            user=user,
            employee_id=emp_id,
            department_name=dept_name,
            designation=desig,
        ):
            continue

        hours = workload_by_user.get(rec.user_id)
        filter_key = _status_filter_key(rec.employment_status, hours)
        if status_key_filter and filter_key != status_key_filter:
            continue

        status_label, status_tone = _status_for_row(employment_status=rec.employment_status, workload_hours=hours)
        record_id = str(rec.id)
        row = FacultyDirectoryTableRow(
            record_id=record_id,
            faculty_name=user.full_name if user else "—",
            employee_id_label=emp_id,
            department_label=dept_name,
            designation_label=desig,
            workload_label=_workload_label(hours),
            status_label=status_label,
            status_tone=status_tone,
            detail_href=f"/college-admin/faculty/faculty-profile?id={record_id}",
        )
        built_rows.append((row, user.full_name if user else ""))

    built_rows.sort(key=lambda pair: pair[1].lower())
    table_rows = [pair[0] for pair in built_rows]
    total = len(table_rows)

    page = max(1, page)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    start = (page - 1) * _PAGE_SIZE
    paged = table_rows[start : start + _PAGE_SIZE]

    department_options = [UserListFilterOption(value="", label="All departments")]
    for dept in sorted(departments, key=lambda d: (d.name or "").lower()):
        department_options.append(UserListFilterOption(value=str(dept.id), label=dept.name or dept.department_code))

    designation_options = [UserListFilterOption(value="", label="All designations")]
    for des in sorted(designation_values, key=str.lower):
        designation_options.append(UserListFilterOption(value=des.lower(), label=des))

    showing_label = f"Showing {len(paged)} of {total:,}" if total else "Showing 0 of 0"

    return FacultyDirectoryPageRead(
        page_title="Faculty Directory",
        page_subtitle="All teaching staff",
        export_label="Export",
        add_faculty_label="Add faculty",
        add_faculty_href="/college-admin/faculty/add-new-faculty-employee",
        search_placeholder="Search name, ID or department",
        department_filter_label="Department",
        designation_filter_label="Designation",
        status_filter_label="Status",
        department_options=department_options,
        designation_options=designation_options,
        status_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS],
        faculty_section_title="Faculty",
        faculty_count_label=f"{total:,} faculty",
        table_headers=["Faculty", "ID", "Department", "Designation", "Workload", "Status"],
        faculty_rows=paged,
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )