"""Organizational hierarchy page (CA 04.07 — organization)."""

from __future__ import annotations

from collections import defaultdict

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus, FacultyRecord, EmployeeRecord
from app.modules.college_admin.identity_models import (
    DepartmentKind,
    DepartmentStaffAssociation,
    DepartmentStatus,
    InstitutionDepartment,
    InstitutionOrganizationUnit,
    OrganizationUnitType,
)
from app.modules.college_admin.institution_policy_models import InstitutionPolicy
from app.modules.college_admin.institution_service import _ensure_profile, _ensure_settings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.tenants.models import Tenant
from app.modules.college_admin.schemas import (
    OrganizationalHierarchyNodeRead,
    OrganizationalHierarchyPageRead,
    OrganizationalHierarchySelectedUnitRead,
    OrganizationalHierarchySummaryItem,
)
from app.modules.students.models import StudentProfile

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
    "registrar",
    "controller",
    "examination",
    "exam",
    "admission",
    "finance",
    "accounts",
    "hr",
    "human resource",
    "library",
    "hostel",
    "estate",
    "office",
    "cell",
)


def _designation_matches(designation: str | None, tokens: tuple[str, ...]) -> bool:
    lowered = (designation or "").lower()
    return any(token in lowered for token in tokens)


async def _resolve_user_name(user_id: PydanticObjectId | None, cache: dict[PydanticObjectId, str]) -> str | None:
    if user_id is None:
        return None
    if user_id in cache:
        return cache[user_id]
    user = await User.get(user_id)
    name = user.full_name if user else None
    cache[user_id] = name or "—"
    return cache[user_id]


async def _find_leader(
    tenant_id: PydanticObjectId,
    tokens: tuple[str, ...],
    *,
    user_cache: dict[PydanticObjectId, str],
) -> tuple[str | None, str | None]:
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    for rec in employees:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        if _designation_matches(rec.designation, tokens):
            name = await _resolve_user_name(rec.user_id, user_cache)
            return name, rec.designation
    faculty = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    for rec in faculty:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        if _designation_matches(rec.designation, tokens):
            name = await _resolve_user_name(rec.user_id, user_cache)
            return name, rec.designation
    return None, None


def _dept_kind(
    dept: InstitutionDepartment,
    *,
    programme_count: int,
    student_count: int,
) -> str:
    if dept.department_kind == DepartmentKind.ADMINISTRATIVE:
        return "administrative"
    if programme_count > 0 or student_count > 0 or dept.programme_codes:
        return "academic"
    name_lower = dept.name.lower()
    if any(keyword in name_lower for keyword in _ADMIN_KEYWORDS):
        return "administrative"
    if dept.organization_unit_id:
        return "academic"
    return "administrative"


def _dept_status(dept: InstitutionDepartment, *, acting: bool) -> tuple[str | None, str | None]:
    if acting and dept.status == DepartmentStatus.ACTIVE:
        return "Acting", "warning"
    if dept.status == DepartmentStatus.ACTIVE:
        return "Active", "success"
    if dept.status == DepartmentStatus.DRAFT:
        return "Draft", "warning"
    if dept.status == DepartmentStatus.INACTIVE:
        return "Inactive", "muted"
    if dept.status == DepartmentStatus.ARCHIVED:
        return "Archived", "muted"
    return None, None


def _format_members(*, faculty: int, staff: int, students: int | None = None) -> str:
    parts: list[str] = []
    if faculty:
        parts.append(f"{faculty} faculty")
    if staff:
        parts.append(f"{staff} staff")
    if students is not None and students > 0:
        parts.append(f"{students:,} students")
    return " · ".join(parts) if parts else "—"


def _first_department_node_id(nodes: list[OrganizationalHierarchyNodeRead]) -> str | None:
    for node in nodes:
        if node.node_id.startswith("dept:"):
            return node.node_id
        nested = _first_department_node_id(node.children)
        if nested:
            return nested
    return None


