"""Multi-step academic year creation wizard (CA 05.02)."""

from __future__ import annotations

from datetime import date
from typing import Any
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.academic_config_models import AcademicYear, AcademicYearWizardDraft
from app.modules.college_admin.academic_year_management_page_service import create_academic_year_management
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicYearCreateFormOption,
    AcademicYearManagementCreate,
    AcademicYearWizardDraftUpdate,
    AcademicYearWizardFormSection,
    AcademicYearWizardFormValues,
    AcademicYearWizardStep,
    AcademicYearWizardSummaryItem,
    InstitutionFieldMeta,
    NewAcademicYearWizardPageRead,
    NewAcademicYearWizardSaveResult,
)

_IST = ZoneInfo("Asia/Kolkata")

_WIZARD_STEPS: list[tuple[str, str]] = [
    ("year_identity", "Year identity"),
    ("calendar", "Calendar & intake"),
    ("semesters", "Semester structure"),
    ("review", "Review & create"),
]

_FIELD_META = [
    InstitutionFieldMeta(key="label", label="Academic year", required=True),
    InstitutionFieldMeta(key="copy_from_year_id", label="Copy structure from", field_type="select"),
    InstitutionFieldMeta(key="start_date", label="Start date", field_type="date"),
    InstitutionFieldMeta(key="end_date", label="End date", field_type="date"),
    InstitutionFieldMeta(key="admission_intake_opens", label="Admission intake opens", field_type="date"),
    InstitutionFieldMeta(key="summer_term_start", label="Summer term start", field_type="date"),
    InstitutionFieldMeta(key="summer_term_end", label="Summer term end", field_type="date"),
    InstitutionFieldMeta(key="year_end_closing", label="Year-end closing", field_type="date"),
    InstitutionFieldMeta(key="semester_count", label="Number of semesters", required=True, field_type="select"),
]


def _parse_optional_date(raw: str | None) -> date | None:
    if not raw or not str(raw).strip():
        return None
    return date.fromisoformat(str(raw).strip())


def _step_status(step_key: str, current: str, completed: list[str]) -> str:
    if step_key in completed:
        return "done"
    if step_key == current:
        return "active"
    return "pending"


def _form_from_values(values: dict[str, Any]) -> AcademicYearWizardFormValues:
    return AcademicYearWizardFormValues(
        label=str(values.get("label") or ""),
        copy_from_year_id=values.get("copy_from_year_id") or None,
        start_date=values.get("start_date") or None,
        end_date=values.get("end_date") or None,
        admission_intake_opens=values.get("admission_intake_opens") or None,
        summer_term_start=values.get("summer_term_start") or None,
        summer_term_end=values.get("summer_term_end") or None,
        year_end_closing=values.get("year_end_closing") or None,
        semester_count=str(values.get("semester_count") or "2"),
    )


def _summary_items(form: AcademicYearWizardFormValues, copy_options: list[AcademicYearCreateFormOption]) -> list[AcademicYearWizardSummaryItem]:
    copy_label = next(
        (o.label for o in copy_options if o.value == (form.copy_from_year_id or "")),
        "None (blank structure)",
    )
    return [
        AcademicYearWizardSummaryItem(key="label", label="Academic year", value=form.label or "—"),
        AcademicYearWizardSummaryItem(key="copy", label="Structure source", value=copy_label),
        AcademicYearWizardSummaryItem(key="dates", label="Academic window", value=f"{form.start_date or '—'} → {form.end_date or '—'}"),
        AcademicYearWizardSummaryItem(
            key="intake",
            label="Admission intake",
            value=form.admission_intake_opens or "—",
        ),
        AcademicYearWizardSummaryItem(key="semesters", label="Semesters", value=form.semester_count),
    ]


async def _copy_options(tenant_id: PydanticObjectId) -> list[AcademicYearCreateFormOption]:
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-created_at").to_list()
    options = [AcademicYearCreateFormOption(value="", label="None (blank structure)")]
    for year in years:
        options.append(AcademicYearCreateFormOption(value=str(year.id), label=year.label))
    return options


async def _ensure_draft(
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId,
    draft_id: str | None,
) -> AcademicYearWizardDraft:
    if draft_id:
        oid = to_object_id(draft_id, "draft_id")
        draft = await AcademicYearWizardDraft.get(oid)
        if draft is None or draft.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Draft not found", status_code=404)
        return draft
    draft = AcademicYearWizardDraft(
        tenant_id=tenant_id,
        created_by=actor_id,
        values={"semester_count": "2"},
    )
    await draft.insert()
    return draft


def _validate_step(step_key: str, values: dict[str, Any]) -> None:
    if step_key == "year_identity":
        label = str(values.get("label") or "").strip()
        if len(label) < 4:
            raise AppError(
                code="VALIDATION_ERROR",
                message="Academic year label must be at least 4 characters.",
                status_code=422,
            )
    if step_key == "calendar":
        start = _parse_optional_date(values.get("start_date"))
        end = _parse_optional_date(values.get("end_date"))
        if start and end and end < start:
            raise AppError(
                code="VALIDATION_ERROR",
                message="End date must be on or after the start date.",
                status_code=422,
            )


