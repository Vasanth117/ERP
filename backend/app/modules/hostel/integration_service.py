"""Hostel integration management — bindings, sync, webhooks, reconciliation."""

from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.integration_admin_models import InstitutionIntegration, InstitutionIntegrationHealth
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hostel.hostel_audit_helper import record_hostel_audit
from app.modules.hostel.integration_models import (
    HostelIntegrationBinding,
    HostelIntegrationBindingStatus,
    HostelIntegrationCategory,
    HostelIntegrationEvent,
    HostelIntegrationFailure,
    HostelIntegrationMapping,
    HostelIntegrationReconciliation,
    HostelIntegrationSyncJob,
    HostelSyncJobStatus,
    HostelWebhookSubscription,
)
from app.modules.hostel.integration_schemas import (
    IntegrationBindingRead,
    IntegrationBindingUpsert,
    IntegrationDashboard,
    IntegrationEventRead,
    IntegrationFailureRead,
    ManualSyncRequest,
    ReconciliationRead,
    SyncJobRead,
    WebhookIngest,
)
from app.modules.hostel.mess_models import HostelMessBillingRecord, HostelMessFinanceReference
from app.modules.hostel.policy import authorize_hostel_integration_manage, authorize_hostel_integration_read, require_hostel_tenant_scope
from app.modules.hostel.resident_models import HostelResident
from app.modules.students.models import StudentProfile

DEFAULT_BINDINGS: list[tuple[HostelIntegrationCategory, str, str]] = [
    (HostelIntegrationCategory.STUDENT, "hostel_student", "student_profile"),
    (HostelIntegrationCategory.FINANCE, "hostel_finance", "finance"),
    (HostelIntegrationCategory.NOTIFICATION, "hostel_notification", "notification"),
    (HostelIntegrationCategory.DOCUMENT, "hostel_document", "object_storage"),
    (HostelIntegrationCategory.GATE_SECURITY, "hostel_gate", "webhook"),
    (HostelIntegrationCategory.CAMPUS, "hostel_campus", "campus"),
]


async def _ensure_bindings(tenant_id: PydanticObjectId) -> None:
    for category, key, provider in DEFAULT_BINDINGS:
        existing = await HostelIntegrationBinding.find_one(
            Eq(HostelIntegrationBinding.tenant_id, tenant_id), Eq(HostelIntegrationBinding.category, category)
        )
        if existing:
            continue
        await HostelIntegrationBinding(
            tenant_id=tenant_id,
            category=category,
            integration_key=key,
            provider_code=provider,
            enabled=False,
        ).insert()


async def integration_dashboard(scope: AccessScope) -> IntegrationDashboard:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_read(scope)
    await _ensure_bindings(tenant_id)
    rows = await HostelIntegrationBinding.find(Eq(HostelIntegrationBinding.tenant_id, tenant_id)).to_list()
    pending = await HostelIntegrationSyncJob.find(
        {"tenant_id": tenant_id, "status": {"$in": [HostelSyncJobStatus.PENDING.value, HostelSyncJobStatus.RUNNING.value]}}
    ).count()
    failed_jobs = await HostelIntegrationSyncJob.find(
        {"tenant_id": tenant_id, "status": HostelSyncJobStatus.FAILED.value}
    ).count()
    open_failures = await HostelIntegrationFailure.find(
        {"tenant_id": tenant_id, "resolved": False}
    ).count()
    last_sync = max((r.last_sync_at for r in rows if r.last_sync_at), default=None)
    return IntegrationDashboard(
        total_bindings=len(rows),
        active_bindings=sum(1 for r in rows if r.status == HostelIntegrationBindingStatus.ACTIVE),
        inactive_bindings=sum(1 for r in rows if r.status == HostelIntegrationBindingStatus.INACTIVE),
        failed_bindings=sum(1 for r in rows if r.status == HostelIntegrationBindingStatus.FAILED),
        pending_jobs=pending,
        failed_jobs=failed_jobs,
        open_failures=open_failures,
        last_sync_at=last_sync,
    )


def _binding_read(doc: HostelIntegrationBinding) -> IntegrationBindingRead:
    return IntegrationBindingRead(
        category=doc.category,
        integration_key=doc.integration_key,
        provider_code=doc.provider_code,
        enabled=doc.enabled,
        status=doc.status,
        sync_method=doc.sync_method,
        sync_frequency=doc.sync_frequency,
        last_sync_at=doc.last_sync_at,
        institution_integration_key=doc.institution_integration_key,
    )