def _node_by_id(nodes: list[OrganizationalHierarchyNodeRead], node_id: str) -> OrganizationalHierarchyNodeRead | None:
    for node in nodes:
        if node.node_id == node_id:
            return node
        found = _node_by_id(node.children, node_id)
        if found:
            return found
    return None


def _walk_parent_titles(
    nodes: list[OrganizationalHierarchyNodeRead],
    target_id: str,
    trail: list[str] | None = None,
) -> list[str] | None:
    trail = trail or []
    for node in nodes:
        if node.node_id == target_id:
            return trail
        result = _walk_parent_titles(node.children, target_id, [*trail, node.title])
        if result is not None:
            return result
    return None


def _selected_unit_from_maps(
    *,
    node_id: str,
    nodes: list[OrganizationalHierarchyNodeRead],
    dept_by_id: dict[str, InstitutionDepartment],
    unit_by_id: dict[str, InstitutionOrganizationUnit],
    faculty_by_dept: dict[str, int],
    staff_by_dept: dict[str, int],
    students_by_dept: dict[str, int],
    user_cache: dict[PydanticObjectId, str],
) -> OrganizationalHierarchySelectedUnitRead | None:
    node = _node_by_id(nodes, node_id)
    if node is None:
        return None
    reports_to = _walk_parent_titles(nodes, node_id) or []
    reports_label = reports_to[-1] if reports_to else "—"

    if node_id.startswith("dept:"):
        dept = dept_by_id.get(node_id.removeprefix("dept:"))
        if dept is None:
            return None
        head = None
        if dept.head_user_id:
            head = user_cache.get(dept.head_user_id)
        did = str(dept.id)
        members = _format_members(
            faculty=faculty_by_dept.get(did, 0),
            staff=staff_by_dept.get(did, 0),
            students=students_by_dept.get(did),
        )
        return OrganizationalHierarchySelectedUnitRead(
            node_id=node_id,
            unit_label=dept.name,
            reports_to_label=reports_label,
            head_label=head or "—",
            members_label=members,
        )

    if node_id.startswith("unit:"):
        unit = unit_by_id.get(node_id.removeprefix("unit:"))
        if unit is None:
            return None
        head = None
        if unit.head_user_id:
            head = user_cache.get(unit.head_user_id)
        dept_ids = [str(d.id) for d in dept_by_id.values() if str(d.organization_unit_id) == str(unit.id)]
        faculty = sum(faculty_by_dept.get(did, 0) for did in dept_ids)
        staff = sum(staff_by_dept.get(did, 0) for did in dept_ids)
        students = sum(students_by_dept.get(did, 0) for did in dept_ids)
        return OrganizationalHierarchySelectedUnitRead(
            node_id=node_id,
            unit_label=unit.name,
            reports_to_label=reports_label,
            head_label=head or node.subtitle.split("·")[0].strip() if node.subtitle else "—",
            members_label=_format_members(faculty=faculty, staff=staff, students=students or None),
        )

    return OrganizationalHierarchySelectedUnitRead(
        node_id=node_id,
        unit_label=node.title,
        reports_to_label=reports_label,
        head_label=node.subtitle or "—",
        members_label=node.badge_label or "—",
    )


