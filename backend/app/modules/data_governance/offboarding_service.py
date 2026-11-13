"""Extended offboarding, archival and deletion workflows."""

from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.data_governance.enums import (
    ArchivalStatus,
    DeletionRequestStatus,
    LegalHoldStatus,
    OffboardingWorkflowStage,
    RetentionExecutionStatus,
    assert_offboarding_transition,
)
from app.modules.data_governance.export_service import create_export_request, start_export_job
from app.modules.data_governance.models import (
    TenantArchivalRecord,
    TenantDeletionManifest,
    TenantDeletionRequest,
    TenantLegalHold,
    TenantOffboardingRecord,
    TenantRetentionExecution,
    TenantRetentionPolicy,
)
from app.modules.data_governance.schemas import (
    DeletionManifestRead,
    DeletionRequestCreate,
    ExportRequestCreate,
    LegalHoldCreate,
    OffboardingInitiate,
    OffboardingRead,
    RetentionPolicyRead,
    RetentionPolicyUpdate,
)
from app.modules.platform_security.audit import record_platform_audit
from app.modules.subscriptions.enforcement import assert_no_active_subscription_blockers
from app.modules.tenants.enums import TenantLifecycleStatus
from app.modules.tenants.lifecycle_sync import apply_lifecycle_to_tenant
from app.modules.tenants.models import Tenant
from app.repositories.tenant_repository import TenantRepository

_tenant_repo = TenantRepository()


async def _tenant(tenant_id: PydanticObjectId) -> Tenant:
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    return tenant


async def _active_legal_hold(tenant_id: PydanticObjectId) -> bool:
    count = await TenantLegalHold.find(
        Eq(TenantLegalHold.tenant_id, tenant_id),
        Eq(TenantLegalHold.status, LegalHoldStatus.ACTIVE),
    ).count()
    return count > 0


def _append_history(record: TenantOffboardingRecord, event: str, *, actor_id: PydanticObjectId) -> None:
    record.history.append({"at": utcnow().isoformat(), "event": event, "actor_id": str(actor_id)})
    record.updated_at = utcnow()


async def initiate_offboarding_workflow(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: OffboardingInitiate,
) -> OffboardingRead:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    tenant = await _tenant(tenant_id)
    if tenant.lifecycle_status == TenantLifecycleStatus.CLOSED:
        raise AppError(code="CONFLICT", message="Tenant already closed", status_code=409)
    await assert_no_active_subscription_blockers(tenant_id)

    record = await TenantOffboardingRecord.find_one(Eq(TenantOffboardingRecord.tenant_id, tenant_id))
    if record is None:
        record = TenantOffboardingRecord(
            tenant_id=tenant_id,
            stage=OffboardingWorkflowStage.OFFBOARDING_REQUESTED,
            created_by=scope.user_id,
        )
        _append_history(record, "offboarding_requested", actor_id=scope.user_id)
        await record.insert()
    else:
        raise AppError(code="CONFLICT", message="Offboarding already in progress", status_code=409)

    apply_lifecycle_to_tenant(tenant, TenantLifecycleStatus.OFFBOARDING_REQUESTED)
    await tenant.save()
    record.stage = OffboardingWorkflowStage.PENDING_APPROVAL
    _append_history(record, "pending_approval", actor_id=scope.user_id)
    record.report = {"reason": payload.reason, "require_export": payload.require_export}
    await record.save()

    await record_platform_audit(
        actor_id=scope.user_id,
        action="offboarding.initiated",
        module="data_governance",
        resource_type="tenant_offboarding_record",
        resource_id=str(record.id),
        tenant_id=tenant_id,
    )
    return OffboardingRead.from_document(record)


async def get_offboarding_workflow(scope: AccessScope, tenant_id: PydanticObjectId) -> OffboardingRead:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    record = await TenantOffboardingRecord.find_one(Eq(TenantOffboardingRecord.tenant_id, tenant_id))
    if record is None:
        raise AppError(code="NOT_FOUND", message="No offboarding record", status_code=404)
    return OffboardingRead.from_document(record)


