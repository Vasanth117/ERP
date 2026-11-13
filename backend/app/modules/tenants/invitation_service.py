"""Secure college admin invitations."""

import secrets
from datetime import timedelta, timezone

from beanie import PydanticObjectId

from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.core.security import hash_refresh_token
from app.modules.audit.service import record_audit
from app.modules.tenants.enums import InvitationStatus
from app.modules.tenants.platform_models import TenantAdminInvitation
from app.repositories.platform_repository import InvitationRepository

_invitation_repo = InvitationRepository()


async def _enforce_invitation_rate_limit(*, actor_id: PydanticObjectId, tenant_id: PydanticObjectId) -> None:
    settings = get_settings()
    try:
        redis = get_redis()
    except RuntimeError:
        if settings.app_env == "test":
            return
        raise
    key = f"rl:invite:{actor_id}:{tenant_id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > settings.invitation_rate_limit_per_minute:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many invitation operations for this tenant",
            status_code=429,
        )


def _new_invitation_token() -> str:
    return secrets.token_urlsafe(48)


async def create_admin_invitation(
    *,
    tenant_id: PydanticObjectId,
    email: str,
    full_name: str,
    actor_id: PydanticObjectId,
) -> tuple[TenantAdminInvitation, str]:
    settings = get_settings()
    await _enforce_invitation_rate_limit(actor_id=actor_id, tenant_id=tenant_id)

    existing = await _invitation_repo.get_active_for_tenant(tenant_id)
    if existing is not None:
        raise AppError(
            code="CONFLICT",
            message="A pending administrator invitation already exists for this college",
            status_code=409,
        )

    plain = _new_invitation_token()
    invitation = TenantAdminInvitation(
        tenant_id=tenant_id,
        email=email.strip().lower(),
        full_name=full_name.strip(),
        token_hash=hash_refresh_token(plain),
        expires_at=utcnow() + timedelta(hours=settings.invitation_expire_hours),
        created_by=actor_id,
    )
    await invitation.insert()
    await record_audit(
        actor_id=actor_id,
        action="tenant.admin_invitation.created",
        resource_type="tenant_admin_invitation",
        resource_id=str(invitation.id),
        tenant_id=tenant_id,
        metadata={"email": invitation.email},
    )
    return invitation, plain


async def resend_admin_invitation(
    *,
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId,
) -> tuple[TenantAdminInvitation, str]:
    settings = get_settings()
    await _enforce_invitation_rate_limit(actor_id=actor_id, tenant_id=tenant_id)

    invitation = await _invitation_repo.get_active_for_tenant(tenant_id)
    if invitation is None:
        raise AppError(
            code="NOT_FOUND",
            message="No pending administrator invitation for this college",
            status_code=404,
        )

    if invitation.status != InvitationStatus.PENDING:
        raise AppError(
            code="CONFLICT",
            message="This invitation cannot be resent",
            status_code=409,
        )
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= utcnow():
        invitation.status = InvitationStatus.EXPIRED
        await invitation.save()
        raise AppError(code="INVITATION_EXPIRED", message="Invitation has expired", status_code=410)

    plain = _new_invitation_token()
    invitation.token_hash = hash_refresh_token(plain)
    invitation.expires_at = utcnow() + timedelta(hours=settings.invitation_expire_hours)
    invitation.sent_count += 1
    invitation.last_sent_at = utcnow()
    await invitation.save()
    await record_audit(
        actor_id=actor_id,
        action="tenant.admin_invitation.resent",
        resource_type="tenant_admin_invitation",
        resource_id=str(invitation.id),
        tenant_id=tenant_id,
        metadata={"email": invitation.email, "sent_count": invitation.sent_count},
    )
    return invitation, plain


async def accept_invitation_token(token: str) -> TenantAdminInvitation:
    """Validate token for acceptance flows (reuse prevention)."""
    token_hash = hash_refresh_token(token)
    invitation = await _invitation_repo.find_by_hash(token_hash)
    if invitation is None:
        raise AppError(code="NOT_FOUND", message="Invalid invitation token", status_code=404)
    if invitation.status == InvitationStatus.ACCEPTED:
        raise AppError(code="CONFLICT", message="Invitation token was already used", status_code=409)
    if invitation.status != InvitationStatus.PENDING:
        raise AppError(code="CONFLICT", message="Invitation is not active", status_code=409)
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= utcnow():
        invitation.status = InvitationStatus.EXPIRED
        await invitation.save()
        raise AppError(code="INVITATION_EXPIRED", message="Invitation has expired", status_code=410)
    return invitation