async def get_organizational_hierarchy_page(
    scope: AccessScope,
    *,
    selected_node_id: str | None = None,
) -> OrganizationalHierarchyPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    profile = await _ensure_profile(tenant)
    settings_doc = await _ensure_settings(tenant_id)
    org_settings = settings_doc.settings.get("organization")
    org_settings = org_settings if isinstance(org_settings, dict) else {}

    user_cache: dict[PydanticObjectId, str] = {}

    governing_title = (
        org_settings.get("governing_body_title")
        or profile.ownership_name
        or profile.legal_name
        or profile.display_name
    )
    chair_label = org_settings.get("governing_body_chair_label")
    if not chair_label:
        chair_name, _ = await _find_leader(tenant_id, ("chair", "chairman", "chairperson"), user_cache=user_cache)
        chair_label = chair_name
    member_count = org_settings.get("governing_body_member_count")
    if member_count is None:
        try:
            member_count = int(org_settings.get("governing_body_members"))
        except (TypeError, ValueError):
            member_count = None

    governing_parts: list[str] = []
    if chair_label:
        governing_parts.append(f"Chair: {chair_label}")
    if member_count is not None:
        governing_parts.append(f"{int(member_count)} members")
    governing_subtitle = " · ".join(governing_parts) if governing_parts else (profile.description or "")

    principal_name, principal_des = await _find_leader(
        tenant_id,
        ("principal", "vice chancellor", "director"),
        user_cache=user_cache,
    )
    dean_name, dean_des = await _find_leader(
        tenant_id,
        ("dean",),
        user_cache=user_cache,
    )

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        In(InstitutionDepartment.status, [DepartmentStatus.ACTIVE, DepartmentStatus.DRAFT]),
    ).to_list()
    units = await InstitutionOrganizationUnit.find(
        Eq(InstitutionOrganizationUnit.tenant_id, tenant_id),
        Eq(InstitutionOrganizationUnit.status, DepartmentStatus.ACTIVE),
    ).to_list()

    unit_by_id = {str(u.id): u for u in units}
    dept_by_id = {str(d.id): d for d in departments}

    acting_dept_ids: set[str] = set()
    associations = await DepartmentStaffAssociation.find(
        Eq(DepartmentStaffAssociation.tenant_id, tenant_id),
    ).to_list()
    for assoc in associations:
        if "acting" in (assoc.association_role or "").lower():
            acting_dept_ids.add(str(assoc.department_id))

    students_by_dept: dict[str, int] = defaultdict(int)
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    for profile_row in profiles:
        if profile_row.department_id is None:
            continue
        students_by_dept[str(profile_row.department_id)] += 1

    faculty_by_dept: dict[str, int] = defaultdict(int)
    staff_by_dept: dict[str, int] = defaultdict(int)
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT or rec.department_id is None:
            continue
        faculty_by_dept[str(rec.department_id)] += 1
    for assoc in associations:
        staff_by_dept[str(assoc.department_id)] += 1

    for dept in departments:
        if dept.head_user_id:
            await _resolve_user_name(dept.head_user_id, user_cache)
    for unit in units:
        if unit.head_user_id:
            await _resolve_user_name(unit.head_user_id, user_cache)

    schools = [
        u
        for u in units
        if u.unit_type in (OrganizationUnitType.SCHOOL, OrganizationUnitType.FACULTY, OrganizationUnitType.DIVISION)
    ]
    schools.sort(key=lambda row: row.name)

    async def build_department_node(dept: InstitutionDepartment) -> OrganizationalHierarchyNodeRead:
        did = str(dept.id)
        acting = did in acting_dept_ids
        head_name = await _resolve_user_name(dept.head_user_id, user_cache) if dept.head_user_id else None
        faculty = faculty_by_dept.get(did, 0)
        kind = _dept_kind(dept, programme_count=len(dept.programme_codes), student_count=students_by_dept.get(did, 0))
        status_label, status_tone = _dept_status(dept, acting=acting)
        subtitle_parts: list[str] = []
        if head_name:
            subtitle_parts.append(f"HoD: {head_name}{' (acting)' if acting else ''}")
        if faculty:
            subtitle_parts.append(f"{faculty} faculty")
        elif staff_by_dept.get(did, 0):
            subtitle_parts.append(f"{staff_by_dept[did]} staff")
        return OrganizationalHierarchyNodeRead(
            node_id=f"dept:{did}",
            node_type="department" if kind == "academic" else "office",
            title=dept.name,
            subtitle=" · ".join(subtitle_parts) if subtitle_parts else "—",
            depth=0,
            icon_slug="users",
            status_label=status_label,
            status_tone=status_tone,
            default_expanded=False,
            children=[],
        )

    async def build_school_node(unit: InstitutionOrganizationUnit) -> OrganizationalHierarchyNodeRead:
        uid = str(unit.id)
        dept_children = [
            d
            for d in departments
            if d.organization_unit_id == unit.id and _dept_kind(d, programme_count=len(d.programme_codes), student_count=students_by_dept.get(str(d.id), 0)) == "academic"
        ]
        dept_children.sort(key=lambda row: row.department_code)
        child_nodes = [await build_department_node(dept) for dept in dept_children]
        student_total = sum(students_by_dept.get(str(d.id), 0) for d in dept_children)
        dept_count = len(dept_children)
        head_name = await _resolve_user_name(unit.head_user_id, user_cache) if unit.head_user_id else None
        subtitle_parts = [f"{dept_count} departments"]
        if student_total:
            subtitle_parts.append(f"{student_total:,} students")
        if head_name and unit.unit_type == OrganizationUnitType.FACULTY:
            subtitle_parts.insert(0, head_name)
        return OrganizationalHierarchyNodeRead(
            node_id=f"unit:{uid}",
            node_type="org_unit",
            title=unit.name,
            subtitle=" · ".join(subtitle_parts),
            depth=0,
            icon_slug="users",
            default_expanded=bool(child_nodes),
            children=child_nodes,
        )

    school_nodes = [await build_school_node(school) for school in schools]

    academic_children: list[OrganizationalHierarchyNodeRead] = []
    if dean_name or school_nodes:
        dean_children = list(school_nodes)
        if dean_name:
            academic_children.append(
                OrganizationalHierarchyNodeRead(
                    node_id="leadership:dean",
                    node_type="leadership",
                    title=dean_des or "Dean, Academics",
                    subtitle=dean_name,
                    depth=0,
                    icon_slug="users",
                    badge_label=f"{len(school_nodes)} units" if school_nodes else None,
                    badge_tone="info" if school_nodes else None,
                    default_expanded=True,
                    children=dean_children,
                )
            )
        else:
            academic_children.extend(school_nodes)

    admin_departments = [
        d
        for d in departments
        if _dept_kind(d, programme_count=len(d.programme_codes), student_count=students_by_dept.get(str(d.id), 0))
        == "administrative"
    ]

    registrar_name, registrar_des = await _find_leader(
        tenant_id,
        ("registrar", "controller of exam"),
        user_cache=user_cache,
    )
    finance_name, finance_des = await _find_leader(
        tenant_id,
        ("finance officer", "finance", "accounts officer"),
        user_cache=user_cache,
    )

    admin_nodes: list[OrganizationalHierarchyNodeRead] = []

    registrar_dept = next(
        (d for d in admin_departments if "registrar" in d.name.lower() or "controller" in d.name.lower()),
        None,
    )
    if registrar_name or registrar_dept:
        reg_children_ids: list[OrganizationalHierarchyNodeRead] = []
        if registrar_dept:
            for dept in admin_departments:
                if dept.parent_department_id == registrar_dept.id or (
                    dept.id != registrar_dept.id
                    and any(tok in dept.name.lower() for tok in ("examination", "exam", "admission"))
                ):
                    reg_children_ids.append(await build_department_node(dept))
        admin_nodes.append(
            OrganizationalHierarchyNodeRead(
                node_id=f"dept:{registrar_dept.id}" if registrar_dept else "leadership:registrar",
                node_type="leadership",
                title=registrar_dept.name if registrar_dept else (registrar_des or "Registrar & Controller of Exams"),
                subtitle=registrar_name or "—",
                depth=0,
                icon_slug="users",
                default_expanded=bool(reg_children_ids),
                children=reg_children_ids,
            )
        )

    finance_dept = next(
        (d for d in admin_departments if "finance" in d.name.lower() or d.name.lower().startswith("accounts")),
        None,
    )
    if finance_name or finance_dept:
        fin_children: list[OrganizationalHierarchyNodeRead] = []
        if finance_dept:
            for dept in admin_departments:
                if dept.parent_department_id == finance_dept.id or (
                    dept.id != finance_dept.id and "account" in dept.name.lower()
                ):
                    fin_children.append(await build_department_node(dept))
        admin_nodes.append(
            OrganizationalHierarchyNodeRead(
                node_id=f"dept:{finance_dept.id}" if finance_dept else "leadership:finance",
                node_type="leadership",
                title=finance_dept.name if finance_dept else (finance_des or "Finance Officer"),
                subtitle=finance_name or "—",
                depth=0,
                icon_slug="users",
                default_expanded=bool(fin_children),
                children=fin_children,
            )
        )

    for dept in admin_departments:
        if dept.parent_department_id is not None:
            continue
        if registrar_dept and dept.id == registrar_dept.id:
            continue
        if finance_dept and dept.id == finance_dept.id:
            continue
        if any(tok in dept.name.lower() for tok in ("examination", "exam", "admission", "account")):
            continue
        admin_nodes.append(await build_department_node(dept))

    principal_children = [*academic_children, *admin_nodes]

    principal_node = OrganizationalHierarchyNodeRead(
        node_id="leadership:principal",
        node_type="leadership",
        title=principal_des or "Principal",
        subtitle=principal_name or "—",
        depth=0,
        icon_slug="layers",
        default_expanded=True,
        children=principal_children,
    )

    governing_node = OrganizationalHierarchyNodeRead(
        node_id="governing:root",
        node_type="governing_body",
        title=governing_title,
        subtitle=governing_subtitle,
        depth=0,
        icon_slug="building",
        default_expanded=True,
        children=[principal_node],
    )

    tree = [governing_node]

    def set_depth(nodes: list[OrganizationalHierarchyNodeRead], depth: int) -> None:
        for node in nodes:
            node.depth = depth
            set_depth(node.children, depth + 1)

    set_depth(tree, 0)

    academic_dept_count = sum(
        1
        for d in departments
        if _dept_kind(d, programme_count=len(d.programme_codes), student_count=students_by_dept.get(str(d.id), 0))
        == "academic"
    )
    admin_office_count = sum(
        1
        for d in departments
        if _dept_kind(d, programme_count=len(d.programme_codes), student_count=students_by_dept.get(str(d.id), 0))
        == "administrative"
    )
    policies = await InstitutionPolicy.find(Eq(InstitutionPolicy.tenant_id, tenant_id)).to_list()
    committee_count = sum(1 for p in policies if "committee" in (p.category or "").lower())
    if not committee_count:
        committee_count = sum(1 for d in departments if "committee" in d.name.lower())

    summary_items = [
        OrganizationalHierarchySummaryItem(key="schools", label="Schools", value=str(len(schools))),
        OrganizationalHierarchySummaryItem(
            key="academic_departments",
            label="Academic departments",
            value=str(academic_dept_count),
        ),
        OrganizationalHierarchySummaryItem(
            key="administrative_offices",
            label="Administrative offices",
            value=str(admin_office_count),
        ),
        OrganizationalHierarchySummaryItem(key="committees", label="Committees", value=str(committee_count)),
    ]

    if selected_node_id:
        if _node_by_id(tree, selected_node_id) is None:
            raise AppError(code="NOT_FOUND", message="Hierarchy node not found", status_code=404)
        selected_id = selected_node_id
    else:
        selected_id = _first_department_node_id(tree) or tree[0].node_id

    selected_unit = _selected_unit_from_maps(
        node_id=selected_id,
        nodes=tree,
        dept_by_id=dept_by_id,
        unit_by_id=unit_by_id,
        faculty_by_dept=faculty_by_dept,
        staff_by_dept=staff_by_dept,
        students_by_dept=students_by_dept,
        user_cache=user_cache,
    )

    return OrganizationalHierarchyPageRead(
        page_title="Organizational Hierarchy",
        page_subtitle="Reporting structure from governing council to departments",
        export_label="Export chart",
        edit_structure_label="Edit structure",
        edit_structure_href="/college-admin/organization/department-management-dashboard",
        structure_section_title="Organization structure",
        structure_section_hint="Expand any unit to see its members.",
        tree=tree,
        selected_unit=selected_unit,
        summary_section_title="Structure summary",
        summary_items=summary_items,
        footer_disclaimer="Live institutional data · Organization units, departments, staffing · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )