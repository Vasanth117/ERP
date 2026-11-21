"""Batch & section configuration page (CA — college admin academics)."""

from __future__ import annotations

import math
import re
from copy import deepcopy
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicRegulation, ConfigPublicationStatus
from app.modules.college_admin.department_performance_overview_service import _programme_level
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    BatchSectionAddSectionSave,
    BatchSectionAllocationField,
    BatchSectionAllocationRulesForm,
    BatchSectionAllocationRulesSave,
    BatchSectionAutoAllocateSave,
    BatchSectionBatchTab,
    BatchSectionConfigurationPageRead,
    BatchSectionOverviewRow,
    BatchSectionPendingTaskRow,
    BatchSectionTableRow,
    InstitutionFieldOption,
    PoliciesPagination,
)
from app.modules.college_admin.student_admin_models import StudentAdmission, StudentRecord
from app.modules.department_admin.class_management_helpers import section_enrolled_count
from app.modules.department_admin.models import (
    DepartmentBatch,
    DepartmentBatchStatus,
    DepartmentSection,
    DepartmentSectionStatus,
)
from app.modules.students.models import StudentProfile

_SCOPE_KEY = "batch_section_allocation"
_PAGE_SIZE = 6

_DEFAULT_RULES: dict[str, Any] = {
    "default_section_size": "60",
    "allocation_method": "alphabetical",
    "balance_by_gender": "yes",
    "lateral_entry_handling": "distribute_existing",
}

_ALLOCATION_METHOD_OPTIONS = [
    InstitutionFieldOption(value="alphabetical", label="Alphabetical by name"),
    InstitutionFieldOption(value="roll_number", label="By roll number"),
    InstitutionFieldOption(value="random", label="Random (seeded)"),
]

_GENDER_OPTIONS = [
    InstitutionFieldOption(value="yes", label="Yes"),
    InstitutionFieldOption(value="no", label="No"),
]

_LATERAL_OPTIONS = [
    InstitutionFieldOption(value="distribute_existing", label="Distribute to existing sections"),
    InstitutionFieldOption(value="separate_section", label="Dedicated lateral section"),
    InstitutionFieldOption(value="manual", label="Manual allocation only"),
]

_LEVEL_PREFIX = {
    "undergraduate": "B.E.",
    "postgraduate": "M.E.",
    "doctoral": "Ph.D",
}


def _batch_year(label: str) -> int | None:
    match = re.search(r"(20\d{2})", label or "")
    return int(match.group(1)) if match else None


def _normalize_batch_label(year: str) -> str:
    return f"{year} batch"


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


async def _rules(tenant_id: PydanticObjectId) -> dict[str, str]:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    merged = deepcopy(_DEFAULT_RULES)
    if doc and doc.rules:
        for key, value in doc.rules.items():
            merged[key] = str(value)
    return merged


def _rules_form(rules: dict[str, str]) -> BatchSectionAllocationRulesForm:
    return BatchSectionAllocationRulesForm(
        section_title="Allocation rules",
        fields=[
            BatchSectionAllocationField(
                key="default_section_size",
                label="Default section size",
                required=True,
                field_type="number",
                value=rules["default_section_size"],
            ),
            BatchSectionAllocationField(
                key="allocation_method",
                label="Allocation method",
                required=True,
                field_type="select",
                options=_ALLOCATION_METHOD_OPTIONS,
                value=rules["allocation_method"],
            ),
            BatchSectionAllocationField(
                key="balance_by_gender",
                label="Balance by gender",
                required=True,
                field_type="select",
                options=_GENDER_OPTIONS,
                value=rules["balance_by_gender"],
            ),
            BatchSectionAllocationField(
                key="lateral_entry_handling",
                label="Lateral entry handling",
                required=True,
                field_type="select",
                options=_LATERAL_OPTIONS,
                value=rules["lateral_entry_handling"],
            ),
        ],
    )


def _programme_short(prog: AcademicProgramme) -> str:
    prefix = _LEVEL_PREFIX.get(_programme_level(prog), "Prog.")
    return f"{prefix} {prog.programme_code.upper()}"


async def _resolve_central_id(
    tenant_id: PydanticObjectId,
    prog: AcademicProgramme,
    dept_by_id: dict[str, InstitutionDepartment],
) -> PydanticObjectId | None:
    if not prog.department_id:
        return None
    inst = dept_by_id.get(str(prog.department_id))
    if inst is None:
        inst = await InstitutionDepartment.get(prog.department_id)
    if inst is None or inst.tenant_id != tenant_id:
        return None
    return inst.central_department_id or inst.id


