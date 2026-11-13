"""College and department persistence."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.tenants.models import Department, Tenant


class TenantRepository:
  async def find_tenant_by_code(self, code: str) -> Tenant | None:
    from app.modules.tenants.domain_utils import normalize_tenant_code

    return await Tenant.find_one(Eq(Tenant.code, normalize_tenant_code(code)))

  async def get_tenant(self, tenant_id: PydanticObjectId) -> Tenant | None:
    return await Tenant.get(tenant_id)

  async def list_tenants(self, *, skip: int, limit: int) -> list[Tenant]:
    return await Tenant.find_all().sort("-created_at").skip(skip).limit(limit).to_list()

  async def count_tenants(self) -> int:
    return await Tenant.find_all().count()

  async def find_department_by_code(
    self,
    tenant_id: PydanticObjectId,
    code: str,
  ) -> Department | None:
    return await Department.find_one(Eq(Department.tenant_id, tenant_id), Eq(Department.code, code))

  async def list_departments(
    self,
    tenant_id: PydanticObjectId,
    *,
    skip: int,
    limit: int,
  ) -> list[Department]:
    return (
      await Department.find(Eq(Department.tenant_id, tenant_id))
      .sort("-created_at")
      .skip(skip)
      .limit(limit)
      .to_list()
    )

  async def count_departments(self, tenant_id: PydanticObjectId) -> int:
    return await Department.find(Eq(Department.tenant_id, tenant_id)).count()
