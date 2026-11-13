"""College, onboarding, and department routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import AccessScope, get_access_scope, pagination_params, require_permission
from app.authorization.permissions import Permission
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.tenants.enums import TenantOperationalStatus
from app.modules.tenants.schemas import (
    AvailabilityResponse,
    DepartmentCreate,
    DepartmentRead,
    InvitationCreateResponse,
    OnboardingStatusRead,
    ProvisioningJobRead,
    TenantCreate,
    TenantMetadataUpdate,
    TenantRead,
    TenantRegisterCreate,
    TenantRegistrationResult,
    TenantStatusHistoryRead,
    TenantValidateRequest,
    TenantValidationResult,
)
from app.modules.configuration.router import tenant_config_router
from app.modules.tenants.lifecycle_router import router as lifecycle_router
from app.modules.tenants.service import (
    cancel_tenant_onboarding,
    check_domain_availability,
    check_tenant_code_availability,
    create_department,
    create_tenant,
    get_latest_provisioning_job,
    get_onboarding_history,
    get_onboarding_status,
    get_tenant,
    get_tenant_activity,
    initiate_admin_invitation,
    list_departments,
    list_tenants,
    register_tenant,
    resend_admin_invitation_route,
    retry_tenant_provisioning,
    update_tenant_metadata,
    validate_tenant_registration,
)

router = APIRouter()

router.include_router(lifecycle_router, prefix="/{tenant_id}/lifecycle", tags=["tenant-lifecycle"])
router.include_router(tenant_config_router, prefix="/{tenant_id}", tags=["tenant-configuration"])


@router.post("/register", response_model=ApiResponse[TenantRegistrationResult], status_code=status.HTTP_201_CREATED)
async def register_tenant_route(
    payload: TenantRegisterCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantRegistrationResult]:
    data = await register_tenant(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("", response_model=ApiResponse[TenantRead], status_code=status.HTTP_201_CREATED)
async def create_tenant_route(
    payload: TenantCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantRead]:
    data = await create_tenant(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/validate", response_model=ApiResponse[TenantValidationResult])
async def validate_tenant_route(
    payload: TenantValidateRequest,
    _: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_TENANT_MANAGE))],
) -> ApiResponse[TenantValidationResult]:
    data = await validate_tenant_registration(payload)
    return success_response(data, request_id=get_request_id())


@router.get("/availability/code/{code}", response_model=ApiResponse[AvailabilityResponse])
async def tenant_code_availability_route(
    code: str,
    _: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_TENANT_READ))],
) -> ApiResponse[AvailabilityResponse]:
    data = await check_tenant_code_availability(code)
    return success_response(data, request_id=get_request_id())


@router.get("/availability/domain/{domain}", response_model=ApiResponse[AvailabilityResponse])
async def tenant_domain_availability_route(
    domain: str,
    _: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_TENANT_READ))],
) -> ApiResponse[AvailabilityResponse]:
    data = await check_domain_availability(domain)
    return success_response(data, request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[TenantRead]])
async def list_tenants_route(
    _: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_TENANT_READ))],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status_filter: Annotated[TenantOperationalStatus | None, Query(alias="status")] = None,
) -> ApiResponse[Page[TenantRead]]:
    data = await list_tenants(pagination, status=status_filter)
    return success_response(data, request_id=get_request_id())


@router.get("/{tenant_id}", response_model=ApiResponse[TenantRead])
async def get_tenant_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantRead]:
    data = await get_tenant(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/{tenant_id}", response_model=ApiResponse[TenantRead])
async def update_tenant_route(
    tenant_id: str,
    payload: TenantMetadataUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantRead]:
    data = await update_tenant_metadata(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/{tenant_id}/onboarding", response_model=ApiResponse[OnboardingStatusRead])
async def get_onboarding_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OnboardingStatusRead]:
    data = await get_onboarding_status(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/{tenant_id}/onboarding/history", response_model=ApiResponse[list[OnboardingStatusRead]])
async def get_onboarding_history_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[OnboardingStatusRead]]:
    data = await get_onboarding_history(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/{tenant_id}/activity", response_model=ApiResponse[list[TenantStatusHistoryRead]])
async def get_tenant_activity_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[TenantStatusHistoryRead]]:
    data = await get_tenant_activity(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/{tenant_id}/provisioning/retry", response_model=ApiResponse[TenantRegistrationResult])
async def retry_provisioning_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantRegistrationResult]:
    data = await retry_tenant_provisioning(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/{tenant_id}/provisioning/jobs/latest", response_model=ApiResponse[ProvisioningJobRead])
async def latest_provisioning_job_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ProvisioningJobRead]:
    data = await get_latest_provisioning_job(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post(
    "/{tenant_id}/admin-invitations",
    response_model=ApiResponse[InvitationCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_invitation_route(
    tenant_id: str,
    email: Annotated[str, Query()],
    full_name: Annotated[str, Query()],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[InvitationCreateResponse]:
    data = await initiate_admin_invitation(
        scope,
        to_object_id(tenant_id, "tenant id"),
        email=email,
        full_name=full_name,
    )
    return success_response(data, request_id=get_request_id())


@router.post("/{tenant_id}/admin-invitations/resend", response_model=ApiResponse[InvitationCreateResponse])
async def resend_admin_invitation_http_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[InvitationCreateResponse]:
    data = await resend_admin_invitation_route(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/{tenant_id}/onboarding/cancel", response_model=ApiResponse[OnboardingStatusRead])
async def cancel_onboarding_route(
    tenant_id: str,
    reason: Annotated[str, Query(min_length=3, max_length=500)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OnboardingStatusRead]:
    data = await cancel_tenant_onboarding(scope, to_object_id(tenant_id, "tenant id"), reason=reason)
    return success_response(data, request_id=get_request_id())


@router.post(
    "/{tenant_id}/departments",
    response_model=ApiResponse[DepartmentRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_department_route(
    tenant_id: str,
    payload: DepartmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[DepartmentRead]:
    data = await create_department(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/{tenant_id}/departments", response_model=ApiResponse[Page[DepartmentRead]])
async def list_departments_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[DepartmentRead]]:
    data = await list_departments(scope, to_object_id(tenant_id, "tenant id"), pagination)
    return success_response(data, request_id=get_request_id())
