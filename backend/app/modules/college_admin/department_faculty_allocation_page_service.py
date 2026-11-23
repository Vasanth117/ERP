"""Department faculty allocation page (CA 04.09 — organization)."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import date, datetime
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    FacultyDepartmentAssignment,
    FacultyEmploymentStatus,
    FacultyEmploymentHistory,
    FacultyRecord,
    FacultyWorkloadRecord,
)
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.institution_service import _ensure_settings
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    DepartmentFacultyAllocationFormValues,
    DepartmentFacultyAllocationPageRead,
    DepartmentFacultyAllocationSavePayload,
    DepartmentFacultyAllocationSaveResult,
    DepartmentFacultyCapacityRow,
    DepartmentFacultyDesignationBar,
    DepartmentFacultyVacancyItem,
    InstitutionFieldOption,
    PoliciesPagination,
)
from app.modules.hr.enums import HrJobOpeningStatus
from app.modules.hr.recruitment_models import HrJobOpening

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10
_WORKLOAD_TARGET_HOURS = 18.0
_reader = OperationalDataReader()

_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
)

_DESIGNATION_BUCKETS: tuple[tuple[str, str], ...] = (
    ("professor", "Professors"),
    ("associate_professor", "Associate Professors"),
    ("assistant_professor", "Assistant Professors"),
    ("visiting", "Visiting faculty"),
)


def _norm_designation(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _designation_bucket(designation: str | None) -> str | None:
    d = _norm_designation(designation)
    if not d:
        return None
    if any(k in d for k in ("visiting", "adjunct", "guest")):
        return "visiting"
    if "assistant professor" in d or d.startswith("asst"):
        return "assistant_professor"
    if "associate professor" in d:
        return "associate_professor"
    if re.search(r"\bprofessor\b", d) and "assistant" not in d and "associate" not in d:
        return "professor"
    return None


def _parse_iso_date(raw: str | None) -> date:
    if not raw or not str(raw).strip():
        return utcnow().date()
    text = str(raw).strip()
    try:
        if "T" in text:
            return date.fromisoformat(text.split("T", maxsplit=1)[0])
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise AppError(code="VALIDATION_ERROR", message=f"Invalid date: {raw}", status_code=422) from exc


def _workload_status(pct: float | None) -> tuple[str, str, str]:
    if pct is None:
        return "unknown", "—", "muted"
    if pct >= 110:
        return "overloaded", "Overloaded", "error"
    if pct >= 105:
        return "stretched", "Stretched", "warning"
    return "balanced", "Balanced", "success"


def _opening_role_summary(title: str) -> str:
    parts: list[str] = []
    title_lower = title.lower()
    for token, label in (
        ("professor", "Prof"),
        ("associate", "Assoc. Prof"),
        ("assistant", "Asst. Prof"),
        ("asst", "Asst. Prof"),
    ):
        if token in title_lower:
            parts.append(label)
    return " · ".join(parts) if parts else title[:80]


async def get_department_faculty_allocation_page(
    scope: AccessScope,
    *,
    page: int = 1,
    semester_label: str | None = None,
    department_id: str | None = None,
    designation_filter: str | None = None,
) -> DepartmentFacultyAllocationPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    settings_doc = await _ensure_settings(tenant_id)
    org_settings = settings_doc.settings.get("organization")
    org_settings = org_settings if isinstance(org_settings, dict) else {}
    sanction_by_dept: dict[str, int] = {}
    raw_sanction = org_settings.get("faculty_sanctioned_by_department")
    if isinstance(raw_sanction, dict):
        sanction_by_dept = {str(k): int(v) for k, v in raw_sanction.items() if v is not None}

    year_label, current_semester = await _reader.current_academic_term(tenant_id)
    selected_semester = semester_label or current_semester or "1"
    semester_display = f"{'Odd' if selected_semester in {'1', '3', '5', '7'} else 'Even'} semester"
    if year_label:
        semester_display = f"{semester_display} {year_label.split('-')[0] if '-' in year_label else year_label}"

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        In(InstitutionDepartment.status, [DepartmentStatus.ACTIVE, DepartmentStatus.DRAFT]),
    ).sort("+department_code").to_list()

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    faculty_by_dept: dict[str, list[FacultyRecord]] = defaultdict(list)
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT or rec.department_id is None:
            continue
        bucket = _designation_bucket(rec.designation)
        if designation_filter and bucket != designation_filter:
            continue
        faculty_by_dept[str(rec.department_id)].append(rec)

    openings = await HrJobOpening.find(
        Eq(HrJobOpening.tenant_id, tenant_id),
        Eq(HrJobOpening.status, HrJobOpeningStatus.PUBLISHED),
    ).to_list()
    vacant_by_dept: dict[str, int] = defaultdict(int)
    vacancy_details: dict[str, list[HrJobOpening]] = defaultdict(list)
    for opening in openings:
        slots = max(0, opening.vacancies - opening.filled_count)
        if slots <= 0:
            continue
        key = str(opening.department_id)
        vacant_by_dept[key] += slots
        vacancy_details[key].append(opening)

    workloads = await FacultyWorkloadRecord.find(Eq(FacultyWorkloadRecord.tenant_id, tenant_id)).to_list()
    workload_by_user: dict[PydanticObjectId, float] = {}
    for row in workloads:
        if row.semester_label != selected_semester and current_semester:
            continue
        if year_label and row.academic_year_label != year_label:
            continue
        workload_by_user[row.user_id] = max(workload_by_user.get(row.user_id, 0), row.total_hours)

    filtered_departments = departments
    if department_id:
        dept_oid = to_object_id(department_id, "department_id")
        filtered_departments = [d for d in departments if d.id == dept_oid]

    capacity_rows: list[DepartmentFacultyCapacityRow] = []
    for dept in filtered_departments:
        did = str(dept.id)
        in_position = len(faculty_by_dept.get(did, []))
        vacant = vacant_by_dept.get(did, 0)
        sanctioned = sanction_by_dept.get(did, in_position + vacant)
        hours: list[float] = []
        for rec in faculty_by_dept.get(did, []):
            if rec.user_id in workload_by_user:
                hours.append(workload_by_user[rec.user_id])
        if hours:
            avg_hours = sum(hours) / len(hours)
            workload_pct = round((avg_hours / _WORKLOAD_TARGET_HOURS) * 100)
        elif in_position:
            workload_pct = round((sum(workload_by_user.get(r.user_id, 0) for r in faculty_by_dept[did]) / max(in_position, 1) / _WORKLOAD_TARGET_HOURS) * 100)
        else:
            workload_pct = None
        status_code, status_label, status_tone = _workload_status(
            float(workload_pct) if workload_pct is not None else None
        )
        capacity_rows.append(
            DepartmentFacultyCapacityRow(
                department_id=did,
                department_label=dept.department_code,
                sanctioned=sanctioned,
                in_position=in_position,
                vacant=vacant,
                workload_pct=workload_pct,
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    total = len(capacity_rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = capacity_rows[start : start + _PAGE_SIZE]
    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    designation_counts: dict[str, int] = defaultdict(int)
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        bucket = _designation_bucket(rec.designation)
        if bucket:
            designation_counts[bucket] += 1
    max_designation = max(designation_counts.values(), default=1)
    designation_bars = [
        DepartmentFacultyDesignationBar(
            key=key,
            label=label,
            value=designation_counts.get(key, 0),
            max_value=max_designation,
        )
        for key, label in _DESIGNATION_BUCKETS
    ]

    vacancy_items: list[DepartmentFacultyVacancyItem] = []
    for dept in sorted(departments, key=lambda d: vacant_by_dept.get(str(d.id), 0), reverse=True):
        did = str(dept.id)
        open_slots = vacant_by_dept.get(did, 0)
        if open_slots <= 0:
            continue
        openings_for_dept = vacancy_details.get(did, [])
        role_parts = [_opening_role_summary(o.job_title) for o in openings_for_dept[:3]]
        detail = " · ".join(role_parts) if role_parts else "Open faculty positions"
        vacancy_items.append(
            DepartmentFacultyVacancyItem(
                department_id=did,
                department_label=dept.department_code,
                detail=detail,
                count=open_slots,
                badge_tone="warning" if open_slots >= 3 else "info",
            )
        )
        if len(vacancy_items) >= 6:
            break

    user_ids = [r.user_id for r in faculty_records if r.employment_status in _ACTIVE_EMPLOYMENT]
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    users_by_id = {u.id: u for u in users}

    faculty_options: list[InstitutionFieldOption] = [
        InstitutionFieldOption(value="", label="Select faculty member"),
    ]
    for rec in sorted(faculty_records, key=lambda r: (users_by_id.get(r.user_id).full_name if r.user_id in users_by_id else "")):
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        user = users_by_id.get(rec.user_id)
        if not user:
            continue
        dept_code = next((d.department_code for d in departments if d.id == rec.department_id), "")
        label = f"{user.full_name} · {dept_code}" if dept_code else user.full_name
        faculty_options.append(InstitutionFieldOption(value=str(rec.user_id), label=label))

    dept_options = [InstitutionFieldOption(value="", label="All departments")]
    allocate_options = [InstitutionFieldOption(value="", label="Select department")]
    for dept in departments:
        dept_options.append(InstitutionFieldOption(value=str(dept.id), label=dept.department_code))
        allocate_options.append(InstitutionFieldOption(value=str(dept.id), label=dept.name))

    semester_options = [
        InstitutionFieldOption(value=selected_semester, label=semester_display),
    ]
    if current_semester and current_semester != selected_semester:
        semester_options.append(
            InstitutionFieldOption(value=current_semester, label=f"Current semester ({current_semester})"),
        )

    designation_options = [InstitutionFieldOption(value="", label="All designations")]
    for key, label in _DESIGNATION_BUCKETS:
        designation_options.append(InstitutionFieldOption(value=key, label=label))

    form = DepartmentFacultyAllocationFormValues(
        faculty_user_id="",
        allocate_to_department_id="",
        allocation_type="shared_50",
        effective_from=utcnow().date().isoformat(),
    )

    generated = utcnow()
    updated_label = generated.astimezone(_IST).strftime("Updated %H:%M IST")

    sanction_note = org_settings.get("faculty_sanction_note")
    if not sanction_note:
        sanction_note = "Sanctioned = in-position plus published vacancies (or institution staffing settings)"

    return DepartmentFacultyAllocationPageRead(
        page_title="Department Faculty Allocation",
        page_subtitle="Allocate faculty to departments and balance teaching capacity",
        export_label="Export",
        allocate_faculty_label="+ Allocate faculty",
        allocate_faculty_href="#move-share-faculty",
        semester_filter_label="Semester",
        department_filter_label="Departments",
        designation_filter_label="Designations",
        resources_nav_label="Resources",
        resources_nav_href="/college-admin/organization/department-resource-management",
        updated_at_label=updated_label,
        semester_options=semester_options,
        department_options=dept_options,
        designation_options=designation_options,
        selected_semester=selected_semester,
        selected_department_id=department_id or "",
        selected_designation=designation_filter or "",
        capacity_section_title="Capacity vs requirement",
        capacity_table_headers=["Department", "Sanctioned", "In position", "Vacant", "Workload", "Status"],
        capacity_table_footer_note=sanction_note,
        capacity_rows=page_slice,
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        move_share_section_title="Move or share faculty",
        faculty_field_label="Faculty member",
        faculty_options=faculty_options,
        allocate_to_field_label="Allocate to",
        department_allocate_options=allocate_options,
        allocation_type_field_label="Allocation type",
        allocation_type_options=[
            InstitutionFieldOption(value="primary", label="Primary (100%)"),
            InstitutionFieldOption(value="shared_50", label="Shared (50%)"),
            InstitutionFieldOption(value="shared_25", label="Shared (25%)"),
            InstitutionFieldOption(value="visiting", label="Visiting"),
        ],
        effective_from_field_label="From",
        form=form,
        move_footer_note="Changes are saved to the audit log with your name and time.",
        cancel_label="Cancel",
        save_label="Save allocation",
        vacancies_section_title="Vacancies",
        hr_recruitment_label="HR recruitment →",
        hr_recruitment_href="/college-admin/hr/recruitment-management",
        vacancy_items=vacancy_items,
        designation_mix_section_title="Designation mix",
        designation_bars=designation_bars,
        can_save=False,
        footer_disclaimer="Live institutional data · Faculty records, workload and recruitment · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=generated,
    )


async def save_department_faculty_allocation(
    scope: AccessScope,
    payload: DepartmentFacultyAllocationSavePayload,
) -> DepartmentFacultyAllocationSaveResult:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    form = payload.form
    if not form.faculty_user_id:
        raise AppError(code="VALIDATION_ERROR", message="Faculty member is required", status_code=422)
    if not form.allocate_to_department_id:
        raise AppError(code="VALIDATION_ERROR", message="Allocate to department is required", status_code=422)

    user_id = to_object_id(form.faculty_user_id, "faculty_user_id")
    dept_id = to_object_id(form.allocate_to_department_id, "department_id")
    dept = await InstitutionDepartment.get(dept_id)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)

    record = await FacultyRecord.find_one(
        Eq(FacultyRecord.tenant_id, tenant_id),
        Eq(FacultyRecord.user_id, user_id),
    )
    if record is None:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)

    effective_from = _parse_iso_date(form.effective_from)
    allocation_type = (form.allocation_type or "shared_50").strip().lower()
    is_primary = allocation_type == "primary"

    if is_primary:
        record.department_id = dept_id
        record.updated_at = utcnow()
        await record.save()
        user = await User.get(user_id)
        if user:
            user.department_id = dept_id
            await user.save()
        for prev in await FacultyDepartmentAssignment.find(
            Eq(FacultyDepartmentAssignment.tenant_id, tenant_id),
            Eq(FacultyDepartmentAssignment.user_id, user_id),
            Eq(FacultyDepartmentAssignment.is_primary, True),
        ).to_list():
            prev.is_primary = False
            prev.effective_to = effective_from
            await prev.save()

    await FacultyDepartmentAssignment(
        tenant_id=tenant_id,
        user_id=user_id,
        department_id=dept_id,
        is_primary=is_primary,
        effective_from=effective_from,
        actor_id=scope.user_id,
    ).insert()

    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type="department_allocation",
        note=f"{allocation_type} allocation to {dept.department_code}",
        effective_date=effective_from,
        actor_id=scope.user_id,
    ).insert()

    page = await get_department_faculty_allocation_page(scope)
    return DepartmentFacultyAllocationSaveResult(message="Faculty allocation saved", page=page)