"""HR employee management directory (CA 11.02)."""

from __future__ import annotations

import math
from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.employee_directory_page_service import _matches_search, _page_numbers
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.faculty_employee_dashboard_page_service import _employee_active
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    EmployeeDirectoryPageRead,
    EmployeeDirectoryTableRow,
    PoliciesPagination,
    UserListFilterOption,
)
from app.modules.hr.employment_change_models import HrContractRecord

_PAGE_SIZE = 4
_CONTRACT_WARNING_DAYS = 60

_TYPE_FILTERS: list[tuple[str, str]] = [
    ("", "All types"),
    ("permanent", "Permanent"),
    ("probation", "Probation"),
    ("contract", "Contract"),
]

_STATUS_FILTERS: list[tuple[str, str]] = [
    ("", "All statuses"),
    ("active", "Active"),
    ("probation", "Probation"),
    ("notice", "Notice"),
    ("on_leave", "On leave"),
]

_TABLE_HEADERS = ["Employee", "ID", "Department", "Designation", "Type", "Status"]


def _hr_type_label(emp: EmployeeRecord) -> str:
    if emp.employment_status == FacultyEmploymentStatus.PROBATION:
        return "Probation"
    blob = f"{emp.employment_type or ''}".lower()
    if any(k in blob for k in ("contract", "temporary", "visiting", "adhoc", "guest")):
        return "Contract"
    return "Permanent"


def _hr_type_key(emp: EmployeeRecord) -> str:
    label = _hr_type_label(emp)
    return label.lower()


def _hr_status(
    employment_status: FacultyEmploymentStatus,
    *,
    contract_ending: bool,
) -> tuple[str, str, str]:
    if employment_status == FacultyEmploymentStatus.NOTICE_PERIOD:
        return "notice", "Notice", "warning"
    if employment_status == FacultyEmploymentStatus.PROBATION:
        return "probation", "Probation", "info"
    if employment_status == FacultyEmploymentStatus.ON_LEAVE:
        return "on_leave", "On leave", "muted"
    if contract_ending:
        return "contract_ends", "Contract ends", "warning"
    if employment_status in (FacultyEmploymentStatus.ACTIVE, FacultyEmploymentStatus.CONFIRMED):
        return "active", "Active", "success"
    label = employment_status.value.replace("_", " ").title()
    return employment_status.value, label, "muted"


