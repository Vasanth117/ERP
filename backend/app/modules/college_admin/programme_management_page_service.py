"""Programme management page (CA 05 — college admin academics)."""

from __future__ import annotations

import math
from collections import defaultdict

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.college_admin.academic_config_models import AcademicProgramme, ConfigPublicationStatus
from app.modules.college_admin.department_performance_overview_service import (
    _level_matches,
    _programme_level,
)
from app.modules.college_admin.identity_models import DepartmentKind, DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.programme_course_mapping_page_service import (
    _duration_label,
    _regulation_label,
)
from app.modules.college_admin.schemas import (
    AcademicYearCreateFormField,
    AcademicYearCreateFormOption,
    PoliciesPagination,
    ProgrammeManagementCreate,
    ProgrammeManagementPageRead,
    InstitutionPolicyFilterOption,
    ProgrammeManagementTableRow,
)
from app.modules.students.curriculum_models import CurriculumReference
from app.modules.students.models import StudentProfile

_PAGE_SIZE = 10
_LEVEL_LABEL = {
    "undergraduate": "UG",
    "postgraduate": "PG",
    "doctoral": "Doctoral",
}


def _programme_status(prog: AcademicProgramme) -> tuple[str, str, str]:
    if not prog.is_active or prog.status == ConfigPublicationStatus.ARCHIVED:
        return "suspended", "Suspended", "info"
    if prog.status == ConfigPublicationStatus.DRAFT:
        return "proposed", "Proposed", "warning"
    return "active", "Active", "success"


def _resolve_department(
    prog: AcademicProgramme,
    depts_by_id: dict[str, InstitutionDepartment],
    code_to_dept: dict[str, InstitutionDepartment],
) -> InstitutionDepartment | None:
    if prog.department_id:
        dept = depts_by_id.get(str(prog.department_id))
        if dept:
            return dept
    return code_to_dept.get(prog.programme_code.upper())


def _intake_display(
    prog: AcademicProgramme,
    dept: InstitutionDepartment | None,
    students_by_code: dict[str, int],
) -> str:
    level = _programme_level(prog)
    if dept and level == "undergraduate" and dept.approved_intake_ug:
        return str(dept.approved_intake_ug)
    count = students_by_code.get(prog.programme_code.upper(), 0)
    if count > 0:
        return str(count)
    return "—"


def _matches_search(prog: AcademicProgramme, needle: str) -> bool:
    hay = f"{prog.name} {prog.programme_code}".lower()
    return needle in hay


def _matches_regulation(prog: AcademicProgramme, regulation_filter: str, curriculum_by_prog: dict) -> bool:
    if not regulation_filter:
        return True
    label = _regulation_label(prog.programme_code, curriculum_by_prog)
    return label != "—" and label.lower() == regulation_filter.lower()


