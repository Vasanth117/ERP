"""Employee directory list page (CA 07.04)."""

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
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.faculty_employee_dashboard_page_service import _employee_active, _page_numbers
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    EmployeeDirectoryPageRead,
    EmployeeDirectoryTableRow,
    PoliciesPagination,
    UserListFilterOption,
)
from app.modules.hr.employment_change_models import HrContractRecord

_PAGE_SIZE = 5
_CONTRACT_WARNING_DAYS = 60

_ACTIVE_LISTING = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
        FacultyEmploymentStatus.NOTICE_PERIOD,
    }
)

_TYPE_FILTERS: list[tuple[str, str]] = [
    ("", "All types"),
    ("staff", "Staff"),
    ("contract", "Contract"),
    ("faculty", "Faculty"),
]

_STATUS_FILTERS: list[tuple[str, str]] = [
    ("", "All statuses"),
    ("active", "Active"),
    ("contract_ends", "Contract ends"),
    ("on_leave", "On leave"),
    ("probation", "Probation"),
]


def _listing_active(status: FacultyEmploymentStatus) -> bool:
    return status in _ACTIVE_LISTING


def _type_label(emp: EmployeeRecord) -> str:
    if emp.is_faculty:
        return "Faculty"
    blob = (emp.employment_type or "").lower()
    if any(k in blob for k in ("contract", "temporary", "visiting", "adhoc", "guest")):
        return "Contract"
    return "Staff"


def _type_filter_key(emp: EmployeeRecord) -> str:
    label = _type_label(emp)
    if label == "Faculty":
        return "faculty"
    if label == "Contract":
        return "contract"
    return "staff"


def _matches_search(
    *,
    query: str,
    user: User | None,
    employee_id: str,
    unit_name: str,
    role: str,
) -> bool:
    if not query:
        return True
    q = query.lower()
    blobs = [
        user.full_name if user else "",
        user.email if user else "",
        employee_id,
        unit_name,
        role,
    ]
    return any(q in (value or "").lower() for value in blobs)


def _status_presentation(
    employment_status: FacultyEmploymentStatus,
    *,
    contract_ending: bool,
) -> tuple[str, str, str]:
    if contract_ending:
        return "contract_ends", "Contract ends", "warning"
    if employment_status == FacultyEmploymentStatus.ON_LEAVE:
        return "on_leave", "On leave", "muted"
    if employment_status == FacultyEmploymentStatus.PROBATION:
        return "probation", "Probation", "info"
    if employment_status in (FacultyEmploymentStatus.ACTIVE, FacultyEmploymentStatus.CONFIRMED):
        return "active", "Active", "success"
    if employment_status == FacultyEmploymentStatus.NOTICE_PERIOD:
        return "notice", "Notice period", "warning"
    label = employment_status.value.replace("_", " ").title()
    return employment_status.value, label, "muted"


def _empty_page(now) -> EmployeeDirectoryPageRead:
    empty_pagination = PoliciesPagination(
        page=1,
        page_size=_PAGE_SIZE,
        total=0,
        total_pages=0,
        page_numbers=[],
        has_previous=False,
        has_next=False,
    )
    return EmployeeDirectoryPageRead(
        page_title="Employee Directory",
        page_subtitle="Teaching and non-teaching staff",
        export_label="Export",
        add_employee_label="Add employee",
        add_employee_href="/college-admin/faculty/add-new-faculty-employee",
        search_placeholder="Search name, ID or unit",
        unit_filter_label="Unit",
        role_filter_label="Role",
        type_filter_label="Type",
        status_filter_label="Status",
        unit_options=[UserListFilterOption(value="", label="All units")],
        role_options=[UserListFilterOption(value="", label="All roles")],
        type_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _TYPE_FILTERS],
        status_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS],
        employees_section_title="Employees",
        employees_count_label="0 employees",
        table_headers=["Employee", "ID", "Department / unit", "Role", "Type", "Status"],
        employee_rows=[],
        showing_label="Showing 0 of 0",
        pagination=empty_pagination,
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_employee_directory_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    unit_id: str | None = None,
    role: str | None = None,
    type_filter: str | None = None,
    status_filter: str | None = None,
) -> EmployeeDirectoryPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.date()

    unit_oid = to_object_id(unit_id, "unit_id") if unit_id else None
    role_filter = (role or "").strip().lower() or None
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

    for emp in employees:
        if not _listing_active(emp.employment_status):
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

    if not rows_source:
        return _empty_page(now)

    user_ids = list({emp.user_id for emp, _ in rows_source})
    users = await User.find(In(User.id, user_ids)).to_list()
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

    role_values: set[str] = set()
    built: list[EmployeeDirectoryTableRow] = []

    for emp, faculty in rows_source:
        if unit_oid and emp.department_id != unit_oid:
            continue
        user = user_by_id.get(emp.user_id)
        dept = dept_by_id.get(emp.department_id) if emp.department_id else None
        unit_name = dept.name if dept else "—"
        role_label = emp.designation or (faculty.designation if faculty else None) or "—"
        if role_filter and role_label.lower() != role_filter:
            continue
        if role_label and role_label != "—":
            role_values.add(role_label)

        emp_id = emp.employee_id or (faculty.faculty_code if faculty else None) or "—"
        if not _matches_search(query=search_q, user=user, employee_id=emp_id, unit_name=unit_name, role=role_label):
            continue

        if type_key and _type_filter_key(emp) != type_key:
            continue

        contract_ending = emp.user_id in contract_ending_users
        filter_key, status_label, status_tone = _status_presentation(
            emp.employment_status,
            contract_ending=contract_ending,
        )
        if status_key and filter_key != status_key:
            continue

        if faculty and faculty.id:
            record_id = str(faculty.id)
            detail_href = f"/college-admin/faculty/faculty-profile?id={record_id}"
            row_record_id = record_id
        else:
            row_record_id = str(emp.id) if emp.id else str(emp.user_id)
            detail_href = f"/college-admin/faculty/employee-profile-management?id={row_record_id}"

        built.append(
            EmployeeDirectoryTableRow(
                record_id=row_record_id,
                employee_name=user.full_name if user else "—",
                employee_id_label=emp_id,
                unit_label=unit_name,
                role_label=role_label,
                type_label=_type_label(emp),
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

    unit_options = [UserListFilterOption(value="", label="All units")]
    for dept in sorted(departments, key=lambda d: (d.name or "").lower()):
        unit_options.append(UserListFilterOption(value=str(dept.id), label=dept.name or dept.department_code))

    role_options = [UserListFilterOption(value="", label="All roles")]
    for r in sorted(role_values, key=str.lower):
        role_options.append(UserListFilterOption(value=r.lower(), label=r))

    return EmployeeDirectoryPageRead(
        page_title="Employee Directory",
        page_subtitle="Teaching and non-teaching staff",
        export_label="Export",
        add_employee_label="Add employee",
        add_employee_href="/college-admin/faculty/add-new-faculty-employee",
        search_placeholder="Search name, ID or unit",
        unit_filter_label="Unit",
        role_filter_label="Role",
        type_filter_label="Type",
        status_filter_label="Status",
        unit_options=unit_options,
        role_options=role_options,
        type_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _TYPE_FILTERS],
        status_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS],
        employees_section_title="Employees",
        employees_count_label=f"{total:,} employees",
        table_headers=["Employee", "ID", "Department / unit", "Role", "Type", "Status"],
        employee_rows=paged,
        showing_label=f"Showing {len(paged)} of {total:,}" if total else "Showing 0 of 0",
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