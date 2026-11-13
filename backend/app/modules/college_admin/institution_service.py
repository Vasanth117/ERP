"""Institution profile, campuses, and settings."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.college_admin.enums import InstitutionActivityKind
from app.modules.college_admin.models import (
    InstitutionActivityLog,
    InstitutionBranding,
    InstitutionCampus,
    InstitutionConfigurationVersion,
    InstitutionProfile,
    InstitutionSettings,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.repositories import (
    InstitutionCampusRepository,
    InstitutionHistoryRepository,
    InstitutionProfileRepository,
    InstitutionSettingsRepository,
)
from app.modules.college_admin.schemas import (
    CampusCreate,
    CampusRead,
    CampusUpdate,
    InstitutionConfigurationHistoryItem,
    InstitutionProfileRead,
    InstitutionProfileUpdate,
    InstitutionSettingsRead,
)
from app.modules.college_admin.settings_registry import (
    InstitutionBrandingUpdate,
    InstitutionSettingsUpdate,
    merge_institution_settings,
)
from app.modules.configuration.models import TenantBranding
from app.modules.tenants.models import Tenant
from app.modules.tenants.platform_models import InstitutionAddress

_profile_repo = InstitutionProfileRepository()
_campus_repo = InstitutionCampusRepository()
_settings_repo = InstitutionSettingsRepository()
_history_repo = InstitutionHistoryRepository()


async def _snapshot(
    *,
    tenant_id: PydanticObjectId,
    scope: str,
    version_number: int,
    snapshot: dict,
    actor_id: PydanticObjectId,
    changed_keys: list[str],
) -> None:
    await _history_repo.insert_version(
        InstitutionConfigurationVersion(
            tenant_id=tenant_id,
            scope=scope,
            version_number=version_number,
            snapshot=snapshot,
            changed_keys=changed_keys,
            created_by=actor_id,
        )
    )


async def _log_activity(
    *,
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId,
    kind: InstitutionActivityKind,
    resource_type: str,
    resource_id: str | None,
    summary: str,
    metadata: dict | None = None,
) -> None:
    await InstitutionActivityLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        activity_kind=kind,
        resource_type=resource_type,
        resource_id=resource_id,
        summary=summary,
        metadata=metadata or {},
    ).insert()


async def _ensure_profile(tenant: Tenant) -> InstitutionProfile:
    profile = await _profile_repo.get_by_tenant(tenant.id)
    if profile is not None:
        return profile
    profile = InstitutionProfile(
        tenant_id=tenant.id,
        legal_name=tenant.name,
        display_name=tenant.name,
        institution_email=tenant.institution_email,
        contact_phone=tenant.contact_phone,
        address=tenant.address,
        institution_type=tenant.institution_type,
    )
    await profile.insert()
    return profile


async def _ensure_settings(tenant_id: PydanticObjectId) -> InstitutionSettings:
    doc = await _settings_repo.get_settings(tenant_id)
    if doc is None:
        tenant = await Tenant.get(tenant_id)
        defaults = {"locale": tenant.locale if tenant else "en-US", "timezone": tenant.timezone if tenant else "UTC"}
        doc = InstitutionSettings(tenant_id=tenant_id, settings=defaults)
        await doc.insert()
    return doc


async def _ensure_branding(tenant: Tenant) -> InstitutionBranding:
    doc = await _settings_repo.get_branding(tenant.id)
    if doc is not None:
        return doc
    legacy = await TenantBranding.find_one(Eq(TenantBranding.tenant_id, tenant.id))
    doc = InstitutionBranding(
        tenant_id=tenant.id,
        display_name=legacy.display_name if legacy else tenant.name,
        logo_file_id=legacy.logo_file_id if legacy else None,
        favicon_file_id=legacy.favicon_file_id if legacy else None,
        primary_color=legacy.primary_color if legacy else "#1E40AF",
        secondary_color=legacy.secondary_color if legacy else "#64748B",
        theme=dict(legacy.theme) if legacy else {},
    )
    await doc.insert()
    return doc


async def get_institution_profile(scope: AccessScope) -> InstitutionProfileRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    profile = await _ensure_profile(tenant)
    return InstitutionProfileRead.from_document(
        profile,
        tenant_code=tenant.code,
        timezone=tenant.timezone,
        locale=tenant.locale,
    )


async def update_institution_profile(scope: AccessScope, payload: InstitutionProfileUpdate) -> InstitutionProfileRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    profile = await _ensure_profile(tenant)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return await get_institution_profile(scope)

    if "institution_email" in updates:
        tenant.institution_email = str(updates["institution_email"]).lower()
        profile.institution_email = tenant.institution_email
        updates.pop("institution_email")
    if "contact_phone" in updates:
        tenant.contact_phone = updates["contact_phone"]
        profile.contact_phone = updates["contact_phone"]
        updates.pop("contact_phone")
    if "address" in updates:
        tenant.address = updates["address"]
        profile.address = updates["address"]
        updates.pop("address")
    if "institution_type" in updates:
        tenant.institution_type = updates["institution_type"]
        profile.institution_type = updates["institution_type"]
        updates.pop("institution_type")
    if "display_name" in updates:
        tenant.name = updates["display_name"]
        profile.display_name = updates["display_name"]
        updates.pop("display_name")

    for key, value in updates.items():
        setattr(profile, key, value)

    profile.version += 1
    profile.updated_at = utcnow()
    profile.updated_by = scope.user_id
    tenant.updated_at = utcnow()
    await tenant.save()
    await profile.save()

    await _snapshot(
        tenant_id=tenant_id,
        scope="institution_profile",
        version_number=profile.version,
        snapshot=profile.model_dump(mode="json"),
        actor_id=scope.user_id,
        changed_keys=list(payload.model_dump(exclude_none=True).keys()),
    )
    await _log_activity(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        kind=InstitutionActivityKind.PROFILE_UPDATED,
        resource_type="institution_profile",
        resource_id=str(profile.id),
        summary="Institution profile updated",
    )
    await record_audit(
        actor_id=scope.user_id,
        action="institution.profile.updated",
        resource_type="institution_profile",
        resource_id=str(profile.id),
        tenant_id=tenant_id,
    )
    return await get_institution_profile(scope)


async def list_campuses(scope: AccessScope, *, active_only: bool = False) -> list[CampusRead]:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await _campus_repo.list_for_tenant(tenant_id, active_only=active_only)
    return [CampusRead.from_document(row) for row in rows]


async def create_campus(scope: AccessScope, payload: CampusCreate) -> CampusRead:
    authorize(scope, Permission.INSTITUTION_CAMPUS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    existing = await _campus_repo.get_by_code(tenant_id, payload.campus_code.upper())
    if existing is not None:
        raise AppError(code="CONFLICT", message="Campus code already exists", status_code=409)
    if payload.is_main:
        for main_campus in await InstitutionCampus.find(
            Eq(InstitutionCampus.tenant_id, tenant_id),
            Eq(InstitutionCampus.is_main, True),
        ).to_list():
            main_campus.is_main = False
            await main_campus.save()
    campus = InstitutionCampus(
        tenant_id=tenant_id,
        campus_code=payload.campus_code.upper(),
        name=payload.name,
        is_main=payload.is_main,
        address=payload.address or InstitutionAddress(),
        contact_email=str(payload.contact_email).lower() if payload.contact_email else None,
        contact_phone=payload.contact_phone,
        timezone=payload.timezone,
        locale=payload.locale,
        updated_by=scope.user_id,
    )
    await campus.insert()
    await _log_activity(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        kind=InstitutionActivityKind.CAMPUS_CREATED,
        resource_type="institution_campus",
        resource_id=str(campus.id),
        summary=f"Campus {campus.campus_code} created",
    )
    await record_audit(
        actor_id=scope.user_id,
        action="institution.campus.created",
        resource_type="institution_campus",
        resource_id=str(campus.id),
        tenant_id=tenant_id,
    )
    return CampusRead.from_document(campus)


async def get_campus(scope: AccessScope, campus_id: PydanticObjectId) -> CampusRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    campus = await _campus_repo.get_by_id(tenant_id, campus_id)
    if campus is None:
        raise AppError(code="NOT_FOUND", message="Campus not found", status_code=404)
    return CampusRead.from_document(campus)


async def update_campus(scope: AccessScope, campus_id: PydanticObjectId, payload: CampusUpdate) -> CampusRead:
    authorize(scope, Permission.INSTITUTION_CAMPUS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    campus = await _campus_repo.get_by_id(tenant_id, campus_id)
    if campus is None:
        raise AppError(code="NOT_FOUND", message="Campus not found", status_code=404)
    data = payload.model_dump(exclude_none=True)
    if payload.is_main is True:
        for main_campus in await InstitutionCampus.find(
            Eq(InstitutionCampus.tenant_id, tenant_id),
            Eq(InstitutionCampus.is_main, True),
        ).to_list():
            if main_campus.id != campus.id:
                main_campus.is_main = False
                await main_campus.save()
    for key, value in data.items():
        if key == "contact_email" and value is not None:
            value = str(value).lower()
        setattr(campus, key, value)
    campus.updated_at = utcnow()
    campus.updated_by = scope.user_id
    await campus.save()
    await _log_activity(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        kind=InstitutionActivityKind.CAMPUS_UPDATED,
        resource_type="institution_campus",
        resource_id=str(campus.id),
        summary=f"Campus {campus.campus_code} updated",
    )
    await record_audit(
        actor_id=scope.user_id,
        action="institution.campus.updated",
        resource_type="institution_campus",
        resource_id=str(campus.id),
        tenant_id=tenant_id,
    )
    return CampusRead.from_document(campus)


async def get_institution_settings(scope: AccessScope) -> InstitutionSettingsRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_READ)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    settings = await _ensure_settings(tenant_id)
    branding = await _ensure_branding(tenant)
    return InstitutionSettingsRead.from_parts(settings, branding)


async def update_institution_settings(
    scope: AccessScope,
    payload: InstitutionSettingsUpdate,
    branding: InstitutionBrandingUpdate | None = None,
) -> InstitutionSettingsRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    settings = await _ensure_settings(tenant_id)
    updates = payload.to_settings_dict()
    if updates:
        try:
            settings.settings = merge_institution_settings(settings.settings, updates)
        except (ValueError, TypeError) as exc:
            raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc
        if "timezone" in updates:
            tenant.timezone = updates["timezone"]
        if "locale" in updates:
            tenant.locale = updates["locale"]
        settings.version += 1
        settings.updated_at = utcnow()
        settings.updated_by = scope.user_id
        tenant.updated_at = utcnow()
        await tenant.save()
        await settings.save()
        await _snapshot(
            tenant_id=tenant_id,
            scope="institution_settings",
            version_number=settings.version,
            snapshot=settings.settings,
            actor_id=scope.user_id,
            changed_keys=list(updates.keys()),
        )
        await _log_activity(
            tenant_id=tenant_id,
            actor_id=scope.user_id,
            kind=InstitutionActivityKind.SETTINGS_UPDATED,
            resource_type="institution_settings",
            resource_id=str(settings.id),
            summary="Institution settings updated",
            metadata={"keys": list(updates.keys())},
        )

    if branding is not None:
        branding_doc = await _ensure_branding(tenant)
        brand_updates = branding.model_dump(exclude_none=True)
        for key, value in brand_updates.items():
            setattr(branding_doc, key, value)
        branding_doc.version += 1
        branding_doc.updated_at = utcnow()
        branding_doc.updated_by = scope.user_id
        await branding_doc.save()
        legacy = await TenantBranding.find_one(Eq(TenantBranding.tenant_id, tenant_id))
        if legacy is None:
            legacy = TenantBranding(tenant_id=tenant_id, display_name=branding_doc.display_name)
        for key in ("display_name", "logo_file_id", "favicon_file_id", "primary_color", "secondary_color", "theme"):
            if key in brand_updates:
                setattr(legacy, key, brand_updates[key])
        legacy.version = branding_doc.version
        legacy.updated_at = utcnow()
        legacy.updated_by = scope.user_id
        await legacy.save()
        await _snapshot(
            tenant_id=tenant_id,
            scope="institution_branding",
            version_number=branding_doc.version,
            snapshot=branding_doc.model_dump(mode="json"),
            actor_id=scope.user_id,
            changed_keys=list(brand_updates.keys()),
        )
        await _log_activity(
            tenant_id=tenant_id,
            actor_id=scope.user_id,
            kind=InstitutionActivityKind.BRANDING_UPDATED,
            resource_type="institution_branding",
            resource_id=str(branding_doc.id),
            summary="Institution branding updated",
        )

    await record_audit(
        actor_id=scope.user_id,
        action="institution.settings.updated",
        resource_type="institution_settings",
        resource_id=str(settings.id),
        tenant_id=tenant_id,
    )
    return await get_institution_settings(scope)


async def get_configuration_history(scope: AccessScope) -> list[InstitutionConfigurationHistoryItem]:
    authorize(scope, Permission.INSTITUTION_SETTINGS_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await _history_repo.list_history(tenant_id)
    return [InstitutionConfigurationHistoryItem.from_document(row) for row in rows]