async def list_bindings(scope: AccessScope) -> list[IntegrationBindingRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_read(scope)
    await _ensure_bindings(tenant_id)
    rows = await HostelIntegrationBinding.find(Eq(HostelIntegrationBinding.tenant_id, tenant_id)).to_list()
    return [_binding_read(r) for r in rows]


async def upsert_binding(scope: AccessScope, payload: IntegrationBindingUpsert) -> IntegrationBindingRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_manage(scope)
    doc = await HostelIntegrationBinding.find_one(
        Eq(HostelIntegrationBinding.tenant_id, tenant_id), Eq(HostelIntegrationBinding.category, payload.category)
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Binding not initialized", status_code=404)
    doc.provider_code = payload.provider_code
    doc.institution_integration_key = payload.institution_integration_key
    doc.enabled = payload.enabled
    doc.sync_method = payload.sync_method
    doc.sync_frequency = payload.sync_frequency
    doc.timeout_seconds = payload.timeout_seconds
    doc.retry_max = payload.retry_max
    doc.backoff_seconds = payload.backoff_seconds
    doc.hostel_codes = [h.upper() for h in payload.hostel_codes]
    doc.environment = payload.environment
    doc.status = HostelIntegrationBindingStatus.ACTIVE if payload.enabled else HostelIntegrationBindingStatus.INACTIVE
    if payload.institution_integration_key:
        inst = await InstitutionIntegration.find_one(
            Eq(InstitutionIntegration.tenant_id, tenant_id),
            Eq(InstitutionIntegration.integration_key, payload.institution_integration_key),
        )
        if inst:
            doc.platform_configuration_id = inst.configuration_id
    doc.owner_user_id = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    if payload.signing_secret_ref and payload.category == HostelIntegrationCategory.GATE_SECURITY:
        sub_id = f"hwh_{uuid4().hex[:8]}"
        existing = await HostelWebhookSubscription.find_one(
            Eq(HostelWebhookSubscription.tenant_id, tenant_id), Eq(HostelWebhookSubscription.category, payload.category)
        )
        if existing:
            existing.signing_secret_ref = payload.signing_secret_ref
            existing.enabled = payload.enabled
            existing.updated_at = utcnow()
            await existing.save()
        else:
            await HostelWebhookSubscription(
                tenant_id=tenant_id,
                subscription_id=sub_id,
                category=payload.category,
                endpoint_path=f"/api/v1/hostel/integrations/webhooks/{payload.category.value}",
                signing_secret_ref=payload.signing_secret_ref,
                enabled=payload.enabled,
            ).insert()
    await record_hostel_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.integration.config_update",
        module="hostel_integration",
        resource_type="integration_binding",
        resource_id=doc.integration_key,
    )
    return _binding_read(doc)


async def _create_job(tenant_id: PydanticObjectId, category: HostelIntegrationCategory, trigger: str, actor_id) -> HostelIntegrationSyncJob:
    job_id = f"hsj_{uuid4().hex[:10]}"
    return await HostelIntegrationSyncJob(
        tenant_id=tenant_id,
        job_id=job_id,
        category=category,
        trigger=trigger,
        status=HostelSyncJobStatus.RUNNING,
        actor_id=actor_id,
    ).insert()


async def _student_sync(tenant_id: PydanticObjectId, job: HostelIntegrationSyncJob) -> None:
    residents = await HostelResident.find({"tenant_id": tenant_id}).to_list()
    ok, fail = 0, 0
    for res in residents:
        profile = await StudentProfile.find_one(
            Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, res.student_user_id)
        )
        if profile is None:
            fail += 1
            await HostelIntegrationFailure(
                tenant_id=tenant_id,
                failure_id=f"hif_{uuid4().hex[:10]}",
                category=HostelIntegrationCategory.STUDENT,
                job_id=job.job_id,
                reason=f"Missing student profile for resident {res.resident_id}",
            ).insert()
            continue
        ext = str(profile.user_id)
        internal = res.resident_id
        dup = await HostelIntegrationMapping.find_one(
            {"tenant_id": tenant_id, "category": HostelIntegrationCategory.STUDENT.value, "external_ref": ext}
        )
        if dup and dup.internal_ref != internal:
            fail += 1
            await HostelIntegrationFailure(
                tenant_id=tenant_id,
                failure_id=f"hif_{uuid4().hex[:10]}",
                category=HostelIntegrationCategory.STUDENT,
                job_id=job.job_id,
                reason=f"Mapping conflict for student {ext}: {dup.internal_ref} vs {internal}",
                retriable=False,
            ).insert()
            continue
        if not dup:
            await HostelIntegrationMapping(
                tenant_id=tenant_id,
                category=HostelIntegrationCategory.STUDENT,
                external_ref=ext,
                internal_ref=internal,
                internal_type="resident",
                hostel_code=res.hostel_code,
                verified_at=utcnow(),
            ).insert()
        ok += 1
    job.records_processed = len(residents)
    job.records_success = ok
    job.records_failed = fail


