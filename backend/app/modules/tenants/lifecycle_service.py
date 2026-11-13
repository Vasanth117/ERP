"""Tenant lifecycle state machine and operations."""

from datetime import datetime, timedelta
from uuid import uuid4

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.token_service import revoke_all_refresh_tokens_for_tenant
from app.modules.tenants.enums import (
    LifecycleOperationStatus,
    LifecycleOperationType,
    OffboardingApprovalStatus,
    OnboardingStage,
    ProvisioningJobStatus,
    TenantLifecycleStatus,
    assert_lifecycle_transition,
)
from app.modules.tenants.lifecycle_models import OffboardingDetails, TenantLifecycleOperation
from app.modules.tenants.lifecycle_sync import apply_lifecycle_to_tenant
from app.modules.tenants.models import Tenant
from app.modules.tenants.schemas_lifecycle import (
    LifecycleConfirmation,
    LifecycleOperationRead,
    LifecycleStatusRead,
    LifecycleTransitionRequest,
    OffboardingInitiateRequest,
    OffboardingStatusRead,
)
from app.repositories.lifecycle_repository import LifecycleRepository
from app.repositories.platform_repository import OnboardingRepository, ProvisioningRepository, StatusHistoryRepository
from app.repositories.tenant_repository import TenantRepository

_tenant_repo = TenantRepository()
_lifecycle_repo = LifecycleRepository()
_history_repo = StatusHistoryRepository()
_onboarding_repo = OnboardingRepository()
_provisioning_repo = ProvisioningRepository()

_HIGH_IMPACT = frozenset(
    {
        LifecycleOperationType.SUSPEND,
        LifecycleOperationType.OFFBOARDING_INITIATE,
        LifecycleOperationType.OFFBOARDING_START,
    }
)

_ACTIVATION_ELIGIBLE_ONBOARDING = frozenset(
    {
        OnboardingStage.COMPLETED,
        OnboardingStage.PROVISIONED,
        OnboardingStage.ADMIN_SETUP_PENDING,
        OnboardingStage.ADMIN_INVITATION_PENDING,
    }
)


def _validate_confirmation(tenant: Tenant, op_type: LifecycleOperationType, confirmation: LifecycleConfirmation) -> None:
    if not confirmation.acknowledged:
        raise AppError(
            code="CONFIRMATION_REQUIRED",
            message="Explicit confirmation is required",
            status_code=400,
        )
    if op_type in _HIGH_IMPACT:
        if not confirmation.confirmation_phrase:
            raise AppError(
                code="CONFIRMATION_PHRASE_REQUIRED",
                message="Confirmation phrase (tenant code) is required",
                status_code=400,
            )
        if confirmation.confirmation_phrase.strip().lower() != tenant.code:
            raise AppError(
                code="CONFIRMATION_MISMATCH",
                message="Confirmation phrase does not match tenant code",
                status_code=400,
            )


async def _assert_no_conflicting_operation(tenant_id: PydanticObjectId) -> None:
    active = await _lifecycle_repo.find_active_for_tenant(tenant_id)
    if active is not None:
        raise AppError(
            code="LIFECYCLE_CONFLICT",
            message="Another lifecycle operation is in progress for this college",
            status_code=409,
            details=[{"operation_id": str(active.id), "type": active.operation_type.value}],
        )


async def _record_lifecycle_transition(
    tenant: Tenant,
    target: TenantLifecycleStatus,
    *,
    actor_id: PydanticObjectId,
    reason: str | None,
    operation_id: str | None,
) -> None:
    previous_lifecycle = tenant.lifecycle_status.value
    previous_operational = tenant.status.value
    try:
        assert_lifecycle_transition(tenant.lifecycle_status, target)
    except ValueError as exc:
        raise AppError(code="INVALID_LIFECYCLE_TRANSITION", message=str(exc), status_code=409) from exc

    apply_lifecycle_to_tenant(tenant, target)
    if target == TenantLifecycleStatus.ACTIVE:
        tenant.activated_at = utcnow()
    if target == TenantLifecycleStatus.SUSPENDED:
        tenant.suspended_at = utcnow()
    tenant.updated_at = utcnow()
    await tenant.save()
    await _history_repo.append(
        tenant_id=tenant.id,
        from_status=previous_operational,
        to_status=tenant.status.value,
        from_lifecycle=previous_lifecycle,
        to_lifecycle=target.value,
        operation_id=operation_id,
        actor_id=actor_id,
        reason=reason,
    )


