"""Lifecycle API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.tenants.enums import (
    LifecycleOperationStatus,
    LifecycleOperationType,
    OffboardingApprovalStatus,
    TenantLifecycleStatus,
)
from app.modules.tenants.lifecycle_models import OffboardingDetails, TenantLifecycleOperation
from app.modules.tenants.models import Tenant


class LifecycleConfirmation(BaseModel):
    acknowledged: bool = Field(description="Must be true for high-impact lifecycle changes.")
    confirmation_phrase: str | None = Field(
        default=None,
        description="Must match tenant code for suspension and offboarding.",
    )


class LifecycleTransitionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=3, max_length=500)
    confirmation: LifecycleConfirmation = Field(default_factory=LifecycleConfirmation)
    scheduled_for: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)


class OffboardingInitiateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=3, max_length=500)
    effective_date: datetime
    data_retention_policy: str = Field(min_length=3, max_length=200)
    export_required: bool = False
    subscription_status: str = Field(default="active", max_length=64)
    billing_status: str = Field(default="current", max_length=64)
    outstanding_dependencies: list[str] = Field(default_factory=list, max_length=20)
    confirmation: LifecycleConfirmation
    idempotency_key: str | None = Field(default=None, max_length=128)


class LifecycleOperationRead(BaseModel):
    id: str
    tenant_id: str
    operation_type: LifecycleOperationType
    status: LifecycleOperationStatus
    scheduled_for: datetime | None
    reason: str | None
    approval_status: OffboardingApprovalStatus
    progress_steps: list[dict[str, Any]]
    last_error: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_document(cls, op: TenantLifecycleOperation) -> "LifecycleOperationRead":
        return cls(
            id=str(op.id),
            tenant_id=str(op.tenant_id),
            operation_type=op.operation_type,
            status=op.status,
            scheduled_for=op.scheduled_for,
            reason=op.reason,
            approval_status=op.approval_status,
            progress_steps=op.progress_steps,
            last_error=op.last_error,
            created_at=op.created_at,
            completed_at=op.completed_at,
        )


class LifecycleStatusRead(BaseModel):
    tenant_id: str
    lifecycle_status: TenantLifecycleStatus
    operational_status: str
    is_active: bool
    activated_at: datetime | None
    suspended_at: datetime | None
    pending_operation: LifecycleOperationRead | None = None
    offboarding_approval: OffboardingApprovalStatus | None = None

    @classmethod
    def from_tenant(
        cls,
        tenant: Tenant,
        *,
        pending_operation: TenantLifecycleOperation | None,
        offboarding_operation: TenantLifecycleOperation | None,
    ) -> "LifecycleStatusRead":
        offboarding_approval = None
        if offboarding_operation and offboarding_operation.offboarding is not None:
            offboarding_approval = offboarding_operation.offboarding.approval_status
        return cls(
            tenant_id=str(tenant.id),
            lifecycle_status=tenant.lifecycle_status,
            operational_status=tenant.status.value,
            is_active=tenant.is_active,
            activated_at=tenant.activated_at,
            suspended_at=tenant.suspended_at,
            pending_operation=(
                LifecycleOperationRead.from_document(pending_operation) if pending_operation else None
            ),
            offboarding_approval=offboarding_approval,
        )


class OffboardingStatusRead(BaseModel):
    tenant_id: str
    lifecycle_status: TenantLifecycleStatus
    operation_id: str
    details: OffboardingDetails
    approval_status: OffboardingApprovalStatus

    @classmethod
    def from_operation(cls, op: TenantLifecycleOperation, tenant: Tenant) -> "OffboardingStatusRead":
        assert op.offboarding is not None
        return cls(
            tenant_id=str(tenant.id),
            lifecycle_status=tenant.lifecycle_status,
            operation_id=str(op.id),
            details=op.offboarding,
            approval_status=op.offboarding.approval_status,
        )