async def get_programme_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    level_filter: str | None = None,
    department_id: str | None = None,
    regulation_filter: str | None = None,
    status_filter: str | None = None,
) -> ProgrammeManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    needle = (search or "").strip().lower()

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.department_kind, DepartmentKind.ACADEMIC),
    ).to_list()
    active_departments = [d for d in departments if d.status != DepartmentStatus.ARCHIVED]
    depts_by_id = {str(d.id): d for d in active_departments}
    code_to_dept: dict[str, InstitutionDepartment] = {}
    for dept in active_departments:
        for code in dept.programme_codes:
            code_to_dept.setdefault(code.upper(), dept)
        if dept.department_code:
            code_to_dept.setdefault(dept.department_code.upper(), dept)

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).sort("+name").to_list()
    curriculum_rows = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    curriculum_by_prog: dict[str, list[CurriculumReference]] = defaultdict(list)
    for row in curriculum_rows:
        curriculum_by_prog[row.programme_code.upper()].append(row)

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    students_by_code: dict[str, int] = defaultdict(int)
    for profile in profiles:
        code = (profile.programme_code or "").upper()
        if code:
            students_by_code[code] += 1

    regulation_labels: set[str] = set()
    for prog in programmes:
        label = _regulation_label(prog.programme_code, curriculum_by_prog)
        if label != "—":
            regulation_labels.add(label)

    filtered: list[AcademicProgramme] = []
    for prog in programmes:
        level = _programme_level(prog)
        if needle and not _matches_search(prog, needle):
            continue
        if not _level_matches(level, level_filter):
            continue
        dept = _resolve_department(prog, depts_by_id, code_to_dept)
        if dept_oid and (dept is None or dept.id != dept_oid):
            continue
        if not _matches_regulation(prog, regulation_filter or "", curriculum_by_prog):
            continue
        status_code, _, _ = _programme_status(prog)
        status_key = (status_filter or "").strip().lower()
        if status_key and status_code != status_key:
            continue
        filtered.append(prog)

    total = len(filtered)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = filtered[start : start + _PAGE_SIZE]

    table_rows: list[ProgrammeManagementTableRow] = []
    for prog in page_slice:
        dept = _resolve_department(prog, depts_by_id, code_to_dept)
        department_label = dept.department_code if dept else "—"
        status_code, status_label, status_tone = _programme_status(prog)
        level = _programme_level(prog)
        table_rows.append(
            ProgrammeManagementTableRow(
                programme_id=str(prog.id),
                programme_name=prog.name,
                programme_code=prog.programme_code,
                level_label=_LEVEL_LABEL.get(level, "UG"),
                department_label=department_label,
                duration_label=_duration_label(prog.duration_semesters),
                intake_label=_intake_display(prog, dept, students_by_code),
                regulation_label=_regulation_label(prog.programme_code, curriculum_by_prog),
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    all_programme_count = len(programmes)
    count_label = (
        f"{all_programme_count:,} programme{'s' if all_programme_count != 1 else ''}"
        if all_programme_count
        else "No programmes"
    )

    shown = len(table_rows)
    showing_label = (
        f"Showing {shown} of {total:,}" if total else "Showing 0 of 0"
    )

    dept_options = [InstitutionPolicyFilterOption(value="", label="All departments")]
    for dept in sorted(active_departments, key=lambda d: d.department_code):
        dept_options.append(InstitutionPolicyFilterOption(value=str(dept.id), label=dept.department_code))

    reg_options = [InstitutionPolicyFilterOption(value="", label="All regulations")]
    for label in sorted(regulation_labels):
        reg_options.append(InstitutionPolicyFilterOption(value=label, label=label))

    create_dept_options = [AcademicYearCreateFormOption(value="", label="— Select department —")]
    for dept in sorted(active_departments, key=lambda d: d.name):
        create_dept_options.append(
            AcademicYearCreateFormOption(value=str(dept.id), label=f"{dept.department_code} · {dept.name}")
        )

    return ProgrammeManagementPageRead(
        page_title="Programme Management",
        page_subtitle="Degree programmes, intake and duration offered by the college",
        export_label="Export",
        add_programme_label="Add programme",
        search_placeholder="Search programmes...",
        level_filter_label="Level",
        department_filter_label="Department",
        regulation_filter_label="Regulation",
        status_filter_label="Status",
        level_options=[
            InstitutionPolicyFilterOption(value="", label="All levels"),
            InstitutionPolicyFilterOption(value="ug", label="UG"),
            InstitutionPolicyFilterOption(value="pg", label="PG"),
            InstitutionPolicyFilterOption(value="doctoral", label="Doctoral"),
        ],
        department_options=dept_options,
        regulation_options=reg_options,
        status_options=[
            InstitutionPolicyFilterOption(value="", label="All statuses"),
            InstitutionPolicyFilterOption(value="active", label="Active"),
            InstitutionPolicyFilterOption(value="proposed", label="Proposed"),
            InstitutionPolicyFilterOption(value="suspended", label="Suspended"),
        ],
        programmes_section_title="Programmes",
        programmes_count_label=count_label,
        table_headers=[
            "Programme",
            "Code",
            "Level",
            "Department",
            "Duration",
            "Intake",
            "Regulation",
            "Status",
        ],
        programmes=table_rows,
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        create_section_title="Add programme",
        create_form_note="New programmes are saved as proposed until published through academic configuration.",
        create_submit_label="Create programme",
        create_cancel_label="Cancel",
        create_fields=[
            AcademicYearCreateFormField(key="name", label="Programme name", required=True),
            AcademicYearCreateFormField(key="programme_code", label="Programme code", required=True),
            AcademicYearCreateFormField(
                key="department_id",
                label="Owning department",
                required=False,
                field_type="select",
            ),
            AcademicYearCreateFormField(
                key="duration_semesters",
                label="Duration (semesters)",
                required=True,
                field_type="number",
            ),
            AcademicYearCreateFormField(
                key="credits_required",
                label="Credits required",
                required=True,
                field_type="number",
            ),
        ],
        create_department_options=create_dept_options,
        footer_disclaimer="Live academic data · Programmes and curriculum references · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def create_programme_management(
    scope: AccessScope,
    payload: ProgrammeManagementCreate,
) -> ProgrammeManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.programme_code.strip().upper()
    if not code:
        raise AppError("Programme code is required", status_code=400)

    existing = await AcademicProgramme.find_one(
        Eq(AcademicProgramme.tenant_id, tenant_id),
        Eq(AcademicProgramme.programme_code, code),
    )
    if existing:
        raise AppError("A programme with this code already exists", status_code=409)

    dept_id: PydanticObjectId | None = None
    if payload.department_id:
        dept_id = to_object_id(payload.department_id, "department_id")
        dept = await InstitutionDepartment.get(dept_id)
        if dept is None or dept.tenant_id != tenant_id:
            raise AppError("Department not found", status_code=404)

    doc = AcademicProgramme(
        tenant_id=tenant_id,
        programme_code=code,
        name=payload.name.strip(),
        department_id=dept_id,
        duration_semesters=payload.duration_semesters,
        credits_required=payload.credits_required,
        status=ConfigPublicationStatus.DRAFT,
        is_active=True,
    )
    await doc.insert()

    await record_audit(
        actor_id=scope.user_id,
        action="academic.programme.created",
        resource_type="academic_programme",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )

    return await get_programme_management_page(scope, page=1)