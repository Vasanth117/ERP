"""Regulation management page (CA 05 — college admin academics)."""

from __future__ import annotations

import re
from copy import deepcopy
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.college_admin.academic_config_models import (
    AcademicProgramme,
    AcademicRegulation,
    AcademicRegulationCatalog,
    RegulationDocumentEmbed,
    RegulationHighlightEmbed,
    RegulationPhaseOutStepEmbed,
)
from app.modules.college_admin.credit_grading_page_service import _progression_regulation
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    RegulationDocumentRow,
    RegulationHighlightRow,
    RegulationManagementCreate,
    RegulationManagementPageRead,
    RegulationManagementTableRow,
    RegulationPhaseOutStepRow,
)
from app.modules.college_admin.institution_academic_settings_page_service import _DEFAULT_VALUES
from app.modules.students.curriculum_models import CurriculumReference
from app.modules.students.models import StudentProfile

_INSTITUTION_SCOPE = "institution_academic_defaults"

_STATUS_PRESENTATION = {
    "current": ("Current", "success"),
    "active": ("Active", "success"),
    "phasing_out": ("Phasing out", "warning"),
    "draft": ("Draft", "info"),
}


def _batch_year(code: str) -> int | None:
    match = re.search(r"(20\d{2})", code.upper())
    return int(match.group(1)) if match else None


def _display_label(code: str) -> str:
    base = code.strip()
    if "(draft)" in base.lower():
        return base
    return base


async def _institution_rules(tenant_id: PydanticObjectId) -> dict:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _INSTITUTION_SCOPE),
    )
    if doc is None:
        return deepcopy(_DEFAULT_VALUES)
    return {**_DEFAULT_VALUES, **(doc.rules or {})}


def _grading_scheme_label(value: str) -> str:
    mapping = {
        "10_point_relative": "10-point relative grading",
        "10_point_absolute": "10-point absolute grading",
        "letter_grade": "Letter grade (A–F)",
    }
    return mapping.get(value, value.replace("_", " "))


async def _discover_codes(tenant_id: PydanticObjectId) -> set[str]:
    codes: set[str] = set()
    curriculum = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    for ref in curriculum:
        codes.update(ref.academic_regulations)
        if ref.central_version:
            codes.add(ref.central_version)
    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    for course in courses:
        if course.regulation_label:
            codes.add(course.regulation_label.strip())
    catalog = await AcademicRegulationCatalog.find(Eq(AcademicRegulationCatalog.tenant_id, tenant_id)).to_list()
    for row in catalog:
        codes.add(row.regulation_code)
    return {c.strip() for c in codes if c and c.strip()}


def _programmes_for_code(curriculum: list[CurriculumReference], code: str) -> set[str]:
    upper = code.upper()
    progs: set[str] = set()
    for ref in curriculum:
        if upper in {r.upper() for r in ref.academic_regulations}:
            progs.add(ref.programme_code.upper())
        elif ref.central_version and ref.central_version.upper() == upper:
            progs.add(ref.programme_code.upper())
    return progs


