"""Platform operator account management."""

import secrets
from datetime import timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.platform_roles import PLATFORM_ROLE_PERMISSIONS
from app.authorization.policy import authorize
from app.authorization.resolver import effective_permissions_for_user
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import hash_password, hash_refresh_token, verify_password
from app.modules.audit.service import record_audit
from app.modules.auth.models import RefreshToken, User
from app.modules.auth.token_service import issue_refresh_token, revoke_all_for_user
from app.modules.platform_identity.enums import PlatformAccessReviewStatus, PlatformInvitationStatus, PlatformRoleCode
from app.modules.platform_identity.models import (
    PlatformAccessReview,
    PlatformInvitation,
    PlatformOperatorProfile,
    PlatformRoleAssignment,
    PlatformSession,
)
from app.modules.platform_identity.schemas import (
    PlatformAccessReviewComplete,
    PlatformAccessReviewCreate,
    PlatformAccessReviewRead,
    PlatformInvitationRead,
    PlatformPermissionsUpdate,
    PlatformRoleAssignRequest,
    PlatformSessionRead,
    PlatformSuspendRequest,
    PlatformUserCreate,
    PlatformUserInviteCreate,
    PlatformUserRead,
    PlatformUserUpdate,
)
from app.modules.platform_identity.security_helpers import assert_mfa_if_required, assert_reauth
from app.modules.platform_security.audit import record_platform_audit
from app.modules.platform_security.events import emit_security_event
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()


async def _get_profile(user_id: PydanticObjectId) -> PlatformOperatorProfile:
    profile = await PlatformOperatorProfile.find_one(Eq(PlatformOperatorProfile.user_id, user_id))
    if profile is None:
        raise AppError(code="NOT_FOUND", message="Platform operator profile not found", status_code=404)
    return profile


async def _ensure_not_escalation(
    actor: AccessScope,
    target_role: PlatformRoleCode,
) -> None:
    actor_perms = actor.effective_permissions
    if Permission.PLATFORM_USER_MANAGE not in actor_perms:
        raise AppError(code="FORBIDDEN", message="Cannot assign platform roles", status_code=403)
    if target_role == PlatformRoleCode.PLATFORM_OWNER and not actor.is_platform_owner:
        raise AppError(
            code="PRIVILEGE_ESCALATION",
            message="Only a platform owner may assign the owner role",
            status_code=403,
        )


async def create_platform_user(scope: AccessScope, payload: PlatformUserCreate) -> PlatformUserRead:
    authorize(scope, Permission.PLATFORM_USER_MANAGE)
    actor_user = await User.get(scope.user_id)
    if actor_user is None:
        raise AppError(code="UNAUTHORIZED", message="Actor not found", status_code=401)

    await _ensure_not_escalation(scope, payload.platform_role_code)
    email = str(payload.email).lower()
    existing = await _user_repo.find_by_email_in_tenant(email, None)
    if existing is not None:
        raise AppError(code="CONFLICT", message="A platform user with this email already exists", status_code=409)

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=Role.PLATFORM_ADMIN,
        tenant_id=None,
    )
    await user.insert()
    profile = PlatformOperatorProfile(
        user_id=user.id,
        platform_role_code=payload.platform_role_code,
        mfa_enabled=payload.mfa_enabled,
        mfa_enrolled_at=utcnow() if payload.mfa_enabled else None,
    )
    await profile.insert()
    await PlatformRoleAssignment(
        user_id=user.id,
        role_code=payload.platform_role_code,
        assigned_by=scope.user_id,
    ).insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_user.created",
        module="platform_identity",
        resource_type="platform_user",
        resource_id=str(user.id),
        after_state={"role": payload.platform_role_code.value, "email": email},
    )
    return PlatformUserRead.from_parts(user, profile)


async def invite_platform_user(
    scope: AccessScope,
    payload: PlatformUserInviteCreate,
) -> tuple[PlatformInvitationRead, str]:
    authorize(scope, Permission.PLATFORM_USER_MANAGE)
    await _ensure_not_escalation(scope, payload.platform_role_code)
    settings = get_settings()
    plain = secrets.token_urlsafe(48)
    invitation = PlatformInvitation(
        email=str(payload.email).lower(),
        full_name=payload.full_name,
        role_code=payload.platform_role_code,
        token_hash=hash_refresh_token(plain),
        expires_at=utcnow() + timedelta(hours=settings.invitation_expire_hours),
        created_by=scope.user_id,
    )
    await invitation.insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_user.invited",
        module="platform_identity",
        resource_type="platform_invitation",
        resource_id=str(invitation.id),
        metadata={"email": invitation.email},
    )
    return PlatformInvitationRead.from_document(invitation), plain


