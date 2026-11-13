"""College and department routes."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, status

from app.api.deps import AccessScope, get_access_scope, pagination_params, require_roles
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.tenants.schemas import DepartmentCreate, DepartmentRead, TenantCreate, TenantRead
from app.modules.tenants.service import (
    create_department,
    create_tenant,
    get_tenant,
    list_departments,
    list_tenants,
)

router = APIRouter()


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant_route(
    payload: TenantCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN))],
) -> TenantRead:
    return await create_tenant(scope, payload)


@router.get("", response_model=Page[TenantRead])
async def list_tenants_route(
    _: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN))],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> Page[TenantRead]:
    return await list_tenants(pagination)


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> TenantRead:
    return await get_tenant(scope, to_object_id(tenant_id, "tenant id"))


@router.post(
    "/{tenant_id}/departments",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_department_route(
    tenant_id: str,
    payload: DepartmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> DepartmentRead:
    return await create_department(scope, to_object_id(tenant_id, "tenant id"), payload)


@router.get("/{tenant_id}/departments", response_model=Page[DepartmentRead])
async def list_departments_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> Page[DepartmentRead]:
    return await list_departments(scope, to_object_id(tenant_id, "tenant id"), pagination)
