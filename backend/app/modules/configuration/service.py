"""Platform and tenant configuration services."""

import secrets
from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import hash_refresh_token
from app.modules.audit.service import record_audit
from app.modules.configuration.models import (
    ConfigurationChangeHistory,
    ConfigurationVersion,
    PlatformConfiguration,
    TenantBranding,
    TenantConfiguration,
    TenantFeatureFlags,
)
from app.modules.configuration.registry import (
    PLATFORM_SETTINGS_ALLOWLIST,
    PROTECTED_PLATFORM_KEYS,
    PlatformSettingsUpdate,
    TenantBrandingUpdate,
    TenantFeatureFlagsUpdate,
    TenantSettingsUpdate,
    merge_allowlisted_settings,
    TENANT_SETTINGS_ALLOWLIST,
)
from app.modules.configuration.schemas import (
    BrandingRead,
    ConfigurationHistoryItem,
    ConfigurationVersionRead,
    DomainVerificationInitResult,
    DomainVerificationStatusRead,
    FeatureFlagsRead,
    PlatformConfigurationRead,
    TenantConfigurationRead,
)
from app.modules.tenants.domain_utils import normalize_domain
from app.modules.tenants.enums import DomainVerificationStatus
from app.modules.tenants.lifecycle_models import DomainVerificationRecord
from app.modules.tenants.platform_models import TenantDomain
from app.repositories.tenant_repository import TenantRepository

_tenant_repo = TenantRepository()


async def _ensure_platform_config() -> PlatformConfiguration:
    doc = await PlatformConfiguration.find_one(Eq(PlatformConfiguration.scope_key, "global"))
    if doc is None:
        doc = PlatformConfiguration(settings={})
        await doc.insert()
    return doc


async def _ensure_tenant_config(tenant_id: PydanticObjectId) -> TenantConfiguration:
    doc = await TenantConfiguration.find_one(Eq(TenantConfiguration.tenant_id, tenant_id))
    if doc is None:
        doc = TenantConfiguration(tenant_id=tenant_id, settings={})
        await doc.insert()
    return doc


async def _snapshot_version(
    *,
    tenant_id: PydanticObjectId | None,
    scope: str,
    version_number: int,
    snapshot: dict,
    actor_id: PydanticObjectId,
    changed_keys: list[str],
) -> None:
    await ConfigurationVersion(
        tenant_id=tenant_id,
        scope=scope,
        version_number=version_number,
        snapshot=snapshot,
        created_by=actor_id,
    ).insert()
    await ConfigurationChangeHistory(
        tenant_id=tenant_id,
        scope=scope,
        version_number=version_number,
        changed_keys=changed_keys,
        actor_id=actor_id,
    ).insert()


async def get_global_configuration(scope: AccessScope) -> PlatformConfigurationRead:
    authorize(scope, Permission.PLATFORM_CONFIG_READ)
    doc = await _ensure_platform_config()
    return PlatformConfigurationRead.from_document(doc)


async def update_global_configuration(
    scope: AccessScope,
    payload: PlatformSettingsUpdate,
) -> PlatformConfigurationRead:
    authorize(scope, Permission.PLATFORM_CONFIG_MANAGE)
    for key in payload.to_settings_dict():
        if key in PROTECTED_PLATFORM_KEYS:
            raise AppError(
                code="FORBIDDEN",
                message="Cannot modify protected platform security settings",
                status_code=403,
            )
    doc = await _ensure_platform_config()
    updates = payload.to_settings_dict()
    try:
        doc.settings = merge_allowlisted_settings(doc.settings, updates, PLATFORM_SETTINGS_ALLOWLIST)
    except (ValueError, TypeError) as exc:
        raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc
    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await _snapshot_version(
        tenant_id=None,
        scope="platform",
        version_number=doc.version,
        snapshot=doc.settings,
        actor_id=scope.user_id,
        changed_keys=list(updates.keys()),
    )
    await record_audit(
        actor_id=scope.user_id,
        action="platform.config.updated",
        resource_type="platform_configuration",
        resource_id="global",
        tenant_id=None,
        metadata={"keys": list(updates.keys()), "version": doc.version},
    )
    return PlatformConfigurationRead.from_document(doc)


async def get_tenant_configuration(scope: AccessScope, tenant_id: PydanticObjectId) -> TenantConfigurationRead:
    authorize(scope, Permission.TENANT_CONFIG_READ)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    doc = await _ensure_tenant_config(tenant_id)
    flags = await TenantFeatureFlags.find_one(Eq(TenantFeatureFlags.tenant_id, tenant_id))
    branding = await TenantBranding.find_one(Eq(TenantBranding.tenant_id, tenant_id))
    return TenantConfigurationRead.from_parts(doc, flags=flags, branding=branding, tenant=tenant)


