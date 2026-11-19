"""Parent account security — sessions, contact change, relationship review."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.models import AuditLog
from app.modules.auth.models import RefreshToken, User
from app.modules.auth.token_service import revoke_all_for_user
from app.modules.parents.enums import ParentAccountStatus, ParentRelationshipReviewAction
from app.modules.parents.models import ParentAccountContactChangeRequest, ParentRelationshipAccessReviewRequest
from app.modules.parents.phase5_schemas import (
    ParentContactChangeRequestCreate,
    ParentRelationshipReviewCreate,
    ParentSecurityAccountRead,
    ParentSecuritySessionRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.profile_service import ensure_parent_profile, start_contact_verification
from app.modules.parents.repositories import ParentRelationshipRepository
from app.modules.parents.schemas import ParentContactVerificationStart

_relationship_repo = ParentRelationshipRepository()


async def get_security_account(scope: AccessScope, parent: User) -> ParentSecurityAccountRead:
    authorize(scope, Permission.PARENT_SECURITY_READ)
    tenant_id = require_parent_scope(scope)
    profile = await ensure_parent_profile(scope, parent)
    rels = await _relationship_repo.list_active_for_parent(tenant_id, parent.id)
    return ParentSecurityAccountRead(
        account_status=profile.account_status.value,
        email=parent.email,
        email_verified=profile.email_verified,
        contact_phone=profile.contact_phone,
        mobile_verified=profile.mobile_verified,
        linked_students=len(rels),
        mfa_hint=None,
    )


async def list_sessions(scope: AccessScope, parent: User) -> list[ParentSecuritySessionRead]:
    authorize(scope, Permission.PARENT_SECURITY_READ)
    require_parent_scope(scope)
    tokens = await RefreshToken.find(
        RefreshToken.user_id == parent.id,
        Eq(RefreshToken.revoked_at, None),
    ).sort("-created_at").limit(20).to_list()
    return [
        ParentSecuritySessionRead(
            family_id=str(t.family_id),
            issued_at=t.created_at,
            revoked=False,
        )
        for t in tokens
    ]


async def revoke_other_sessions(scope: AccessScope, parent: User) -> dict:
    authorize(scope, Permission.PARENT_SECURITY_MANAGE)
    require_parent_scope(scope)
    count = await revoke_all_for_user(parent.id)
    return {"revoked_sessions": count}


async def login_activity(scope: AccessScope, parent: User, limit: int = 20) -> list[dict]:
    authorize(scope, Permission.PARENT_SECURITY_READ)
    tenant_id = require_parent_scope(scope)
    rows = (
        await AuditLog.find(
            {
                "tenant_id": tenant_id,
                "actor_id": parent.id,
                "action": {"$in": ["auth.login.success", "auth.login.failure"]},
            }
        )
        .sort("-created_at")
        .limit(limit)
        .to_list()
    )
    return [
        {
            "action": r.action,
            "outcome": r.outcome,
            "created_at": r.created_at,
            "ip_address": getattr(r, "ip_address", None),
        }
        for r in rows
    ]


async def request_contact_change(
    scope: AccessScope, parent: User, payload: ParentContactChangeRequestCreate
) -> dict:
    authorize(scope, Permission.PARENT_SECURITY_MANAGE)
    tenant_id = require_parent_scope(scope)
    profile = await ensure_parent_profile(scope, parent)
    if profile.account_status == ParentAccountStatus.SUSPENDED:
        raise AppError(code="FORBIDDEN", message="Account suspended", status_code=403)
    doc = ParentAccountContactChangeRequest(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        channel=payload.channel,
        proposed_value=payload.proposed_value.strip(),
        status="pending",
    )
    await doc.insert()
    verification = await start_contact_verification(
        scope,
        parent,
        ParentContactVerificationStart(channel=payload.channel, target_value=payload.proposed_value),
    )
    doc.verification_id = PydanticObjectId(verification["verification_id"])
    doc.updated_at = utcnow()
    await doc.save()
    return {"request_id": str(doc.id), "verification_id": verification["verification_id"]}


async def submit_relationship_review(
    scope: AccessScope, parent: User, relationship_id: str, payload: ParentRelationshipReviewCreate
) -> dict:
    authorize(scope, Permission.PARENT_SECURITY_MANAGE)
    tenant_id = require_parent_scope(scope)
    rel_oid = PydanticObjectId(relationship_id)
    from app.modules.parents.models import ParentStudentRelationship

    rel = await ParentStudentRelationship.get(rel_oid)
    if rel is None or str(rel.tenant_id) != str(tenant_id) or str(rel.parent_user_id) != str(parent.id):
        raise AppError(code="NOT_FOUND", message="Relationship not found", status_code=404)
    if payload.action not in {a.value for a in ParentRelationshipReviewAction}:
        raise AppError(code="VALIDATION_ERROR", message="Invalid action", status_code=422)
    row = ParentRelationshipAccessReviewRequest(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        relationship_id=rel.id,
        student_user_id=rel.student_user_id,
        action=payload.action,
        reason=payload.reason.strip(),
    )
    await row.insert()
    return {"request_id": str(row.id), "status": row.status}