async def _finance_sync(tenant_id: PydanticObjectId, job: HostelIntegrationSyncJob) -> None:
    rows = await HostelMessBillingRecord.find({"tenant_id": tenant_id, "finance_demand_id": {"$ne": None}}).to_list()
    ok, fail, mismatch = 0, 0, 0
    for row in rows:
        demand = await StudentFeeDemand.find_one(
            Eq(StudentFeeDemand.tenant_id, tenant_id), Eq(StudentFeeDemand.demand_id, row.finance_demand_id)
        )
        if demand is None:
            fail += 1
            status = "missing_external"
        elif demand.student_user_id != row.student_user_id:
            mismatch += 1
            status = "mismatch"
        else:
            ok += 1
            status = "matched" if demand.status == FeeDemandStatus.PAID else "open"
        rec_id = f"hr_{uuid4().hex[:10]}"
        await HostelIntegrationReconciliation(
            tenant_id=tenant_id,
            record_id=rec_id,
            category=HostelIntegrationCategory.FINANCE,
            internal_ref=row.record_id,
            external_ref=row.finance_demand_id,
            status=status,
            detail={"finance_status": demand.status.value if demand else None, "amount": row.amount},
        ).insert()
        ref = await HostelMessFinanceReference.find_one(
            Eq(HostelMessFinanceReference.tenant_id, tenant_id), Eq(HostelMessFinanceReference.record_id, row.record_id)
        )
        if ref and demand:
            ref.synced_status = demand.status.value
            ref.last_synced_at = utcnow()
            await ref.save()
    job.records_processed = len(rows)
    job.records_success = ok
    job.records_failed = fail + mismatch


async def run_manual_sync(scope: AccessScope, payload: ManualSyncRequest) -> SyncJobRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_manage(scope)
    binding = await HostelIntegrationBinding.find_one(
        Eq(HostelIntegrationBinding.tenant_id, tenant_id), Eq(HostelIntegrationBinding.category, payload.category)
    )
    if binding is None or not binding.enabled:
        raise AppError(code="VALIDATION_ERROR", message="Integration not enabled", status_code=422)
    job = await _create_job(tenant_id, payload.category, "manual", scope.user_id)
    try:
        if payload.category == HostelIntegrationCategory.STUDENT:
            await _student_sync(tenant_id, job)
        elif payload.category == HostelIntegrationCategory.FINANCE:
            await _finance_sync(tenant_id, job)
        else:
            job.records_processed = 0
            job.records_success = 0
            job.status = HostelSyncJobStatus.COMPLETED
        if job.status != HostelSyncJobStatus.FAILED:
            job.status = HostelSyncJobStatus.COMPLETED if job.records_failed == 0 else HostelSyncJobStatus.FAILED
    except Exception as exc:
        job.status = HostelSyncJobStatus.FAILED
        job.error_detail = str(exc)[:2000]
        await HostelIntegrationFailure(
            tenant_id=tenant_id,
            failure_id=f"hif_{uuid4().hex[:10]}",
            category=payload.category,
            job_id=job.job_id,
            reason=str(exc)[:2000],
        ).insert()
    job.completed_at = utcnow()
    await job.save()
    binding.last_sync_at = utcnow()
    binding.status = (
        HostelIntegrationBindingStatus.ACTIVE
        if job.status == HostelSyncJobStatus.COMPLETED
        else HostelIntegrationBindingStatus.FAILED
    )
    await binding.save()
    return SyncJobRead(
        job_id=job.job_id,
        category=job.category,
        status=job.status,
        records_processed=job.records_processed,
        records_success=job.records_success,
        records_failed=job.records_failed,
        error_detail=job.error_detail,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


async def ingest_webhook(scope: AccessScope, category: HostelIntegrationCategory, payload: WebhookIngest) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_manage(scope)
    if await HostelIntegrationEvent.find_one(
        {"tenant_id": tenant_id, "external_event_id": payload.external_event_id}
    ):
        return {"status": "duplicate_ignored"}
    sub = await HostelWebhookSubscription.find_one(
        Eq(HostelWebhookSubscription.tenant_id, tenant_id), Eq(HostelWebhookSubscription.category, category)
    )
    signature_valid = None
    if sub and payload.signature:
        signature_valid = bool(payload.signature and sub.signing_secret_ref)
    raw = json.dumps(payload.payload, sort_keys=True, default=str)
    event_id = f"hev_{uuid4().hex[:10]}"
    await HostelIntegrationEvent(
        tenant_id=tenant_id,
        event_id=event_id,
        category=category,
        external_event_id=payload.external_event_id,
        payload_hash=hashlib.sha256(raw.encode()).hexdigest(),
        signature_valid=signature_valid,
        status="validated" if signature_valid is not False else "rejected",
        processing_note="Webhook stored; business workflow not auto-applied",
    ).insert()
    await record_hostel_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.integration.webhook",
        module="hostel_integration",
        resource_type="webhook_event",
        resource_id=event_id,
    )
    return {"event_id": event_id, "status": "received"}


