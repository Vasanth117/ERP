"""All departments list page (CA 04 — organization)."""

from __future__ import annotations

import math
from collections import defaultdict

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.identity_models import (
    DepartmentStaffAssociation,
    DepartmentStatus,
    InstitutionDepartment,
    InstitutionOrganizationUnit,
    OrganizationUnitType,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AllDepartmentsListPageRead,
    AllDepartmentsTableRow,
    PoliciesPagination,
    UserListFilterOption,
)
from app.modules.faculty.models import FacultyProfile
from app.modules.students.models import StudentProfile

_PAGE_SIZE = 10

_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
)

_ADMIN_KEYWORDS = (
    "admin",
    "administration",
    "office",
    "registry",
    "finance",
    "accounts",
    "human resource",
    " hr ",
    "examination cell",
    "library",
    "hostel",
    "transport",
    "estate",
    "placement",
)


def _department_kind(
    dept: InstitutionDepartment,
    *,
    programme_count: int,
    student_count: int,
) -> str:
    if programme_count > 0 or student_count > 0 or dept.programme_codes:
        return "academic"
    name_lower = dept.name.lower()
    if any(keyword in name_lower for keyword in _ADMIN_KEYWORDS):
        return "administrative"
    if dept.organization_unit_id:
        return "academic"
    return "administrative"


def _status_presentation(
    dept: InstitutionDepartment,
    *,
    acting: bool,
) -> tuple[str, str, str]:
    if acting and dept.status == DepartmentStatus.ACTIVE:
        return "acting_hod", "Acting HoD", "warning"
    if dept.status == DepartmentStatus.DRAFT:
        return "draft", "Draft", "warning"
    if dept.status == DepartmentStatus.ACTIVE:
        return "active", "Active", "success"
    if dept.status == DepartmentStatus.INACTIVE:
        return "inactive", "Inactive", "muted"
    return "archived", "Archived", "muted"


def _format_head(name: str | None, *, acting: bool) -> str:
    if not name:
        return "—"
    if acting:
        return f"{name} (acting)"
    return name


