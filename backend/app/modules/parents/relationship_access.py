"""Verified parent–student relationship and permission enforcement."""

from beanie import PydanticObjectId

from app.core.exceptions import AppError
from app.modules.parents.enums import ACTIVE_RELATIONSHIP_STATUSES, ParentDataPermission, ParentRelationshipStatus
from app.modules.parents.models import ParentRelationshipPermissions, ParentStudentRelationship
from app.modules.parents.repositories import ParentRelationshipRepository

_relationship_repo = ParentRelationshipRepository()


async def get_active_relationship(
    tenant_id: PydanticObjectId,
    parent_user_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
) -> ParentStudentRelationship | None:
    rel = await _relationship_repo.get_pair(tenant_id, parent_user_id, student_user_id)
    if rel is None:
        return None
    if rel.status not in ACTIVE_RELATIONSHIP_STATUSES:
        return None
    return rel


async def require_student_access(
    tenant_id: PydanticObjectId,
    parent_user_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    permission: ParentDataPermission | None = None,
) -> tuple[ParentStudentRelationship, ParentRelationshipPermissions | None]:
    """Validate an active verified relationship and optional data permission."""
    rel = await _relationship_repo.get_pair(tenant_id, parent_user_id, student_user_id)
    if rel is None or rel.status not in ACTIVE_RELATIONSHIP_STATUSES:
        raise AppError(
            code="FORBIDDEN",
            message="No active verified relationship with this student",
            status_code=403,
        )
    perms = await _relationship_repo.permissions_for_relationship(tenant_id, rel.id)
    if permission is not None:
        if perms is None or not perms.grants.get(permission.value, False):
            raise AppError(
                code="FORBIDDEN",
                message="You are not permitted to access this category of student information",
                status_code=403,
            )
    return rel, perms


async def record_relationship_status_change(
    tenant_id: PydanticObjectId,
    relationship: ParentStudentRelationship,
    *,
    to_status: ParentRelationshipStatus,
    changed_by: PydanticObjectId | None,
    reason: str | None = None,
) -> None:
    from app.modules.parents.models import ParentRelationshipStatusHistory

    await ParentRelationshipStatusHistory(
        tenant_id=tenant_id,
        relationship_id=relationship.id,
        from_status=relationship.status,
        to_status=to_status,
        reason=reason,
        changed_by=changed_by,
    ).insert()
    relationship.status = to_status
    from app.common.time import utcnow

    relationship.updated_at = utcnow()
    await relationship.save()