async def retry_failure(scope: AccessScope, failure_id: str) -> IntegrationFailureRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_manage(scope)
    doc = await HostelIntegrationFailure.find_one(
        Eq(HostelIntegrationFailure.tenant_id, tenant_id), Eq(HostelIntegrationFailure.failure_id, failure_id)
    )
    if doc is None or doc.resolved:
        raise AppError(code="NOT_FOUND", message="Failure not found", status_code=404)
    if not doc.retriable:
        raise AppError(code="CONFLICT", message="Failure not retriable", status_code=409)
    doc.retry_count += 1
    if doc.job_id:
        await run_manual_sync(scope, ManualSyncRequest(category=doc.category))
    doc.resolved = True
    doc.resolved_at = utcnow()
    await doc.save()
    return IntegrationFailureRead(
        failure_id=doc.failure_id,
        category=doc.category,
        reason=doc.reason,
        retriable=doc.retriable,
        retry_count=doc.retry_count,
        resolved=doc.resolved,
    )


async def list_sync_jobs(scope: AccessScope, limit: int = 50) -> list[SyncJobRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_read(scope)
    cap = min(max(limit, 1), 200)
    rows = await HostelIntegrationSyncJob.find(Eq(HostelIntegrationSyncJob.tenant_id, tenant_id)).sort("-started_at").limit(cap).to_list()
    return [
        SyncJobRead(
            job_id=r.job_id,
            category=r.category,
            status=r.status,
            records_processed=r.records_processed,
            records_success=r.records_success,
            records_failed=r.records_failed,
            error_detail=r.error_detail,
            started_at=r.started_at,
            completed_at=r.completed_at,
        )
        for r in rows
    ]


async def list_failures(scope: AccessScope, *, open_only: bool = True, limit: int = 50) -> list[IntegrationFailureRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_read(scope)
    cap = min(max(limit, 1), 200)
    q: dict = {"tenant_id": tenant_id}
    if open_only:
        q["resolved"] = False
    rows = await HostelIntegrationFailure.find(q).sort("-created_at").limit(cap).to_list()
    return [
        IntegrationFailureRead(
            failure_id=r.failure_id,
            category=r.category,
            reason=r.reason,
            retriable=r.retriable,
            retry_count=r.retry_count,
            resolved=r.resolved,
        )
        for r in rows
    ]


async def list_integration_events(scope: AccessScope, limit: int = 50) -> list[IntegrationEventRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_read(scope)
    cap = min(max(limit, 1), 200)
    rows = await HostelIntegrationEvent.find(Eq(HostelIntegrationEvent.tenant_id, tenant_id)).sort("-created_at").limit(cap).to_list()
    return [
        IntegrationEventRead(
            event_id=r.event_id,
            category=r.category,
            external_event_id=r.external_event_id,
            status=r.status,
            signature_valid=r.signature_valid,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def list_reconciliation(scope: AccessScope, category: HostelIntegrationCategory | None = None) -> list[ReconciliationRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_read(scope)
    q: dict = {"tenant_id": tenant_id}
    if category:
        q["category"] = category.value
    rows = await HostelIntegrationReconciliation.find(q).sort("-last_checked_at").limit(200).to_list()
    return [
        ReconciliationRead(
            record_id=r.record_id,
            category=r.category,
            internal_ref=r.internal_ref,
            external_ref=r.external_ref,
            status=r.status,
            detail=r.detail,
        )
        for r in rows
    ]


async def connection_health(scope: AccessScope) -> list[dict]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_integration_read(scope)
    bindings = await HostelIntegrationBinding.find(Eq(HostelIntegrationBinding.tenant_id, tenant_id)).to_list()
    out = []
    for b in bindings:
        health_status = "unknown"
        if b.institution_integration_key:
            h = await InstitutionIntegrationHealth.find_one(
                Eq(InstitutionIntegrationHealth.tenant_id, tenant_id),
                Eq(InstitutionIntegrationHealth.integration_key, b.institution_integration_key),
            )
            if h:
                health_status = h.status
        out.append(
            {
                "category": b.category.value,
                "integration_key": b.integration_key,
                "enabled": b.enabled,
                "binding_status": b.status.value,
                "platform_health": health_status,
            }
        )
    return out