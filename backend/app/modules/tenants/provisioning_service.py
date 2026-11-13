"""Idempotent tenant provisioning orchestration."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.tenants.domain_utils import normalize_domain
from app.modules.tenants.enums import (
    DomainVerificationStatus,
    OnboardingStage,
    ProvisioningJobStatus,
    ProvisioningStep,
    TenantOperationalStatus,
)
from app.modules.tenants.invitation_service import create_admin_invitation
from app.modules.tenants.lifecycle_sync import apply_lifecycle_to_tenant, default_lifecycle_for_operational
from app.modules.tenants.models import Tenant
from app.modules.tenants.onboarding_service import advance_onboarding_stage
from app.modules.tenants.platform_models import TenantDomain, TenantOnboarding, TenantProvisioningJob
from app.repositories.platform_repository import DomainRepository, ProvisioningRepository, StatusHistoryRepository

_domain_repo = DomainRepository()
_provisioning_repo = ProvisioningRepository()
_status_history_repo = StatusHistoryRepository()


async def _set_tenant_status(
    tenant: Tenant,
    status: TenantOperationalStatus,
    *,
    actor_id: PydanticObjectId | None,
    reason: str | None = None,
) -> None:
    previous = tenant.status.value
    previous_lifecycle = tenant.lifecycle_status.value
    lifecycle = default_lifecycle_for_operational(status)
    apply_lifecycle_to_tenant(tenant, lifecycle)
    if status == TenantOperationalStatus.ACTIVE:
        tenant.activated_at = utcnow()
    if status == TenantOperationalStatus.SUSPENDED:
        tenant.suspended_at = utcnow()
    tenant.updated_at = utcnow()
    await tenant.save()
    await _status_history_repo.append(
        tenant_id=tenant.id,
        from_status=previous,
        to_status=tenant.status.value,
        from_lifecycle=previous_lifecycle,
        to_lifecycle=tenant.lifecycle_status.value,
        actor_id=actor_id,
        reason=reason,
    )


async def _ensure_job(
    tenant_id: PydanticObjectId,
    idempotency_key: str | None,
) -> TenantProvisioningJob:
    key = idempotency_key or f"provision-{tenant_id}"
    existing = await _provisioning_repo.get_job(tenant_id, key)
    if existing is not None:
        return existing
    job = TenantProvisioningJob(tenant_id=tenant_id, idempotency_key=key)
    await job.insert()
    return job


async def run_provisioning(
    *,
    tenant: Tenant,
    onboarding: TenantOnboarding,
    actor_id: PydanticObjectId,
    domain: str,
    admin_email: str,
    admin_full_name: str,
    idempotency_key: str | None = None,
) -> tuple[TenantProvisioningJob, str | None]:
    settings = get_settings()
    job = await _ensure_job(tenant.id, idempotency_key)

    from app.modules.platform_ops.job_registry import ensure_job_registry

    key = idempotency_key or f"provision-{tenant.id}"
    await ensure_job_registry(
        job_type="tenant.provisioning",
        job_key=key,
        safe_to_retry=True,
        summary=f"Tenant provisioning ({tenant.code})",
        tenant_id=tenant.id,
        idempotency_key=key,
    )

    if job.status == ProvisioningJobStatus.SUCCEEDED:
        return job, None

    if job.status == ProvisioningJobStatus.FAILED:
        job.status = ProvisioningJobStatus.PENDING
        job.last_error = None
        await job.save()

    if job.attempt_count >= settings.tenant_provisioning_max_attempts:
        raise AppError(
            code="PROVISIONING_LIMIT",
            message="Provisioning retry limit reached",
            status_code=409,
        )

    job.status = ProvisioningJobStatus.RUNNING
    job.attempt_count += 1
    job.started_at = job.started_at or utcnow()
    job.updated_at = utcnow()
    await job.save()

    await _set_tenant_status(tenant, TenantOperationalStatus.PROVISIONING, actor_id=actor_id)
    await advance_onboarding_stage(
        onboarding,
        OnboardingStage.PROVISIONING,
        actor_id=actor_id,
        note="provisioning_started",
    )

    invitation_token: str | None = None
    try:
        if ProvisioningStep.REGISTRY not in job.steps_completed:
            job.steps_completed.append(ProvisioningStep.REGISTRY)
            await job.save()

        if ProvisioningStep.CONFIGURATION not in job.steps_completed:
            job.steps_completed.append(ProvisioningStep.CONFIGURATION)
            await job.save()

        if ProvisioningStep.DOMAIN not in job.steps_completed:
            normalized = normalize_domain(domain)
            existing_domain = await _domain_repo.find_by_normalized(normalized)
            if existing_domain is not None and existing_domain.tenant_id != tenant.id:
                raise AppError(
                    code="CONFLICT",
                    message="Domain is already assigned to another college",
                    status_code=409,
                )
            current = await _domain_repo.get_primary(tenant.id)
            if current is None:
                record = TenantDomain(
                    tenant_id=tenant.id,
                    domain=domain,
                    normalized_domain=normalized,
                    is_primary=True,
                    verification_status=DomainVerificationStatus.PENDING,
                )
                await record.insert()
            tenant.primary_domain = normalized
            tenant.updated_at = utcnow()
            await tenant.save()
            job.steps_completed.append(ProvisioningStep.DOMAIN)
            await job.save()

        if ProvisioningStep.ADMIN_INVITATION not in job.steps_completed:
            invitation, plain = await create_admin_invitation(
                tenant_id=tenant.id,
                email=admin_email,
                full_name=admin_full_name,
                actor_id=actor_id,
            )
            invitation_token = plain
            job.steps_completed.append(ProvisioningStep.ADMIN_INVITATION)
            await job.save()
            await advance_onboarding_stage(
                onboarding,
                OnboardingStage.ADMIN_INVITATION_PENDING,
                actor_id=actor_id,
                note=str(invitation.id),
            )

        if ProvisioningStep.FINALIZE not in job.steps_completed:
            job.steps_completed.append(ProvisioningStep.FINALIZE)
            job.status = ProvisioningJobStatus.SUCCEEDED
            job.finished_at = utcnow()
            job.updated_at = utcnow()
            await job.save()
            await advance_onboarding_stage(
                onboarding,
                OnboardingStage.PROVISIONED,
                actor_id=actor_id,
                note="provisioned",
            )
            await _set_tenant_status(
                tenant,
                TenantOperationalStatus.ONBOARDING,
                actor_id=actor_id,
                reason="awaiting_admin_setup",
            )
            await record_audit(
                actor_id=actor_id,
                action="tenant.provisioning.succeeded",
                resource_type="tenant",
                resource_id=str(tenant.id),
                tenant_id=tenant.id,
                metadata={"job_id": str(job.id), "idempotency_key": job.idempotency_key},
            )
    except AppError:
        job.status = ProvisioningJobStatus.FAILED
        job.last_error = "provisioning_failed"
        job.updated_at = utcnow()
        await job.save()
        await advance_onboarding_stage(
            onboarding,
            OnboardingStage.FAILED,
            actor_id=actor_id,
            note="provisioning_failed",
        )
        await _set_tenant_status(tenant, TenantOperationalStatus.FAILED, actor_id=actor_id)
        await record_audit(
            actor_id=actor_id,
            action="tenant.provisioning.failed",
            resource_type="tenant",
            resource_id=str(tenant.id),
            tenant_id=tenant.id,
            outcome="failure",
            metadata={"job_id": str(job.id)},
        )
        raise
    except Exception as exc:
        job.status = ProvisioningJobStatus.FAILED
        job.last_error = str(exc)[:500]
        job.updated_at = utcnow()
        await job.save()
        await advance_onboarding_stage(
            onboarding,
            OnboardingStage.FAILED,
            actor_id=actor_id,
            note="provisioning_failed",
        )
        await _set_tenant_status(tenant, TenantOperationalStatus.FAILED, actor_id=actor_id)
        raise AppError(
            code="PROVISIONING_FAILED",
            message="Tenant provisioning failed",
            status_code=500,
        ) from exc

    return job, invitation_token


async def retry_failed_provisioning(
    *,
    tenant: Tenant,
    onboarding: TenantOnboarding,
    actor_id: PydanticObjectId,
    domain: str,
    admin_email: str,
    admin_full_name: str,
) -> tuple[TenantProvisioningJob, str | None]:
    if onboarding.stage not in {OnboardingStage.FAILED, OnboardingStage.PROVISIONING}:
        raise AppError(
            code="CONFLICT",
            message="Provisioning can only be retried from a failed state",
            status_code=409,
        )
    idempotency_key = f"retry-{uuid4()}"
    return await run_provisioning(
        tenant=tenant,
        onboarding=onboarding,
        actor_id=actor_id,
        domain=domain,
        admin_email=admin_email,
        admin_full_name=admin_full_name,
        idempotency_key=idempotency_key,
    )
