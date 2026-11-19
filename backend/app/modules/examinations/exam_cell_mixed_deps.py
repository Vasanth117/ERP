"""Examination cell routes that also admit enrolled students."""

from typing import Annotated

from fastapi import Depends

from app.api.deps import get_access_scope, get_current_user
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_policy import require_examination_cell_tenant
from app.modules.students.policy import require_student_scope


async def examination_cell_or_student_user(
    user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> User:
    if Permission.EXAMINATION_CELL_SESSION_READ in scope.effective_permissions or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions:
        require_examination_cell_tenant(scope)
    elif Permission.STUDENT_EXAM_REGISTRATION_READ in scope.effective_permissions:
        require_student_scope(scope)
    elif Permission.STUDENT_EXAM_RESULTS_READ in scope.effective_permissions:
        require_student_scope(scope)
    else:
        authorize(scope, Permission.EXAMINATION_CELL_SESSION_READ)
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    if not user.is_active:
        raise AppError(code="FORBIDDEN", message="Account is inactive", status_code=403)
    return user