async def get_new_academic_year_wizard_page(
    scope: AccessScope,
    draft_id: str | None = None,
) -> NewAcademicYearWizardPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    draft = await _ensure_draft(tenant_id, scope.user_id, draft_id)
    copy_options = await _copy_options(tenant_id)
    form = _form_from_values(draft.values)
    step_index = next(i for i, (key, _) in enumerate(_WIZARD_STEPS) if key == draft.current_step_key)
    generated = utcnow()
    snapshot = as_utc_aware(generated).astimezone(_IST).strftime("Sample snapshot · %d %b %Y, %H:%M IST")

    return NewAcademicYearWizardPageRead(
        draft_id=str(draft.id),
        page_title="New academic year",
        page_subtitle=f"Step {step_index + 1} of {len(_WIZARD_STEPS)} · {_WIZARD_STEPS[step_index][1]}",
        back_href="/college-admin/academics/academic-year-management",
        back_label="Back to academic years",
        save_draft_label="Save draft",
        continue_label="Continue",
        finalize_label="Create academic year",
        current_step_key=draft.current_step_key,
        step_position_label=f"Step {step_index + 1} of {len(_WIZARD_STEPS)}",
        steps=[
            AcademicYearWizardStep(
                key=key,
                label=label,
                step_number=index + 1,
                status=_step_status(key, draft.current_step_key, draft.completed_steps),
            )
            for index, (key, label) in enumerate(_WIZARD_STEPS)
        ],
        sections=[
            AcademicYearWizardFormSection(key="year_identity", title="Year identity"),
            AcademicYearWizardFormSection(key="calendar", title="Important dates"),
            AcademicYearWizardFormSection(key="semesters", title="Semester structure"),
            AcademicYearWizardFormSection(key="review", title="Review summary"),
        ],
        field_meta=_FIELD_META,
        copy_from_options=copy_options,
        semester_count_options=[
            AcademicYearCreateFormOption(value="1", label="1"),
            AcademicYearCreateFormOption(value="2", label="2"),
            AcademicYearCreateFormOption(value="3", label="3"),
            AcademicYearCreateFormOption(value="4", label="4"),
        ],
        form=form,
        summary_title="Year summary",
        summary_items=_summary_items(form, copy_options),
        footer_disclaimer="Drafts are stored until you finish the wizard · All times IST",
        footer_snapshot_label=snapshot,
        generated_at=generated,
    )


async def save_academic_year_wizard_draft(
    scope: AccessScope,
    payload: AcademicYearWizardDraftUpdate,
) -> NewAcademicYearWizardSaveResult:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    draft = await _ensure_draft(tenant_id, scope.user_id, payload.draft_id)
    step_key = payload.step_key or draft.current_step_key

    if payload.values:
        draft.values = {**draft.values, **payload.values}

    _validate_step(step_key, draft.values)

    if payload.finalize:
        if draft.current_step_key != "review":
            raise AppError(code="VALIDATION_ERROR", message="Complete all steps before creating the year.", status_code=422)
        form = _form_from_values(draft.values)
        _validate_step("year_identity", draft.values)
        _validate_step("calendar", draft.values)
        create_payload = AcademicYearManagementCreate(
            label=form.label.strip(),
            copy_from_year_id=form.copy_from_year_id or None,
            start_date=_parse_optional_date(form.start_date),
            end_date=_parse_optional_date(form.end_date),
            admission_intake_opens=_parse_optional_date(form.admission_intake_opens),
            semester_count=int(form.semester_count or "2"),
            summer_term_start=_parse_optional_date(form.summer_term_start),
            summer_term_end=_parse_optional_date(form.summer_term_end),
            year_end_closing=_parse_optional_date(form.year_end_closing),
        )
        await create_academic_year_management(scope, create_payload)
        created = await AcademicYear.find_one(
            Eq(AcademicYear.tenant_id, tenant_id),
            Eq(AcademicYear.label, form.label.strip()),
        )
        created_year_id = str(created.id) if created else None
        await draft.delete()
        details_href = (
            f"/college-admin/academics/academic-year-details?year_id={created_year_id}"
            if created_year_id
            else None
        )
        return NewAcademicYearWizardSaveResult(
            page=None,
            created_year_id=created_year_id,
            details_href=details_href,
        )

    draft.updated_at = utcnow()

    if payload.advance:
        if step_key not in draft.completed_steps:
            draft.completed_steps = [*draft.completed_steps, step_key]
        step_index = next(i for i, (key, _) in enumerate(_WIZARD_STEPS) if key == step_key)
        if step_index < len(_WIZARD_STEPS) - 1:
            draft.current_step_key = _WIZARD_STEPS[step_index + 1][0]

    if payload.step_key:
        draft.current_step_key = payload.step_key

    await draft.save()
    page = await get_new_academic_year_wizard_page(scope, str(draft.id))
    return NewAcademicYearWizardSaveResult(page=page)