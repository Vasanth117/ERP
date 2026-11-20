"""Department head assignment page (CA 04.06 — organization)."""

from __future__ import annotations

import math
from datetime import date, datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.identity_models import (
    DepartmentHeadAssignment,
    DepartmentStaffAssociation,
    DepartmentStatus,
    InstitutionAccountStatus,
    InstitutionDepartment,
    InstitutionUser,
)
from app.modules.college_admin.identity_schemas import DepartmentHeadAssign
from app.modules.college_admin.organization_service import assign_department_head
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    DepartmentHeadAssignmentFormValues,
    DepartmentHeadAssignmentPageRead,
    DepartmentHeadAssignmentSavePayload,
    DepartmentHeadAssignmentSaveResult,
    DepartmentHeadAssignmentTableRow,
    DepartmentHeadEligibilityRow,
    InstitutionFieldOption,
    PoliciesPagination,
)
from app.modules.faculty.models import FacultyProfile

_PAGE_SIZE = 10
_DEFAULT_TERM_YEARS = 3
_PHD_KEYWORDS = ("ph.d", "phd", "doctoral", "doctor of philosophy", "d.phil")
_TEACHING_YEARS_REQUIRED = 10.0


def _month_year_label(value: date) -> str:
    return value.strftime("%b %Y")


def _parse_iso_date(raw: str | None) -> date | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    try:
        if "T" in text:
            return date.fromisoformat(text.split("T", maxsplit=1)[0])
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Invalid date: {raw}",
            status_code=422,
        ) from exc


def _default_term_end(effective_from: date) -> date:
    """Align to 31 May following the default three-year term."""
    target_year = effective_from.year + _DEFAULT_TERM_YEARS
    if effective_from.month > 5 or (effective_from.month == 5 and effective_from.day > 31):
        target_year += 1
    return date(target_year, 5, 31)


def _has_phd(qualifications: list) -> bool:
    for row in qualifications:
        degree = (getattr(row, "degree", "") or "").lower()
        if any(token in degree for token in _PHD_KEYWORDS):
            return True
    return False


def _teaching_years_label(years: float | None) -> str:
    if years is None:
        return "Teaching experience not recorded"
    whole = int(years)
    months = int(round((years - whole) * 12))
    if months >= 12:
        whole += 1
        months = 0
    if months:
        return f"Has {whole} years {months} months"
    return f"Has {whole} years"