async def _assert_activation_eligible(tenant_id: PydanticObjectId) -> None:
    onboarding = await _onboarding_repo.get_by_tenant(tenant_id)
    if onboarding is None:
        raise AppError(
            code="ACTIVATION_BLOCKED",
            message="Onboarding record is required before activation",
            status_code=409,
        )
    if onboarding.stage not in _ACTIVATION_ELIGIBLE_ONBOARDING:
        raise AppError(
            code="ACTIVATION_BLOCKED",
            message="Tenant must be verified and provisioned before activation",
            status_code=409,
        )
    job = await _provisioning_repo.latest_job(tenant_id)
    if job is not None and job.status != ProvisioningJobStatus.SUCCEEDED:
        raise AppError(
            code="ACTIVATION_BLOCKED",
            message="Provisioning must succeed before activation",
            status_code=409,
        )


def _operation_to_read(op: TenantLifecycleOperation) -> LifecycleOperationRead:
    return LifecycleOperationRead.from_document(op)


async def get_lifecycle_status(scope: AccessScope, tenant_id: PydanticObjectId) -> LifecycleStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_READ)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    pending = await _lifecycle_repo.find_active_for_tenant(tenant_id)
    offboarding_op = None
    for op in await _lifecycle_repo.list_for_tenant(tenant_id, limit=10):
        if op.operation_type == LifecycleOperationType.OFFBOARDING_INITIATE:
            offboarding_op = op
            break
    return LifecycleStatusRead.from_tenant(tenant, pending_operation=pending, offboarding_operation=offboarding_op)


async def get_lifecycle_history(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
) -> list[LifecycleOperationRead]:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_READ)
    operations = await _lifecycle_repo.list_for_tenant(tenant_id)
    return [_operation_to_read(op) for op in operations]


async def list_pending_lifecycle_operations(scope: AccessScope) -> list[LifecycleOperationRead]:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_READ)
    ops = await _lifecycle_repo.list_pending()
    return [_operation_to_read(op) for op in ops]


async def activate_tenant(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: LifecycleTransitionRequest,
) -> LifecycleStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    idempotency_key = payload.idempotency_key or f"activate-{tenant_id}"
    existing = await _lifecycle_repo.get_by_idempotency(tenant_id, idempotency_key)
    if existing and existing.status == LifecycleOperationStatus.SUCCEEDED:
        return await get_lifecycle_status(scope, tenant_id)

    await _assert_no_conflicting_operation(tenant_id)
    await _assert_activation_eligible(tenant_id)

    operation = TenantLifecycleOperation(
        tenant_id=tenant_id,
        operation_type=LifecycleOperationType.ACTIVATE,
        status=LifecycleOperationStatus.RUNNING,
        reason=payload.reason,
        actor_id=scope.user_id,
        confirmation_phrase_ok=payload.confirmation.acknowledged,
        idempotency_key=idempotency_key,
        started_at=utcnow(),
    )
    await operation.insert()

    try:
        if payload.scheduled_for and payload.scheduled_for > utcnow():
            operation.status = LifecycleOperationStatus.SCHEDULED
            operation.scheduled_for = payload.scheduled_for
            await operation.save()
            return await get_lifecycle_status(scope, tenant_id)

        await _record_lifecycle_transition(
            tenant,
            TenantLifecycleStatus.ACTIVE,
            actor_id=scope.user_id,
            reason=payload.reason,
            operation_id=str(operation.id),
        )
        operation.status = LifecycleOperationStatus.SUCCEEDED
        operation.completed_at = utcnow()
        operation.progress_steps.append({"step": "activated", "at": utcnow()})
        await operation.save()
        await record_audit(
            actor_id=scope.user_id,
            action="tenant.lifecycle.activated",
            resource_type="tenant",
            resource_id=str(tenant.id),
            tenant_id=tenant.id,
            metadata={"reason": payload.reason},
        )
    except AppError as exc:
        operation.status = LifecycleOperationStatus.FAILED
        operation.last_error = exc.message
        await operation.save()
        raise

    return await get_lifecycle_status(scope, tenant_id)


