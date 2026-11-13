"""Tenant onboarding stage transitions."""

from typing import Any

from beanie import PydanticObjectId

from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.tenants.enums import OnboardingStage, assert_onboarding_transition
from app.modules.tenants.platform_models import TenantOnboarding

CANCELLABLE_STAGES = frozenset(
    {
        OnboardingStage.DRAFT,
        OnboardingStage.SUBMITTED,
        OnboardingStage.VERIFICATION_PENDING,
        OnboardingStage.VERIFIED,
        OnboardingStage.PROVISIONING,
        OnboardingStage.FAILED,
        OnboardingStage.ADMIN_INVITATION_PENDING,
        OnboardingStage.ADMIN_SETUP_PENDING,
    }
)


async def create_onboarding_record(tenant_id: PydanticObjectId) -> TenantOnboarding:
    onboarding = TenantOnboarding(
        tenant_id=tenant_id,
        stage=OnboardingStage.DRAFT,
        stage_history=[
            {
                "stage": OnboardingStage.DRAFT.value,
                "at": utcnow(),
                "actor_id": None,
                "note": "created",
            }
        ],
    )
    await onboarding.insert()
    return onboarding


async def advance_onboarding_stage(
    onboarding: TenantOnboarding,
    target: OnboardingStage,
    *,
    actor_id: PydanticObjectId | None,
    note: str | None = None,
) -> TenantOnboarding:
    try:
        assert_onboarding_transition(onboarding.stage, target)
    except ValueError as exc:
        raise AppError(code="INVALID_TRANSITION", message=str(exc), status_code=409) from exc

    history_item: dict[str, Any] = {
        "stage": target.value,
        "at": utcnow(),
        "actor_id": str(actor_id) if actor_id else None,
        "note": note,
    }
    onboarding.stage_history.append(history_item)
    onboarding.stage = target
    onboarding.updated_at = utcnow()
    if target == OnboardingStage.COMPLETED:
        onboarding.completed_at = utcnow()
    if target == OnboardingStage.CANCELLED:
        onboarding.cancelled_at = utcnow()
    await onboarding.save()
    return onboarding


async def cancel_onboarding(
    onboarding: TenantOnboarding,
    *,
    actor_id: PydanticObjectId | None,
    reason: str,
) -> TenantOnboarding:
    if onboarding.stage not in CANCELLABLE_STAGES:
        raise AppError(
            code="CONFLICT",
            message="Onboarding cannot be cancelled in the current stage",
            status_code=409,
        )
    onboarding.cancel_reason = reason
    return await advance_onboarding_stage(
        onboarding,
        OnboardingStage.CANCELLED,
        actor_id=actor_id,
        note=reason,
    )
