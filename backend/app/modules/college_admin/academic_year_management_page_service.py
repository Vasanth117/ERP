"""Academic year management page (CA 05.02 – college admin academics)."""

from __future__ import annotations

import math
import re
from uuid import uuid4
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.college_admin.academic_config_models import (
    AcademicTerm,
    AcademicYear,
    ConfigPublicationStatus,
)
from app.modules.college_admin.institution_service import _ensure_settings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicYearClosingChecklistItem,
    AcademicYearCreateFormField,
    AcademicYearCreateFormOption,
    AcademicYearManagementCreate,
    AcademicYearManagementPageRead,
    AcademicYearManagementRulesSave,
    AcademicYearManagementTableRow,
    AcademicYearRuleToggle,
)
from app.modules.college_admin.settings_registry import merge_institution_settings
from app.modules.college_admin.years_semesters_nav import years_semesters_sub_nav
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.examinations.result_publication_models import SemesterResultPublication
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentEnrollment, StudentEnrollmentHistory

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 8
_SETTINGS_ONLY_CURRENT = "academic_only_one_current_year"
_SETTINGS_LOCK_CLOSED = "academic_lock_closed_years"

_TERM_PRESETS: list[tuple[str, str]] = [
    ("ODD", "Odd semester"),
    ("EVEN", "Even semester"),
    ("SUMMER", "Summer term"),
    ("SPECIAL", "Special term"),
]


def _format_date(value) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y")


def _year_status(year: AcademicYear, today) -> tuple[str, str, str]:
    if year.is_current:
        return "current", "Current", "success"
    if year.status == ConfigPublicationStatus.ARCHIVED:
        return "archived", "Archived", "muted"
    if year.end_date and year.end_date < today:
        return "closed", "Closed", "muted"
    if year.start_date and year.start_date > today:
        return "planned", "Planned", "info"
    if year.status == ConfigPublicationStatus.PUBLISHED:
        return "published", "Published", "info"
    return "draft", "Draft", "warning"


def _settings_bool(settings: dict, key: str, default: bool) -> bool:
    raw = settings.get(key)
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.lower() in {"1", "true", "yes", "on"}
    return bool(raw)


async def _student_counts_by_year(tenant_id: PydanticObjectId) -> dict[str, int]:
    enrollments = await StudentEnrollment.find(Eq(StudentEnrollment.tenant_id, tenant_id)).to_list()
    counts: dict[str, set[PydanticObjectId]] = {}
    for row in enrollments:
        if row.status not in {
            StudentEnrollmentStatus.ACTIVE,
            StudentEnrollmentStatus.PROVISIONAL,
            StudentEnrollmentStatus.COMPLETED,
        }:
            continue
        counts.setdefault(row.academic_year_label, set()).add(row.user_id)
    return {label: len(users) for label, users in counts.items()}