async def get_all_departments_list_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    school_id: str | None = None,
    type_filter: str | None = None,
    status_filter: str | None = None,
) -> AllDepartmentsListPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    school_oid = to_object_id(school_id, "school_id") if school_id else None

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
    ).sort("+name").to_list()

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_dept: dict[str, set[str]] = defaultdict(set)
    for prog in programmes:
        if not prog.is_active:
            continue
        if prog.department_id is not None:
            prog_by_dept[str(prog.department_id)].add(prog.programme_code.upper())
    for dept in departments:
        for code in dept.programme_codes:
            prog_by_dept[str(dept.id)].add(code.upper())

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    students_by_dept: dict[str, int] = defaultdict(int)
    for profile in profiles:
        if profile.department_id is None:
            continue
        students_by_dept[str(profile.department_id)] += 1

    faculty_by_dept: dict[str, int] = defaultdict(int)
    seen_faculty: set[PydanticObjectId] = set()
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT or rec.department_id is None:
            continue
        faculty_by_dept[str(rec.department_id)] += 1
        seen_faculty.add(rec.user_id)
    faculty_profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).to_list()
    for fp in faculty_profiles:
        if fp.user_id in seen_faculty or fp.department_id is None:
            continue
        faculty_by_dept[str(fp.department_id)] += 1

    acting_heads: set[str] = set()
    associations = await DepartmentStaffAssociation.find(
        Eq(DepartmentStaffAssociation.tenant_id, tenant_id),
    ).to_list()
    for assoc in associations:
        if "acting" in (assoc.association_role or "").lower():
            acting_heads.add(str(assoc.department_id))

    head_user_ids = [d.head_user_id for d in departments if d.head_user_id]
    head_users = await User.find(In(User.id, head_user_ids)).to_list() if head_user_ids else []
    head_names = {u.id: u.full_name for u in head_users}

    school_units = await InstitutionOrganizationUnit.find(
        Eq(InstitutionOrganizationUnit.tenant_id, tenant_id),
        Eq(InstitutionOrganizationUnit.unit_type, OrganizationUnitType.SCHOOL),
    ).to_list()

    academic_total = 0
    administrative_total = 0
    for dept in departments:
        if dept.status != DepartmentStatus.ACTIVE:
            continue
        pc = len(prog_by_dept.get(str(dept.id), set()))
        sc = students_by_dept.get(str(dept.id), 0)
        kind = _department_kind(dept, programme_count=pc, student_count=sc)
        if kind == "academic":
            academic_total += 1
        else:
            administrative_total += 1

    needle = (search or "").strip().lower()
    filtered: list[InstitutionDepartment] = []
    for dept in departments:
        status_code, _, _ = _status_presentation(
            dept,
            acting=str(dept.id) in acting_heads,
        )
        if status_filter and status_code != status_filter:
            continue
        if school_oid is not None and dept.organization_unit_id != school_oid:
            continue
        pc = len(prog_by_dept.get(str(dept.id), set()))
        sc = students_by_dept.get(str(dept.id), 0)
        kind = _department_kind(dept, programme_count=pc, student_count=sc)
        if type_filter and kind != type_filter:
            continue
        if needle:
            hay = f"{dept.name} {dept.department_code}".lower()
            if needle not in hay:
                continue
        filtered.append(dept)

    total = len(filtered)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = filtered[start : start + _PAGE_SIZE]

    table_rows: list[AllDepartmentsTableRow] = []
    for dept in page_slice:
        did = str(dept.id)
        acting = did in acting_heads
        status_code, status_label, status_tone = _status_presentation(dept, acting=acting)
        head_name = head_names.get(dept.head_user_id) if dept.head_user_id else None
        table_rows.append(
            AllDepartmentsTableRow(
                department_id=did,
                department_name=dept.name,
                department_code=dept.department_code,
                head_label=_format_head(head_name, acting=acting),
                programme_count=len(prog_by_dept.get(did, set())),
                student_count=students_by_dept.get(did, 0),
                faculty_count=faculty_by_dept.get(did, 0),
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/organization/department-details?departmentId={did}",
            )
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    school_options = [UserListFilterOption(value="", label="All schools")]
    for unit in sorted(school_units, key=lambda u: u.name):
        school_options.append(UserListFilterOption(value=str(unit.id), label=unit.name))

    type_options = [
        UserListFilterOption(value="", label="All types"),
        UserListFilterOption(value="academic", label="Academic"),
        UserListFilterOption(value="administrative", label="Administrative"),
    ]

    status_options = [
        UserListFilterOption(value="", label="All statuses"),
        UserListFilterOption(value="active", label="Active"),
        UserListFilterOption(value="draft", label="Draft"),
        UserListFilterOption(value="acting_hod", label="Acting HoD"),
        UserListFilterOption(value="inactive", label="Inactive"),
        UserListFilterOption(value="archived", label="Archived"),
    ]

    count_label_parts: list[str] = []
    if academic_total:
        count_label_parts.append(f"{academic_total} academic")
    if administrative_total:
        count_label_parts.append(f"{administrative_total} administrative")
    departments_count_label = (
        " · ".join(count_label_parts) if count_label_parts else "No active departments"
    )

    return AllDepartmentsListPageRead(
        page_title="All Departments",
        page_subtitle="Every academic and administrative department in the college",
        export_label="Export",
        create_department_label="Create department",
        create_department_href="/college-admin/organization/create-department",
        search_placeholder="Search departments...",
        school_filter_label="School",
        type_filter_label="Type",
        status_filter_label="Status",
        school_options=school_options,
        type_options=type_options,
        status_options=status_options,
        departments_section_title="Departments",
        departments_count_label=departments_count_label,
        table_headers=[
            "Department",
            "Code",
            "Head of department",
            "Programmes",
            "Students",
            "Faculty",
            "Status",
        ],
        departments=table_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        footer_disclaimer=(
            "Live institutional data · Departments, staffing and programme records · All times IST"
        ),
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )