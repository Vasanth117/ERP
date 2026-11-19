"""Parent–student linking and relationship lifecycle (parent-facing)."""

import hashlib
import secrets
from datetime import timedelta

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.parents.enums import (
    ParentLinkRequestStatus,
    ParentRelationshipStatus,
)
from app.modules.parents.models import (
    ParentLinkReferenceHint,
    ParentRelationshipPermissions,
    ParentRelationshipStatusHistory,
    ParentRelationshipVerificationHistory,
    ParentStudentLinkRequest,
    ParentStudentRelationship,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.repositories import ParentLinkRequestRepository, ParentRelationshipRepository
from app.modules.parents.schemas import (
    ParentLinkRequestCreate,
    ParentLinkRequestRead,
    StudentReferencePreview,
    StudentReferenceResolve,
)
from app.modules.students.models import StudentProfile

_link_repo = ParentLinkRequestRepository()
_relationship_repo = ParentRelationshipRepository()

_REFERENCE_FIELDS = {
    "roll_number": "roll_number",
    "student_id": "student_id",
    "admission_number": "admission_number",
}


def _mask_name(full_name: str) -> str:
    parts = full_name.split()
    if not parts:
        return "Student"
    if len(parts) == 1:
        return parts[0][:1] + "***"
    return f"{parts[0]} {parts[-1][:1]}***"


async def _resolve_student_user(
    tenant_id: PydanticObjectId, reference_type: str, reference_value: str
) -> tuple[PydanticObjectId, StudentProfile | None, User | None]:
    field = _REFERENCE_FIELDS.get(reference_type)
    if field is None:
        raise AppError(code="VALIDATION_ERROR", message="Invalid reference type", status_code=422)
    normalized = reference_value.strip()
    profile = await StudentProfile.find_one({"tenant_id": tenant_id, field: normalized})
    if profile is None:
        record = await StudentRecord.find_one({"tenant_id": tenant_id, field: normalized})
        if record is None:
            raise AppError(code="NOT_FOUND", message="No matching student reference in this college", status_code=404)
        profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": record.user_id})
        student_user_id = record.user_id
    else:
        student_user_id = profile.user_id
    student_user = await User.get(student_user_id)
    if student_user is None or str(student_user.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Student account not found", status_code=404)
    return student_user_id, profile, student_user


async def resolve_student_reference(
    scope: AccessScope, user: User, payload: StudentReferenceResolve
) -> StudentReferencePreview:
    authorize(scope, Permission.PARENT_LINKING_MANAGE)
    tenant_id = require_parent_scope(scope)
    student_user_id, profile, student_user = await _resolve_student_user(
        tenant_id, payload.reference_type, payload.reference_value
    )
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    await ParentLinkReferenceHint(
        tenant_id=tenant_id,
        parent_user_id=user.id,
        student_user_id=student_user_id,
        token_hash=token_hash,
        expires_at=utcnow() + timedelta(minutes=20),
    ).insert()
    roll_suffix = None
    if profile and profile.roll_number and len(profile.roll_number) >= 3:
        roll_suffix = profile.roll_number[-3:]
    programme_hint = None
    if profile and profile.programme_code:
        programme_hint = profile.programme_code[:3] + "***"
    return StudentReferencePreview(
        hint_token=token,
        masked_display_name=_mask_name(student_user.full_name),
        programme_hint=programme_hint,
        batch_hint=profile.batch_label if profile else None,
        roll_suffix=roll_suffix,
    )


async def _consume_hint(tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId, hint_token: str) -> PydanticObjectId:
    token_hash = hashlib.sha256(hint_token.encode()).hexdigest()
    hint = await ParentLinkReferenceHint.find_one({"token_hash": token_hash, "consumed": False})
    if hint is None or hint.expires_at < utcnow():
        raise AppError(code="VALIDATION_ERROR", message="Student reference session expired; resolve again", status_code=422)
    if str(hint.tenant_id) != str(tenant_id) or str(hint.parent_user_id) != str(parent_user_id):
        raise AppError(code="FORBIDDEN", message="Invalid reference token", status_code=403)
    hint.consumed = True
    await hint.save()
    return hint.student_user_id


async def submit_link_request(scope: AccessScope, user: User, payload: ParentLinkRequestCreate) -> ParentLinkRequestRead:
    authorize(scope, Permission.PARENT_LINKING_MANAGE)
    tenant_id = require_parent_scope(scope)
    student_user_id = await _consume_hint(tenant_id, user.id, payload.hint_token)

    existing_rel = await _relationship_repo.get_pair(tenant_id, user.id, student_user_id)
    if existing_rel is not None and existing_rel.status in {
        ParentRelationshipStatus.ACTIVE,
        ParentRelationshipStatus.VERIFIED,
        ParentRelationshipStatus.SUSPENDED,
    }:
        raise AppError(code="CONFLICT", message="A relationship already exists for this student", status_code=409)

    pending = await _link_repo.pending_for_pair(tenant_id, user.id, student_user_id)
    if pending is not None:
        raise AppError(code="CONFLICT", message="A pending link request already exists", status_code=409)

    req = ParentStudentLinkRequest(
        tenant_id=tenant_id,
        parent_user_id=user.id,
        student_user_id=student_user_id,
        relationship_type=payload.relationship_type,
        relationship_declaration=payload.relationship_declaration,
        reference_type="hint",
        reference_value="redacted",
        document_refs=payload.document_refs,
        status=ParentLinkRequestStatus.PENDING_VERIFICATION,
    )
    await req.insert()

    relationship = existing_rel
    if relationship is None:
        relationship = ParentStudentRelationship(
            tenant_id=tenant_id,
            parent_user_id=user.id,
            student_user_id=student_user_id,
            relationship_type=payload.relationship_type,
            status=ParentRelationshipStatus.PENDING_VERIFICATION,
            link_request_id=req.id,
        )
        await relationship.insert()
    else:
        relationship.status = ParentRelationshipStatus.PENDING_VERIFICATION
        relationship.link_request_id = req.id
        relationship.relationship_type = payload.relationship_type
        relationship.updated_at = utcnow()
        await relationship.save()

    await ParentRelationshipStatusHistory(
        tenant_id=tenant_id,
        relationship_id=relationship.id,
        from_status=existing_rel.status if existing_rel else None,
        to_status=ParentRelationshipStatus.PENDING_VERIFICATION,
        reason="Link request submitted",
        changed_by=user.id,
    ).insert()

    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=user.id,
        action="parent.linking.request",
        resource_type="parent_student_link_request",
        resource_id=str(req.id),
        tenant_id=tenant_id,
        metadata={"student_user_id": str(student_user_id)},
    )
    return ParentLinkRequestRead.from_doc(req)


async def list_link_requests(scope: AccessScope, user: User) -> list[ParentLinkRequestRead]:
    authorize(scope, Permission.PARENT_LINKING_MANAGE)
    tenant_id = require_parent_scope(scope)
    rows = await _link_repo.list_for_parent(tenant_id, user.id)
    return [ParentLinkRequestRead.from_doc(r) for r in rows]