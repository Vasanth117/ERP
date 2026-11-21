"""Batch & section allocation workspace (CA 06.09 — Students tab)."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicRegulation
from app.modules.college_admin.batch_section_configuration_page_service import (
    _SCOPE_KEY,
    _batch_year,
    _is_lateral_section,
    _programme_short,
    _rules,
)
from app.modules.college_admin.department_performance_overview_service import _programme_level
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    BatchSectionAllocationField,
    BatchSectionAllocationPageRead,
    BatchSectionAllocationRulesSubmit,
    BatchSectionAllocationSectionRow,
    BatchSectionAllocationUnallocatedRow,
    InstitutionFieldOption,
    PoliciesPagination,
)
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.college_admin.student_statistics_overview_service import _study_year
from app.modules.department_admin.class_management_helpers import section_enrolled_count
from app.modules.department_admin.models import DepartmentBatch, DepartmentBatchStatus, DepartmentSection, DepartmentSectionStatus
from app.modules.hostel.hostel_models import HostelRoomAllocation
from app.modules.students.models import StudentProfile

_reader = OperationalDataReader()
_SECTION_PAGE_SIZE = 4
_UNALLOCATED_PAGE_SIZE = 6

_METHOD_OPTIONS = [
    InstitutionFieldOption(value="alphabetical_balanced", label="Alphabetical balanced"),
    InstitutionFieldOption(value="alphabetical", label="Alphabetical by name"),
    InstitutionFieldOption(value="roll_number", label="By roll number"),
    InstitutionFieldOption(value="random", label="Random (seeded)"),
]

_KEEP_GROUP_OPTIONS = [
    InstitutionFieldOption(value="none", label="No grouping"),
    InstitutionFieldOption(value="hostel_blocks", label="Hostel blocks"),
    InstitutionFieldOption(value="programme", label="Programme"),
    InstitutionFieldOption(value="gender", label="Gender"),
]

_LEVEL_PREFIX = {
    "undergraduate": "B.E.",
    "postgraduate": "M.E.",
    "doctoral": "Ph.D",
}


def _programme_table_label(prog: AcademicProgramme) -> str:
    prefix = _LEVEL_PREFIX.get(_programme_level(prog), "Prog.")
    if prog.name:
        return f"{prefix} {prog.name}"
    return _programme_short(prog)


def _strength_status(enrolled: int, capacity: int) -> tuple[str, str]:
    if capacity <= 0:
        return "Open", "success"
    if enrolled >= capacity:
        return "Full", "muted"
    if enrolled >= max(1, int(capacity * 0.92)):
        return "Near full", "warning"
    return "Open", "success"


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _rules_to_ui(rules: dict[str, str]) -> dict[str, str]:
    method = rules.get("allocation_method", "alphabetical")
    balance = rules.get("balance_by_gender", "yes")
    if method == "alphabetical" and balance == "yes":
        ui_method = "alphabetical_balanced"
    else:
        ui_method = method if method in {o.value for o in _METHOD_OPTIONS} else "alphabetical_balanced"
    return {
        "allocation_method": ui_method,
        "default_section_size": rules.get("default_section_size", "65"),
        "keep_groups_together": rules.get("keep_groups_together", "hostel_blocks"),
    }


def _ui_to_storage(ui: dict[str, str]) -> dict[str, str]:
    method = ui.get("allocation_method", "alphabetical_balanced")
    if method == "alphabetical_balanced":
        return {
            "allocation_method": "alphabetical",
            "balance_by_gender": "yes",
            "default_section_size": str(ui.get("default_section_size", "65")),
            "keep_groups_together": ui.get("keep_groups_together", "none"),
            "lateral_entry_handling": "distribute_existing",
        }
    return {
        "allocation_method": method,
        "balance_by_gender": "no",
        "default_section_size": str(ui.get("default_section_size", "65")),
        "keep_groups_together": ui.get("keep_groups_together", "none"),
        "lateral_entry_handling": "distribute_existing",
    }


def _allocation_rules_form(ui: dict[str, str]) -> list[BatchSectionAllocationField]:
    return [
        BatchSectionAllocationField(
            key="allocation_method",
            label="Method",
            required=True,
            field_type="select",
            options=_METHOD_OPTIONS,
            value=ui["allocation_method"],
        ),
        BatchSectionAllocationField(
            key="default_section_size",
            label="Max per section",
            required=True,
            field_type="number",
            value=ui["default_section_size"],
        ),
        BatchSectionAllocationField(
            key="keep_groups_together",
            label="Keep groups together",
            required=True,
            field_type="select",
            options=_KEEP_GROUP_OPTIONS,
            value=ui["keep_groups_together"],
        ),
    ]


async def _hostel_block_key(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> str:
    alloc = await HostelRoomAllocation.find_one(
        Eq(HostelRoomAllocation.tenant_id, tenant_id),
        Eq(HostelRoomAllocation.student_user_id, user_id),
    )
    if alloc and alloc.block:
        return alloc.block.lower()
    return "zz_none"


async def _sort_unallocated(
    tenant_id: PydanticObjectId,
    profiles: list[StudentProfile],
    rules: dict[str, str],
) -> list[StudentProfile]:
    method = rules.get("allocation_method", "alphabetical")
    keep = rules.get("keep_groups_together", "none")

    if keep == "hostel_blocks":
        enriched: list[tuple[str, str, StudentProfile]] = []
        for p in profiles:
            block = await _hostel_block_key(tenant_id, p.user_id)
            name_key = p.student_id or str(p.user_id)
            enriched.append((block, name_key, p))
        enriched.sort(key=lambda row: (row[0], row[1]))
        return [row[2] for row in enriched]
    if keep == "programme":
        profiles.sort(key=lambda p: (p.programme_code or "", p.roll_number or "", str(p.user_id)))
        return profiles
    if method == "roll_number":
        profiles.sort(key=lambda p: (p.roll_number or "", p.student_id or "", str(p.user_id)))
        return profiles
    profiles.sort(key=lambda p: (p.student_id or "", str(p.user_id)))
    return profiles


async def _build_section_rows(tenant_id: PydanticObjectId, ay_label: str | None) -> list[BatchSectionAllocationSectionRow]:
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}

    batches = await DepartmentBatch.find(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.status, DepartmentBatchStatus.ACTIVE),
    ).to_list()
    batch_by_id = {b.id: b for b in batches if b.id is not None}

    sections = await DepartmentSection.find(
        Eq(DepartmentSection.tenant_id, tenant_id),
        Eq(DepartmentSection.status, DepartmentSectionStatus.ACTIVE),
    ).to_list()

    rows: list[BatchSectionAllocationSectionRow] = []
    for section in sorted(sections, key=lambda s: (s.section_code, s.name)):
        if _is_lateral_section(section):
            continue
        batch = batch_by_id.get(section.department_batch_id)
        if batch is None:
            continue
        prog = prog_by_code.get(batch.programme_code.upper())
        programme_label = _programme_table_label(prog) if prog else batch.programme_code
        enrolled = await section_enrolled_count(
            tenant_id,
            section.central_department_id,
            programme_code=batch.programme_code,
            batch_label=batch.batch_label,
            section_code=section.section_code,
        )
        status_label, status_tone = _strength_status(enrolled, section.capacity)
        sem = _study_year(batch.batch_label, ay_label)
        rows.append(
            BatchSectionAllocationSectionRow(
                section_id=str(section.id),
                section_label=section.name or f"Section {section.section_code}",
                programme_label=programme_label,
                semester_label=str(sem) if sem is not None else "—",
                strength_count=enrolled,
                capacity_count=section.capacity,
                status_label=status_label,
                status_tone=status_tone,
            )
        )
    return rows


async def get_batch_section_allocation_page(
    scope: AccessScope,
    *,
    section_page: int = 1,
    unallocated_page: int = 1,
) -> BatchSectionAllocationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    ay_label, _ = await _reader.current_academic_term(tenant_id)

    rules_raw = await _rules(tenant_id)
    ui_rules = _rules_to_ui(rules_raw)

    section_rows_all = await _build_section_rows(tenant_id, ay_label)
    total_sections = len(section_rows_all)
    section_total_pages = math.ceil(total_sections / _SECTION_PAGE_SIZE) if total_sections else 0
    section_page = min(max(1, section_page), section_total_pages or 1)
    sec_start = (section_page - 1) * _SECTION_PAGE_SIZE
    section_slice = section_rows_all[sec_start : sec_start + _SECTION_PAGE_SIZE]

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    eligible = [
        r
        for r in records
        if r.lifecycle_status in (StudentLifecycleStatus.ACTIVE, StudentLifecycleStatus.ADMITTED)
        and not (r.section_code or "").strip()
    ]
    user_ids = [r.user_id for r in eligible]
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users if u.id is not None}

    profiles = await StudentProfile.find(
        Eq(StudentProfile.tenant_id, tenant_id),
        In(StudentProfile.user_id, user_ids),
    ).to_list() if user_ids else []
    profile_by_user = {p.user_id: p for p in profiles}

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}

    unallocated_all: list[BatchSectionAllocationUnallocatedRow] = []
    for record in eligible:
        user = user_by_id.get(record.user_id)
        if user is None:
            continue
        profile = profile_by_user.get(record.user_id)
        code = (record.programme_code or (profile.programme_code if profile else "") or "").upper()
        prog = prog_by_code.get(code)
        programme_label = _programme_table_label(prog) if prog else (code or "—")
        register = record.roll_number or record.student_id or (profile.roll_number if profile else "") or "—"
        unallocated_all.append(
            BatchSectionAllocationUnallocatedRow(
                record_id=str(record.id),
                student_name=user.full_name,
                register_number=register,
                programme_label=programme_label,
                detail_href=f"/college-admin/students/student-details?id={record.id}",
            )
        )

    unallocated_all.sort(key=lambda row: row.student_name.lower())
    total_unallocated = len(unallocated_all)
    unalloc_total_pages = math.ceil(total_unallocated / _UNALLOCATED_PAGE_SIZE) if total_unallocated else 0
    unallocated_page = min(max(1, unallocated_page), unalloc_total_pages or 1)
    un_start = (unallocated_page - 1) * _UNALLOCATED_PAGE_SIZE
    unallocated_slice = unallocated_all[un_start : un_start + _UNALLOCATED_PAGE_SIZE]

    return BatchSectionAllocationPageRead(
        page_title="Batch & Section Allocation",
        page_subtitle="Allocate students to sections",
        auto_allocate_label="Auto-allocate",
        confirm_label="Confirm",
        section_strength_title="Section strength",
        section_summary_label=f"{len(section_slice)} of {total_sections:,} sections",
        section_table_headers=["Section", "Programme", "Sem", "Strength", "Capacity", "Status"],
        section_rows=section_slice,
        section_pagination=PoliciesPagination(
            page=section_page,
            page_size=_SECTION_PAGE_SIZE,
            total=total_sections,
            total_pages=section_total_pages,
            page_numbers=_page_numbers(section_total_pages),
            has_previous=section_page > 1 and bool(total_sections),
            has_next=section_page < section_total_pages,
        ),
        allocation_rules_title="Allocation rule",
        allocation_rules_fields=_allocation_rules_form(ui_rules),
        unallocated_title="Unallocated students",
        unallocated_summary_label=f"{len(unallocated_slice)} of {total_unallocated:,}",
        unallocated_table_headers=["Student", "Register no.", "Programme"],
        unallocated_rows=unallocated_slice,
        unallocated_pagination=PoliciesPagination(
            page=unallocated_page,
            page_size=_UNALLOCATED_PAGE_SIZE,
            total=total_unallocated,
            total_pages=unalloc_total_pages,
            page_numbers=_page_numbers(unalloc_total_pages),
            has_previous=unallocated_page > 1 and bool(total_unallocated),
            has_next=unallocated_page < unalloc_total_pages,
        ),
        updated_at_label=_fmt_time_label(now),
        footer_disclaimer="Live institutional data · Student section allocation · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def _persist_rules(tenant_id: PydanticObjectId, scope: AccessScope, storage: dict[str, str]) -> None:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        doc = AcademicRegulation(tenant_id=tenant_id, scope_key=_SCOPE_KEY, rules=storage)
        await doc.insert()
    else:
        merged = deepcopy(doc.rules or {})
        merged.update(storage)
        doc.rules = merged
        doc.updated_at = utcnow()
        await doc.save()
    await record_audit(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        action="batch_section_allocation.rules_saved",
        resource_type="academic_regulation",
        resource_id=str(doc.id),
        metadata=storage,
    )


async def save_batch_section_allocation_rules(
    scope: AccessScope,
    payload: BatchSectionAllocationRulesSubmit,
) -> BatchSectionAllocationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    ui = {
        "allocation_method": payload.allocation_method,
        "default_section_size": str(payload.max_per_section),
        "keep_groups_together": payload.keep_groups_together,
    }
    await _persist_rules(tenant_id, scope, _ui_to_storage(ui))
    return await get_batch_section_allocation_page(
        scope,
        section_page=payload.section_page,
        unallocated_page=payload.unallocated_page,
    )


async def auto_allocate_batch_section_allocation(
    scope: AccessScope,
    *,
    section_page: int = 1,
    unallocated_page: int = 1,
) -> BatchSectionAllocationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rules = await _rules(tenant_id)

    batches = await DepartmentBatch.find(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.status, DepartmentBatchStatus.ACTIVE),
    ).to_list()

    allocated_count = 0
    for batch in batches:
        sections = await DepartmentSection.find(
            Eq(DepartmentSection.tenant_id, tenant_id),
            Eq(DepartmentSection.department_batch_id, batch.id),
            Eq(DepartmentSection.status, DepartmentSectionStatus.ACTIVE),
        ).to_list()
        regular = [s for s in sections if not _is_lateral_section(s)]
        if not regular:
            continue

        unallocated_profiles = await StudentProfile.find(
            {
                "tenant_id": tenant_id,
                "department_id": batch.central_department_id,
                "programme_code": batch.programme_code.upper(),
                "batch_label": batch.batch_label,
                "$or": [{"section_code": None}, {"section_code": ""}],
            }
        ).to_list()
        if not unallocated_profiles:
            continue

        unallocated_profiles = await _sort_unallocated(tenant_id, unallocated_profiles, rules)

        seats: dict[str, int] = {}
        for sec in regular:
            enrolled = await section_enrolled_count(
                tenant_id,
                batch.central_department_id,
                programme_code=batch.programme_code,
                batch_label=batch.batch_label,
                section_code=sec.section_code,
            )
            seats[sec.section_code.upper()] = max(sec.capacity - enrolled, 0)

        for profile in unallocated_profiles:
            target = next((code for code, open_seats in seats.items() if open_seats > 0), None)
            if target is None:
                break
            profile.section_code = target
            profile.updated_at = utcnow()
            await profile.save()
            record = await StudentRecord.find_one(
                Eq(StudentRecord.tenant_id, tenant_id),
                Eq(StudentRecord.user_id, profile.user_id),
            )
            if record:
                record.section_code = target
                record.updated_at = utcnow()
                record.updated_by = scope.user_id
                await record.save()
            seats[target] -= 1
            allocated_count += 1

    await record_audit(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        action="batch_section_allocation.auto_allocated",
        resource_type="department_batch",
        resource_id=_SCOPE_KEY,
        metadata={"students_allocated": allocated_count},
    )
    return await get_batch_section_allocation_page(
        scope,
        section_page=section_page,
        unallocated_page=unallocated_page,
    )


async def confirm_batch_section_allocation(
    scope: AccessScope,
    payload: BatchSectionAllocationRulesSubmit,
) -> BatchSectionAllocationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    ui = {
        "allocation_method": payload.allocation_method,
        "default_section_size": str(payload.max_per_section),
        "keep_groups_together": payload.keep_groups_together,
    }
    storage = _ui_to_storage(ui)
    storage["last_confirmed_at"] = utcnow().isoformat()
    await _persist_rules(tenant_id, scope, storage)
    await record_audit(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        action="batch_section_allocation.confirmed",
        resource_type="academic_regulation",
        resource_id=_SCOPE_KEY,
        metadata={"confirmed_at": storage["last_confirmed_at"]},
    )
    return await get_batch_section_allocation_page(
        scope,
        section_page=payload.section_page,
        unallocated_page=payload.unallocated_page,
    )