async def _build_closing_checklist(
    tenant_id: PydanticObjectId,
    year: AcademicYear | None,
) -> list[AcademicYearClosingChecklistItem]:
    if year is None:
        return []
    label = year.label
    enrollments = await StudentEnrollment.find(
        Eq(StudentEnrollment.tenant_id, tenant_id),
        Eq(StudentEnrollment.academic_year_label, label),
    ).to_list()
    active_students = {row.user_id for row in enrollments}
    publications = await SemesterResultPublication.find(
        Eq(SemesterResultPublication.tenant_id, tenant_id),
        Eq(SemesterResultPublication.academic_year_label, label),
    ).to_list()
    published_students = {
        row.student_user_id
        for row in publications
        if row.status == SemesterResultPublicationStatus.PUBLISHED and row.published_at is not None
    }
    results_complete = not active_students or active_students.issubset(published_students)

    provisional = any(row.status == StudentEnrollmentStatus.PROVISIONAL for row in enrollments)
    promotions_complete = not provisional

    open_demands = 0
    if active_students:
        demands = await StudentFeeDemand.find(
            Eq(StudentFeeDemand.tenant_id, tenant_id),
            In(StudentFeeDemand.student_user_id, list(active_students)),
            Eq(StudentFeeDemand.status, FeeDemandStatus.OPEN),
        ).to_list()
        open_demands = len(demands)
    fees_complete = open_demands == 0

    history_rows = await StudentEnrollmentHistory.find(
        Eq(StudentEnrollmentHistory.tenant_id, tenant_id),
        Eq(StudentEnrollmentHistory.academic_year_label, label),
    ).to_list()
    archive_complete = bool(history_rows) or not active_students

    year_closed = not year.is_current and (
        year.status == ConfigPublicationStatus.ARCHIVED
        or (year.end_date is not None and year.end_date < utcnow().date())
    )

    terms = await AcademicTerm.find(
        Eq(AcademicTerm.tenant_id, tenant_id),
        Eq(AcademicTerm.academic_year_id, year.id),
    ).to_list()
    non_current_terms = [t for t in terms if not t.is_current]
    due_term = non_current_terms[-1] if non_current_terms else (terms[-1] if terms else None)
    results_due = (
        f"{due_term.label} · due {_format_date(due_term.end_date)}"
        if due_term and due_term.end_date
        else None
    )

    return [
        AcademicYearClosingChecklistItem(
            key="results",
            title="All results published",
            detail=results_due if not results_complete and results_due else (None if results_complete else f"{len(active_students - published_students)} students pending"),
            completed=results_complete,
        ),
        AcademicYearClosingChecklistItem(
            key="promotions",
            title="Promotions processed",
            detail=None if promotions_complete else "Auto after results",
            completed=promotions_complete,
        ),
        AcademicYearClosingChecklistItem(
            key="fees",
            title="Fee dues carried forward",
            detail=None if fees_complete else "Finance",
            completed=fees_complete,
        ),
        AcademicYearClosingChecklistItem(
            key="archive",
            title="Archive attendance & marks",
            detail=None if archive_complete else "Locks editing",
            completed=archive_complete,
        ),
        AcademicYearClosingChecklistItem(
            key="close",
            title="Close year record",
            completed=year_closed,
        ),
    ]


def _slug_code(label: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", label.strip().upper()).strip("-")
    return (cleaned[:24] or f"AY-{uuid4().hex[:6].upper()}")


async def get_academic_year_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> AcademicYearManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    today = utcnow().date()
    page = max(1, page)

    settings_doc = await _ensure_settings(tenant_id)
    settings = settings_doc.settings or {}
    only_one_current = _settings_bool(settings, _SETTINGS_ONLY_CURRENT, True)
    lock_closed = _settings_bool(settings, _SETTINGS_LOCK_CLOSED, True)

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    student_counts = await _student_counts_by_year(tenant_id)
    total_years = len(years)
    total_pages = max(1, math.ceil(total_years / _PAGE_SIZE)) if total_years else 1
    if page > total_pages:
        page = total_pages
    start = (page - 1) * _PAGE_SIZE
    page_years = years[start : start + _PAGE_SIZE]

    table_rows: list[AcademicYearManagementTableRow] = []
    for year in page_years:
        code, status_label, tone = _year_status(year, today)
        table_rows.append(
            AcademicYearManagementTableRow(
                year_id=str(year.id),
                label=year.label,
                start_label=_format_date(year.start_date),
                end_label=_format_date(year.end_date),
                student_count=student_counts.get(year.label, 0),
                status_code=code,
                status_label=status_label,
                status_tone=tone,
            )
        )

    current_year = next((y for y in years if y.is_current), None)
    close_enabled = current_year is not None and current_year.status != ConfigPublicationStatus.ARCHIVED

    copy_options = [AcademicYearCreateFormOption(value="", label="None (blank structure)")]
    for year in years:
        copy_options.append(AcademicYearCreateFormOption(value=str(year.id), label=year.label))

    checklist_title = (
        f"Year closing checklist – {current_year.label}"
        if current_year
        else "Year closing checklist"
    )
    checklist = await _build_closing_checklist(tenant_id, current_year)

    generated = utcnow()
    snapshot = as_utc_aware(generated).astimezone(_IST).strftime("Sample snapshot · %d %b %Y, %H:%M IST")

    return AcademicYearManagementPageRead(
        page_title="Academic Year Management",
        page_subtitle="Create, open and close academic years",
        close_current_year_label="Close current year",
        close_current_year_enabled=close_enabled,
        close_target_year_label=current_year.label if current_year else None,
        new_academic_year_label="New academic year",
        academic_years_table_title="Academic years",
        table_headers=["Academic year", "Start", "End", "Students", "Status"],
        academic_years=table_rows,
        academic_year_count_label=f"{total_years} academic year{'s' if total_years != 1 else ''}",
        page=page,
        page_size=_PAGE_SIZE,
        total_pages=total_pages,
        total_years=total_years,
        create_section_title="Create academic year",
        create_form_note="Changes are saved to the audit log with your name and time.",
        create_submit_label="Create academic year",
        cancel_label="Cancel",
        create_fields=[
            AcademicYearCreateFormField(key="label", label="Academic year", required=True, field_type="text"),
            AcademicYearCreateFormField(key="copy_from_year_id", label="Copy structure from", field_type="select"),
            AcademicYearCreateFormField(key="start_date", label="Start date", field_type="date"),
            AcademicYearCreateFormField(key="end_date", label="End date", field_type="date"),
            AcademicYearCreateFormField(key="semester_count", label="Number of semesters", field_type="select"),
            AcademicYearCreateFormField(key="admission_intake_opens", label="Admission intake opens", field_type="date"),
        ],
        copy_from_options=copy_options,
        semester_count_options=[
            AcademicYearCreateFormOption(value="1", label="1"),
            AcademicYearCreateFormOption(value="2", label="2"),
            AcademicYearCreateFormOption(value="3", label="3"),
            AcademicYearCreateFormOption(value="4", label="4"),
        ],
        checklist_title=checklist_title,
        checklist_items=checklist,
        rules_section_title="Rules",
        rules=[
            AcademicYearRuleToggle(
                key="only_one_current_year",
                title="Only one current academic year",
                description="Required",
                enabled=only_one_current,
            ),
            AcademicYearRuleToggle(
                key="lock_closed_years",
                title="Lock closed years",
                description="No edits after closing",
                enabled=lock_closed,
            ),
        ],
        sub_nav=years_semesters_sub_nav(active="years"),
        semesters_button_label="Semesters",
        semesters_button_href="/college-admin/academics/semester-management",
        footer_disclaimer="Live academic configuration · Years and terms · All times IST",
        footer_snapshot_label=snapshot,
        generated_at=generated,
    )


async def _create_terms_for_year(
    tenant_id: PydanticObjectId,
    year_id: PydanticObjectId,
    *,
    semester_count: int,
    source_terms: list[AcademicTerm] | None = None,
) -> None:
    if source_terms:
        for term in source_terms[:semester_count]:
            await AcademicTerm(
                tenant_id=tenant_id,
                academic_year_id=year_id,
                term_code=term.term_code,
                label=term.label,
                start_date=term.start_date,
                end_date=term.end_date,
            ).insert()
        return
    for index in range(semester_count):
        code, label = _TERM_PRESETS[index]
        await AcademicTerm(
            tenant_id=tenant_id,
            academic_year_id=year_id,
            term_code=code,
            label=label,
        ).insert()


async def create_academic_year_management(
    scope: AccessScope,
    payload: AcademicYearManagementCreate,
) -> AcademicYearManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    settings_doc = await _ensure_settings(tenant_id)
    only_one_current = _settings_bool(settings_doc.settings or {}, _SETTINGS_ONLY_CURRENT, True)

    code = _slug_code(payload.label)
    existing_code = await AcademicYear.find_one(
        Eq(AcademicYear.tenant_id, tenant_id),
        Eq(AcademicYear.year_code, code),
    )
    if existing_code:
        code = f"{code}-{uuid4().hex[:4].upper()}"

    source_terms: list[AcademicTerm] | None = None
    copy_fields: dict = {}
    if payload.copy_from_year_id:
        source_id = to_object_id(payload.copy_from_year_id, "copy_from_year_id")
        source = await AcademicYear.get(source_id)
        if source is None or source.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Source academic year not found", status_code=404)
        source_terms = await AcademicTerm.find(
            Eq(AcademicTerm.tenant_id, tenant_id),
            Eq(AcademicTerm.academic_year_id, source_id),
        ).sort("+term_code").to_list()
        copy_fields = {
            "summer_term_start": source.summer_term_start,
            "summer_term_end": source.summer_term_end,
            "year_end_closing": source.year_end_closing,
        }

    make_current = False
    if payload.start_date and payload.start_date <= utcnow().date():
        make_current = True

    if make_current and only_one_current:
        for other in await AcademicYear.find(
            Eq(AcademicYear.tenant_id, tenant_id),
            Eq(AcademicYear.is_current, True),
        ).to_list():
            other.is_current = False
            await other.save()

    doc = AcademicYear(
        tenant_id=tenant_id,
        year_code=code,
        label=payload.label.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date,
        admission_intake_opens=payload.admission_intake_opens,
        is_current=make_current,
        updated_by=scope.user_id,
        **copy_fields,
    )
    await doc.insert()
    await _create_terms_for_year(
        tenant_id,
        doc.id,
        semester_count=payload.semester_count,
        source_terms=source_terms,
    )

    await record_audit(
        actor_id=scope.user_id,
        action="academic.year.created",
        resource_type="academic_year",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    return await get_academic_year_management_page(scope)


async def close_current_academic_year(scope: AccessScope) -> AcademicYearManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    settings_doc = await _ensure_settings(tenant_id)
    lock_closed = _settings_bool(settings_doc.settings or {}, _SETTINGS_LOCK_CLOSED, True)

    current = await AcademicYear.find_one(
        Eq(AcademicYear.tenant_id, tenant_id),
        Eq(AcademicYear.is_current, True),
    )
    if current is None:
        raise AppError(code="NOT_FOUND", message="No current academic year", status_code=404)

    checklist = await _build_closing_checklist(tenant_id, current)
    incomplete = [item for item in checklist if not item.completed and item.key != "close"]
    if incomplete:
        raise AppError(
            code="CONFLICT",
            message="Complete the year closing checklist before closing",
            status_code=409,
        )

    current.is_current = False
    if lock_closed:
        current.status = ConfigPublicationStatus.ARCHIVED
    elif current.status == ConfigPublicationStatus.DRAFT:
        current.status = ConfigPublicationStatus.PUBLISHED
    if current.end_date is None:
        current.end_date = utcnow().date()
    if current.year_end_closing is None:
        current.year_end_closing = current.end_date
    current.updated_at = utcnow()
    current.updated_by = scope.user_id
    await current.save()

    await record_audit(
        actor_id=scope.user_id,
        action="academic.year.closed",
        resource_type="academic_year",
        resource_id=str(current.id),
        tenant_id=tenant_id,
    )
    return await get_academic_year_management_page(scope)


async def save_academic_year_management_rules(
    scope: AccessScope,
    payload: AcademicYearManagementRulesSave,
) -> AcademicYearManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    settings_doc = await _ensure_settings(tenant_id)
    updates = {
        _SETTINGS_ONLY_CURRENT: payload.only_one_current_year,
        _SETTINGS_LOCK_CLOSED: payload.lock_closed_years,
    }
    settings_doc.settings = merge_institution_settings(settings_doc.settings, updates)
    settings_doc.version += 1
    settings_doc.updated_at = utcnow()
    settings_doc.updated_by = scope.user_id
    await settings_doc.save()
    await record_audit(
        actor_id=scope.user_id,
        action="academic.year.rules.updated",
        resource_type="institution_settings",
        resource_id=str(settings_doc.id),
        tenant_id=tenant_id,
    )
    return await get_academic_year_management_page(scope)