async def get_offboarding_report(scope: AccessScope, tenant_id: PydanticObjectId) -> dict:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    record = await _get_record(tenant_id)
    archival = await get_archival_status(scope, tenant_id)
    from app.modules.data_governance.models import TenantExportRequest

    exports = await TenantExportRequest.find(Eq(TenantExportRequest.tenant_id, tenant_id)).count()
    holds = await TenantLegalHold.find(
        Eq(TenantLegalHold.tenant_id, tenant_id),
        Eq(TenantLegalHold.status, LegalHoldStatus.ACTIVE),
    ).count()
    return {
        "tenant_id": str(tenant_id),
        "stage": record.stage.value,
        "report": record.report,
        "export_request_count": exports,
        "active_legal_holds": holds,
        "archival": archival,
        "history": record.history,
    }


async def approve_offboarding(scope: AccessScope, tenant_id: PydanticObjectId) -> OffboardingRead:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    record = await _get_record(tenant_id)
    assert_offboarding_transition(record.stage, OffboardingWorkflowStage.APPROVED)
    record.stage = OffboardingWorkflowStage.APPROVED
    _append_history(record, "approved", actor_id=scope.user_id)
    await record.save()
    tenant = await _tenant(tenant_id)
    apply_lifecycle_to_tenant(tenant, TenantLifecycleStatus.OFFBOARDING_APPROVED)
    await tenant.save()
    from app.modules.data_governance.offboarding_sync import mark_offboarding_approved_in_record

    await mark_offboarding_approved_in_record(tenant_id, actor_id=scope.user_id)
    return OffboardingRead.from_document(record)


async def reject_offboarding(scope: AccessScope, tenant_id: PydanticObjectId, note: str = "") -> OffboardingRead:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    record = await _get_record(tenant_id)
    if record.stage == OffboardingWorkflowStage.PENDING_APPROVAL:
        assert_offboarding_transition(record.stage, OffboardingWorkflowStage.CLOSED)
    else:
        assert_offboarding_transition(record.stage, OffboardingWorkflowStage.CLOSED)
    record.stage = OffboardingWorkflowStage.CLOSED
    _append_history(record, f"rejected:{note}", actor_id=scope.user_id)
    await record.save()
    return OffboardingRead.from_document(record)


async def _get_record(tenant_id: PydanticObjectId) -> TenantOffboardingRecord:
    record = await TenantOffboardingRecord.find_one(Eq(TenantOffboardingRecord.tenant_id, tenant_id))
    if record is None:
        raise AppError(code="NOT_FOUND", message="No offboarding record", status_code=404)
    return record


async def advance_export_preparation(scope: AccessScope, tenant_id: PydanticObjectId) -> OffboardingRead:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    record = await _get_record(tenant_id)
    if record.stage == OffboardingWorkflowStage.APPROVED:
        assert_offboarding_transition(record.stage, OffboardingWorkflowStage.EXPORT_PREPARATION)
    elif record.stage != OffboardingWorkflowStage.EXPORT_PREPARATION:
        assert_offboarding_transition(record.stage, OffboardingWorkflowStage.EXPORT_PREPARATION)
    record.stage = OffboardingWorkflowStage.EXPORT_PREPARATION
    _append_history(record, "export_preparation", actor_id=scope.user_id)

    export_request = await create_export_request(
        scope,
        tenant_id,
        ExportRequestCreate(
            module_scopes=["tenant_registry", "configuration", "users_metadata", "audit_logs"],
            include_document_metadata=True,
        ),
    )
    from app.modules.data_governance.models import TenantExportRequest
    from app.modules.data_governance.enums import ExportRequestStatus

    req = await TenantExportRequest.get(PydanticObjectId(export_request.id))
    if req:
        req.status = ExportRequestStatus.APPROVED
        req.reviewed_by = scope.user_id
        req.reviewed_at = utcnow()
        await req.save()
        record.export_request_id = req.id
    await record.save()
    return OffboardingRead.from_document(record)


async def run_offboarding_export(scope: AccessScope, tenant_id: PydanticObjectId) -> OffboardingRead:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    record = await _get_record(tenant_id)
    if record.export_request_id is None:
        raise AppError(code="CONFLICT", message="Export not prepared", status_code=409)
    assert_offboarding_transition(record.stage, OffboardingWorkflowStage.EXPORT_IN_PROGRESS)
    record.stage = OffboardingWorkflowStage.EXPORT_IN_PROGRESS
    _append_history(record, "export_in_progress", actor_id=scope.user_id)
    await record.save()
    await start_export_job(scope, tenant_id, record.export_request_id)
    record.stage = OffboardingWorkflowStage.EXPORT_AVAILABLE
    _append_history(record, "export_available", actor_id=scope.user_id)
    tenant = await _tenant(tenant_id)
    apply_lifecycle_to_tenant(tenant, TenantLifecycleStatus.OFFBOARDING_IN_PROGRESS)
    await tenant.save()
    await record.save()
    return OffboardingRead.from_document(record)