async def _load_faculty_context(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> dict:
    faculty = await FacultyRecord.find_one(
        Eq(FacultyRecord.tenant_id, tenant_id),
        Eq(FacultyRecord.user_id, user_id),
    )
    profile = await FacultyProfile.find_one(
        Eq(FacultyProfile.tenant_id, tenant_id),
        Eq(FacultyProfile.user_id, user_id),
    )
    qualifications = []
    experience_years: float | None = None
    designation = ""
    if faculty is not None:
        qualifications = list(faculty.qualifications)
        experience_years = faculty.experience_years
        designation = faculty.designation or ""
    if profile is not None and profile.qualifications:
        if not qualifications:
            qualifications = list(profile.qualifications)
        if not designation and profile.designation:
            designation = profile.designation
    return {
        "qualifications": qualifications,
        "experience_years": experience_years,
        "designation": designation,
    }


def _build_eligibility_rows(
    *,
    qualifications: list,
    experience_years: float | None,
    disciplinary_clear: bool,
    disciplinary_detail: str,
) -> list[DepartmentHeadEligibilityRow]:
    has_phd = _has_phd(qualifications)
    rows = [
        DepartmentHeadEligibilityRow(
            key="phd",
            label="Ph.D. qualification",
            detail="Required",
            status_code="met" if has_phd else "not_met",
            status_label="Met" if has_phd else "Not met",
            status_tone="success" if has_phd else "error",
        ),
        DepartmentHeadEligibilityRow(
            key="teaching_years",
            label="10+ years teaching",
            detail=_teaching_years_label(experience_years),
            status_code="met" if (experience_years or 0) >= _TEACHING_YEARS_REQUIRED else "waiver",
            status_label="Met" if (experience_years or 0) >= _TEACHING_YEARS_REQUIRED else "Waiver needed",
            status_tone="success" if (experience_years or 0) >= _TEACHING_YEARS_REQUIRED else "warning",
        ),
        DepartmentHeadEligibilityRow(
            key="disciplinary",
            label="No pending disciplinary case",
            detail=disciplinary_detail,
            status_code="met" if disciplinary_clear else "not_met",
            status_label="Met" if disciplinary_clear else "Review",
            status_tone="success" if disciplinary_clear else "warning",
        ),
    ]
    return rows


async def _disciplinary_status(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> tuple[bool, str]:
    institution_user = await InstitutionUser.find_one(
        Eq(InstitutionUser.tenant_id, tenant_id),
        Eq(InstitutionUser.user_id, user_id),
    )
    if institution_user is None:
        return True, "HR record"
    if institution_user.account_status == InstitutionAccountStatus.SUSPENDED:
        code = (institution_user.suspension_reason_code or "").lower()
        if "disciplinary" in code or "ragging" in (institution_user.suspension_reason or "").lower():
            return False, "Pending disciplinary action"
        return False, "Account suspended"
    if institution_user.account_status in {
        InstitutionAccountStatus.DEACTIVATED,
        InstitutionAccountStatus.INVITED,
    }:
        return False, institution_user.account_status.value.replace("_", " ").title()
    return True, "HR record"


def _head_presentation_status(
    *,
    dept: InstitutionDepartment,
    assignment: DepartmentHeadAssignment | None,
    acting_dept_ids: set[str],
    today: date,
) -> tuple[str, str, str, str, str]:
    """Return since_label, term_ends_label, status_code, status_label, status_tone."""
    if not dept.head_user_id:
        return "—", "Until filled", "vacant", "Vacant", "muted"

    since = assignment.effective_from if assignment else today
    since_label = _month_year_label(since)

    effective_to = assignment.effective_to if assignment else None
    acting = (
        str(dept.id) in acting_dept_ids
        or (assignment is not None and assignment.appointment_type == "acting")
    )
    if acting:
        term_label = _month_year_label(effective_to) if effective_to else "Until filled"
        return since_label, term_label, "acting", "Acting", "info"

    if effective_to and effective_to < today:
        term_label = f"{_month_year_label(effective_to)} + ext."
        return since_label, term_label, "extended", "Extended", "warning"

    if effective_to:
        term_label = _month_year_label(effective_to)
    else:
        inferred_end = _default_term_end(since)
        term_label = _month_year_label(inferred_end)
    return since_label, term_label, "regular", "Regular", "success"


async def _faculty_options_for_department(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
) -> list[InstitutionFieldOption]:
    active_statuses = {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    dept_matches = [
        rec
        for rec in faculty_records
        if rec.employment_status in active_statuses
        and (department_id is None or rec.department_id == department_id)
    ]
    pool = dept_matches if dept_matches else [
        rec for rec in faculty_records if rec.employment_status in active_statuses
    ]
    user_ids = [rec.user_id for rec in pool]
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    users_by_id = {u.id: u for u in users}

    options: list[InstitutionFieldOption] = [InstitutionFieldOption(value="", label="Select faculty member")]

    def sort_key(rec: FacultyRecord) -> str:
        user = users_by_id.get(rec.user_id)
        return (user.full_name if user else "").lower()

    for rec in sorted(pool, key=sort_key):
        user = users_by_id.get(rec.user_id)
        if user is None:
            continue
        designation = rec.designation or "Faculty"
        options.append(
            InstitutionFieldOption(value=str(rec.user_id), label=f"{user.full_name} · {designation}")
        )
    return options


async def get_department_head_assignment_page(
    scope: AccessScope,
    *,
    page: int = 1,
    selected_department_id: str | None = None,
    faculty_user_id: str | None = None,
) -> DepartmentHeadAssignmentPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    today = utcnow().date()

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
    ).sort("+department_code").to_list()
    active_departments = [d for d in departments if d.status != DepartmentStatus.ARCHIVED]

    assignments = await DepartmentHeadAssignment.find(
        Eq(DepartmentHeadAssignment.tenant_id, tenant_id),
    ).to_list()
    latest_assignment: dict[str, DepartmentHeadAssignment] = {}
    for row in assignments:
        key = str(row.department_id)
        existing = latest_assignment.get(key)
        if existing is None or row.effective_from > existing.effective_from:
            latest_assignment[key] = row

    acting_dept_ids: set[str] = set()
    staff_assoc = await DepartmentStaffAssociation.find(
        Eq(DepartmentStaffAssociation.tenant_id, tenant_id),
    ).to_list()
    for assoc in staff_assoc:
        if "acting" in (assoc.association_role or "").lower():
            acting_dept_ids.add(str(assoc.department_id))

    head_user_ids = [d.head_user_id for d in active_departments if d.head_user_id]
    head_users = await User.find(In(User.id, head_user_ids)).to_list() if head_user_ids else []
    head_names = {u.id: u.full_name for u in head_users}

    selected_oid: PydanticObjectId | None = None
    if selected_department_id:
        selected_oid = to_object_id(selected_department_id, "department_id")
        if not any(d.id == selected_oid for d in active_departments):
            selected_oid = None

    if selected_oid is None and active_departments:
        selected_oid = active_departments[0].id

    total = len(active_departments)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = active_departments[start : start + _PAGE_SIZE]

    table_rows: list[DepartmentHeadAssignmentTableRow] = []
    for dept in page_slice:
        assignment = latest_assignment.get(str(dept.id))
        since_label, term_label, status_code, status_label, status_tone = _head_presentation_status(
            dept=dept,
            assignment=assignment,
            acting_dept_ids=acting_dept_ids,
            today=today,
        )
        head_name = head_names.get(dept.head_user_id, "—") if dept.head_user_id else "—"
        table_rows.append(
            DepartmentHeadAssignmentTableRow(
                department_id=str(dept.id),
                department_label=dept.department_code,
                head_name=head_name,
                since_label=since_label,
                term_ends_label=term_label,
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                is_selected=selected_oid == dept.id if selected_oid else False,
            )
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    selected_dept = next((d for d in active_departments if d.id == selected_oid), None)
    panel_title = f"Assign head – {selected_dept.name}" if selected_dept else "Assign head"
    panel_subtitle = "Complete the form and send for Principal approval"

    faculty_oid: PydanticObjectId | None = None
    if faculty_user_id:
        faculty_oid = to_object_id(faculty_user_id, "faculty_user_id")
    elif selected_dept and selected_dept.head_user_id:
        faculty_oid = selected_dept.head_user_id

    faculty_options = await _faculty_options_for_department(tenant_id, selected_dept.id if selected_dept else None)

    default_from = today
    default_term_end = _default_term_end(default_from)
    assignment = latest_assignment.get(str(selected_dept.id)) if selected_dept else None
    default_appointment = "acting" if (selected_dept and str(selected_dept.id) in acting_dept_ids) else "regular"

    form = DepartmentHeadAssignmentFormValues(
        faculty_user_id=str(faculty_oid) if faculty_oid else "",
        appointment_type=default_appointment,
        effective_from=default_from.isoformat(),
        term_end=(assignment.effective_to.isoformat() if assignment and assignment.effective_to else default_term_end.isoformat()),
        order_reference=assignment.order_reference if assignment and assignment.order_reference else "",
    )

    eligibility_rows: list[DepartmentHeadEligibilityRow] = []
    if faculty_oid:
        faculty_ctx = await _load_faculty_context(tenant_id, faculty_oid)
        clear, detail = await _disciplinary_status(tenant_id, faculty_oid)
        eligibility_rows = _build_eligibility_rows(
            qualifications=faculty_ctx["qualifications"],
            experience_years=faculty_ctx["experience_years"],
            disciplinary_clear=clear,
            disciplinary_detail=detail,
        )
    else:
        eligibility_rows = [
            DepartmentHeadEligibilityRow(
                key="placeholder",
                label="Select a faculty member",
                detail="Eligibility checks will appear here",
                status_code="muted",
                status_label="—",
                status_tone="muted",
            )
        ]

    appointment_type_options = [
        InstitutionFieldOption(value="regular", label="Regular"),
        InstitutionFieldOption(value="acting", label="Acting"),
        InstitutionFieldOption(value="extension", label="Extension"),
    ]

    return DepartmentHeadAssignmentPageRead(
        page_title="Department Head Assignment",
        page_subtitle="Assign, change or rotate heads of department",
        rotation_policy_label="Rotation policy",
        rotation_policy_href="/college-admin/institution/policies",
        assign_head_label="+ Assign head",
        current_heads_section_title="Current heads of department",
        table_headers=["Department", "Head of department", "Since", "Term ends", "Status"],
        table_rows=table_rows,
        departments_count_label=f"{total:,} departments",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        assign_panel_title=panel_title,
        assign_panel_subtitle=panel_subtitle,
        faculty_field_label="Faculty member",
        faculty_options=faculty_options,
        appointment_type_field_label="Appointment type",
        appointment_type_options=appointment_type_options,
        effective_from_field_label="Effective from",
        term_end_field_label="Term end",
        order_reference_field_label="Order reference",
        eligibility_section_title="Eligibility check",
        eligibility_rows=eligibility_rows,
        form=form,
        selected_department_id=str(selected_oid) if selected_oid else None,
        cancel_label="Cancel",
        submit_label="Send to Principal for approval",
        footer_note="Changes are saved to the audit log with your name and time.",
        footer_disclaimer="Live institutional data · Head appointments and HR records · All times IST",
        footer_snapshot_label="Live snapshot",
        can_submit=bool(selected_dept)
        and bool(form.faculty_user_id)
        and bool((form.order_reference or "").strip()),
        generated_at=utcnow(),
    )


async def save_department_head_assignment(
    scope: AccessScope,
    payload: DepartmentHeadAssignmentSavePayload,
) -> DepartmentHeadAssignmentSaveResult:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    department_id = to_object_id(payload.department_id, "department_id")
    dept = await InstitutionDepartment.get(department_id)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)

    if not payload.form.faculty_user_id:
        raise AppError(code="VALIDATION_ERROR", message="Faculty member is required", status_code=422)
    if not (payload.form.order_reference or "").strip():
        raise AppError(code="VALIDATION_ERROR", message="Order reference is required", status_code=422)

    effective_from = _parse_iso_date(payload.form.effective_from) or utcnow().date()
    effective_to = _parse_iso_date(payload.form.term_end)

    await assign_department_head(
        scope,
        department_id,
        DepartmentHeadAssign(
            user_id=payload.form.faculty_user_id,
            effective_from=datetime.combine(effective_from, datetime.min.time()),
            effective_to=effective_to,
            appointment_type=payload.form.appointment_type or "regular",
            order_reference=payload.form.order_reference or None,
            send_for_principal_approval=True,
        ),
    )

    page = await get_department_head_assignment_page(
        scope,
        selected_department_id=str(department_id),
        faculty_user_id=payload.form.faculty_user_id,
    )
    return DepartmentHeadAssignmentSaveResult(
        message="Head assignment submitted for Principal approval",
        approval_status="pending",
        page=page,
    )