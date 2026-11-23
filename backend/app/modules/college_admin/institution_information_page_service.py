"""Institution information form screen (CA 02.02)."""

from __future__ import annotations

from datetime import date
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.form_values import normalize_form_values
from app.modules.auth.models import User
from app.modules.college_admin.institution_service import _ensure_profile
from app.modules.college_admin.models import InstitutionActivityLog
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.repositories import InstitutionHistoryRepository
from app.modules.college_admin.schemas import (
    InstitutionFieldMeta,
    InstitutionFieldOption,
    InstitutionInformationFormValues,
    InstitutionInformationNotice,
    InstitutionInformationPageRead,
    InstitutionRecentChange,
    InstitutionUsageContext,
)
from app.modules.tenants.models import Tenant

_history_repo = InstitutionHistoryRepository()

_INSTITUTION_TYPE_OPTIONS = [
    InstitutionFieldOption(value="autonomous_private_aided", label="Autonomous - Private aided"),
    InstitutionFieldOption(value="autonomous_private_unaided", label="Autonomous - Private unaided"),
    InstitutionFieldOption(value="affiliated_government", label="Affiliated - Government"),
    InstitutionFieldOption(value="affiliated_private", label="Affiliated - Private"),
    InstitutionFieldOption(value="deemed_university", label="Deemed university"),
    InstitutionFieldOption(value="constituent", label="Constituent college"),
]

_MEDIUM_OPTIONS = [
    InstitutionFieldOption(value="English", label="English"),
    InstitutionFieldOption(value="Tamil", label="Tamil"),
    InstitutionFieldOption(value="Hindi", label="Hindi"),
    InstitutionFieldOption(value="Telugu", label="Telugu"),
    InstitutionFieldOption(value="Kannada", label="Kannada"),
    InstitutionFieldOption(value="Malayalam", label="Malayalam"),
    InstitutionFieldOption(value="Bilingual", label="Bilingual"),
]

_UGC_OPTIONS = [
    InstitutionFieldOption(value="yes_both", label="Yes - both"),
    InstitutionFieldOption(value="2f_only", label="2(f) only"),
    InstitutionFieldOption(value="12b_only", label="12(B) only"),
    InstitutionFieldOption(value="not_applicable", label="Not applicable"),
    InstitutionFieldOption(value="pending", label="Pending"),
]

_USAGE_CONTEXTS = [
    InstitutionUsageContext(
        title="Degree certificates & transcripts",
        description="Name, logo, affiliation",
    ),
    InstitutionUsageContext(
        title="Fee receipts & invoices",
        description="Name, address, GSTIN",
    ),
    InstitutionUsageContext(
        title="Hall tickets",
        description="Name, logo, exam cell",
    ),
    InstitutionUsageContext(
        title="Student & staff ID cards",
        description="Name, logo, address",
    ),
]

_FIELD_META = [
    InstitutionFieldMeta(key="legal_name", label="Institution name", required=True),
    InstitutionFieldMeta(key="short_name", label="Short name", required=True),
    InstitutionFieldMeta(key="institution_code", label="Institution code", required=True, locked=True),
    InstitutionFieldMeta(key="year_established", label="Year established", required=True),
    InstitutionFieldMeta(key="institution_type", label="Institution type", required=True, field_type="select"),
    InstitutionFieldMeta(key="medium_of_instruction", label="Medium of instruction", field_type="select"),
    InstitutionFieldMeta(key="description", label="Description", field_type="textarea"),
    InstitutionFieldMeta(key="affiliation_name", label="Affiliating university", required=True, field_type="select"),
    InstitutionFieldMeta(
        key="autonomous_status_valid_until",
        label="Autonomous status valid till",
        field_type="date",
    ),
    InstitutionFieldMeta(key="affiliation_id", label="AICTE permanent ID", required=True),
    InstitutionFieldMeta(key="aishe_code", label="AISHE code", required=True),
    InstitutionFieldMeta(key="ugc_recognition", label="UGC 2(f) / 12(B)", field_type="select"),
    InstitutionFieldMeta(key="ownership_name", label="Trust / society name"),
    InstitutionFieldMeta(key="institution_email", label="Official email", required=True, field_type="email"),
    InstitutionFieldMeta(key="contact_phone", label="Phone", required=True),
    InstitutionFieldMeta(key="official_website", label="Website", field_type="url"),
    InstitutionFieldMeta(key="contact_fax", label="Fax"),
]

