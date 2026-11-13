"""Platform tenant lifecycle persistence."""

from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE, In

from app.modules.tenants.enums import (
    InvitationStatus,
    OnboardingStage,
    PlatformAlertSeverity,
    ProvisioningJobStatus,
    TenantOperationalStatus,
)
from app.modules.tenants.models import Tenant
from app.modules.tenants.platform_models import (
    PlatformAlert,
    PlatformMetricsSnapshot,
    TenantAdminInvitation,
    TenantDomain,
    TenantOnboarding,
    TenantProvisioningJob,
    TenantStatusHistory,
)


class PlatformTenantRepository:
    async def count_tenants_by_status(self) -> dict[str, int]:
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        rows = await Tenant.get_motor_collection().aggregate(pipeline).to_list(length=20)
        return {row["_id"]: row["count"] for row in rows}

    async def count_total_tenants(self) -> int:
        return await Tenant.find_all().count()

    async def list_tenants_filtered(
        self,
        *,
        skip: int,
        limit: int,
        status: TenantOperationalStatus | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[Tenant]:
        query = Tenant.find_all()
        if status is not None:
            query = Tenant.find(Eq(Tenant.status, status))
        if created_from is not None:
            query = query.find(GTE(Tenant.created_at, created_from))
        if created_to is not None:
            query = query.find(LTE(Tenant.created_at, created_to))
        return await query.sort("-created_at").skip(skip).limit(limit).to_list()

    async def count_tenants_filtered(
        self,
        *,
        status: TenantOperationalStatus | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> int:
        query = Tenant.find_all()
        if status is not None:
            query = Tenant.find(Eq(Tenant.status, status))
        if created_from is not None:
            query = query.find(GTE(Tenant.created_at, created_from))
        if created_to is not None:
            query = query.find(LTE(Tenant.created_at, created_to))
        return await query.count()

    async def recent_tenants(self, *, limit: int = 10) -> list[Tenant]:
        return await Tenant.find_all().sort("-created_at").limit(limit).to_list()

    async def recently_activated(self, *, limit: int = 10) -> list[Tenant]:
        return (
            await Tenant.find(Eq(Tenant.status, TenantOperationalStatus.ACTIVE))
            .find({"activated_at": {"$ne": None}})
            .sort("-activated_at")
            .limit(limit)
            .to_list()
        )


class OnboardingRepository:
    async def get_by_tenant(self, tenant_id: PydanticObjectId) -> TenantOnboarding | None:
        return await TenantOnboarding.find_one(Eq(TenantOnboarding.tenant_id, tenant_id))

    async def count_by_stages(self, stages: list[OnboardingStage]) -> int:
        if not stages:
            return 0
        return await TenantOnboarding.find(In(TenantOnboarding.stage, stages)).count()

    async def stage_distribution(self) -> dict[str, int]:
        pipeline = [{"$group": {"_id": "$stage", "count": {"$sum": 1}}}]
        rows = await TenantOnboarding.get_motor_collection().aggregate(pipeline).to_list(length=20)
        return {row["_id"]: row["count"] for row in rows}

    async def completion_stats(self) -> dict[str, int]:
        total = await TenantOnboarding.find_all().count()
        completed = await TenantOnboarding.find(
            Eq(TenantOnboarding.stage, OnboardingStage.COMPLETED)
        ).count()
        in_progress = total - completed
        return {"total": total, "completed": completed, "in_progress": in_progress}


class DomainRepository:
    async def find_by_normalized(self, normalized: str) -> TenantDomain | None:
        return await TenantDomain.find_one(Eq(TenantDomain.normalized_domain, normalized))

    async def get_primary(self, tenant_id: PydanticObjectId) -> TenantDomain | None:
        return await TenantDomain.find_one(
            Eq(TenantDomain.tenant_id, tenant_id),
            Eq(TenantDomain.is_primary, True),
        )


class InvitationRepository:
    async def get_active_for_tenant(self, tenant_id: PydanticObjectId) -> TenantAdminInvitation | None:
        rows = (
            await TenantAdminInvitation.find(
                Eq(TenantAdminInvitation.tenant_id, tenant_id),
                Eq(TenantAdminInvitation.status, InvitationStatus.PENDING),
            )
            .sort("-created_at")
            .limit(1)
            .to_list()
        )
        return rows[0] if rows else None

    async def find_by_hash(self, token_hash: str) -> TenantAdminInvitation | None:
        return await TenantAdminInvitation.find_one(Eq(TenantAdminInvitation.token_hash, token_hash))


class ProvisioningRepository:
    async def get_job(
        self,
        tenant_id: PydanticObjectId,
        idempotency_key: str,
    ) -> TenantProvisioningJob | None:
        return await TenantProvisioningJob.find_one(
            Eq(TenantProvisioningJob.tenant_id, tenant_id),
            Eq(TenantProvisioningJob.idempotency_key, idempotency_key),
        )

    async def latest_job(self, tenant_id: PydanticObjectId) -> TenantProvisioningJob | None:
        return (
            await TenantProvisioningJob.find(Eq(TenantProvisioningJob.tenant_id, tenant_id))
            .sort("-created_at")
            .limit(1)
            .to_list()
        )

    async def count_by_status(self, status: ProvisioningJobStatus) -> int:
        return await TenantProvisioningJob.find(Eq(TenantProvisioningJob.status, status)).count()


class StatusHistoryRepository:
    async def list_for_tenant(
        self,
        tenant_id: PydanticObjectId,
        *,
        limit: int = 50,
    ) -> list[TenantStatusHistory]:
        return (
            await TenantStatusHistory.find(Eq(TenantStatusHistory.tenant_id, tenant_id))
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )

    async def append(
        self,
        *,
        tenant_id: PydanticObjectId,
        from_status: str | None,
        to_status: str,
        actor_id: PydanticObjectId | None,
        reason: str | None = None,
        from_lifecycle: str | None = None,
        to_lifecycle: str | None = None,
        operation_id: str | None = None,
    ) -> TenantStatusHistory:
        entry = TenantStatusHistory(
            tenant_id=tenant_id,
            from_status=from_status,
            to_status=to_status,
            from_lifecycle=from_lifecycle,
            to_lifecycle=to_lifecycle,
            operation_id=operation_id,
            actor_id=actor_id,
            reason=reason,
        )
        await entry.insert()
        return entry


class PlatformAlertRepository:
    async def list_open(
        self,
        *,
        limit: int = 50,
        severity: PlatformAlertSeverity | None = None,
    ) -> list[PlatformAlert]:
        query = PlatformAlert.find(Eq(PlatformAlert.acknowledged, False))
        if severity is not None:
            query = query.find(Eq(PlatformAlert.severity, severity))
        return await query.sort("-created_at").limit(limit).to_list()

    async def count_critical_open(self) -> int:
        return await PlatformAlert.find(
            Eq(PlatformAlert.acknowledged, False),
            Eq(PlatformAlert.severity, PlatformAlertSeverity.CRITICAL),
        ).count()


class MetricsSnapshotRepository:
    async def latest(self) -> PlatformMetricsSnapshot | None:
        rows = await PlatformMetricsSnapshot.find_all().sort("-captured_at").limit(1).to_list()
        return rows[0] if rows else None
