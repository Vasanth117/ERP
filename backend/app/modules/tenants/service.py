"""College and department operations."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope, assert_tenant_access
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.tenants.models import Department, Tenant
from app.modules.tenants.schemas import DepartmentCreate, DepartmentRead, TenantCreate, TenantRead
from app.repositories.tenant_repository import TenantRepository

_tenant_repo = TenantRepository()


async def create_tenant(scope: AccessScope, payload: TenantCreate) -> TenantRead:
    authorize(scope, Permission.PLATFORM_TENANT_MANAGE)
    existing = await _tenant_repo.find_tenant_by_code(payload.code)
    if existing is not None:
        raise AppError(
            code="CONFLICT",
            message="A college with this code already exists",
            status_code=409,
        )
    tenant = Tenant(name=payload.name, code=payload.code.strip().lower())
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
    total = await _tenant_repo.count_tenants()
    documents = await _tenant_repo.list_tenants(
        skip=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[TenantRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_tenant(scope: AccessScope, tenant_id: PydanticObjectId) -> TenantRead:
    authorize(scope, Permission.TENANT_READ)
    assert_tenant_access(scope, tenant_id)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    return TenantRead.from_document(tenant)


async def _require_active_tenant(scope: AccessScope, tenant_id: PydanticObjectId) -> Tenant:
    assert_tenant_access(scope, tenant_id)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    if not tenant.is_active:
        raise AppError(code="TENANT_INACTIVE", message="This college is inactive", status_code=409)
    return tenant


async def create_department(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: DepartmentCreate,
) -> DepartmentRead:
    authorize(scope, Permission.TENANT_DEPARTMENT_MANAGE)
    await _require_active_tenant(scope, tenant_id)
    existing = await _tenant_repo.find_department_by_code(tenant_id, payload.code)
    if existing is not None:
        raise AppError(
            code="CONFLICT",
            message="A department with this code already exists in this college",
            status_code=409,
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
    authorize(scope, Permission.TENANT_DEPARTMENT_READ)
    assert_tenant_access(scope, tenant_id)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    total = await _tenant_repo.count_departments(tenant_id)
    documents = await _tenant_repo.list_departments(
        tenant_id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[DepartmentRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
