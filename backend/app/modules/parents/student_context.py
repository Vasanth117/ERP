"""Resolve and authorize a parent-selected linked student."""

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.parents.enums import ParentDataPermission
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access


async def resolve_student_for_parent(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    permission: ParentDataPermission | None = None,
) -> PydanticObjectId:
    tenant_id = require_parent_scope(scope)
    if str(parent.id) != str(scope.user_id):
        raise AppError(code="FORBIDDEN", message="Token user mismatch", status_code=403)
    sid = to_object_id(student_user_id, "student_user_id")
    await require_student_access(tenant_id, parent.id, sid, permission)
    return sid