def _is_lateral_section(section: DepartmentSection) -> bool:
    blob = f"{section.name} {section.section_code}".lower()
    return "lateral" in blob or section.section_code.upper().startswith("LAT")


def _section_status(
    *,
    section: DepartmentSection,
    enrolled: int,
    is_lateral: bool,
) -> tuple[str, str]:
    if section.coordinator_user_id is None and not is_lateral and section.status != DepartmentSectionStatus.DRAFT:
        return "Pending", "info"
    if is_lateral:
        if enrolled == 0:
            return "Pending", "info"
        return f"{enrolled} students", "info"
    if enrolled >= section.capacity:
        return "Full", "success"
    open_seats = section.capacity - enrolled
    if open_seats > 0:
        return f"{open_seats} open seat{'s' if open_seats != 1 else ''}", "warning"
    return "Open", "warning"


async def _advisor_label(coordinator_id: PydanticObjectId | None) -> str:
    if coordinator_id is None:
        return "—"
    user = await User.get(coordinator_id)
    if user is None:
        return "—"
    return user.full_name


async def _discover_batch_years(tenant_id: PydanticObjectId) -> list[str]:
    years: set[int] = set()
    for row in await DepartmentBatch.find(Eq(DepartmentBatch.tenant_id, tenant_id)).to_list():
        y = _batch_year(row.batch_label)
        if y:
            years.add(y)
    for row in await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list():
        y = _batch_year(row.batch_label)
        if y:
            years.add(y)
    for row in await StudentAdmission.find(Eq(StudentAdmission.tenant_id, tenant_id)).to_list():
        y = _batch_year(row.batch_label)
        if y:
            years.add(y)
    if not years:
        years.add(utcnow().year)
    return [str(y) for y in sorted(years, reverse=True)[:8]]


async def _pick_programme(
    tenant_id: PydanticObjectId,
    batch_label: str,
    programme_code: str | None,
) -> AcademicProgramme | None:
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    if not programmes:
        return None
    if programme_code:
        picked = next((p for p in programmes if p.programme_code.upper() == programme_code.upper()), None)
        if picked:
            return picked
    batches = await DepartmentBatch.find(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.batch_label, batch_label),
    ).to_list()
    if batches:
        code = batches[0].programme_code.upper()
        return next((p for p in programmes if p.programme_code.upper() == code), programmes[0])
    counts: dict[str, int] = {}
    for profile in await StudentProfile.find(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.batch_label, batch_label),
    ).to_list():
        if profile.programme_code:
            code = profile.programme_code.upper()
            counts[code] = counts.get(code, 0) + 1
    if counts:
        top = max(counts, key=counts.get)
        return next((p for p in programmes if p.programme_code.upper() == top), programmes[0])
    return programmes[0]


async def _ensure_batch(
    tenant_id: PydanticObjectId,
    *,
    central_id: PydanticObjectId,
    institution_department_id: PydanticObjectId,
    programme_code: str,
    batch_label: str,
) -> DepartmentBatch:
    existing = await DepartmentBatch.find_one(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.central_department_id, central_id),
        Eq(DepartmentBatch.programme_code, programme_code.upper()),
        Eq(DepartmentBatch.batch_label, batch_label),
    )
    if existing:
        return existing
    doc = DepartmentBatch(
        tenant_id=tenant_id,
        institution_department_id=institution_department_id,
        central_department_id=central_id,
        programme_code=programme_code.upper(),
        batch_label=batch_label,
        admission_year=str(_batch_year(batch_label) or ""),
        status=DepartmentBatchStatus.ACTIVE,
    )
    await doc.insert()
    return doc