async def suspend_tenant(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: LifecycleTransitionRequest,
) -> LifecycleStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    _validate_confirmation(tenant, LifecycleOperationType.SUSPEND, payload.confirmation)
    await _assert_no_conflicting_operation(tenant_id)

    idempotency_key = payload.idempotency_key or f"suspend-{tenant_id}-{uuid4().hex[:8]}"
    operation = TenantLifecycleOperation(
        tenant_id=tenant_id,
        operation_type=LifecycleOperationType.SUSPEND,
        status=LifecycleOperationStatus.RUNNING,
        reason=payload.reason,
        actor_id=scope.user_id,
        confirmation_phrase_ok=True,
        idempotency_key=idempotency_key,
        started_at=utcnow(),
    )
    await operation.insert()

    try:
        if payload.scheduled_for and payload.scheduled_for > utcnow():
            operation.status = LifecycleOperationStatus.SCHEDULED
            operation.scheduled_for = payload.scheduled_for
            await operation.save()
            return await get_lifecycle_status(scope, tenant_id)

        await _record_lifecycle_transition(
            tenant,
            TenantLifecycleStatus.SUSPENDED,
            actor_id=scope.user_id,
            reason=payload.reason,
            operation_id=str(operation.id),
        )
        revoked = await revoke_all_refresh_tokens_for_tenant(tenant_id)
        operation.progress_steps.append({"step": "sessions_revoked", "count": revoked, "at": utcnow()})
        operation.status = LifecycleOperationStatus.SUCCEEDED
        operation.completed_at = utcnow()
        await operation.save()
        await record_audit(
            actor_id=scope.user_id,
            action="tenant.lifecycle.suspended",
            resource_type="tenant",
            resource_id=str(tenant.id),
            tenant_id=tenant.id,
            metadata={"reason": payload.reason, "sessions_revoked": revoked},
        )
    except AppError as exc:
        operation.status = LifecycleOperationStatus.FAILED
        operation.last_error = exc.message
        await operation.save()
        raise

    return await get_lifecycle_status(scope, tenant_id)


async def reactivate_tenant(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: LifecycleTransitionRequest,
) -> LifecycleStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    if tenant.lifecycle_status != TenantLifecycleStatus.SUSPENDED:
        raise AppError(
            code="REACTIVATION_BLOCKED",
            message="Only suspended colleges can be reactivated",
            status_code=409,
        )

    await _assert_no_conflicting_operation(tenant_id)
    idempotency_key = payload.idempotency_key or f"reactivate-{tenant_id}"
    operation = TenantLifecycleOperation(
        tenant_id=tenant_id,
        operation_type=LifecycleOperationType.REACTIVATE,
        status=LifecycleOperationStatus.RUNNING,
        reason=payload.reason,
        actor_id=scope.user_id,
        confirmation_phrase_ok=payload.confirmation.acknowledged,
        idempotency_key=idempotency_key,
        started_at=utcnow(),
    )
    await operation.insert()

    try:
        await _record_lifecycle_transition(
            tenant,
            TenantLifecycleStatus.ACTIVE,
            actor_id=scope.user_id,
            reason=payload.reason,
            operation_id=str(operation.id),
        )
        operation.status = LifecycleOperationStatus.SUCCEEDED
        operation.completed_at = utcnow()
        await operation.save()
        await record_audit(
            actor_id=scope.user_id,
            action="tenant.lifecycle.reactivated",
            resource_type="tenant",
            resource_id=str(tenant.id),
            tenant_id=tenant.id,
            metadata={"reason": payload.reason},
        )
    except AppError as exc:
        operation.status = LifecycleOperationStatus.FAILED
        operation.last_error = exc.message
        await operation.save()
        raise

    return await get_lifecycle_status(scope, tenant_id)


async def initiate_offboarding(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: OffboardingInitiateRequest,
) -> OffboardingStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    _validate_confirmation(tenant, LifecycleOperationType.OFFBOARDING_INITIATE, payload.confirmation)
    await _assert_no_conflicting_operation(tenant_id)

    idempotency_key = payload.idempotency_key or f"offboard-{tenant_id}"
    details = OffboardingDetails(
        reason=payload.reason,
        effective_date=payload.effective_date,
        data_retention_policy=payload.data_retention_policy,
        export_required=payload.export_required,
        subscription_status=payload.subscription_status,
        billing_status=payload.billing_status,
        outstanding_dependencies=payload.outstanding_dependencies,
    )
    operation = TenantLifecycleOperation(
        tenant_id=tenant_id,
        operation_type=LifecycleOperationType.OFFBOARDING_INITIATE,
        status=LifecycleOperationStatus.SUCCEEDED,
        reason=payload.reason,
        actor_id=scope.user_id,
        confirmation_phrase_ok=True,
        approval_status=OffboardingApprovalStatus.PENDING,
        idempotency_key=idempotency_key,
        offboarding=details,
        completed_at=utcnow(),
    )
    await operation.insert()

    await _record_lifecycle_transition(
        tenant,
        TenantLifecycleStatus.OFFBOARDING_REQUESTED,
        actor_id=scope.user_id,
        reason=payload.reason,
        operation_id=str(operation.id),
    )
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.offboarding.initiated",
        resource_type="tenant",
        resource_id=str(tenant.id),
        tenant_id=tenant.id,
        metadata={"effective_date": payload.effective_date.isoformat()},
    )
    from app.modules.data_governance.offboarding_sync import ensure_offboarding_record_from_lifecycle

    await ensure_offboarding_record_from_lifecycle(
        tenant_id=tenant_id,
        created_by=scope.user_id,
        lifecycle_operation_id=operation.id,
        reason=payload.reason,
        export_required=payload.export_required,
    )
    return OffboardingStatusRead.from_operation(operation, tenant)


async def approve_offboarding(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: LifecycleTransitionRequest,
) -> OffboardingStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    if tenant.lifecycle_status != TenantLifecycleStatus.OFFBOARDING_REQUESTED:
        raise AppError(code="CONFLICT", message="Tenant is not awaiting offboarding approval", status_code=409)

    operation = None
    for op in await _lifecycle_repo.list_for_tenant(tenant_id, limit=20):
        if op.operation_type == LifecycleOperationType.OFFBOARDING_INITIATE and op.offboarding is not None:
            operation = op
            break
    if operation is None or operation.offboarding is None:
        raise AppError(code="NOT_FOUND", message="Offboarding request not found", status_code=404)
    if operation.offboarding.approval_status != OffboardingApprovalStatus.PENDING:
        raise AppError(code="CONFLICT", message="Offboarding already reviewed", status_code=409)

    from app.modules.subscriptions.enforcement import assert_no_active_subscription_blockers

    await assert_no_active_subscription_blockers(tenant_id)

    operation.offboarding.approval_status = OffboardingApprovalStatus.APPROVED
    operation.offboarding.approved_by = scope.user_id
    operation.offboarding.approved_at = utcnow()
    operation.approval_status = OffboardingApprovalStatus.APPROVED
    operation.updated_at = utcnow()
    await operation.save()

    await _record_lifecycle_transition(
        tenant,
        TenantLifecycleStatus.OFFBOARDING_APPROVED,
        actor_id=scope.user_id,
        reason=payload.reason,
        operation_id=str(operation.id),
    )
    from app.modules.data_governance.offboarding_sync import mark_offboarding_approved_in_record

    await mark_offboarding_approved_in_record(tenant_id, actor_id=scope.user_id)
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.offboarding.approved",
        resource_type="tenant",
        resource_id=str(tenant.id),
        tenant_id=tenant.id,
    )
    return OffboardingStatusRead.from_operation(operation, await _tenant_repo.get_tenant(tenant_id))


