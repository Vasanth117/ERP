"""Campus creation / edit wizard (CA 02.04)."""

from __future__ import annotations

from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.form_values import blank_to_none
from app.modules.college_admin.institution_service import create_campus, update_campus
from app.modules.college_admin.models import InstitutionCampus, InstitutionCampusCreationDraft, InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CampusCreate,
    CampusCreationDraftUpdate,
    CampusCreationFinishPayload,
    CampusCreationFinishResult,
    CampusCreationFormValues,
    CampusCreationPageRead,
    CampusCreationWizardStep,
    CampusUpdate,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)
from app.modules.tenants.platform_models import InstitutionAddress

_WIZARD_STEPS: list[tuple[str, str, str]] = [
    ("identity", "Identity", "Code & name"),
    ("location", "Location", "Address & region"),
    ("contact", "Contact", "Official contacts"),
    ("capacity", "Capacity", "Area & buildings"),
    ("facilities", "Facilities", "Planned facilities"),
    ("review", "Review", "Confirm & save"),
]

_TIMEZONE_OPTIONS = [
    ("Asia/Kolkata", "India (IST)"),
    ("Asia/Dubai", "Gulf (GST)"),
    ("Asia/Singapore", "Singapore"),
    ("Europe/London", "United Kingdom"),
    ("America/New_York", "US Eastern"),
]

_LOCALE_OPTIONS = [
    ("en-IN", "English (India)"),
    ("en-US", "English (US)"),
    ("hi-IN", "Hindi (India)"),
]


def _sanitize_values(raw: dict[str, Any]) -> dict[str, Any]:
    """Map JSON nulls from the client to empty strings for wizard form fields."""
    form_keys = set(CampusCreationFormValues.model_fields.keys())
    out = dict(raw)
    for key in form_keys:
        if key in out and out[key] is None:
            out[key] = ""
    return out


def _coerce_form(raw: dict[str, Any]) -> CampusCreationFormValues:
    sanitized = _sanitize_values(raw)
    return CampusCreationFormValues(**{**CampusCreationFormValues().model_dump(), **sanitized})


def _wizard_steps(current_key: str) -> list[CampusCreationWizardStep]:
    keys = [k for k, _, _ in _WIZARD_STEPS]
    try:
        current_index = keys.index(current_key)
    except ValueError:
        current_index = 0
    steps: list[CampusCreationWizardStep] = []
    for index, (key, label, subtitle) in enumerate(_WIZARD_STEPS):
        if index < current_index:
            status = "done"
        elif key == current_key:
            status = "active"
        else:
            status = "pending"
        steps.append(
            CampusCreationWizardStep(
                key=key,
                label=label,
                subtitle=subtitle,
                step_number=index + 1,
                status=status,
            )
        )
    return steps


def _next_step_key(current: str) -> str:
    keys = [k for k, _, _ in _WIZARD_STEPS]
    try:
        index = keys.index(current)
    except ValueError:
        return keys[0]
    if index + 1 < len(keys):
        return keys[index + 1]
    return current


def _prev_step_key(current: str) -> str:
    keys = [k for k, _, _ in _WIZARD_STEPS]
    try:
        index = keys.index(current)
    except ValueError:
        return keys[0]
    if index > 0:
        return keys[index - 1]
    return keys[0]