async def list_platform_users(scope: AccessScope, pagination: Pagination) -> Page[PlatformUserRead]:
    authorize(scope, Permission.PLATFORM_USER_READ)
    profiles = (
        await PlatformOperatorProfile.find_all()
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    total = await PlatformOperatorProfile.find_all().count()
    items: list[PlatformUserRead] = []
    for profile in profiles:
        user = await User.get(profile.user_id)
        if user is not None:
            items.append(PlatformUserRead.from_parts(user, profile))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_platform_user(scope: AccessScope, user_id: PydanticObjectId) -> PlatformUserRead:
    authorize(scope, Permission.PLATFORM_USER_READ)
    user = await User.get(user_id)
    if user is None or user.tenant_id is not None:
        raise AppError(code="NOT_FOUND", message="Platform user not found", status_code=404)
    profile = await _get_profile(user_id)
    return PlatformUserRead.from_parts(user, profile)


async def update_platform_user(
    scope: AccessScope,
    user_id: PydanticObjectId,
    payload: PlatformUserUpdate,
) -> PlatformUserRead:
    authorize(scope, Permission.PLATFORM_USER_MANAGE)
    user = await User.get(user_id)
    if user is None or user.tenant_id is not None:
        raise AppError(code="NOT_FOUND", message="Platform user not found", status_code=404)
    profile = await _get_profile(user_id)
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.mfa_enabled is not None:
        profile.mfa_enabled = payload.mfa_enabled
        profile.mfa_enrolled_at = utcnow() if payload.mfa_enabled else None
    user.updated_at = utcnow()
    profile.updated_at = utcnow()
    await user.save()
    await profile.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_user.updated",
        module="platform_identity",
        resource_type="platform_user",
        resource_id=str(user.id),
    )
    return PlatformUserRead.from_parts(user, profile)


async def assign_platform_role(
    scope: AccessScope,
    user_id: PydanticObjectId,
    payload: PlatformRoleAssignRequest,
) -> PlatformUserRead:
    authorize(scope, Permission.PLATFORM_USER_MANAGE)
    actor_user = await User.get(scope.user_id)
    if actor_user is None:
        raise AppError(code="UNAUTHORIZED", message="Actor not found", status_code=401)
    await assert_reauth(actor_user, payload.reauth_password)
    await _ensure_not_escalation(scope, payload.platform_role_code)

    user = await User.get(user_id)
    if user is None or user.tenant_id is not None:
        raise AppError(code="NOT_FOUND", message="Platform user not found", status_code=404)
    profile = await _get_profile(user_id)
    await assert_mfa_if_required(await _get_profile(scope.user_id))

    before = profile.platform_role_code.value
    profile.platform_role_code = payload.platform_role_code
    profile.updated_at = utcnow()
    await profile.save()
    await PlatformRoleAssignment(
        user_id=user_id,
        role_code=payload.platform_role_code,
        assigned_by=scope.user_id,
    ).insert()
    await emit_security_event(
        code="privileged_role_change",
        category="identity",
        title="Platform role assignment",
        description=f"Role changed from {before} to {payload.platform_role_code.value}",
        severity="high",
        actor_id=scope.user_id,
        metadata={"target_user_id": str(user_id)},
    )
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_user.role_assigned",
        module="platform_identity",
        resource_type="platform_user",
        resource_id=str(user.id),
        before_state={"role": before},
        after_state={"role": payload.platform_role_code.value},
    )
    return PlatformUserRead.from_parts(user, profile)


async def update_platform_permissions(
    scope: AccessScope,
    user_id: PydanticObjectId,
    payload: PlatformPermissionsUpdate,
) -> PlatformUserRead:
    authorize(scope, Permission.PLATFORM_USER_MANAGE)
    actor_user = await User.get(scope.user_id)
    if actor_user is None:
        raise AppError(code="UNAUTHORIZED", message="Actor not found", status_code=401)
    await assert_reauth(actor_user, payload.reauth_password)
    await assert_mfa_if_required(await _get_profile(scope.user_id))

    user = await User.get(user_id)
    if user is None or user.tenant_id is not None:
        raise AppError(code="NOT_FOUND", message="Platform user not found", status_code=404)
    profile = await _get_profile(user_id)
    for code in payload.grant:
        if code not in profile.granted_permissions:
            profile.granted_permissions.append(code)
    for code in payload.revoke:
        if code not in profile.denied_permissions:
            profile.denied_permissions.append(code)
    profile.updated_at = utcnow()
    await profile.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_user.permissions_updated",
        module="platform_identity",
        resource_type="platform_user",
        resource_id=str(user.id),
        metadata={"grant": payload.grant, "revoke": payload.revoke},
    )
    return PlatformUserRead.from_parts(user, profile)


