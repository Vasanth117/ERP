"""College logo & branding screen (CA 02.03)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from fastapi import UploadFile

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.enums import InstitutionActivityKind
from app.modules.college_admin.institution_service import (
    _ensure_branding,
    _ensure_profile,
    _log_activity,
    update_institution_settings,
)
from app.modules.college_admin.models import (
    InstitutionBranding,
    InstitutionBrandingAsset,
    InstitutionDocumentBrandTemplate,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    BrandingAssetRow,
    BrandingColorField,
    BrandingDocumentTemplateRow,
    BrandingPreviewItem,
    BrandingPrimaryLogoPanel,
    InstitutionBrandingAssetRead,
    InstitutionBrandingFormValues,
    InstitutionBrandingPageRead,
)
from app.modules.college_admin.settings_registry import InstitutionBrandingUpdate, InstitutionSettingsUpdate
from app.modules.lms import storage as file_storage
from app.modules.tenants.models import Tenant

_ASSET_SPECS = [
    ("primary_logo", "Primary logo", "SVG · 512 × 512", True),
    ("logo_white", "Logo – white", "SVG · for dark headers", True),
    ("favicon", "Favicon", "ICO · 32 × 32", True),
    ("official_seal", "Official seal", "PNG · for certificates", True),
    ("principal_signature", "Principal signature", "PNG · for certificates", True),
]

_DEFAULT_TEMPLATES = [
    ("letterhead_a4", "Letterhead – A4", "Circulars, letters"),
    ("fee_receipt", "Fee receipt", "Finance receipts"),
    ("degree_certificate", "Degree certificate", "Examination cell"),
    ("student_id_card", "ID card – student", "Student ID cards"),
]

_PREVIEW_ITEMS = [
    BrandingPreviewItem(title="Student portal header", description="Primary colour with white logo"),
    BrandingPreviewItem(title="Fee receipt", description="Letterhead + seal"),
]

_COLOR_FIELDS = [
    ("primary_color", "Primary colour", True),
    ("secondary_color", "Secondary colour", False),
    ("text_on_primary", "Text on primary", False),
    ("accent_status", "Accent for status", False),
]


async def _ensure_assets(tenant_id: PydanticObjectId) -> list[InstitutionBrandingAsset]:
    rows: list[InstitutionBrandingAsset] = []
    for key, label, hint, editable in _ASSET_SPECS:
        doc = await InstitutionBrandingAsset.find_one(
            Eq(InstitutionBrandingAsset.tenant_id, tenant_id),
            Eq(InstitutionBrandingAsset.asset_key, key),
        )
        if doc is None:
            doc = InstitutionBrandingAsset(
                tenant_id=tenant_id,
                asset_key=key,
                label=label,
                detail_hint=hint,
            )
            await doc.insert()
        rows.append(doc)
    return rows


async def _ensure_templates(tenant_id: PydanticObjectId) -> list[InstitutionDocumentBrandTemplate]:
    rows: list[InstitutionDocumentBrandTemplate] = []
    for key, title, used_for in _DEFAULT_TEMPLATES:
        doc = await InstitutionDocumentBrandTemplate.find_one(
            Eq(InstitutionDocumentBrandTemplate.tenant_id, tenant_id),
            Eq(InstitutionDocumentBrandTemplate.template_key, key),
        )
        if doc is None:
            doc = InstitutionDocumentBrandTemplate(
                tenant_id=tenant_id,
                template_key=key,
                title=title,
                used_for=used_for,
                status="draft",
            )
            await doc.insert()
        rows.append(doc)
    return rows


def _merge_branding_form(branding: InstitutionBranding) -> dict[str, Any]:
    theme = dict(branding.theme or {})
    base = {
        "primary_color": branding.primary_color,
        "secondary_color": branding.secondary_color,
        "text_on_primary": theme.get("text_on_primary"),
        "accent_status": theme.get("accent_status"),
        "display_name": branding.display_name,
    }
    for key, value in (branding.draft_values or {}).items():
        if key in base and value is not None:
            base[key] = value
    return base


def _status_label(status: str) -> str:
    if status == "published":
        return "Published"
    if status == "uploaded":
        return "Uploaded"
    if status == "missing":
        return "Missing"
    return status.replace("_", " ").title()


def _date_label(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y")


def _asset_detail(doc: InstitutionBrandingAsset) -> str:
    if doc.file_name and doc.detail_hint:
        return f"{doc.file_name} · {doc.detail_hint}"
    if doc.file_name:
        return doc.file_name
    return doc.detail_hint or "—"


async def get_institution_branding_page(scope: AccessScope) -> InstitutionBrandingPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_READ)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    branding = await _ensure_branding(tenant)
    await _ensure_profile(tenant)
    assets = await _ensure_assets(tenant_id)
    templates = await _ensure_templates(tenant_id)
    merged = _merge_branding_form(branding)

    primary = next((a for a in assets if a.asset_key == "primary_logo"), None)
    current_summary = None
    if primary and primary.file_name:
        uploaded = _date_label(primary.uploaded_at)
        current_summary = f"Current: {primary.file_name} · uploaded {uploaded}"

    form = InstitutionBrandingFormValues(
        primary_color=str(merged.get("primary_color") or branding.primary_color),
        secondary_color=str(merged.get("secondary_color") or branding.secondary_color),
        text_on_primary=merged.get("text_on_primary"),
        accent_status=merged.get("accent_status"),
        display_name=merged.get("display_name"),
    )

    color_fields = [
        BrandingColorField(
            key=key,
            label=label,
            value=str(merged.get(key) or getattr(form, key, None) or ""),
            required=required,
        )
        for key, label, required in _COLOR_FIELDS
    ]

    template_rows = [
        BrandingDocumentTemplateRow(
            template_key=row.template_key,
            title=row.title,
            used_for=row.used_for,
            last_updated_label=_date_label(row.updated_at),
            status=row.status,
            status_label=_status_label(row.status),
        )
        for row in templates
    ]

    asset_rows = [
        BrandingAssetRow(
            asset_key=doc.asset_key,
            label=doc.label,
            detail_line=_asset_detail(doc),
            status="uploaded" if doc.file_id else "missing",
            status_label=_status_label("uploaded" if doc.file_id else "missing"),
            editable=True,
            file_name=doc.file_name,
            file_id=doc.file_id,
        )
        for doc in assets
    ]

    return InstitutionBrandingPageRead(
        form=form,
        primary_logo=BrandingPrimaryLogoPanel(
            upload_hint="PNG or SVG · min 512 × 512 px · transparent background",
            current_summary=current_summary,
            file_id=(primary.file_id if primary else None) or branding.logo_file_id,
        ),
        color_fields=color_fields,
        document_templates=template_rows,
        template_count_label=f"{len(templates)} templates",
        templates_manage_href="/college-admin/institution/policies",
        brand_assets=asset_rows,
        preview_items=_PREVIEW_ITEMS,
        preview_portal_href="/student",
        footer_note=(
            "Published branding updates the student, faculty and parent portals within 10 minutes."
        ),
        has_draft=bool(branding.draft_values),
        generated_at=utcnow(),
    )


async def save_institution_branding_draft(scope: AccessScope, values: dict[str, Any]) -> InstitutionBrandingPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    branding = await _ensure_branding(tenant)
    allowed = {key for key, _, _ in _COLOR_FIELDS} | {"display_name"}
    branding.draft_values = {k: v for k, v in values.items() if k in allowed and v is not None}
    branding.updated_at = utcnow()
    branding.updated_by = scope.user_id
    await branding.save()
    return await get_institution_branding_page(scope)


async def publish_institution_branding(scope: AccessScope, values: dict[str, Any]) -> InstitutionBrandingPageRead:
    from app.core.form_values import normalize_form_values

    values = normalize_form_values(values)
    authorize(scope, Permission.INSTITUTION_SETTINGS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    branding = await _ensure_branding(tenant)
    merged = {**_merge_branding_form(branding), **{k: v for k, v in values.items() if v is not None}}

    theme = dict(branding.theme or {})
    if merged.get("text_on_primary"):
        theme["text_on_primary"] = str(merged["text_on_primary"])
    if merged.get("accent_status"):
        theme["accent_status"] = str(merged["accent_status"])

    assets = await _ensure_assets(tenant_id)
    primary = next((a for a in assets if a.asset_key == "primary_logo"), None)
    favicon = next((a for a in assets if a.asset_key == "favicon"), None)

    payload: dict[str, Any] = {
        "primary_color": merged.get("primary_color"),
        "secondary_color": merged.get("secondary_color"),
        "logo_file_id": primary.file_id if primary else branding.logo_file_id,
        "favicon_file_id": favicon.file_id if favicon else branding.favicon_file_id,
    }
    if merged.get("display_name"):
        payload["display_name"] = merged["display_name"]
    if theme:
        payload["theme"] = theme
    brand_update = InstitutionBrandingUpdate(**{k: v for k, v in payload.items() if v is not None})
    await update_institution_settings(scope, InstitutionSettingsUpdate(), branding=brand_update)

    branding = await _ensure_branding(tenant)
    branding.draft_values = {}
    branding.published_at = utcnow()
    branding.updated_at = utcnow()
    branding.updated_by = scope.user_id
    await branding.save()

    await _log_activity(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        kind=InstitutionActivityKind.BRANDING_UPDATED,
        resource_type="institution_branding",
        resource_id=str(branding.id),
        summary="Branding published",
    )

    return await get_institution_branding_page(scope)


_MIME_BY_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
}


async def read_institution_branding_file(
    scope: AccessScope,
    storage_key: str,
) -> tuple[bytes, str, str]:
    """Stream a tenant-scoped branding asset (logo, favicon, etc.)."""
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    prefix = f"{tenant_id}/"
    if not storage_key or not storage_key.startswith(prefix):
        raise AppError(code="FORBIDDEN", message="Invalid branding file", status_code=403)
    if ".." in storage_key or storage_key.startswith("/"):
        raise AppError(code="FORBIDDEN", message="Invalid branding file", status_code=403)

    data = file_storage.read_bytes(storage_key)
    ext = Path(storage_key).suffix.lower()
    mime = _MIME_BY_EXT.get(ext, "application/octet-stream")
    filename = Path(storage_key).name
    return data, mime, filename


async def upload_branding_asset(
    scope: AccessScope,
    asset_key: str,
    upload: UploadFile,
) -> InstitutionBrandingAssetRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    valid_keys = {spec[0] for spec in _ASSET_SPECS}
    if asset_key not in valid_keys:
        raise AppError(code="NOT_FOUND", message="Unknown brand asset", status_code=404)

    await _ensure_assets(tenant_id)
    doc = await InstitutionBrandingAsset.find_one(
        Eq(InstitutionBrandingAsset.tenant_id, tenant_id),
        Eq(InstitutionBrandingAsset.asset_key, asset_key),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Brand asset not found", status_code=404)

    raw = await upload.read()
    mime = upload.content_type or "application/octet-stream"
    file_storage.validate_upload(upload.filename or "asset.bin", mime, len(raw))
    storage_key = file_storage.storage_key_for(str(tenant_id), "institution_branding", upload.filename or "asset.bin")
    file_storage.write_bytes(storage_key, raw)

    doc.file_id = storage_key
    doc.file_name = upload.filename
    doc.mime_type = mime
    doc.uploaded_at = utcnow()
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()

    tenant = await Tenant.get(tenant_id)
    if tenant and asset_key == "primary_logo":
        branding = await _ensure_branding(tenant)
        branding.logo_file_id = storage_key
        await branding.save()
    if tenant and asset_key == "favicon":
        branding = await _ensure_branding(tenant)
        branding.favicon_file_id = storage_key
        await branding.save()

    return InstitutionBrandingAssetRead(
        asset_key=doc.asset_key,
        file_id=doc.file_id,
        file_name=doc.file_name,
        uploaded_at=doc.uploaded_at,
    )