async def _sync_catalog(
    tenant_id: PydanticObjectId,
    codes: set[str],
) -> list[AcademicRegulationCatalog]:
    existing = await AcademicRegulationCatalog.find(Eq(AcademicRegulationCatalog.tenant_id, tenant_id)).to_list()
    by_code = {row.regulation_code.upper(): row for row in existing}

    for code in sorted(codes, key=lambda c: _batch_year(c) or 0, reverse=True):
        key = code.upper()
        year = _batch_year(code)
        is_draft = "draft" in code.lower()
        if key not in by_code:
            label = _display_label(code)
            entry = AcademicRegulationCatalog(
                tenant_id=tenant_id,
                regulation_code=key,
                display_label=label,
                effective_from_label=f"{year} batch" if year else None,
                batch_range_label="—",
                status_code="draft" if is_draft else "active",
                status_label=_STATUS_PRESENTATION["draft" if is_draft else "active"][0],
                status_tone=_STATUS_PRESENTATION["draft" if is_draft else "active"][1],
                batch_start_year=year,
                batch_end_year=None,
                is_draft=is_draft,
                sort_order=year or 0,
            )
            await entry.insert()
            by_code[key] = entry

    curriculum = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    active_prog_codes = {p.programme_code.upper() for p in programmes if p.is_active}

    stats: list[tuple[AcademicRegulationCatalog, int, int]] = []
    for entry in by_code.values():
        progs = _programmes_for_code(curriculum, entry.regulation_code)
        prog_count = len(progs & active_prog_codes) or len(progs)
        student_count = sum(1 for profile in profiles if (profile.programme_code or "").upper() in progs)
        batch_years: list[int] = []
        for profile in profiles:
            if (profile.programme_code or "").upper() not in progs:
                continue
            if profile.batch_label:
                match = re.search(r"(20\d{2})", profile.batch_label)
                if match:
                    batch_years.append(int(match.group(1)))
            elif profile.admission_date:
                batch_years.append(profile.admission_date.year)
        if batch_years:
            start, end = min(batch_years), max(batch_years)
            entry.batch_start_year = entry.batch_start_year or start
            if entry.is_draft:
                entry.batch_range_label = "—"
            elif end >= start:
                present = end >= (max(batch_years) if batch_years else end)
                entry.batch_range_label = (
                    f"{start} – present" if present and start == max(batch_years) else f"{start} – {end}"
                )
            entry.batch_end_year = None if "present" in (entry.batch_range_label or "") else end
        entry.effective_from_label = entry.effective_from_label or (
            f"{entry.batch_start_year} batch" if entry.batch_start_year else "—"
        )
        await entry.save()
        stats.append((entry, student_count, prog_count))

    non_draft = [(e, s, p) for e, s, p in stats if not e.is_draft]
    non_draft.sort(key=lambda row: (row[0].batch_start_year or 0, row[1]), reverse=True)
    for index, (entry, student_count, _) in enumerate(non_draft):
        if index == 0 and student_count > 0:
            code, label, tone = "current", "Current", "success"
        elif student_count < 200 and (entry.batch_start_year or 0) < (non_draft[0][0].batch_start_year or 0 if non_draft else 0):
            code, label, tone = "phasing_out", "Phasing out", "warning"
        elif entry.is_draft:
            code, label, tone = "draft", "Draft", "info"
        else:
            code, label, tone = "active", "Active", "success"
        entry.status_code = code
        entry.status_label = label
        entry.status_tone = tone
        entry.sort_order = entry.batch_start_year or 0
        await entry.save()

    return sorted(by_code.values(), key=lambda e: (-(e.batch_start_year or 0), e.regulation_code))


async def _build_highlights(
    tenant_id: PydanticObjectId,
    entry: AcademicRegulationCatalog,
) -> list[RegulationHighlightRow]:
    if entry.highlights:
        return [RegulationHighlightRow(key=h.key, label=h.label, value=h.value) for h in entry.highlights]

    inst = await _institution_rules(tenant_id)
    progression = (await _progression_regulation(tenant_id)).rules or {}
    calc = progression.get("calculation") or {}
    honour_opt = calc.get("honours_additional", "")
    honour_labels = {
        "additional_18": "Allowed from semester 5",
        "additional_24": "Honours track available",
        "none": "Not permitted",
    }
    rows = [
        RegulationHighlightRow(key="grading", label="Grading", value=_grading_scheme_label(str(inst.get("grading_scheme", "")))),
        RegulationHighlightRow(
            key="internal_external",
            label="Internal : external",
            value=str(inst.get("internal_external_weightage", "—")),
        ),
        RegulationHighlightRow(
            key="honours",
            label="Honours / minor",
            value=honour_labels.get(str(honour_opt), str(honour_opt) or "—"),
        ),
        RegulationHighlightRow(
            key="attendance",
            label="Minimum attendance",
            value=str(inst.get("minimum_attendance_for_exams", "—")),
        ),
        RegulationHighlightRow(
            key="max_duration",
            label="Maximum duration",
            value=str(progression.get("max_duration_label") or "As per statute"),
        ),
        RegulationHighlightRow(
            key="approved_by",
            label="Approved by",
            value=entry.approved_by_label or "Academic Council",
        ),
    ]
    return rows


