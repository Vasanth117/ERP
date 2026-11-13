"""Sync Phase 2 lifecycle offboarding with Phase 5 offboarding records."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.data_governance.enums import OffboardingWorkflowStage
from app.modules.data_governance.models import TenantOffboardingRecord
from app.modules.tenants.enums import OffboardingApprovalStatus


async def ensure_offboarding_record_from_lifecycle(
    *,
    tenant_id: PydanticObjectId,
    created_by: PydanticObjectId,
    lifecycle_operation_id: PydanticObjectId,
    reason: str,
    export_required: bool,
) -> TenantOffboardingRecord:
    existing = await TenantOffboardingRecord.find_one(Eq(TenantOffboardingRecord.tenant_id, tenant_id))
    if existing is not None:
        existing.lifecycle_operation_id = lifecycle_operation_id
        existing.report = {**existing.report, "reason": reason, "export_required": export_required}
        existing.updated_at = utcnow()
        await existing.save()
        return existing
    record = TenantOffboardingRecord(
        tenant_id=tenant_id,
        stage=OffboardingWorkflowStage.PENDING_APPROVAL,
        lifecycle_operation_id=lifecycle_operation_id,
        created_by=created_by,
        report={"reason": reason, "export_required": export_required, "source": "lifecycle"},
    )
    record.history.append(
        {"at": utcnow().isoformat(), "event": "synced_from_lifecycle", "actor_id": str(created_by)}
    )
    await record.insert()
    return record


async def mark_offboarding_approved_in_record(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId,
) -> None:
    record = await TenantOffboardingRecord.find_one(Eq(TenantOffboardingRecord.tenant_id, tenant_id))
    if record is None:
        return
    record.stage = OffboardingWorkflowStage.APPROVED
    record.history.append({"at": utcnow().isoformat(), "event": "lifecycle_approved", "actor_id": str(actor_id)})
    record.updated_at = utcnow()
    await record.save()


async def mark_offboarding_started_in_record(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId,
) -> None:
    record = await TenantOffboardingRecord.find_one(Eq(TenantOffboardingRecord.tenant_id, tenant_id))
    if record is None:
        return
    if record.stage == OffboardingWorkflowStage.APPROVED:
        record.stage = OffboardingWorkflowStage.EXPORT_PREPARATION
    record.history.append({"at": utcnow().isoformat(), "event": "lifecycle_offboarding_started", "actor_id": str(actor_id)})
    record.updated_at = utcnow()
    await record.save()
