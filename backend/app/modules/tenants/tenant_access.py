"""Tenant access policy for suspended and offboarding colleges."""

from beanie import PydanticObjectId

from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.tenants.enums import TenantLifecycleStatus
from app.modules.tenants.models import Tenant

_BLOCKING_LIFECYCLE = frozenset(
    {
        TenantLifecycleStatus.SUSPENDED,
        TenantLifecycleStatus.OFFBOARDING_REQUESTED,
        TenantLifecycleStatus.OFFBOARDING_APPROVED,
        TenantLifecycleStatus.OFFBOARDING_IN_PROGRESS,
        TenantLifecycleStatus.ARCHIVED,
        TenantLifecycleStatus.CLOSED,
    }
)


def tenant_blocks_end_user_access(tenant: Tenant) -> bool:
    return tenant.lifecycle_status in _BLOCKING_LIFECYCLE


async def assert_tenant_allows_user_access(
    tenant_id: PydanticObjectId | None,
    *,
    role: Role,
) -> None:
    """Super/platform admins bypass; college users require an active tenant."""
    if tenant_id is None:
        return
    if role in {Role.SUPER_ADMIN, Role.PLATFORM_ADMIN}:
        return
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    if tenant_blocks_end_user_access(tenant) or not tenant.is_active:
        raise AppError(
            code="TENANT_SUSPENDED",
            message="This college is not available for login or API access",
            status_code=403,
        )
