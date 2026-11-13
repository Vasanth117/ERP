"""Access scope for authenticated requests."""

from dataclasses import dataclass

from beanie import PydanticObjectId

from app.common.roles import Role


@dataclass(frozen=True)
class AccessScope:
    role: Role
    user_id: PydanticObjectId
    tenant_id: PydanticObjectId | None
    department_id: PydanticObjectId | None

    @property
    def is_super_admin(self) -> bool:
        return self.role == Role.SUPER_ADMIN