async def get_batch_section_configuration_page(
    scope: AccessScope,
    *,
    batch_year: str | None = None,
    programme_code: str | None = None,
    page: int = 1,
) -> BatchSectionConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    generated = utcnow()
    rules = await _rules(tenant_id)

    years = await _discover_batch_years(tenant_id)
    selected_year = batch_year if batch_year in years else years[0]
    batch_label = _normalize_batch_label(selected_year)

    batch_tabs = [
        BatchSectionBatchTab(batch_year=y, label=f"{y} batch", active=y == selected_year) for y in years[:4]
    ]

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    dept_rows = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
    dept_by_id = {str(d.id): d for d in dept_rows}

    prog = await _pick_programme(tenant_id, batch_label, programme_code)
    programme_options = [
        InstitutionFieldOption(value=p.programme_code.upper(), label=_programme_short(p)) for p in programmes
    ]
    if prog is None:
        snapshot = generated.astimezone().strftime("%d %b %Y, %H:%M IST")
        return BatchSectionConfigurationPageRead(
            page_title="Batch & Section Configuration",
            page_subtitle="Batches by admission year and their sections, capacity and advisors",
            auto_allocate_label="Auto-allocate sections",
            add_section_label="Add section",
            batch_tabs=batch_tabs,
            selected_batch_year=selected_year,
            selected_programme_code="",
            programme_options=programme_options,
            sections_panel_title="Sections",
            table_headers=["Section", "Class advisor", "Capacity", "Allocated", "Room", "Status"],
            section_rows=[],
            section_summary_label="0 sections · 0 students",
            pagination=PoliciesPagination(
                page=1,
                page_size=_PAGE_SIZE,
                total=0,
                total_pages=0,
                page_numbers=[],
                has_previous=False,
                has_next=False,
            ),
            allocation_rules=_rules_form(rules),
            overview_title="Batches",
            overview_rows=[],
            pending_tasks_title="Pending tasks",
            pending_tasks=[],
            footer_note="Changes are saved to the audit log with your name and time.",
            cancel_label="Cancel",
            save_label="Save sections",
            footer_disclaimer="Live academic configuration · Batches and sections · All times IST",
            footer_snapshot_label=f"Sample snapshot · {snapshot}",
            generated_at=generated,
        )

    central_id = await _resolve_central_id(tenant_id, prog, dept_by_id)
    inst_dept = dept_by_id.get(str(prog.department_id)) if prog.department_id else None

    section_docs: list[DepartmentSection] = []
    if central_id:
        batch = await DepartmentBatch.find_one(
            Eq(DepartmentBatch.tenant_id, tenant_id),
            Eq(DepartmentBatch.central_department_id, central_id),
            Eq(DepartmentBatch.programme_code, prog.programme_code.upper()),
            Eq(DepartmentBatch.batch_label, batch_label),
        )
        if batch:
            section_docs = await DepartmentSection.find(
                Eq(DepartmentSection.tenant_id, tenant_id),
                Eq(DepartmentSection.department_batch_id, batch.id),
            ).sort("+section_code").to_list()

    table_rows: list[BatchSectionTableRow] = []
    total_students = 0
    for section in section_docs:
        enrolled = 0
        if central_id:
            enrolled = await section_enrolled_count(
                tenant_id,
                central_id,
                programme_code=prog.programme_code,
                batch_label=batch_label,
                section_code=section.section_code,
            )
        total_students += enrolled
        is_lateral = _is_lateral_section(section)
        status_label, status_tone = _section_status(section=section, enrolled=enrolled, is_lateral=is_lateral)
        capacity_label = "—" if is_lateral else str(section.capacity)
        table_rows.append(
            BatchSectionTableRow(
                section_id=str(section.id),
                section_label=section.name if section.name else f"Section {section.section_code}",
                advisor_label=await _advisor_label(section.coordinator_user_id),
                capacity_label=capacity_label,
                allocated_count=enrolled if not is_lateral else enrolled,
                room_label=section.room_label or "—",
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    total = len(table_rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    offset = (page - 1) * _PAGE_SIZE
    page_rows = table_rows[offset : offset + _PAGE_SIZE]

    overview_rows: list[BatchSectionOverviewRow] = []
    for year in years[:4]:
        label = _normalize_batch_label(year)
        cap = 0
        filled = 0
        for batch in await DepartmentBatch.find(
            Eq(DepartmentBatch.tenant_id, tenant_id),
            Eq(DepartmentBatch.batch_label, label),
        ).to_list():
            central = batch.central_department_id
            sections = await DepartmentSection.find(
                Eq(DepartmentSection.tenant_id, tenant_id),
                Eq(DepartmentSection.department_batch_id, batch.id),
            ).to_list()
            for sec in sections:
                if _is_lateral_section(sec):
                    continue
                cap += sec.capacity
                filled += await section_enrolled_count(
                    tenant_id,
                    central,
                    programme_code=batch.programme_code,
                    batch_label=label,
                    section_code=sec.section_code,
                )
        if cap <= 0:
            cap = filled or 1
        overview_rows.append(
            BatchSectionOverviewRow(
                batch_label=f"{year} batch",
                seats_filled_label=f"{filled:,} of {max(cap, filled):,} seats",
                bar_percent=round(min(100, 100 * filled / cap), 1) if cap else 0,
            )
        )

    pending: list[BatchSectionPendingTaskRow] = []
    lateral_unallocated = 0
    if central_id:
        lateral_profiles = await StudentProfile.find(
            {
                "tenant_id": tenant_id,
                "department_id": central_id,
                "programme_code": prog.programme_code.upper(),
                "batch_label": batch_label,
                "$or": [{"section_code": None}, {"section_code": ""}],
            }
        ).to_list()
        for profile in lateral_profiles:
            category = ""
            if profile.admission_number:
                admission = await StudentAdmission.find_one(
                    Eq(StudentAdmission.tenant_id, tenant_id),
                    Eq(StudentAdmission.admission_number, profile.admission_number),
                )
                if admission and admission.metadata:
                    category = str(admission.metadata.get("category", "")).lower()
            if "lateral" in category or "lateral" in (profile.batch_label or "").lower():
                lateral_unallocated += 1
    if lateral_unallocated > 0:
        pending.append(
            BatchSectionPendingTaskRow(
                task_id="lateral-unallocated",
                title=f"{lateral_unallocated} lateral entry student{'s' if lateral_unallocated != 1 else ''}",
                subtitle="Need section allocation",
                action_label="Allocate",
                action_kind="auto_allocate_lateral",
                status_tone="warning",
            )
        )

    missing_advisor = [s for s in section_docs if s.coordinator_user_id is None and not _is_lateral_section(s)]
    if missing_advisor:
        first = missing_advisor[0]
        pending.append(
            BatchSectionPendingTaskRow(
                task_id=f"missing-advisor-{first.id}",
                title="Class advisor missing",
                subtitle=f"{_programme_short(prog)} {selected_year} – {first.name or first.section_code}",
                action_label="Assign",
                action_kind="assign_advisor",
                action_href="/college-admin/organization/department-faculty-allocation",
                status_tone="danger",
            )
        )

    snapshot = generated.astimezone().strftime("%d %b %Y, %H:%M IST")
    summary = f"{total} section{'s' if total != 1 else ''} · {total_students:,} students"

    return BatchSectionConfigurationPageRead(
        page_title="Batch & Section Configuration",
        page_subtitle="Batches by admission year and their sections, capacity and advisors",
        auto_allocate_label="Auto-allocate sections",
        add_section_label="Add section",
        batch_tabs=batch_tabs,
        selected_batch_year=selected_year,
        selected_programme_code=prog.programme_code.upper(),
        programme_options=programme_options,
        sections_panel_title=f"{_programme_short(prog)} – {batch_label} sections",
        table_headers=["Section", "Class advisor", "Capacity", "Allocated", "Room", "Status"],
        section_rows=page_rows,
        section_summary_label=summary,
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        allocation_rules=_rules_form(rules),
        overview_title="Batches",
        overview_rows=overview_rows,
        pending_tasks_title="Pending tasks",
        pending_tasks=pending,
        footer_note="Changes are saved to the audit log with your name and time.",
        cancel_label="Cancel",
        save_label="Save sections",
        footer_disclaimer="Live academic configuration · Batches and sections · All times IST",
        footer_snapshot_label=f"Sample snapshot · {snapshot}",
        generated_at=generated,
    )


async def save_batch_section_allocation_rules(
    scope: AccessScope,
    payload: BatchSectionAllocationRulesSave,
) -> BatchSectionConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rules = {
        "default_section_size": str(payload.default_section_size),
        "allocation_method": payload.allocation_method,
        "balance_by_gender": payload.balance_by_gender,
        "lateral_entry_handling": payload.lateral_entry_handling,
    }
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        doc = AcademicRegulation(tenant_id=tenant_id, scope_key=_SCOPE_KEY, rules=rules)
        await doc.insert()
    else:
        doc.rules = rules
        doc.updated_at = utcnow()
        await doc.save()
    await record_audit(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        action="batch_section.rules_saved",
        resource_type="academic_regulation",
        resource_id=str(doc.id),
        metadata=rules,
    )
    return await get_batch_section_configuration_page(scope)


async def add_batch_section_configuration_section(
    scope: AccessScope,
    payload: BatchSectionAddSectionSave,
) -> BatchSectionConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog = next((p for p in programmes if p.programme_code.upper() == payload.programme_code.upper()), None)
    if prog is None:
        raise AppError(code="NOT_FOUND", message="Programme not found", status_code=404)
    dept_by_id = {str(d.id): d for d in await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()}
    central_id = await _resolve_central_id(tenant_id, prog, dept_by_id)
    if central_id is None or not prog.department_id:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not linked to a department", status_code=422)
    inst = dept_by_id.get(str(prog.department_id))
    if inst is None:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)
    batch = await _ensure_batch(
        tenant_id,
        central_id=central_id,
        institution_department_id=inst.id,
        programme_code=prog.programme_code,
        batch_label=payload.batch_label.strip(),
    )
    code = payload.section_code.strip().upper()
    if await DepartmentSection.find_one(
        Eq(DepartmentSection.tenant_id, tenant_id),
        Eq(DepartmentSection.department_batch_id, batch.id),
        Eq(DepartmentSection.section_code, code),
    ):
        raise AppError(code="CONFLICT", message="Section code already exists", status_code=409)
    rules = await _rules(tenant_id)
    default_cap = int(rules.get("default_section_size", "60"))
    section = DepartmentSection(
        tenant_id=tenant_id,
        department_batch_id=batch.id,
        central_department_id=central_id,
        section_code=code,
        name=payload.section_name.strip(),
        capacity=payload.capacity or default_cap,
        room_label=payload.room_label.strip() if payload.room_label else None,
        status=DepartmentSectionStatus.ACTIVE,
    )
    await section.insert()
    await record_audit(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        action="batch_section.section_added",
        resource_type="department_section",
        resource_id=str(section.id),
        metadata={"batch_label": batch.batch_label, "section_code": code},
    )
    year = str(_batch_year(batch.batch_label) or utcnow().year)
    return await get_batch_section_configuration_page(
        scope,
        batch_year=year,
        programme_code=prog.programme_code,
    )


async def auto_allocate_batch_sections(
    scope: AccessScope,
    payload: BatchSectionAutoAllocateSave,
) -> BatchSectionConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rules = await _rules(tenant_id)
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog = next((p for p in programmes if p.programme_code.upper() == payload.programme_code.upper()), None)
    if prog is None:
        raise AppError(code="NOT_FOUND", message="Programme not found", status_code=404)
    batch_label = payload.batch_label.strip()
    dept_by_id = {str(d.id): d for d in await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()}
    central_id = await _resolve_central_id(tenant_id, prog, dept_by_id)
    if central_id is None:
        raise AppError(code="VALIDATION_ERROR", message="Programme department missing", status_code=422)
    batch = await DepartmentBatch.find_one(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.central_department_id, central_id),
        Eq(DepartmentBatch.programme_code, prog.programme_code.upper()),
        Eq(DepartmentBatch.batch_label, batch_label),
    )
    if batch is None:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)

    sections = await DepartmentSection.find(
        Eq(DepartmentSection.tenant_id, tenant_id),
        Eq(DepartmentSection.department_batch_id, batch.id),
    ).to_list()
    regular = [s for s in sections if not _is_lateral_section(s) and s.status == DepartmentSectionStatus.ACTIVE]
    if not regular:
        raise AppError(code="VALIDATION_ERROR", message="No active sections to allocate into", status_code=422)

    unallocated = await StudentProfile.find(
        {
            "tenant_id": tenant_id,
            "department_id": central_id,
            "programme_code": prog.programme_code.upper(),
            "batch_label": batch_label,
            "$or": [{"section_code": None}, {"section_code": ""}],
        }
    ).to_list()

    method = rules.get("allocation_method", "alphabetical")
    if method == "roll_number":
        unallocated.sort(key=lambda p: (p.roll_number or "", p.student_id or ""))
    else:
        unallocated.sort(key=lambda p: (p.student_id or "", str(p.user_id)))

    seats: dict[str, int] = {}
    for sec in regular:
        enrolled = await section_enrolled_count(
            tenant_id,
            central_id,
            programme_code=prog.programme_code,
            batch_label=batch_label,
            section_code=sec.section_code,
        )
        seats[sec.section_code.upper()] = max(sec.capacity - enrolled, 0)

    for profile in unallocated:
        target = next((code for code, open_seats in seats.items() if open_seats > 0), None)
        if target is None:
            break
        profile.section_code = target
        profile.updated_at = utcnow()
        await profile.save()
        if profile.user_id:
            record = await StudentRecord.find_one(
                Eq(StudentRecord.tenant_id, tenant_id),
                Eq(StudentRecord.user_id, profile.user_id),
            )
            if record:
                record.section_code = target
                record.updated_at = utcnow()
                await record.save()
        seats[target] -= 1

    await record_audit(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        action="batch_section.auto_allocated",
        resource_type="department_batch",
        resource_id=str(batch.id),
        metadata={"batch_label": batch_label, "students_allocated": len(unallocated)},
    )
    year = str(_batch_year(batch_label) or utcnow().year)
    return await get_batch_section_configuration_page(
        scope,
        batch_year=year,
        programme_code=prog.programme_code,
    )