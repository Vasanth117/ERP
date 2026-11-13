"""Lifecycle operation persistence."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.modules.tenants.enums import LifecycleOperationStatus
from app.modules.tenants.lifecycle_models import TenantLifecycleOperation


ACTIVE_OPERATION_STATUSES = frozenset(
    {
        LifecycleOperationStatus.PENDING,
        LifecycleOperationStatus.SCHEDULED,
        LifecycleOperationStatus.RUNNING,
    }
)


class LifecycleRepository:
    async def get_by_idempotency(
        self,
        tenant_id: PydanticObjectId,
        idempotency_key: str,
    ) -> TenantLifecycleOperation | None:
        return await TenantLifecycleOperation.find_one(
            Eq(TenantLifecycleOperation.tenant_id, tenant_id),
            Eq(TenantLifecycleOperation.idempotency_key, idempotency_key),
        )

    async def find_active_for_tenant(self, tenant_id: PydanticObjectId) -> TenantLifecycleOperation | None:
        rows = (
            await TenantLifecycleOperation.find(
                Eq(TenantLifecycleOperation.tenant_id, tenant_id),
                In(TenantLifecycleOperation.status, list(ACTIVE_OPERATION_STATUSES)),
            )
            .sort("-created_at")
            .limit(1)
            .to_list()
        )
        return rows[0] if rows else None

    async def list_pending(self, *, limit: int = 50) -> list[TenantLifecycleOperation]:
        return (
            await TenantLifecycleOperation.find(
                In(TenantLifecycleOperation.status, list(ACTIVE_OPERATION_STATUSES))
            )
            .sort("scheduled_for")
            .limit(limit)
            .to_list()
        )

    async def list_for_tenant(
        self,
        tenant_id: PydanticObjectId,
        *,
        limit: int = 50,
    ) -> list[TenantLifecycleOperation]:
        return (
            await TenantLifecycleOperation.find(Eq(TenantLifecycleOperation.tenant_id, tenant_id))
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