async def update_tenant_configuration(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: TenantSettingsUpdate,
) -> TenantConfigurationRead:
    authorize(scope, Permission.TENANT_CONFIG_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    doc = await _ensure_tenant_config(tenant_id)
    updates = payload.to_settings_dict()
    try:
        doc.settings = merge_allowlisted_settings(doc.settings, updates, TENANT_SETTINGS_ALLOWLIST)
    except (ValueError, TypeError) as exc:
        raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc
    if "timezone" in updates:
        tenant.timezone = updates["timezone"]
    if "locale" in updates:
        tenant.locale = updates["locale"]
    tenant.updated_at = utcnow()
    await tenant.save()
    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await _snapshot_version(
        tenant_id=tenant_id,
        scope="tenant_configuration",
        version_number=doc.version,
        snapshot=doc.settings,
        actor_id=scope.user_id,
        changed_keys=list(updates.keys()),
    )
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.config.updated",
        resource_type="tenant_configuration",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"keys": list(updates.keys()), "version": doc.version},
    )
    return await get_tenant_configuration(scope, tenant_id)


async def get_tenant_branding(scope: AccessScope, tenant_id: PydanticObjectId) -> BrandingRead:
    authorize(scope, Permission.TENANT_CONFIG_READ)
    branding = await TenantBranding.find_one(Eq(TenantBranding.tenant_id, tenant_id))
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    if branding is None:
        branding = TenantBranding(tenant_id=tenant_id, display_name=tenant.name)
        await branding.insert()
    return BrandingRead.from_document(branding)


async def update_tenant_branding(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: TenantBrandingUpdate,
) -> BrandingRead:
    authorize(scope, Permission.TENANT_CONFIG_MANAGE)
    branding = await TenantBranding.find_one(Eq(TenantBranding.tenant_id, tenant_id))
    if branding is None:
        tenant = await _tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
        branding = TenantBranding(tenant_id=tenant_id, display_name=tenant.name)
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(branding, key, value)
    branding.version += 1
    branding.updated_at = utcnow()
    branding.updated_by = scope.user_id
    await branding.save()
    await _snapshot_version(
        tenant_id=tenant_id,
        scope="tenant_branding",
        version_number=branding.version,
        snapshot=branding.model_dump(mode="json"),
        actor_id=scope.user_id,
        changed_keys=list(data.keys()),
    )
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.branding.updated",
        resource_type="tenant_branding",
        resource_id=str(branding.id),
        tenant_id=tenant_id,
        metadata={"version": branding.version},
    )
    return BrandingRead.from_document(branding)


async def get_feature_flags(scope: AccessScope, tenant_id: PydanticObjectId) -> FeatureFlagsRead:
    authorize(scope, Permission.TENANT_CONFIG_READ)
    doc = await TenantFeatureFlags.find_one(Eq(TenantFeatureFlags.tenant_id, tenant_id))
    if doc is None:
        doc = TenantFeatureFlags(tenant_id=tenant_id, flags={})
        await doc.insert()
    return FeatureFlagsRead.from_document(doc)


async def update_feature_flags(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: TenantFeatureFlagsUpdate,
) -> FeatureFlagsRead:
    authorize(scope, Permission.TENANT_CONFIG_MANAGE)
    doc = await TenantFeatureFlags.find_one(Eq(TenantFeatureFlags.tenant_id, tenant_id))
    if doc is None:
        doc = TenantFeatureFlags(tenant_id=tenant_id, flags={})
    doc.flags = payload.flags
    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.feature_flags.updated",
        resource_type="tenant_feature_flags",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"flags": list(payload.flags.keys())},
    )
    return FeatureFlagsRead.from_document(doc)


async def get_configuration_history(
    scope: AccessScope,
    tenant_id: PydanticObjectId | None,
) -> list[ConfigurationHistoryItem]:
    authorize(scope, Permission.PLATFORM_CONFIG_READ if tenant_id is None else Permission.TENANT_CONFIG_READ)
    query = ConfigurationChangeHistory.find_all()
    if tenant_id is None:
        query = ConfigurationChangeHistory.find(Eq(ConfigurationChangeHistory.tenant_id, None))
    else:
        query = ConfigurationChangeHistory.find(Eq(ConfigurationChangeHistory.tenant_id, tenant_id))
    rows = await query.sort("-created_at").limit(50).to_list()
    return [ConfigurationHistoryItem.from_document(row) for row in rows]


