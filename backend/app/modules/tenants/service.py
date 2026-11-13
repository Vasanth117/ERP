"""College and department operations."""

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.api.deps import AccessScope, assert_tenant_access
from app.common.roles import TENANT_ADMIN_ROLES
from app.common.schemas import Page, Pagination
from app.modules.audit.service import record_audit
from app.modules.tenants.models import Department, Tenant
from app.modules.tenants.schemas import DepartmentCreate, DepartmentRead, TenantCreate, TenantRead


async def create_tenant(scope: AccessScope, payload: TenantCreate) -> TenantRead:
    existing = await Tenant.find_one(Tenant.code == payload.code)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A college with this code already exists")
    tenant = Tenant(name=payload.name, code=payload.code)
    await tenant.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.created",
        resource_type="tenant",
        resource_id=str(tenant.id),
        tenant_id=tenant.id,
        metadata={"code": tenant.code},
    )
    return TenantRead.from_document(tenant)


async def list_tenants(pagination: Pagination) -> Page[TenantRead]:
    total = await Tenant.find_all().count()
    documents = (
        await Tenant.find_all().sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    )
    return Page(
        items=[TenantRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_tenant(scope: AccessScope, tenant_id: PydanticObjectId) -> TenantRead:
    assert_tenant_access(scope, tenant_id)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found")
    return TenantRead.from_document(tenant)


async def _require_active_tenant(scope: AccessScope, tenant_id: PydanticObjectId) -> Tenant:
    assert_tenant_access(scope, tenant_id)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found")
    if not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This college is inactive")
    return tenant


async def create_department(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: DepartmentCreate,
) -> DepartmentRead:
    if scope.role not in TENANT_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission for this action",
        )
    await _require_active_tenant(scope, tenant_id)
    existing = await Department.find_one(Department.tenant_id == tenant_id, Department.code == payload.code)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A department with this code already exists in this college",
        )
    department = Department(tenant_id=tenant_id, name=payload.name, code=payload.code)
    await department.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="department.created",
        resource_type="department",
        resource_id=str(department.id),
        tenant_id=tenant_id,
        metadata={"code": department.code},
    )
    return DepartmentRead.from_document(department)


async def list_departments(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    pagination: Pagination,
) -> Page[DepartmentRead]:
    assert_tenant_access(scope, tenant_id)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found")
    total = await Department.find(Department.tenant_id == tenant_id).count()
    documents = (
        await Department.find(Department.tenant_id == tenant_id)
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    return Page(
        items=[DepartmentRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