_CHANGE_KEY_LABELS: dict[str, str] = {
    "legal_name": "Institution name updated",
    "display_name": "Display name updated",
    "short_name": "Short name updated",
    "institution_code": "Institution code updated",
    "official_website": "Website updated",
    "contact_phone": "Phone number changed",
    "contact_fax": "Fax updated",
    "institution_email": "Official email updated",
    "affiliation_name": "Affiliation updated",
    "affiliation_id": "AICTE ID updated",
    "aishe_code": "AISHE code updated",
    "autonomous_status_valid_until": "Autonomous status renewed",
    "ownership_name": "Trust / society name updated",
    "description": "Institution description updated",
    "ugc_recognition": "UGC recognition updated",
    "medium_of_instruction": "Medium of instruction updated",
    "year_established": "Year established updated",
}


def _merge_draft(profile, draft: dict[str, Any]) -> dict[str, Any]:
    base = {
        "legal_name": profile.legal_name,
        "display_name": profile.display_name,
        "short_name": profile.short_name,
        "institution_code": profile.institution_code,
        "year_established": profile.year_established,
        "institution_type": profile.institution_type,
        "medium_of_instruction": profile.medium_of_instruction,
        "description": profile.description,
        "affiliation_name": profile.affiliation_name,
        "autonomous_status_valid_until": profile.autonomous_status_valid_until,
        "affiliation_id": profile.affiliation_id,
        "aishe_code": profile.aishe_code,
        "ugc_recognition": profile.ugc_recognition,
        "ownership_name": profile.ownership_name,
        "institution_email": profile.institution_email,
        "contact_phone": profile.contact_phone,
        "official_website": profile.official_website,
        "contact_fax": profile.contact_fax,
    }
    for key, value in draft.items():
        if key in base:
            if key == "autonomous_status_valid_until" and isinstance(value, str):
                try:
                    base[key] = date.fromisoformat(value)
                except ValueError:
                    base[key] = value
            else:
                base[key] = value
    return base


def _coerce_form(merged: dict[str, Any]) -> InstitutionInformationFormValues:
    valid_until = merged.get("autonomous_status_valid_until")
    if isinstance(valid_until, str):
        try:
            valid_until = date.fromisoformat(valid_until)
        except ValueError:
            valid_until = None
    year = merged.get("year_established")
    if year is not None and not isinstance(year, int):
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None

    return InstitutionInformationFormValues(
        legal_name=str(merged.get("legal_name") or ""),
        display_name=str(merged.get("display_name") or merged.get("legal_name") or ""),
        short_name=merged.get("short_name"),
        institution_code=merged.get("institution_code"),
        year_established=year,
        institution_type=merged.get("institution_type"),
        medium_of_instruction=merged.get("medium_of_instruction"),
        description=merged.get("description"),
        affiliation_name=merged.get("affiliation_name"),
        autonomous_status_valid_until=valid_until if isinstance(valid_until, date) else None,
        affiliation_id=merged.get("affiliation_id"),
        aishe_code=merged.get("aishe_code"),
        ugc_recognition=merged.get("ugc_recognition"),
        ownership_name=merged.get("ownership_name"),
        institution_email=merged.get("institution_email"),
        contact_phone=merged.get("contact_phone"),
        official_website=merged.get("official_website"),
        contact_fax=merged.get("contact_fax"),
    )


async def _actor_label(user_id: PydanticObjectId | None) -> str:
    if user_id is None:
        return "System"
    user = await User.get(user_id)
    if user is None:
        return "Unknown user"
    return user.full_name or user.email


def _format_change_detail(actor: str, occurred_at) -> str:
    stamp = occurred_at.strftime("%d %b %Y")
    return f"by {actor} · {stamp}"


async def _recent_changes(tenant_id: PydanticObjectId) -> list[InstitutionRecentChange]:
    rows: list[InstitutionRecentChange] = []

    config_rows = await _history_repo.list_history(tenant_id, limit=20)
    for row in config_rows:
        if row.scope != "institution_profile":
            continue
        for key in row.changed_keys[:1]:
            title = _CHANGE_KEY_LABELS.get(key, f"{key.replace('_', ' ').title()} updated")
            actor = await _actor_label(row.created_by)
            rows.append(
                InstitutionRecentChange(
                    change_id=f"cfg-{row.id}-{key}",
                    title=title,
                    detail_line=_format_change_detail(actor, row.created_at),
                    tone="success" if key != "contact_phone" else "info",
                    occurred_at=row.created_at,
                )
            )
        if len(rows) >= 8:
            break

    if len(rows) < 3:
        activities = (
            await InstitutionActivityLog.find(Eq(InstitutionActivityLog.tenant_id, tenant_id))
            .sort("-created_at")
            .limit(10)
            .to_list()
        )
        for item in activities:
            if item.resource_type != "institution_profile":
                continue
            actor = await _actor_label(item.actor_id)
            rows.append(
                InstitutionRecentChange(
                    change_id=f"act-{item.id}",
                    title=item.summary,
                    detail_line=_format_change_detail(actor, item.created_at),
                    tone="success",
                    occurred_at=item.created_at,
                )
            )
            if len(rows) >= 8:
                break

    rows.sort(key=lambda item: item.occurred_at, reverse=True)
    return rows[:6]