def _empty_shell(now, departments: list[InstitutionDepartment]) -> EmployeeDirectoryPageRead:
    dept_options = [UserListFilterOption(value="", label="All departments")]
    for dept in sorted(departments, key=lambda d: (d.name or "").lower()):
        dept_options.append(UserListFilterOption(value=str(dept.id), label=dept.name or dept.department_code or "—"))
    return EmployeeDirectoryPageRead(
        page_title="Employee Management",
        page_subtitle="Directory, status and records",
        export_label="Export",
        add_employee_label="Add employee",
        add_employee_href="/college-admin/faculty/add-new-faculty-employee",
        search_placeholder="Search name, ID or department",
        unit_filter_label="Department",
        role_filter_label="Designation",
        type_filter_label="Type",
        status_filter_label="Status",
        unit_options=dept_options,
        role_options=[UserListFilterOption(value="", label="All designations")],
        type_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _TYPE_FILTERS],
        status_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS],
        employees_section_title="Employees",
        employees_count_label="0 employees",
        table_headers=_TABLE_HEADERS,
        employee_rows=[],
        showing_label="Showing 0 of 0",
        pagination=PoliciesPagination(
            page=1,
            page_size=_PAGE_SIZE,
            total=0,
            total_pages=0,
            page_numbers=[],
            has_previous=False,
            has_next=False,
        ),
        footer_disclaimer="Live institutional data · HR employee records",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_hr_employee_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    department_id: str | None = None,
    type_filter: str | None = None,
    status_filter: str | None = None,
) -> EmployeeDirectoryPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.date()

    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    type_key = (type_filter or "").strip().lower() or None
    status_key = (status_filter or "").strip().lower() or None
    search_q = (search or "").strip()

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_by_id = {d.id: d for d in departments}

    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).sort("-updated_at").to_list()
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    faculty_by_user = {f.user_id: f for f in faculty_records}

    seen_users: set[PydanticObjectId] = set()
    rows_source: list[tuple[EmployeeRecord, FacultyRecord | None]] = []

    active_statuses = {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
        FacultyEmploymentStatus.NOTICE_PERIOD,
    }

    for emp in employees:
        if emp.employment_status not in active_statuses:
            continue
        seen_users.add(emp.user_id)
        rows_source.append((emp, faculty_by_user.get(emp.user_id)))

    for faculty in faculty_records:
        if faculty.user_id in seen_users:
            continue
        if not _employee_active(faculty.employment_status):
            continue
        virtual = EmployeeRecord(
            tenant_id=tenant_id,
            user_id=faculty.user_id,
            employee_id=faculty.faculty_code,
            designation=faculty.designation,
            department_id=faculty.department_id,
            employment_status=faculty.employment_status,
            is_faculty=True,
        )
        rows_source.append((virtual, faculty))

    user_ids = list({emp.user_id for emp, _ in rows_source})
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    contracts = await HrContractRecord.find(
        Eq(HrContractRecord.tenant_id, tenant_id),
        Eq(HrContractRecord.status, "active"),
    ).to_list()
    contract_horizon = today + timedelta(days=_CONTRACT_WARNING_DAYS)
    contract_ending_users = {
        c.employee_user_id
        for c in contracts
        if c.end_date and today <= c.end_date <= contract_horizon
    }

    built: list[EmployeeDirectoryTableRow] = []

    for emp, faculty in rows_source:
        if dept_oid and emp.department_id != dept_oid:
            continue
        user = user_by_id.get(emp.user_id)
        dept = dept_by_id.get(emp.department_id) if emp.department_id else None
        department_name = dept.name if dept else "—"
        designation = emp.designation or (faculty.designation if faculty else None) or "—"
        emp_id = emp.employee_id or (faculty.faculty_code if faculty else None) or "—"

        if not _matches_search(
            query=search_q,
            user=user,
            employee_id=emp_id,
            unit_name=department_name,
            role=designation,
        ):
            continue

        if type_key and _hr_type_key(emp) != type_key:
            continue

        contract_ending = emp.user_id in contract_ending_users
        filter_key, status_label, status_tone = _hr_status(
            emp.employment_status,
            contract_ending=contract_ending,
        )
        if status_key and filter_key != status_key:
            continue

        if faculty and faculty.id:
            row_record_id = str(faculty.id)
        else:
            row_record_id = str(emp.id) if emp.id else str(emp.user_id)

        detail_href = f"/college-admin/hr/employee-detail?record_id={row_record_id}"

        built.append(
            EmployeeDirectoryTableRow(
                record_id=row_record_id,
                employee_name=user.full_name if user else "—",
                employee_id_label=emp_id,
                unit_label=department_name,
                role_label=designation,
                type_label=_hr_type_label(emp),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=detail_href,
            )
        )

    built.sort(key=lambda r: r.employee_name.lower())
    total = len(built)

    page = max(1, page)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    start = (page - 1) * _PAGE_SIZE
    paged = built[start : start + _PAGE_SIZE]
    showing_end = min(total, start + len(paged)) if total else 0

    dept_options = [UserListFilterOption(value="", label="All departments")]
    for dept in sorted(departments, key=lambda d: (d.name or "").lower()):
        dept_options.append(UserListFilterOption(value=str(dept.id), label=dept.name or dept.department_code or "—"))

    if not rows_source:
        shell = _empty_shell(now, departments)
        return shell

    return EmployeeDirectoryPageRead(
        page_title="Employee Management",
        page_subtitle="Directory, status and records",
        export_label="Export",
        add_employee_label="Add employee",
        add_employee_href="/college-admin/faculty/add-new-faculty-employee",
        search_placeholder="Search name, ID or department",
        unit_filter_label="Department",
        role_filter_label="Designation",
        type_filter_label="Type",
        status_filter_label="Status",
        unit_options=dept_options,
        role_options=[UserListFilterOption(value="", label="All designations")],
        type_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _TYPE_FILTERS],
        status_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS],
        employees_section_title="Employees",
        employees_count_label=f"{total:,} employees",
        table_headers=_TABLE_HEADERS,
        employee_rows=paged,
        showing_label=f"Showing {showing_end} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · HR employee records",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )