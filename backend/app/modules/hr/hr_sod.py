"""Separation of duties checks for HR sensitive operations."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.modules.college_admin.security_admin_models import InstitutionSecurityPolicy

_MUTUALLY_EXCLUSIVE: list[tuple[Permission, Permission]] = [
    (Permission.HR_PAYROLL_PREPARE, Permission.HR_PAYROLL_APPROVE),
    (Permission.HR_PAYROLL_APPROVE, Permission.HR_PAYROLL_PAY),
    (Permission.HR_BENEFITS_APPROVE, Permission.HR_BENEFITS_PAY),
]


def assert_separation_of_duties(scope: AccessScope, *, acting_permission: Permission, target_user_id=None) -> None:
    perms = scope.effective_permissions
    for a, b in _MUTUALLY_EXCLUSIVE:
        if acting_permission == a and b in perms:
            raise AppError(code="FORBIDDEN", message="Separation of duties: conflicting permissions", status_code=403)
        if acting_permission == b and a in perms:
            raise AppError(code="FORBIDDEN", message="Separation of duties: conflicting permissions", status_code=403)
    if target_user_id and scope.user_id == target_user_id:
        sensitive = {
            Permission.HR_PAYROLL_APPROVE,
            Permission.HR_BENEFITS_APPROVE,
            Permission.HR_LEAVE_MANAGE,
            Permission.HR_ATTENDANCE_MANAGE,
        }
        if acting_permission in sensitive:
            raise AppError(code="FORBIDDEN", message="Cannot approve own sensitive operation", status_code=403)


async def assert_block_self_approval(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId | None,
    resource_owner_id: PydanticObjectId | None,
) -> None:
    if actor_id is None or resource_owner_id is None or actor_id != resource_owner_id:
        return
    policy = await InstitutionSecurityPolicy.find_one(
        Eq(InstitutionSecurityPolicy.tenant_id, tenant_id),
        Eq(InstitutionSecurityPolicy.policy_id, "default"),
    )
    if policy is not None and not policy.block_self_approval:
        return
    raise AppError(code="FORBIDDEN", message="Self-approval is not permitted", status_code=403)