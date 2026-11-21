"""Demo college read-only enforcement."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.core.config import get_settings
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant

_MUTATION_BYPASS_ROLES = frozenset({Role.SUPER_ADMIN, Role.PLATFORM_ADMIN})


async def tenant_is_demo(tenant_id: PydanticObjectId | None) -> bool:
    if tenant_id is None:
        return False
    tenant = await Tenant.get(tenant_id)
    return tenant is not None and tenant.is_demo


def user_may_mutate_demo(user: User, *, demo_seed_header: str | None = None) -> bool:
    if user.role in _MUTATION_BYPASS_ROLES:
        return True
    settings = get_settings()
    secret = settings.demo_seed_secret
    if secret and demo_seed_header and demo_seed_header == secret:
        return True
    return False


async def demo_blocks_mutation(
    user: User,
    effective_tenant_id: PydanticObjectId | None,
    *,
    demo_seed_header: str | None = None,
) -> bool:
    if not get_settings().demo_mutation_guard_enabled:
        return False
    if user_may_mutate_demo(user, demo_seed_header=demo_seed_header):
        return False
    if effective_tenant_id is None:
        return False
    return await tenant_is_demo(effective_tenant_id)


async def resolve_effective_tenant_id(user: User, x_tenant_id: str | None) -> PydanticObjectId | None:
    """Mirror get_access_scope tenant resolution for the guard middleware."""
    from app.authorization.permissions import Permission
    from app.authorization.resolver import effective_permissions_for_user
    from app.common.ids import to_object_id

    if x_tenant_id:
        perms = await effective_permissions_for_user(user)
        if Permission.PLATFORM_TENANT_READ in perms:
            return to_object_id(x_tenant_id, "X-Tenant-Id")
    return user.tenant_id