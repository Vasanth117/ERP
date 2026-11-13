"""Synchronize lifecycle and legacy operational tenant fields."""

from app.modules.tenants.enums import TenantLifecycleStatus, TenantOperationalStatus, operational_status_for_lifecycle
from app.modules.tenants.models import Tenant


def default_lifecycle_for_operational(status: TenantOperationalStatus) -> TenantLifecycleStatus:
    mapping = {
        TenantOperationalStatus.ONBOARDING: TenantLifecycleStatus.PENDING,
        TenantOperationalStatus.PROVISIONING: TenantLifecycleStatus.PROVISIONING,
        TenantOperationalStatus.ACTIVE: TenantLifecycleStatus.ACTIVE,
        TenantOperationalStatus.SUSPENDED: TenantLifecycleStatus.SUSPENDED,
        TenantOperationalStatus.FAILED: TenantLifecycleStatus.PENDING,
        TenantOperationalStatus.CANCELLED: TenantLifecycleStatus.CLOSED,
    }
    return mapping.get(status, TenantLifecycleStatus.PENDING)


def apply_lifecycle_to_tenant(tenant: Tenant, lifecycle: TenantLifecycleStatus) -> None:
    tenant.lifecycle_status = lifecycle
    tenant.status = operational_status_for_lifecycle(lifecycle)
    if lifecycle == TenantLifecycleStatus.ACTIVE:
        tenant.is_active = True
    elif lifecycle in {
        TenantLifecycleStatus.SUSPENDED,
        TenantLifecycleStatus.OFFBOARDING_REQUESTED,
        TenantLifecycleStatus.OFFBOARDING_APPROVED,
        TenantLifecycleStatus.OFFBOARDING_IN_PROGRESS,
        TenantLifecycleStatus.ARCHIVED,
        TenantLifecycleStatus.CLOSED,
        TenantLifecycleStatus.PENDING,
        TenantLifecycleStatus.PROVISIONING,
    }:
        tenant.is_active = False
