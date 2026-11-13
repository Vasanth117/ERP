"""College and department routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import AccessScope, get_access_scope, pagination_params, require_permission
from app.authorization.permissions import Permission
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.tenants.schemas import DepartmentCreate, DepartmentRead, TenantCreate, TenantRead
from app.modules.tenants.service import (
    create_department,
    create_tenant,
    get_tenant,
    list_departments,
    list_tenants,
)

router = APIRouter()


@router.post("", response_model=ApiResponse[TenantRead], status_code=status.HTTP_201_CREATED)
async def create_tenant_route(
    payload: TenantCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantRead]:
    data = await create_tenant(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[TenantRead]])
async def list_tenants_route(
    _: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_TENANT_READ))],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[TenantRead]]:
    data = await list_tenants(pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/{tenant_id}", response_model=ApiResponse[TenantRead])
async def get_tenant_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[TenantRead]:
    data = await get_tenant(scope, to_object_id(tenant_id, "tenant id"))
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
