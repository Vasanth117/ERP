"""Parent account management."""

import hashlib
import secrets
from datetime import timedelta

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.parents.enums import (
    ParentAccountStatus,
    ParentContactVerificationChannel,
    ParentContactVerificationStatus,
    ParentProfileChangeStatus,
)
from app.modules.parents.models import (
    ParentAccountStatusHistory,
    ParentContactVerification,
    ParentDeactivationRequest,
    ParentProfile,
    ParentProfileChangeRequest,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.repositories import ParentProfileRepository, ParentRelationshipRepository
from app.modules.parents.schemas import (
    ParentCommunicationPreferencesUpdate,
    ParentContactVerificationConfirm,
    ParentContactVerificationStart,
    ParentDeactivationRequestInput,
    ParentProfileCorrectionRequest,
    ParentProfileRead,
    ParentProfileUpdate,
)
from app.modules.parents.schemas import ParentRelationshipRead

_profile_repo = ParentProfileRepository()
_relationship_repo = ParentRelationshipRepository()

_UPDATABLE = frozenset(
    {"display_name", "contact_phone", "alternate_email", "address", "profile_photo_ref", "communication_preferences"}
)


async def ensure_parent_profile(scope: AccessScope, user: User) -> ParentProfile:
    tenant_id = require_parent_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(tenant_id):
        raise AppError(code="FORBIDDEN", message="User does not belong to this college", status_code=403)
    existing = await _profile_repo.get_by_user(tenant_id, user.id)
    if existing is not None:
        return existing
    profile = ParentProfile(
        tenant_id=tenant_id,
        user_id=user.id,
        display_name=user.full_name,
        account_status=ParentAccountStatus.ACTIVE,
        email_verified=True,
        activated_at=utcnow(),
    )
    await profile.insert()
    await ParentAccountStatusHistory(
        tenant_id=tenant_id,
        parent_user_id=user.id,
        from_status=None,
        to_status=ParentAccountStatus.ACTIVE,
        reason="First portal access",
    ).insert()
    return profile


async def get_parent_profile(scope: AccessScope, user: User) -> ParentProfileRead:
    authorize(scope, Permission.PARENT_PROFILE_READ)
    profile = await ensure_parent_profile(scope, user)
    return ParentProfileRead.from_parts(profile, email=user.email, full_name=user.full_name)


async def update_parent_profile(scope: AccessScope, user: User, payload: ParentProfileUpdate) -> ParentProfileRead:
    authorize(scope, Permission.PARENT_PROFILE_UPDATE)
    profile = await ensure_parent_profile(scope, user)
    if profile.account_status == ParentAccountStatus.SUSPENDED:
        raise AppError(code="FORBIDDEN", message="Account is suspended", status_code=403)
    changes: dict = {}
    for field in _UPDATABLE:
        value = getattr(payload, field)
        if value is None:
            continue
        if getattr(profile, field) != value:
            changes[field] = value
            setattr(profile, field, value)
    if changes:
        if "alternate_email" in changes:
            profile.email_verified = False
        if "contact_phone" in changes:
            profile.mobile_verified = False
        profile.updated_at = utcnow()
        await profile.save()
        from app.modules.audit.service import record_audit

        await record_audit(
            actor_id=user.id,
            action="parent.profile.update",
            resource_type="parent_profile",
            resource_id=str(profile.id),
            tenant_id=profile.tenant_id,
            metadata={"fields": list(changes.keys())},
        )
    return ParentProfileRead.from_parts(profile, email=user.email, full_name=user.full_name)


async def update_communication_preferences(
    scope: AccessScope, user: User, payload: ParentCommunicationPreferencesUpdate
) -> ParentProfileRead:
    authorize(scope, Permission.PARENT_PROFILE_UPDATE)
    profile = await ensure_parent_profile(scope, user)
    prefs = profile.communication_preferences
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(prefs, key, value)
    profile.communication_preferences = prefs
    profile.updated_at = utcnow()
    await profile.save()
    return ParentProfileRead.from_parts(profile, email=user.email, full_name=user.full_name)


async def start_contact_verification(scope: AccessScope, user: User, payload: ParentContactVerificationStart) -> dict:
    authorize(scope, Permission.PARENT_PROFILE_UPDATE)
    tenant_id = require_parent_scope(scope)
    channel = ParentContactVerificationChannel(payload.channel)
    token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    doc = ParentContactVerification(
        tenant_id=tenant_id,
        parent_user_id=user.id,
        channel=channel,
        target_value=payload.target_value.strip(),
        token_hash=token_hash,
        expires_at=utcnow() + timedelta(hours=24),
    )
    await doc.insert()
    return {"verification_id": str(doc.id), "delivery": "queued", "dev_token": token}


async def confirm_contact_verification(
    scope: AccessScope, user: User, payload: ParentContactVerificationConfirm
) -> ParentProfileRead:
    authorize(scope, Permission.PARENT_PROFILE_UPDATE)
    tenant_id = require_parent_scope(scope)
    doc = await ParentContactVerification.get(PydanticObjectId(payload.verification_id))
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.parent_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Verification not found", status_code=404)
    if doc.status != ParentContactVerificationStatus.PENDING or doc.expires_at < utcnow():
        raise AppError(code="VALIDATION_ERROR", message="Verification expired or invalid", status_code=422)
    expected = hashlib.sha256(payload.token.encode()).hexdigest()
    if expected != doc.token_hash:
        doc.status = ParentContactVerificationStatus.FAILED
        await doc.save()
        raise AppError(code="VALIDATION_ERROR", message="Invalid verification token", status_code=422)
    doc.status = ParentContactVerificationStatus.VERIFIED
    doc.verified_at = utcnow()
    await doc.save()
    profile = await ensure_parent_profile(scope, user)
    if doc.channel == ParentContactVerificationChannel.EMAIL:
        profile.alternate_email = doc.target_value
        profile.email_verified = True
    else:
        profile.contact_phone = doc.target_value
        profile.mobile_verified = True
    profile.updated_at = utcnow()
    await profile.save()
    return ParentProfileRead.from_parts(profile, email=user.email, full_name=user.full_name)


async def submit_profile_correction(scope: AccessScope, user: User, payload: ParentProfileCorrectionRequest) -> dict:
    authorize(scope, Permission.PARENT_PROFILE_UPDATE)
    tenant_id = require_parent_scope(scope)
    req = ParentProfileChangeRequest(
        tenant_id=tenant_id,
        parent_user_id=user.id,
        requested_fields=payload.fields,
        reason=payload.reason,
    )
    await req.insert()
    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=user.id,
        action="parent.profile.correction_request",
        resource_type="parent_profile_change_request",
        resource_id=str(req.id),
        tenant_id=tenant_id,
    )
    return {"request_id": str(req.id), "status": req.status.value}


