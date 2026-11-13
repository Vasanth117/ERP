"""User persistence."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.auth.models import User


class UserRepository:
  async def find_by_email_for_login(
    self,
    email: str,
    tenant_id: PydanticObjectId | None,
  ) -> User | None:
    """Resolve a user by email within platform or tenant scope."""
    if tenant_id is None:
      return await User.find_one(Eq(User.email, email), Eq(User.tenant_id, None))
    return await User.find_one(Eq(User.email, email), Eq(User.tenant_id, tenant_id))

  async def find_by_email_in_tenant(
    self,
    email: str,
    tenant_id: PydanticObjectId | None,
  ) -> User | None:
    return await self.find_by_email_for_login(email, tenant_id)

  async def list_in_tenant(
    self,
    tenant_id: PydanticObjectId | None,
    *,
    skip: int,
    limit: int,
  ) -> list[User]:
    if tenant_id is None:
      return await User.find(Eq(User.tenant_id, None)).sort("-created_at").skip(skip).limit(limit).to_list()
    return (
      await User.find(Eq(User.tenant_id, tenant_id)).sort("-created_at").skip(skip).limit(limit).to_list()
    )

  async def count_in_tenant(self, tenant_id: PydanticObjectId | None) -> int:
    if tenant_id is None:
      return await User.find(Eq(User.tenant_id, None)).count()
    return await User.find(Eq(User.tenant_id, tenant_id)).count()

  async def get(self, user_id: PydanticObjectId) -> User | None:
    return await User.get(user_id)
