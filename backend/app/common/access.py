"""Access scope for authenticated requests."""

from dataclasses import dataclass, field

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.common.roles import Role


@dataclass(frozen=True)
class AccessScope:
    role: Role
    user_id: PydanticObjectId
    tenant_id: PydanticObjectId | None
    department_id: PydanticObjectId | None
    effective_permissions: frozenset[Permission] = field(default_factory=frozenset)
    support_session_id: PydanticObjectId | None = None
    support_scopes: frozenset[str] = field(default_factory=frozenset)
    support_tenant_id: PydanticObjectId | None = None

    @property
    def is_super_admin(self) -> bool:
        return self.role == Role.SUPER_ADMIN

    @property
    def is_platform_owner(self) -> bool:
        return Permission.PLATFORM_USER_MANAGE in self.effective_permissions