async def request_deactivation(scope: AccessScope, user: User, payload: ParentDeactivationRequestInput) -> dict:
    authorize(scope, Permission.PARENT_PROFILE_UPDATE)
    tenant_id = require_parent_scope(scope)
    profile = await ensure_parent_profile(scope, user)
    doc = ParentDeactivationRequest(tenant_id=tenant_id, parent_user_id=user.id, reason=payload.reason)
    await doc.insert()
    await ParentAccountStatusHistory(
        tenant_id=tenant_id,
        parent_user_id=user.id,
        from_status=profile.account_status,
        to_status=ParentAccountStatus.DEACTIVATION_REQUESTED,
        reason=payload.reason,
    ).insert()
    profile.account_status = ParentAccountStatus.DEACTIVATION_REQUESTED
    profile.updated_at = utcnow()
    await profile.save()
    return {"request_id": str(doc.id), "status": "pending"}


async def list_linked_relationships(scope: AccessScope, user: User) -> list[ParentRelationshipRead]:
    authorize(scope, Permission.PARENT_RELATIONSHIP_READ)
    tenant_id = require_parent_scope(scope)
    rows = await _relationship_repo.list_for_parent(tenant_id, user.id)
    items: list[ParentRelationshipRead] = []
    for row in rows:
        perms_doc = await _relationship_repo.permissions_for_relationship(tenant_id, row.id)
        grants = perms_doc.grants if perms_doc else {}
        items.append(ParentRelationshipRead.from_parts(row, permissions=grants))
    return items


async def recent_security_activity(
    scope: AccessScope, user: User, pagination: Pagination
) -> Page[dict]:
    authorize(scope, Permission.PARENT_PROFILE_READ)
    tenant_id = require_parent_scope(scope)
    total = await AuditLog.find(
        {"tenant_id": tenant_id, "actor_id": user.id, "action": {"$regex": "^parent\\."}}
    ).count()
    rows = (
        await AuditLog.find({"tenant_id": tenant_id, "actor_id": user.id, "action": {"$regex": "^parent\\."}})
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [
        {
            "action": row.action,
            "resource_type": row.resource_type,
            "outcome": row.outcome,
            "created_at": row.created_at,
        }
        for row in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)