async def get_regulation_management_page(
    scope: AccessScope,
    *,
    regulation_code: str | None = None,
) -> RegulationManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)

    codes = await _discover_codes(tenant_id)
    catalog = await _sync_catalog(tenant_id, codes)

    curriculum = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    active_prog_codes = {p.programme_code.upper() for p in programmes if p.is_active}

    table_rows: list[RegulationManagementTableRow] = []
    selected_code = (regulation_code or "").strip().upper()
    if not selected_code:
        current = next((e for e in catalog if e.status_code == "current"), catalog[0] if catalog else None)
        selected_code = current.regulation_code if current else ""

    for entry in catalog:
        progs = _programmes_for_code(curriculum, entry.regulation_code)
        prog_count = len(progs & active_prog_codes) or len(progs)
        student_count = sum(1 for profile in profiles if (profile.programme_code or "").upper() in progs)
        label = entry.display_label
        if entry.is_draft and "(draft)" not in label.lower():
            label = f"{label} (draft)"
        table_rows.append(
            RegulationManagementTableRow(
                regulation_id=str(entry.id),
                regulation_code=entry.regulation_code,
                regulation_label=label,
                effective_from_label=entry.effective_from_label or "—",
                batch_range_label=entry.batch_range_label or "—",
                student_count=student_count,
                programme_count=prog_count,
                status_code=entry.status_code,
                status_label=entry.status_label,
                status_tone=entry.status_tone,
                is_selected=entry.regulation_code.upper() == selected_code,
            )
        )

    selected = next((e for e in catalog if e.regulation_code.upper() == selected_code), None)
    highlights: list[RegulationHighlightRow] = []
    phase_out: list[RegulationPhaseOutStepRow] = []
    documents: list[RegulationDocumentRow] = []
    if selected:
        highlights = await _build_highlights(tenant_id, selected)
        if selected.phase_out_steps:
            phase_out = [
                RegulationPhaseOutStepRow(
                    step_id=s.step_id,
                    title=s.title,
                    date_label=s.date_label,
                    is_active=s.is_active,
                )
                for s in selected.phase_out_steps
            ]
        elif selected.status_code == "phasing_out":
            phase_out = []
        for doc in selected.documents:
            documents.append(
                RegulationDocumentRow(
                    document_id=doc.document_id,
                    title=doc.title,
                    size_label=doc.size_label,
                    download_label="Download →",
                    download_href=doc.download_href,
                )
            )

    count_label = f"{len(table_rows)} regulation{'s' if len(table_rows) != 1 else ''}"

    return RegulationManagementPageRead(
        page_title="Regulation Management",
        page_subtitle="Academic regulations and which batches follow each one",
        compare_label="Compare regulations",
        compare_href="/college-admin/academics/academic-configuration-history",
        new_regulation_label="New regulation",
        regulations_section_title="Regulations",
        regulations_count_label=count_label,
        table_headers=["Regulation", "Effective from", "Batches", "Students", "Programmes", "Status"],
        regulations=table_rows,
        view_documents_label="View documents →",
        view_documents_href="/college-admin/academics/academic-configuration-history",
        selected_regulation_code=selected_code,
        highlights_section_title=f"{selected.display_label if selected else selected_code} highlights",
        highlight_rows=highlights,
        phase_out_section_title=f"{selected.regulation_code} phase-out plan" if selected else "Phase-out plan",
        phase_out_steps=phase_out,
        documents_section_title="Documents",
        documents=documents,
        footer_disclaimer="Live academic data · Regulations, programmes and student batches · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def create_regulation_management(
    scope: AccessScope,
    payload: RegulationManagementCreate,
) -> RegulationManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.regulation_code.strip().upper()
    if not code:
        raise AppError("Regulation code is required", status_code=400)
    existing = await AcademicRegulationCatalog.find_one(
        Eq(AcademicRegulationCatalog.tenant_id, tenant_id),
        Eq(AcademicRegulationCatalog.regulation_code, code),
    )
    if existing:
        raise AppError("Regulation code already exists", status_code=409)
    year = _batch_year(code)
    label = payload.display_label.strip() if payload.display_label else code
    entry = AcademicRegulationCatalog(
        tenant_id=tenant_id,
        regulation_code=code,
        display_label=label,
        effective_from_label=f"{year} batch" if year else None,
        batch_range_label="—",
        status_code="draft",
        status_label="Draft",
        status_tone="info",
        batch_start_year=year,
        is_draft=True,
        sort_order=year or 0,
    )
    await entry.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="academic.regulation.created",
        resource_type="academic_regulation_catalog",
        resource_id=str(entry.id),
        tenant_id=tenant_id,
    )
    return await get_regulation_management_page(scope, regulation_code=code)