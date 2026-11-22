"""Demo college read-only enforcement."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.roles import PLATFORM_ROLES, Role, TENANT_REQUIRED_ROLES
from app.core.config import get_settings
from app.modules.auth.models import User
from app.modules.demo.constants import DEMO_TENANT_CODE
from app.modules.tenants.domain_utils import normalize_tenant_code
from app.modules.tenants.models import Tenant

_MUTATION_BYPASS_ROLES = frozenset({Role.SUPER_ADMIN, Role.PLATFORM_ADMIN})

_DEMO_VIEW_ROLES = TENANT_REQUIRED_ROLES - {Role.STUDENT, Role.PARENT}


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


def demo_college_view_requested(header_value: str | None) -> bool:
    if not header_value:
        return False
    return header_value.strip().lower() in {"1", "true", "yes", "on"}


async def demo_showcase_tenant_id() -> PydanticObjectId | None:
    code = normalize_tenant_code(DEMO_TENANT_CODE)
    tenant = await Tenant.find_one(Eq(Tenant.code, code))
    if tenant is None or not tenant.is_demo:
        return None
    return tenant.id


async def resolve_demo_college_view_tenant_id(user: User, header_value: str | None) -> PydanticObjectId | None:
    """When the college admin UI enables demo mode, scope reads to the showcase tenant."""
    if not demo_college_view_requested(header_value):
        return None
    if user.role in PLATFORM_ROLES:
        return None
    if user.role not in _DEMO_VIEW_ROLES:
        return None
    return await demo_showcase_tenant_id()


async def resolve_effective_tenant_id(
    user: User,
    x_tenant_id: str | None,
    *,
    x_demo_college_view: str | None = None,
) -> PydanticObjectId | None:
    """Mirror get_access_scope tenant resolution for the guard middleware."""
    from app.authorization.permissions import Permission
    from app.authorization.resolver import effective_permissions_for_user
    from app.common.ids import to_object_id

    if x_tenant_id:
        perms = await effective_permissions_for_user(user)
        if Permission.PLATFORM_TENANT_READ in perms:
            return to_object_id(x_tenant_id, "X-Tenant-Id")
    demo_tid = await resolve_demo_college_view_tenant_id(user, x_demo_college_view)
    if demo_tid is not None:
        return demo_tid
    return user.tenant_id