async def start_offboarding(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: LifecycleTransitionRequest,
) -> LifecycleStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    if tenant.lifecycle_status != TenantLifecycleStatus.OFFBOARDING_APPROVED:
        raise AppError(code="CONFLICT", message="Offboarding must be approved before starting", status_code=409)

    idempotency_key = payload.idempotency_key or f"offboard-start-{tenant_id}"
    operation = TenantLifecycleOperation(
        tenant_id=tenant_id,
        operation_type=LifecycleOperationType.OFFBOARDING_START,
        status=LifecycleOperationStatus.SUCCEEDED,
        reason=payload.reason,
        actor_id=scope.user_id,
        confirmation_phrase_ok=True,
        idempotency_key=idempotency_key,
        completed_at=utcnow(),
    )
    await operation.insert()
    await _record_lifecycle_transition(
        tenant,
        TenantLifecycleStatus.OFFBOARDING_IN_PROGRESS,
        actor_id=scope.user_id,
        reason=payload.reason,
        operation_id=str(operation.id),
    )
    from app.modules.data_governance.offboarding_sync import mark_offboarding_started_in_record

    await mark_offboarding_started_in_record(tenant_id, actor_id=scope.user_id)
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.offboarding.started",
        resource_type="tenant",
        resource_id=str(tenant.id),
        tenant_id=tenant.id,
    )
    return await get_lifecycle_status(scope, tenant_id)


async def get_offboarding_status(scope: AccessScope, tenant_id: PydanticObjectId) -> OffboardingStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_READ)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    for op in await _lifecycle_repo.list_for_tenant(tenant_id, limit=20):
        if op.operation_type == LifecycleOperationType.OFFBOARDING_INITIATE and op.offboarding is not None:
            return OffboardingStatusRead.from_operation(op, tenant)
    raise AppError(code="NOT_FOUND", message="No offboarding request found", status_code=404)


async def cancel_scheduled_lifecycle_operation(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    operation_id: str,
    *,
    reason: str,
) -> LifecycleOperationRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE)
    op = await TenantLifecycleOperation.get(PydanticObjectId(operation_id))
    if op is None or op.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Lifecycle operation not found", status_code=404)
    if op.status not in {LifecycleOperationStatus.SCHEDULED, LifecycleOperationStatus.PENDING}:
        raise AppError(
            code="CONFLICT",
            message="Only scheduled or pending operations can be cancelled",
            status_code=409,
        )
    op.status = LifecycleOperationStatus.CANCELLED
    op.last_error = reason
    op.completed_at = utcnow()
    await op.save()
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.lifecycle.operation_cancelled",
        resource_type="tenant_lifecycle_operation",
        resource_id=str(op.id),
        tenant_id=tenant_id,
        metadata={"reason": reason},
    )
    return _operation_to_read(op)


async def retry_failed_lifecycle_operation(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    operation_id: str,
) -> LifecycleStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE)
    op = await TenantLifecycleOperation.get(PydanticObjectId(operation_id))
    if op is None or op.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Lifecycle operation not found", status_code=404)
    if op.status != LifecycleOperationStatus.FAILED:
        raise AppError(code="CONFLICT", message="Only failed operations can be retried", status_code=409)
    if op.operation_type == LifecycleOperationType.SUSPEND:
        tenant = await _tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
        return await suspend_tenant(
            scope,
            tenant_id,
            LifecycleTransitionRequest(
                reason=op.reason or "retry",
                confirmation=LifecycleConfirmation(
                    acknowledged=True,
                    confirmation_phrase=tenant.code,
                ),
                idempotency_key=f"retry-{op.id}",
            ),
        )
    if op.operation_type == LifecycleOperationType.ACTIVATE:
        return await activate_tenant(
            scope,
            tenant_id,
            LifecycleTransitionRequest(
                reason=op.reason or "retry",
                confirmation=LifecycleConfirmation(acknowledged=True),
                idempotency_key=f"retry-{op.id}",
            ),
        )
    raise AppError(code="CONFLICT", message="Retry is not supported for this operation type", status_code=409)