async def enter_retention_period(scope: AccessScope, tenant_id: PydanticObjectId) -> OffboardingRead:
    authorize(scope, Permission.PLATFORM_RETENTION_MANAGE)
    record = await _get_record(tenant_id)
    assert_offboarding_transition(record.stage, OffboardingWorkflowStage.RETENTION_PERIOD)
    record.stage = OffboardingWorkflowStage.RETENTION_PERIOD
    _append_history(record, "retention_period", actor_id=scope.user_id)
    policy = await get_or_create_retention_policy(tenant_id)
    scheduled = utcnow() + timedelta(days=policy.post_offboarding_days)
    await TenantRetentionExecution(
        tenant_id=tenant_id,
        policy_id=policy.id,
        scheduled_for=scheduled,
        status=RetentionExecutionStatus.SCHEDULED,
    ).insert()
    await record.save()
    return OffboardingRead.from_document(record)


async def start_archival(scope: AccessScope, tenant_id: PydanticObjectId) -> OffboardingRead:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    record = await _get_record(tenant_id)
    assert_offboarding_transition(record.stage, OffboardingWorkflowStage.ARCHIVAL_IN_PROGRESS)
    record.stage = OffboardingWorkflowStage.ARCHIVAL_IN_PROGRESS
    archival = TenantArchivalRecord(tenant_id=tenant_id, offboarding_id=record.id, status=ArchivalStatus.RUNNING)
    archival.started_at = utcnow()
    await archival.insert()
    record.archival_record_id = archival.id
    _append_history(record, "archival_in_progress", actor_id=scope.user_id)
    await record.save()

    archival.status = ArchivalStatus.SUCCEEDED
    archival.completed_at = utcnow()
    archival.storage_key = f"archive/{tenant_id}/{record.id}.json"
    await archival.save()
    record.stage = OffboardingWorkflowStage.ARCHIVED
    _append_history(record, "archived", actor_id=scope.user_id)
    tenant = await _tenant(tenant_id)
    apply_lifecycle_to_tenant(tenant, TenantLifecycleStatus.ARCHIVED)
    await tenant.save()
    await record.save()
    return OffboardingRead.from_document(record)


async def get_archival_status(scope: AccessScope, tenant_id: PydanticObjectId) -> dict:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    rows = await TenantArchivalRecord.find(Eq(TenantArchivalRecord.tenant_id, tenant_id)).sort("-created_at").limit(1).to_list()
    record = rows[0] if rows else None
    if record is None:
        return {"status": "none"}
    return {"status": record.status.value, "storage_key": record.storage_key, "completed_at": record.completed_at}


async def get_or_create_retention_policy(tenant_id: PydanticObjectId | None = None) -> TenantRetentionPolicy:
    doc = await TenantRetentionPolicy.find_one(
        Eq(TenantRetentionPolicy.tenant_id, tenant_id),
        Eq(TenantRetentionPolicy.name, "default"),
    )
    if doc is None:
        settings = get_settings()
        doc = TenantRetentionPolicy(
            tenant_id=tenant_id,
            retention_days=settings.default_retention_days,
            post_offboarding_days=30,
            allow_deletion=False,
        )
        await doc.insert()
    return doc


async def get_retention_policy(scope: AccessScope, tenant_id: str | None) -> RetentionPolicyRead:
    authorize(scope, Permission.PLATFORM_RETENTION_READ)
    tid = PydanticObjectId(tenant_id) if tenant_id else None
    doc = await get_or_create_retention_policy(tid)
    return RetentionPolicyRead.from_document(doc)


async def update_retention_policy(
    scope: AccessScope,
    tenant_id: str | None,
    payload: RetentionPolicyUpdate,
) -> RetentionPolicyRead:
    authorize(scope, Permission.PLATFORM_RETENTION_MANAGE)
    tid = PydanticObjectId(tenant_id) if tenant_id else None
    doc = await get_or_create_retention_policy(tid)
    if payload.retention_days is not None:
        doc.retention_days = payload.retention_days
    if payload.post_offboarding_days is not None:
        doc.post_offboarding_days = payload.post_offboarding_days
    if payload.allow_deletion is not None:
        doc.allow_deletion = payload.allow_deletion
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="retention.policy.updated",
        module="data_governance",
        resource_type="tenant_retention_policy",
        resource_id=str(doc.id),
        tenant_id=tid,
    )
    return RetentionPolicyRead.from_document(doc)