async def suspend_platform_user(
    scope: AccessScope,
    user_id: PydanticObjectId,
    payload: PlatformSuspendRequest,
) -> PlatformUserRead:
    authorize(scope, Permission.PLATFORM_USER_MANAGE)
    actor_user = await User.get(scope.user_id)
    if actor_user is None:
        raise AppError(code="UNAUTHORIZED", message="Actor not found", status_code=401)
    await assert_reauth(actor_user, payload.reauth_password)

    user = await User.get(user_id)
    if user is None or user.tenant_id is not None:
        raise AppError(code="NOT_FOUND", message="Platform user not found", status_code=404)
    profile = await _get_profile(user_id)
    profile.suspended_at = utcnow()
    profile.suspension_reason = payload.reason
    user.is_active = False
    await user.save()
    await profile.save()
    await revoke_all_for_user(user_id)
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_user.suspended",
        module="platform_identity",
        resource_type="platform_user",
        resource_id=str(user.id),
        metadata={"reason": payload.reason},
    )
    return PlatformUserRead.from_parts(user, profile)


async def reactivate_platform_user(scope: AccessScope, user_id: PydanticObjectId) -> PlatformUserRead:
    authorize(scope, Permission.PLATFORM_USER_MANAGE)
    user = await User.get(user_id)
    if user is None or user.tenant_id is not None:
        raise AppError(code="NOT_FOUND", message="Platform user not found", status_code=404)
    profile = await _get_profile(user_id)
    profile.suspended_at = None
    profile.suspension_reason = None
    user.is_active = True
    await user.save()
    await profile.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_user.reactivated",
        module="platform_identity",
        resource_type="platform_user",
        resource_id=str(user.id),
    )
    return PlatformUserRead.from_parts(user, profile)


async def list_active_sessions(scope: AccessScope, user_id: PydanticObjectId) -> list[PlatformSessionRead]:
    authorize(scope, Permission.PLATFORM_USER_READ)
    rows = (
        await PlatformSession.find(
            Eq(PlatformSession.user_id, user_id),
            Eq(PlatformSession.revoked_at, None),
        )
        .sort("-last_seen_at")
        .to_list()
    )
    return [PlatformSessionRead.from_document(row) for row in rows]


async def revoke_user_sessions(scope: AccessScope, user_id: PydanticObjectId) -> int:
    authorize(scope, Permission.AUTH_SESSION_MANAGE)
    count = await revoke_all_for_user(user_id)
    now = utcnow()
    sessions = await PlatformSession.find(Eq(PlatformSession.user_id, user_id), Eq(PlatformSession.revoked_at, None)).to_list()
    for session in sessions:
        session.revoked_at = now
        await session.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_user.sessions_revoked",
        module="platform_identity",
        resource_type="platform_user",
        resource_id=str(user_id),
        metadata={"count": count},
    )
    return count


async def create_access_review(
    scope: AccessScope,
    payload: PlatformAccessReviewCreate,
) -> PlatformAccessReviewRead:
    authorize(scope, Permission.PLATFORM_ACCESS_REVIEW_MANAGE)
    review = PlatformAccessReview(
        title=payload.title,
        reviewer_id=scope.user_id,
        inactive_threshold_days=payload.inactive_threshold_days,
    )
    await review.insert()
    return PlatformAccessReviewRead.from_document(review)


async def complete_access_review(
    scope: AccessScope,
    review_id: PydanticObjectId,
    payload: PlatformAccessReviewComplete,
) -> PlatformAccessReviewRead:
    authorize(scope, Permission.PLATFORM_ACCESS_REVIEW_MANAGE)
    review = await PlatformAccessReview.get(review_id)
    if review is None:
        raise AppError(code="NOT_FOUND", message="Access review not found", status_code=404)
    review.decisions = [item.model_dump() for item in payload.decisions]
    review.status = PlatformAccessReviewStatus.COMPLETED
    review.completed_at = utcnow()
    await review.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform.access_review.completed",
        module="platform_identity",
        resource_type="platform_access_review",
        resource_id=str(review.id),
    )
    return PlatformAccessReviewRead.from_document(review)


async def list_inactive_operators(scope: AccessScope, inactive_days: int = 90) -> list[PlatformUserRead]:
    authorize(scope, Permission.PLATFORM_USER_READ)
    threshold = utcnow() - timedelta(days=inactive_days)
    profiles = await PlatformOperatorProfile.find_all().to_list()
    results: list[PlatformUserRead] = []
    for profile in profiles:
        if profile.last_login_at is None or profile.last_login_at < threshold:
            user = await User.get(profile.user_id)
            if user is not None:
                results.append(PlatformUserRead.from_parts(user, profile))
    return results
