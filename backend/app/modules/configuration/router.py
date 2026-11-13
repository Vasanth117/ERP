"""Configuration and branding routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AccessScope, get_access_scope
from app.authorization.permissions import Permission
from app.api.deps import require_permission
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.modules.configuration.registry import (
    PlatformSettingsUpdate,
    TenantBrandingUpdate,
    TenantFeatureFlagsUpdate,
    TenantSettingsUpdate,
)
from app.modules.configuration.schemas import (
    BrandingRead,
    ConfigurationHistoryItem,
    DomainVerificationInitResult,
    DomainVerificationStatusRead,
    FeatureFlagsRead,
    PlatformConfigurationRead,
    TenantConfigurationRead,
)
from app.modules.configuration.service import (
    confirm_domain_verification,
    get_configuration_history,
    get_domain_verification_status,
    get_feature_flags,
    get_global_configuration,
    get_tenant_branding,
    get_tenant_configuration,
    initiate_domain_verification,
    restore_configuration_version,
    update_feature_flags,
    update_global_configuration,
    update_tenant_branding,
    update_tenant_configuration,
)

platform_router = APIRouter()


@platform_router.get("/configuration", response_model=ApiResponse[PlatformConfigurationRead])
async def get_platform_configuration_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_CONFIG_READ))],
) -> ApiResponse[PlatformConfigurationRead]:
    data = await get_global_configuration(scope)
    return success_response(data, request_id=get_request_id())


@platform_router.patch("/configuration", response_model=ApiResponse[PlatformConfigurationRead])
async def patch_platform_configuration_route(
    payload: PlatformSettingsUpdate,
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_CONFIG_MANAGE))],
) -> ApiResponse[PlatformConfigurationRead]:
    data = await update_global_configuration(scope, payload)
    return success_response(data, request_id=get_request_id())


@platform_router.get("/configuration/history", response_model=ApiResponse[list[ConfigurationHistoryItem]])
async def platform_configuration_history_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_CONFIG_READ))],
) -> ApiResponse[list[ConfigurationHistoryItem]]:
    data = await get_configuration_history(scope, None)
    return success_response(data, request_id=get_request_id())


@platform_router.post(
    "/configuration/restore",
    response_model=ApiResponse[PlatformConfigurationRead],
)
async def restore_platform_configuration_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_CONFIG_MANAGE))],
    scope_name: Annotated[str, Query()] = "platform",
    version_number: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[PlatformConfigurationRead]:
    data = await restore_configuration_version(scope, None, scope_name, version_number)
    return success_response(data, request_id=get_request_id())


tenant_config_router = APIRouter()


@tenant_config_router.get("/configuration", response_model=ApiResponse[TenantConfigurationRead])
async def get_tenant_configuration_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantConfigurationRead]:
    data = await get_tenant_configuration(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@tenant_config_router.patch("/configuration", response_model=ApiResponse[TenantConfigurationRead])
async def patch_tenant_configuration_route(
    tenant_id: str,
    payload: TenantSettingsUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantConfigurationRead]:
    data = await update_tenant_configuration(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@tenant_config_router.get("/configuration/history", response_model=ApiResponse[list[ConfigurationHistoryItem]])
async def tenant_configuration_history_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ConfigurationHistoryItem]]:
    data = await get_configuration_history(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@tenant_config_router.post("/configuration/restore", response_model=ApiResponse[TenantConfigurationRead])
async def restore_tenant_configuration_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    scope_name: Annotated[str, Query()] = "tenant_configuration",
    version_number: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[TenantConfigurationRead]:
    data = await restore_configuration_version(
        scope,
        to_object_id(tenant_id, "tenant id"),
        scope_name,
        version_number,
    )
    return success_response(data, request_id=get_request_id())


@tenant_config_router.get("/branding", response_model=ApiResponse[BrandingRead])
async def get_tenant_branding_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[BrandingRead]:
    data = await get_tenant_branding(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@tenant_config_router.patch("/branding", response_model=ApiResponse[BrandingRead])
async def patch_tenant_branding_route(
    tenant_id: str,
    payload: TenantBrandingUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[BrandingRead]:
    data = await update_tenant_branding(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@tenant_config_router.get("/feature-flags", response_model=ApiResponse[FeatureFlagsRead])
async def get_feature_flags_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[FeatureFlagsRead]:
    data = await get_feature_flags(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@tenant_config_router.patch("/feature-flags", response_model=ApiResponse[FeatureFlagsRead])
async def patch_feature_flags_route(
    tenant_id: str,
    payload: TenantFeatureFlagsUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[FeatureFlagsRead]:
    data = await update_feature_flags(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@tenant_config_router.post(
    "/domains/{domain_id}/verification/initiate",
    response_model=ApiResponse[DomainVerificationInitResult],
)
async def initiate_domain_verification_route(
    tenant_id: str,
    domain_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[DomainVerificationInitResult]:
    data = await initiate_domain_verification(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(domain_id, "domain id"),
    )
    return success_response(data, request_id=get_request_id())


@tenant_config_router.get(
    "/domains/{domain_id}/verification",
    response_model=ApiResponse[DomainVerificationStatusRead],
)
async def domain_verification_status_route(
    tenant_id: str,
    domain_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[DomainVerificationStatusRead]:
    data = await get_domain_verification_status(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(domain_id, "domain id"),
    )
    return success_response(data, request_id=get_request_id())


@tenant_config_router.post(
    "/domains/{domain_id}/verification/confirm",
    response_model=ApiResponse[DomainVerificationStatusRead],
)
async def confirm_domain_verification_route(
    tenant_id: str,
    domain_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    token: Annotated[str, Query(min_length=16)],
) -> ApiResponse[DomainVerificationStatusRead]:
    data = await confirm_domain_verification(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(domain_id, "domain id"),
        token,
    )
    return success_response(data, request_id=get_request_id())