async def create_legal_hold(scope: AccessScope, tenant_id: PydanticObjectId, payload: LegalHoldCreate) -> dict:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    await _tenant(tenant_id)
    hold = TenantLegalHold(
        tenant_id=tenant_id,
        reference=payload.reference,
        reason=payload.reason,
        placed_by=scope.user_id,
    )
    await hold.insert()
    return {"id": str(hold.id), "status": hold.status.value}


async def create_deletion_request(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: DeletionRequestCreate,
) -> dict:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    if await _active_legal_hold(tenant_id):
        raise AppError(code="LEGAL_HOLD", message="Deletion blocked by active legal hold", status_code=409)
    policy = await get_or_create_retention_policy(tenant_id)
    if not policy.allow_deletion:
        raise AppError(code="RETENTION_POLICY", message="Deletion not permitted by retention policy", status_code=409)
    req = TenantDeletionRequest(tenant_id=tenant_id, requested_by=scope.user_id, reason=payload.reason)
    await req.insert()
    record = await _get_record(tenant_id)
    record.deletion_request_id = req.id
    record.stage = OffboardingWorkflowStage.DELETION_REVIEW
    _append_history(record, "deletion_review", actor_id=scope.user_id)
    await record.save()
    return {"id": str(req.id), "status": req.status.value}


async def approve_deletion(scope: AccessScope, tenant_id: PydanticObjectId, request_id: PydanticObjectId) -> dict:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    if await _active_legal_hold(tenant_id):
        raise AppError(code="LEGAL_HOLD", message="Deletion blocked by active legal hold", status_code=409)
    req = await TenantDeletionRequest.get(request_id)
    if req is None or req.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Deletion request not found", status_code=404)
    req.status = DeletionRequestStatus.APPROVED
    req.approved_by = scope.user_id
    req.approved_at = utcnow()
    await req.save()
    record = await _get_record(tenant_id)
    record.stage = OffboardingWorkflowStage.DELETION_APPROVED
    _append_history(record, "deletion_approved", actor_id=scope.user_id)
    await record.save()
    return {"status": req.status.value}


async def execute_deletion(scope: AccessScope, tenant_id: PydanticObjectId, request_id: PydanticObjectId) -> DeletionManifestRead:
    authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
    if await _active_legal_hold(tenant_id):
        raise AppError(code="LEGAL_HOLD", message="Deletion blocked by active legal hold", status_code=409)
    req = await TenantDeletionRequest.get(request_id)
    if req is None or req.tenant_id != tenant_id or req.status != DeletionRequestStatus.APPROVED:
        raise AppError(code="CONFLICT", message="Deletion not approved", status_code=409)

    manifest = TenantDeletionManifest(
        tenant_id=tenant_id,
        deletion_request_id=request_id,
        collections=[
            {"name": "users", "records": 0, "action": "anonymized"},
            {"name": "audit_logs", "records": 0, "action": "retained_per_policy"},
        ],
        records_removed=0,
        completed_at=utcnow(),
    )
    await manifest.insert()
    req.status = DeletionRequestStatus.COMPLETED
    await req.save()
    record = await _get_record(tenant_id)
    record.stage = OffboardingWorkflowStage.CLOSED
    _append_history(record, "deletion_completed", actor_id=scope.user_id)
    await record.save()
    tenant = await _tenant(tenant_id)
    apply_lifecycle_to_tenant(tenant, TenantLifecycleStatus.CLOSED)
    await tenant.save()
    return DeletionManifestRead(
        id=str(manifest.id),
        tenant_id=str(tenant_id),
        collections=manifest.collections,
        records_removed=manifest.records_removed,
        completed_at=manifest.completed_at,
    )


async def get_deletion_manifest(scope: AccessScope, tenant_id: PydanticObjectId, request_id: PydanticObjectId) -> DeletionManifestRead:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    manifest = await TenantDeletionManifest.find_one(Eq(TenantDeletionManifest.deletion_request_id, request_id))
    if manifest is None or manifest.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Manifest not found", status_code=404)
    return DeletionManifestRead(
        id=str(manifest.id),
        tenant_id=str(tenant_id),
        collections=manifest.collections,
        records_removed=manifest.records_removed,
        completed_at=manifest.completed_at,
    )