def _field_meta_for_step(step_key: str) -> list[InstitutionFieldMeta]:
    if step_key == "identity":
        return [
            InstitutionFieldMeta(key="campus_code", label="Campus code", required=True),
            InstitutionFieldMeta(key="name", label="Campus name", required=True),
            InstitutionFieldMeta(key="is_main", label="Main campus"),
        ]
    if step_key == "location":
        return [
            InstitutionFieldMeta(key="address_line1", label="Address line 1", required=True),
            InstitutionFieldMeta(key="address_line2", label="Address line 2"),
            InstitutionFieldMeta(key="city", label="City", required=True),
            InstitutionFieldMeta(key="district", label="District"),
            InstitutionFieldMeta(key="state", label="State", required=True),
            InstitutionFieldMeta(key="country", label="Country", required=True),
            InstitutionFieldMeta(key="postal_code", label="Postal code"),
            InstitutionFieldMeta(key="latitude", label="Latitude"),
            InstitutionFieldMeta(key="longitude", label="Longitude"),
        ]
    if step_key == "contact":
        return [
            InstitutionFieldMeta(key="contact_email", label="Contact email", field_type="email"),
            InstitutionFieldMeta(key="contact_phone", label="Contact phone"),
            InstitutionFieldMeta(key="timezone", label="Timezone"),
            InstitutionFieldMeta(key="locale", label="Locale"),
        ]
    if step_key == "capacity":
        return [
            InstitutionFieldMeta(key="area_acres", label="Campus area (acres)"),
            InstitutionFieldMeta(key="built_up_sq_m", label="Built-up area (sq. m)"),
            InstitutionFieldMeta(key="buildings_count", label="Buildings count"),
            InstitutionFieldMeta(key="parking_slots", label="Parking slots"),
        ]
    if step_key == "facilities":
        return [
            InstitutionFieldMeta(key="planned_classrooms", label="Planned classrooms"),
            InstitutionFieldMeta(key="planned_laboratories", label="Planned laboratories"),
            InstitutionFieldMeta(key="hostel_blocks_planned", label="Hostel blocks (planned)"),
            InstitutionFieldMeta(key="library_branches_planned", label="Library branches (planned)"),
            InstitutionFieldMeta(key="facilities_notes", label="Facilities notes", field_type="textarea"),
        ]
    return []


async def _get_or_create_draft(tenant_id: PydanticObjectId, actor_id: PydanticObjectId) -> InstitutionCampusCreationDraft:
    existing = await InstitutionCampusCreationDraft.find_one(
        Eq(InstitutionCampusCreationDraft.tenant_id, tenant_id),
        Eq(InstitutionCampusCreationDraft.created_by, actor_id),
    )
    if existing:
        return existing
    draft = InstitutionCampusCreationDraft(tenant_id=tenant_id, created_by=actor_id)
    await draft.insert()
    return draft


def _campus_to_values(campus: InstitutionCampus) -> dict[str, Any]:
    address = campus.address
    return {
        "campus_code": campus.campus_code,
        "name": campus.name,
        "is_main": "true" if campus.is_main else "false",
        "address_line1": address.line1 or "",
        "address_line2": address.line2 or "",
        "city": address.city or "",
        "district": address.district or "",
        "state": address.state or "",
        "country": address.country or "",
        "postal_code": address.postal_code or "",
        "latitude": str(address.latitude) if address.latitude is not None else "",
        "longitude": str(address.longitude) if address.longitude is not None else "",
        "contact_email": campus.contact_email or "",
        "contact_phone": campus.contact_phone or "",
        "timezone": campus.timezone or "",
        "locale": campus.locale or "",
        "area_acres": str(campus.area_acres) if campus.area_acres is not None else "",
        "built_up_sq_m": str(campus.built_up_sq_m) if campus.built_up_sq_m is not None else "",
        "buildings_count": str(campus.buildings_count) if campus.buildings_count is not None else "",
        "parking_slots": str(campus.parking_slots) if campus.parking_slots is not None else "",
    }


def _parse_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _build_address(form: CampusCreationFormValues) -> InstitutionAddress:
    lat = _parse_float(form.latitude)
    lng = _parse_float(form.longitude)
    return InstitutionAddress(
        line1=form.address_line1.strip(),
        line2=blank_to_none(form.address_line2),
        city=form.city.strip(),
        district=blank_to_none(form.district),
        state=form.state.strip(),
        country=form.country.strip() or "India",
        postal_code=blank_to_none(form.postal_code),
        latitude=lat,
        longitude=lng,
    )