def _affiliation_options(current: str | None) -> list[InstitutionFieldOption]:
    seen: set[str] = set()
    options: list[InstitutionFieldOption] = []
    if current:
        options.append(InstitutionFieldOption(value=current, label=current))
        seen.add(current.lower())
    return options


async def get_institution_information_page(scope: AccessScope) -> InstitutionInformationPageRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    raw = await _ensure_profile(tenant)
    merged = _merge_draft(raw, dict(raw.draft_values))
    form = _coerce_form(merged)

    affiliation_options = _affiliation_options(form.affiliation_name)
    if not affiliation_options:
        affiliation_options = [
            InstitutionFieldOption(value="", label="Select affiliating university"),
        ]

    return InstitutionInformationPageRead(
        form=form,
        field_meta=_FIELD_META,
        institution_type_options=_INSTITUTION_TYPE_OPTIONS,
        medium_of_instruction_options=_MEDIUM_OPTIONS,
        ugc_recognition_options=_UGC_OPTIONS,
        affiliation_options=affiliation_options,
        approval_notice=InstitutionInformationNotice(
            title="Changes to legal name or codes need Principal approval.",
            body=(
                "Edits to institution name, AICTE ID or affiliation are sent to the approval "
                "workflow before they appear on documents."
            ),
        ),
        usage_contexts=_USAGE_CONTEXTS,
        recent_changes=await _recent_changes(tenant_id),
        history_href="/college-admin/institution/configuration-history",
        footer_note="Changes are saved to the audit log with your name and time.",
        has_draft=bool(raw.draft_values),
        generated_at=utcnow(),
    )


async def save_institution_profile_draft(scope: AccessScope, values: dict[str, Any]) -> InstitutionInformationPageRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    profile = await _ensure_profile(tenant)
    allowed = {meta.key for meta in _FIELD_META}
    normalized = normalize_form_values(values)
    profile.draft_values = {k: v for k, v in normalized.items() if k in allowed and v is not None}
    profile.updated_at = utcnow()
    profile.updated_by = scope.user_id
    await profile.save()
    return await get_institution_information_page(scope)


async def publish_institution_information(scope: AccessScope, values: dict[str, Any]) -> InstitutionInformationPageRead:
    """Apply saved form values and clear draft."""
    from app.modules.college_admin.institution_service import update_institution_profile
    from app.modules.college_admin.schemas import InstitutionProfileUpdate

    authorize(scope, Permission.INSTITUTION_PROFILE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    values = normalize_form_values(values)

    valid_until = values.get("autonomous_status_valid_until")
    if isinstance(valid_until, str) and valid_until:
        try:
            valid_until = date.fromisoformat(valid_until)
        except ValueError:
            valid_until = None
    elif not valid_until:
        valid_until = None

    year = values.get("year_established")
    if year is not None and not isinstance(year, int):
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None

    payload = InstitutionProfileUpdate(
        legal_name=values.get("legal_name"),
        display_name=values.get("display_name") or values.get("legal_name"),
        short_name=values.get("short_name"),
        institution_code=values.get("institution_code"),
        year_established=year,
        institution_type=values.get("institution_type"),
        medium_of_instruction=values.get("medium_of_instruction"),
        description=values.get("description"),
        affiliation_name=values.get("affiliation_name"),
        autonomous_status_valid_until=valid_until,
        affiliation_id=values.get("affiliation_id"),
        aishe_code=values.get("aishe_code"),
        ugc_recognition=values.get("ugc_recognition"),
        ownership_name=values.get("ownership_name"),
        institution_email=values.get("institution_email"),
        contact_phone=values.get("contact_phone"),
        official_website=values.get("official_website"),
        contact_fax=values.get("contact_fax"),
    )
    await update_institution_profile(scope, payload)

    profile = await _ensure_profile(tenant)
    profile.draft_values = {}
    profile.updated_at = utcnow()
    profile.updated_by = scope.user_id
    await profile.save()

    return await get_institution_information_page(scope)