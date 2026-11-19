"""Institutional review of parent–student link requests and relationships."""

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.parents.enums import (
    DEFAULT_RELATIONSHIP_PERMISSIONS,
    ParentLinkRequestStatus,
    ParentRelationshipStatus,
    ParentVerificationMethod,
)
from app.modules.parents.models import (
    ParentRelationshipPermissions,
    ParentRelationshipStatusHistory,
    ParentRelationshipVerificationHistory,
    ParentStudentLinkRequest,
    ParentStudentRelationship,
)
from app.modules.parents.relationship_access import record_relationship_status_change
from app.modules.parents.repositories import ParentLinkRequestRepository
from app.modules.parents.schemas import ParentLinkReviewDecision, ParentLinkRequestRead, ParentRelationshipAdminUpdate

_link_repo = ParentLinkRequestRepository()


async def list_pending_link_requests(scope: AccessScope) -> list[ParentLinkRequestRead]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    rows = await _link_repo.list_pending_for_tenant(scope.tenant_id)
    return [ParentLinkRequestRead.from_doc(r) for r in rows]


async def review_link_request(
    scope: AccessScope,
    request_id: PydanticObjectId,
    payload: ParentLinkReviewDecision,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    req = await ParentStudentLinkRequest.get(request_id)
    if req is None or str(req.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Link request not found", status_code=404)
    if req.status not in {
        ParentLinkRequestStatus.PENDING_VERIFICATION,
        ParentLinkRequestStatus.UNDER_REVIEW,
        ParentLinkRequestStatus.ADDITIONAL_INFO_REQUIRED,
    }:
        raise AppError(code="VALIDATION_ERROR", message="Request is not awaiting review", status_code=422)

    relationship = await ParentStudentRelationship.find_one(
        {"tenant_id": req.tenant_id, "parent_user_id": req.parent_user_id, "student_user_id": req.student_user_id}
    )
    if relationship is None:
        raise AppError(code="DISCONNECTED", message="Relationship record missing", status_code=422)

    decision = payload.decision
    if decision == "request_info":
        req.status = ParentLinkRequestStatus.ADDITIONAL_INFO_REQUIRED
        req.review_notes = payload.notes
        req.reviewed_by = reviewer_id
        req.updated_at = utcnow()
        await req.save()
        await record_relationship_status_change(
            req.tenant_id,
            relationship,
            to_status=ParentRelationshipStatus.ADDITIONAL_INFO_REQUIRED,
            changed_by=reviewer_id,
            reason=payload.notes,
        )
        return {"request_id": str(req.id), "status": req.status.value}

    if decision == "reject":
        req.status = ParentLinkRequestStatus.REJECTED
        req.review_notes = payload.notes
        req.reviewed_by = reviewer_id
        req.decided_at = utcnow()
        req.updated_at = utcnow()
        await req.save()
        await record_relationship_status_change(
            req.tenant_id,
            relationship,
            to_status=ParentRelationshipStatus.REJECTED,
            changed_by=reviewer_id,
            reason=payload.notes,
        )
        await ParentRelationshipVerificationHistory(
            tenant_id=req.tenant_id,
            relationship_id=relationship.id,
            link_request_id=req.id,
            parent_user_id=req.parent_user_id,
            student_user_id=req.student_user_id,
            method=payload.verification_method,
            decision="rejected",
            decided_by=reviewer_id,
            notes=payload.notes,
        ).insert()
        from app.modules.audit.service import record_audit

        await record_audit(
            actor_id=reviewer_id,
            action="parent.linking.reject",
            resource_type="parent_student_link_request",
            resource_id=str(req.id),
            tenant_id=req.tenant_id,
        )
        return {"request_id": str(req.id), "status": req.status.value}

    grants = payload.permission_grants or dict(DEFAULT_RELATIONSHIP_PERMISSIONS)
    req.status = ParentLinkRequestStatus.APPROVED
    req.verification_method = payload.verification_method
    req.review_notes = payload.notes
    req.reviewed_by = reviewer_id
    req.decided_at = utcnow()
    req.updated_at = utcnow()
    await req.save()

    relationship.verified_at = utcnow()
    relationship.verified_by = reviewer_id
    relationship.verification_method = payload.verification_method
    await record_relationship_status_change(
        req.tenant_id,
        relationship,
        to_status=ParentRelationshipStatus.ACTIVE,
        changed_by=reviewer_id,
        reason="Link request approved",
    )

    perms = await ParentRelationshipPermissions.find_one(
        {"tenant_id": req.tenant_id, "relationship_id": relationship.id}
    )
    if perms is None:
        perms = ParentRelationshipPermissions(
            tenant_id=req.tenant_id,
            relationship_id=relationship.id,
            parent_user_id=req.parent_user_id,
            student_user_id=req.student_user_id,
            grants=grants,
            updated_by=reviewer_id,
        )
        await perms.insert()
    else:
        perms.grants = grants
        perms.updated_by = reviewer_id
        perms.updated_at = utcnow()
        await perms.save()

    await ParentRelationshipVerificationHistory(
        tenant_id=req.tenant_id,
        relationship_id=relationship.id,
        link_request_id=req.id,
        parent_user_id=req.parent_user_id,
        student_user_id=req.student_user_id,
        method=payload.verification_method or ParentVerificationMethod.MANUAL_INSTITUTIONAL,
        decision="approved",
        decided_by=reviewer_id,
        notes=payload.notes,
    ).insert()
    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=reviewer_id,
        action="parent.linking.approve",
        resource_type="parent_student_link_request",
        resource_id=str(req.id),
        tenant_id=req.tenant_id,
    )
    return {
        "request_id": str(req.id),
        "status": req.status.value,
        "relationship_id": str(relationship.id),
    }


async def admin_update_relationship(
    scope: AccessScope,
    relationship_id: PydanticObjectId,
    payload: ParentRelationshipAdminUpdate,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    rel = await ParentStudentRelationship.get(relationship_id)
    if rel is None or str(rel.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Relationship not found", status_code=404)

    if payload.status is not None:
        await record_relationship_status_change(
            rel.tenant_id,
            rel,
            to_status=payload.status,
            changed_by=reviewer_id,
            reason=payload.reason,
        )
        if payload.status == ParentRelationshipStatus.REVOKED:
            rel.revoked_at = utcnow()
            await rel.save()
        if payload.status == ParentRelationshipStatus.SUSPENDED:
            rel.suspended_at = utcnow()
            await rel.save()

    if payload.permission_grants is not None:
        perms = await ParentRelationshipPermissions.find_one(
            {"tenant_id": rel.tenant_id, "relationship_id": rel.id}
        )
        if perms is None:
            perms = ParentRelationshipPermissions(
                tenant_id=rel.tenant_id,
                relationship_id=rel.id,
                parent_user_id=rel.parent_user_id,
                student_user_id=rel.student_user_id,
                grants=payload.permission_grants,
                updated_by=reviewer_id,
            )
            await perms.insert()
        else:
            perms.grants = payload.permission_grants
            perms.updated_by = reviewer_id
            perms.updated_at = utcnow()
            await perms.save()

    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=reviewer_id,
        action="parent.relationship.admin_update",
        resource_type="parent_student_relationship",
        resource_id=str(rel.id),
        tenant_id=rel.tenant_id,
        metadata=payload.model_dump(exclude_none=True),
    )
    return {"relationship_id": str(rel.id), "status": rel.status.value}