def _validate_step(step_key: str, form: CampusCreationFormValues, *, edit_mode: bool) -> None:
    from app.modules.college_admin.form_validation_details import raise_validation_error, scroll_field

    if step_key == "identity":
        details: list[dict] = []
        if not edit_mode and (not form.campus_code or len(form.campus_code.strip()) < 2):
            details.append(
                scroll_field(
                    "campus_code",
                    label="Campus code",
                    message="Enter a short campus code (at least 2 characters).",
                )
            )
        if not form.name or len(form.name.strip()) < 2:
            details.append(
                scroll_field("name", label="Campus name", message="Enter the campus display name.")
            )
        if details:
            raise_validation_error("Complete the campus identity step before continuing.", details)


def _validate_finalize(form: CampusCreationFormValues, *, edit_mode: bool) -> None:
    from app.modules.college_admin.form_validation_details import raise_validation_error, scroll_field

    _validate_step("identity", form, edit_mode=edit_mode)
    details: list[dict] = []
    if not form.city.strip():
        details.append(scroll_field("city", label="City", message="Enter the campus city."))
    if not form.state.strip():
        details.append(scroll_field("state", label="State", message="Enter the campus state."))
    if details:
        raise_validation_error("Complete the campus location fields before saving.", details)


async def _default_timezone(tenant_id: PydanticObjectId) -> str:
    settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    if settings and isinstance(settings.settings, dict):
        tz = settings.settings.get("timezone")
        if isinstance(tz, str) and tz.strip():
            return tz.strip()
    return "Asia/Kolkata"


async def _page_read(draft: InstitutionCampusCreationDraft) -> CampusCreationPageRead:
    tenant_id = draft.tenant_id
    now = utcnow()
    form = _coerce_form(draft.values)
    if not form.timezone:
        form = form.model_copy(update={"timezone": await _default_timezone(tenant_id)})
    is_edit = draft.edit_campus_id is not None
    title = "Edit campus" if is_edit else "Create campus"
    subtitle = "Update campus profile step by step" if is_edit else "Register a campus with full location, contact and capacity details"
    create_label = "Save campus" if is_edit else "Create campus"

    tz_opts = [InstitutionFieldOption(value="", label="Select timezone")]
    for value, label in _TIMEZONE_OPTIONS:
        tz_opts.append(InstitutionFieldOption(value=value, label=label))

    locale_opts = [InstitutionFieldOption(value="", label="Select locale")]
    for value, label in _LOCALE_OPTIONS:
        locale_opts.append(InstitutionFieldOption(value=value, label=label))

    step_key = draft.step_key or "identity"
    return CampusCreationPageRead(
        draft_id=str(draft.id),
        page_title=title,
        page_subtitle=subtitle,
        back_href="/college-admin/institution/campuses",
        back_label="Campuses",
        save_draft_label="Save draft",
        create_label=create_label,
        current_step_key=step_key,
        steps=_wizard_steps(step_key),
        field_meta=_field_meta_for_step(step_key),
        form=form,
        timezone_options=tz_opts,
        locale_options=locale_opts,
        is_edit_mode=is_edit,
        edit_campus_id=str(draft.edit_campus_id) if draft.edit_campus_id else None,
        has_draft=bool(draft.values),
        generated_at=now,
    )


