"""Programme details page (college admin academics)."""

from __future__ import annotations

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.academic_config_models import AcademicProgramme, ConfigPublicationStatus
from app.modules.college_admin.department_performance_overview_service import _programme_level
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.programme_course_mapping_page_service import _duration_label
from app.modules.college_admin.programme_management_page_service import (
    _LEVEL_LABEL,
    _programme_status,
)
from app.modules.college_admin.schemas import (
    AcademicYearLinkedConfig,
    AcademicYearRuleToggle,
    ProgrammeDetailsPageRead,
    ProgrammeDetailsSummaryRow,
)

_MODE_LABELS = {
    "full_time": "Full-time",
    "part_time": "Part-time",
    "evening": "Evening / weekend",
}


def _effective_level(prog: AcademicProgramme) -> str:
    if prog.programme_level:
        return prog.programme_level
    return _programme_level(prog)


async def get_programme_details_page(
    scope: AccessScope,
    *,
    programme_id: str,
) -> ProgrammeDetailsPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    prog_oid = to_object_id(programme_id, "programme_id")
    prog = await AcademicProgramme.get(prog_oid)
    if prog is None or prog.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Programme not found", status_code=404)

    dept_label = "—"
    if prog.department_id:
        dept = await InstitutionDepartment.get(prog.department_id)
        if dept and dept.tenant_id == tenant_id and dept.status != DepartmentStatus.ARCHIVED:
            dept_label = f"{dept.department_code} · {dept.name}"

    level = _effective_level(prog)
    _, status_label, status_tone = _programme_status(prog)

    regulation = prog.regulation_code or "—"
    intake = str(prog.approved_intake) if prog.approved_intake is not None else "—"
    mode = _MODE_LABELS.get(prog.mode_of_study or "full_time", (prog.mode_of_study or "full_time").replace("_", " ").title())

    summary = [
        ProgrammeDetailsSummaryRow(label="Level", value=_LEVEL_LABEL.get(level, level.title())),
        ProgrammeDetailsSummaryRow(label="Department", value=dept_label),
        ProgrammeDetailsSummaryRow(label="Duration", value=_duration_label(prog.duration_semesters)),
        ProgrammeDetailsSummaryRow(label="Credits required", value=str(int(prog.credits_required))),
        ProgrammeDetailsSummaryRow(label="Approved intake (per year)", value=intake),
        ProgrammeDetailsSummaryRow(label="Regulation", value=regulation),
        ProgrammeDetailsSummaryRow(label="Mode of study", value=mode),
    ]
    if prog.short_name:
        summary.insert(0, ProgrammeDetailsSummaryRow(label="Short name", value=prog.short_name))
    if prog.entry_qualification:
        summary.append(ProgrammeDetailsSummaryRow(label="Entry qualification", value=prog.entry_qualification))

    has_dept = prog.department_id is not None
    has_reg = bool(prog.regulation_code)
    has_intake = prog.approved_intake is not None
    published = prog.status == ConfigPublicationStatus.PUBLISHED

    checklist = [
        AcademicYearRuleToggle(
            key="identity",
            title="Programme identity complete",
            description="Name and code registered in academic configuration",
            enabled=True,
        ),
        AcademicYearRuleToggle(
            key="department",
            title="Owning department linked",
            description=dept_label if has_dept else "Assign a department before publishing",
            enabled=has_dept,
        ),
        AcademicYearRuleToggle(
            key="regulation",
            title="Regulation version set",
            description=regulation if has_reg else "Link a regulation cohort for this intake",
            enabled=has_reg,
        ),
        AcademicYearRuleToggle(
            key="intake",
            title="Approved intake recorded",
            description=f"{intake} seats" if has_intake else "Define sanctioned intake for admissions",
            enabled=has_intake,
        ),
        AcademicYearRuleToggle(
            key="published",
            title="Published to academic configuration",
            description="Proposed until published via configuration workflow",
            enabled=published,
        ),
    ]

    linked = [
        AcademicYearLinkedConfig(
            key="curriculum",
            title="Curriculum",
            description="Map courses and credits by semester",
            href="/college-admin/academics/curriculum-management",
            icon_slug="library-big",
        ),
        AcademicYearLinkedConfig(
            key="mapping",
            title="Programme–course mapping",
            description="Review owned courses for this programme",
            href="/college-admin/organization/programme-course-mapping",
            icon_slug="notebook-text",
        ),
    ]

    return ProgrammeDetailsPageRead(
        page_title="Programme details",
        page_subtitle="Review structure, regulation, and linked academic configuration",
        programme_name=prog.name,
        programme_code=prog.programme_code,
        status_label=status_label,
        status_tone=status_tone,
        back_href="/college-admin/academics/programme-management",
        edit_note="Changes to published programmes require an academic configuration revision.",
        summary_rows=summary,
        description=prog.description,
        checklist_title="Setup checklist",
        checklist_items=checklist,
        linked_title="Linked configuration",
        linked_items=linked,
        generated_at=utcnow(),
    )