async def restore_configuration_version(
    scope: AccessScope,
    tenant_id: PydanticObjectId | None,
    scope_name: str,
    version_number: int,
) -> TenantConfigurationRead | PlatformConfigurationRead:
    if tenant_id is None:
        authorize(scope, Permission.PLATFORM_CONFIG_MANAGE)
    else:
        authorize(scope, Permission.TENANT_CONFIG_MANAGE)
    version_doc = await ConfigurationVersion.find_one(
        Eq(ConfigurationVersion.tenant_id, tenant_id),
        Eq(ConfigurationVersion.scope, scope_name),
        Eq(ConfigurationVersion.version_number, version_number),
    )
    if version_doc is None:
        raise AppError(code="NOT_FOUND", message="Configuration version not found", status_code=404)

    if tenant_id is None:
        doc = await _ensure_platform_config()
        doc.settings = version_doc.snapshot
        doc.version += 1
        doc.updated_at = utcnow()
        doc.updated_by = scope.user_id
        await doc.save()
        return PlatformConfigurationRead.from_document(doc)

    doc = await _ensure_tenant_config(tenant_id)
    doc.settings = version_doc.snapshot
    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    return await get_tenant_configuration(scope, tenant_id)


async def initiate_domain_verification(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    domain_id: PydanticObjectId,
) -> DomainVerificationInitResult:
    authorize(scope, Permission.TENANT_CONFIG_MANAGE)
    domain = await TenantDomain.get(domain_id)
    if domain is None or domain.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Domain not found", status_code=404)
    settings = get_settings()
    token_plain = secrets.token_urlsafe(32)
    record_name = f"_erp-verify.{normalize_domain(domain.normalized_domain)}"
    record_value = f"erp-verify={token_plain}"
    record = DomainVerificationRecord(
        tenant_id=tenant_id,
        domain_id=domain_id,
        normalized_domain=domain.normalized_domain,
        token_hash=hash_refresh_token(token_plain),
        dns_record_name=record_name,
        dns_record_value=record_value,
        expires_at=utcnow() + timedelta(hours=settings.invitation_expire_hours),
    )
    await record.insert()
    domain.verification_status = DomainVerificationStatus.PENDING
    domain.updated_at = utcnow()
    await domain.save()
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.domain_verification.initiated",
        resource_type="tenant_domain",
        resource_id=str(domain.id),
        tenant_id=tenant_id,
    )
    return DomainVerificationInitResult(
        domain_id=str(domain.id),
        dns_record_name=record_name,
        dns_record_value=record_value,
        verification_token=token_plain,
        expires_at=record.expires_at,
    )


async def get_domain_verification_status(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    domain_id: PydanticObjectId,
) -> DomainVerificationStatusRead:
    authorize(scope, Permission.TENANT_CONFIG_READ)
    domain = await TenantDomain.get(domain_id)
    if domain is None or domain.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Domain not found", status_code=404)
    latest = (
        await DomainVerificationRecord.find(
            Eq(DomainVerificationRecord.tenant_id, tenant_id),
            Eq(DomainVerificationRecord.domain_id, domain_id),
        )
        .sort("-created_at")
        .limit(1)
        .to_list()
    )
    record = latest[0] if latest else None
    return DomainVerificationStatusRead.from_domain(domain, record)


async def confirm_domain_verification(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    domain_id: PydanticObjectId,
    token: str,
) -> DomainVerificationStatusRead:
    authorize(scope, Permission.TENANT_CONFIG_MANAGE)
    token_hash = hash_refresh_token(token)
    record = await DomainVerificationRecord.find_one(Eq(DomainVerificationRecord.token_hash, token_hash))
    if record is None or record.tenant_id != tenant_id or record.domain_id != domain_id:
        raise AppError(code="NOT_FOUND", message="Invalid verification token", status_code=404)
    if record.expires_at <= utcnow():
        record.status = "expired"
        await record.save()
        raise AppError(code="VERIFICATION_EXPIRED", message="Verification token expired", status_code=410)
    domain = await TenantDomain.get(domain_id)
    if domain is None:
        raise AppError(code="NOT_FOUND", message="Domain not found", status_code=404)
    record.status = "verified"
    record.verified_at = utcnow()
    await record.save()
    domain.verification_status = DomainVerificationStatus.VERIFIED
    domain.verified_at = utcnow()
    domain.updated_at = utcnow()
    await domain.save()
    return DomainVerificationStatusRead.from_domain(domain, record)