async def get_campus_creation_page(scope: AccessScope, *, campus_id: str | None = None) -> CampusCreationPageRead:
    authorize(scope, Permission.INSTITUTION_CAMPUS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    draft = await _get_or_create_draft(tenant_id, actor_id)

    if campus_id and draft.edit_campus_id is None:
        campus_oid = to_object_id(campus_id, "campus_id")
        campus = await InstitutionCampus.find_one(
            Eq(InstitutionCampus.tenant_id, tenant_id),
            Eq(InstitutionCampus.id, campus_oid),
        )
        if campus is None:
            raise AppError(code="NOT_FOUND", message="Campus not found", status_code=404)
        draft.edit_campus_id = campus_oid
        if not draft.values:
            draft.values = _campus_to_values(campus)
        draft.step_key = draft.step_key or "identity"
        draft.updated_at = utcnow()
        await draft.save()

    if not draft.values and not draft.edit_campus_id:
        draft.values = {"country": "India", "is_main": "false"}
        await draft.save()

    return await _page_read(draft)


async def save_campus_creation_draft(
    scope: AccessScope,
    payload: CampusCreationDraftUpdate,
) -> CampusCreationPageRead:
    authorize(scope, Permission.INSTITUTION_CAMPUS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    if payload.draft_id:
        draft_oid = to_object_id(payload.draft_id, "draft_id")
        draft = await InstitutionCampusCreationDraft.get(draft_oid)
        if draft is None or draft.tenant_id != tenant_id or draft.created_by != actor_id:
            raise AppError(code="NOT_FOUND", message="Draft not found", status_code=404)
    else:
        draft = await _get_or_create_draft(tenant_id, actor_id)

    merged = _sanitize_values({**draft.values, **(payload.values or {})})
    current_key = payload.step_key or draft.step_key or "identity"
    form = _coerce_form(merged)
    is_edit = draft.edit_campus_id is not None

    if payload.retreat:
        step_key = _prev_step_key(draft.step_key or "identity")
    elif payload.advance:
        _validate_step(current_key, form, edit_mode=is_edit)
        step_key = _next_step_key(current_key)
    else:
        step_key = current_key

    draft.values = merged
    draft.step_key = step_key
    draft.updated_at = utcnow()
    await draft.save()
    return await _page_read(draft)


async def finish_campus_creation(
    scope: AccessScope,
    payload: CampusCreationFinishPayload,
) -> CampusCreationFinishResult:
    authorize(scope, Permission.INSTITUTION_CAMPUS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    draft_oid = to_object_id(payload.draft_id, "draft_id")
    draft = await InstitutionCampusCreationDraft.get(draft_oid)
    if draft is None or draft.tenant_id != tenant_id or draft.created_by != actor_id:
        raise AppError(code="NOT_FOUND", message="Draft not found", status_code=404)

    merged = _sanitize_values({**draft.values, **(payload.values or {})})
    form = _coerce_form(merged)
    is_edit = draft.edit_campus_id is not None
    _validate_finalize(form, edit_mode=is_edit)

    address = _build_address(form)
    is_main = form.is_main.strip().lower() in {"true", "1", "yes", "on"}

    if is_edit:
        assert draft.edit_campus_id is not None
        update_payload = CampusUpdate(
            name=form.name.strip(),
            is_main=is_main,
            address=address,
            contact_email=blank_to_none(form.contact_email),
            contact_phone=blank_to_none(form.contact_phone),
            timezone=blank_to_none(form.timezone),
            locale=blank_to_none(form.locale),
            area_acres=_parse_float(form.area_acres),
            built_up_sq_m=_parse_float(form.built_up_sq_m),
            buildings_count=_parse_int(form.buildings_count),
            parking_slots=_parse_int(form.parking_slots),
        )
        campus = await update_campus(scope, draft.edit_campus_id, update_payload)
        campus_id = campus.campus_id
    else:
        create_payload = CampusCreate(
            campus_code=form.campus_code.strip().upper(),
            name=form.name.strip(),
            is_main=is_main,
            address=address,
            contact_email=blank_to_none(form.contact_email),
            contact_phone=blank_to_none(form.contact_phone),
            timezone=blank_to_none(form.timezone),
            locale=blank_to_none(form.locale),
            area_acres=_parse_float(form.area_acres),
            built_up_sq_m=_parse_float(form.built_up_sq_m),
            buildings_count=_parse_int(form.buildings_count),
            parking_slots=_parse_int(form.parking_slots),
        )
        campus = await create_campus(scope, create_payload)
        campus_id = campus.campus_id

    draft.values = merged
    draft.updated_at = utcnow()
    await draft.delete()

    detail_href = f"/college-admin/institution/campuses/{campus_id}"
    return CampusCreationFinishResult(campus_id=campus_id, detail_href=detail_href)