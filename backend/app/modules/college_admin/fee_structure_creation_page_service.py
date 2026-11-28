"""Fee structure creation wizard page (CA 10.02 modal)."""

from __future__ import annotations

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FeeStructureCreationPageRead,
    FeeStructureCreationProgrammeOption,
    StudentAdminDashboardFilterOption,
)

_reader = OperationalDataReader()

_DEFAULT_LINES = [
    {"name": "Tuition fee", "amount": 0},
    {"name": "Development fee", "amount": 0},
    {"name": "Examination fee", "amount": 0},
    {"name": "Library fee", "amount": 0},
]

_STREAM_OPTIONS = [
    StudentAdminDashboardFilterOption(value="", label="All streams"),
    StudentAdminDashboardFilterOption(value="undergraduate", label="UG (Undergraduate)"),
    StudentAdminDashboardFilterOption(value="postgraduate", label="PG (Postgraduate)"),
    StudentAdminDashboardFilterOption(value="doctoral", label="Doctoral / Ph.D."),
]


def _level_label(level: str | None) -> str:
    if not level:
        return ""
    key = level.lower()
    if key == "undergraduate":
        return "UG"
    if key == "postgraduate":
        return "PG"
    if key in {"doctoral", "phd", "doctorate"}:
        return "Doctoral"
    return level


async def get_fee_structure_creation_page(scope: AccessScope) -> FeeStructureCreationPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).sort("+name").to_list()
    dept_options = [
        StudentAdminDashboardFilterOption(value="", label="All departments"),
        *[
            StudentAdminDashboardFilterOption(value=str(d.id), label=d.name or "Department")
            for d in departments
        ],
    ]

    programmes = await AcademicProgramme.find(
        Eq(AcademicProgramme.tenant_id, tenant_id),
        Eq(AcademicProgramme.is_active, True),
    ).sort("+name").to_list()
    dept_name_by_id = {str(d.id): d.name or "—" for d in departments}
    programme_options: list[FeeStructureCreationProgrammeOption] = []
    for prog in programmes:
        dept_id = str(prog.department_id) if prog.department_id else ""
        programme_options.append(
            FeeStructureCreationProgrammeOption(
                programme_code=prog.programme_code.upper(),
                programme_label=prog.name or prog.programme_code,
                department_id=dept_id or None,
                department_name=dept_name_by_id.get(dept_id) if dept_id else None,
                programme_level=prog.programme_level,
                stream_label=_level_label(prog.programme_level),
            )
        )

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    current_year, _ = await _reader.current_academic_term(tenant_id)
    ay_options = [
        StudentAdminDashboardFilterOption(value=y.year_code, label=y.label or y.year_code) for y in years
    ]
    if not ay_options and current_year:
        ay_options = [StudentAdminDashboardFilterOption(value=current_year, label=current_year)]

    semester_options = [StudentAdminDashboardFilterOption(value=str(n), label=f"Semester {n}") for n in range(1, 9)]

    return FeeStructureCreationPageRead(
        page_title="Create fee structure",
        page_subtitle="Define fees by department, stream, programme and semester",
        department_filter_label="Department",
        stream_filter_label="Stream",
        programme_filter_label="Programme",
        academic_year_filter_label="Academic year",
        semester_filter_label="Semester",
        department_options=dept_options,
        stream_options=_STREAM_OPTIONS,
        programme_options=programme_options,
        academic_year_options=ay_options,
        semester_options=semester_options,
        default_line_items=list(_DEFAULT_LINES),
        save_draft_label="Save draft",
        continue_label="Continue",
        publish_label="Publish structure",
        generated_at=now,
    )