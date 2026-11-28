"""Student fee assign wizard page (single / group / bulk)."""

from __future__ import annotations

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.all_students_list_page_service import _programme_label, _register_number
from app.modules.college_admin.finance_admin_models import InstitutionFeeStructure
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    StudentAdminDashboardFilterOption,
    StudentFeeAssignPageRead,
    StudentFeeAssignStructureOption,
    StudentFeeAssignStudentOption,
)
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.college_admin.student_statistics_overview_service import _ENROLLED_LIFECYCLE
from app.modules.students.models import StudentProfile

_MAX_STUDENTS = 500


def _format_inr(amount: float) -> str:
    rupees = int(round(amount))
    return f"₹{rupees:,}"


async def get_student_fee_assign_page(scope: AccessScope) -> StudentFeeAssignPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    structures = await InstitutionFeeStructure.find(
        Eq(InstitutionFeeStructure.tenant_id, tenant_id),
        Eq(InstitutionFeeStructure.published, True),
    ).sort("-updated_at").to_list()

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}

    structure_options: list[StudentFeeAssignStructureOption] = []
    for doc in structures:
        prog = prog_by_code.get(doc.programme_code.upper())
        prog_name = (prog.name if prog else doc.programme_code) or doc.programme_code
        structure_options.append(
            StudentFeeAssignStructureOption(
                structure_id=doc.structure_id,
                label=f"{prog_name} · Sem {doc.semester_label} · {doc.academic_year_label}",
                programme_code=doc.programme_code.upper(),
                academic_year_label=doc.academic_year_label,
                semester_label=doc.semester_label,
                total_amount=doc.total_amount,
                total_label=_format_inr(doc.total_amount),
            )
        )

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    enrolled = [r for r in records if r.lifecycle_status.value in _ENROLLED_LIFECYCLE]
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}
    user_ids = {r.user_id for r in enrolled[:_MAX_STUDENTS]}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    student_options: list[StudentFeeAssignStudentOption] = []
    for record in enrolled[:_MAX_STUDENTS]:
        profile = profile_by_user.get(record.user_id)
        user = user_by_id.get(record.user_id)
        if not user:
            continue
        name = (user.full_name or "Student").strip()
        register = _register_number(record, profile)
        code = (record.programme_code or profile.programme_code if profile else None) or ""
        programme_label = _programme_label(code.upper() if code else None, profile, prog_by_code)
        student_options.append(
            StudentFeeAssignStudentOption(
                student_user_id=str(record.user_id),
                label=f"{name} · {register} · {programme_label}",
                register_number=register,
                programme_code=code.upper() if code else None,
                batch_label=record.batch_label or (profile.batch_label if profile else None),
                section_code=record.section_code or (profile.section_code if profile else None),
            )
        )
    student_options.sort(key=lambda row: row.label.lower())

    programme_options: list[StudentAdminDashboardFilterOption] = [
        StudentAdminDashboardFilterOption(value="", label="Select programme"),
    ]
    programme_codes = sorted({o.programme_code for o in student_options if o.programme_code})
    for code in programme_codes:
        prog = prog_by_code.get(code)
        programme_options.append(
            StudentAdminDashboardFilterOption(
                value=code,
                label=prog.name if prog else code,
            )
        )

    batch_labels = sorted({o.batch_label for o in student_options if o.batch_label})
    section_codes = sorted({o.section_code for o in student_options if o.section_code})
    batch_options = [
        StudentAdminDashboardFilterOption(value="", label="All batches"),
        *[StudentAdminDashboardFilterOption(value=b, label=b) for b in batch_labels],
    ]
    section_options = [
        StudentAdminDashboardFilterOption(value="", label="All sections"),
        *[StudentAdminDashboardFilterOption(value=s, label=s) for s in section_codes],
    ]

    return StudentFeeAssignPageRead(
        page_title="Assign fees to students",
        page_subtitle="Single student, semester group, or Excel import",
        single_tab_label="Single student",
        group_tab_label="Group assign",
        bulk_tab_label="Bulk import",
        structure_label="Fee structure",
        student_label="Student",
        programme_label="Programme",
        batch_filter_label="Batch",
        section_filter_label="Section",
        concession_label="Concession (₹)",
        assign_submit_label="Assign fees",
        bulk_file_label="Excel or CSV file",
        bulk_template_hint="Columns: register_number, structure_id (optional), concession_amount (optional)",
        structure_options=structure_options,
        student_options=student_options,
        programme_options=programme_options,
        batch_options=batch_options,
        section_options=section_options,
        generated_at=now,
    )