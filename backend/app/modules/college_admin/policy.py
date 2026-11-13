"""College admin access policy."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.core.exceptions import AppError


def require_college_tenant_scope(scope: AccessScope) -> PydanticObjectId:
    if scope.tenant_id is None:
        raise AppError(
            code="FORBIDDEN",
            message="This action requires an active college context",
            status_code=403,
        )
    return scope.tenant_id


def assert_institution_tenant(scope: AccessScope, tenant_id: PydanticObjectId) -> None:
    if scope.tenant_id is None or str(scope.tenant_id) != str(tenant_id):
        raise AppError(
            code="FORBIDDEN",
            message="You cannot access another college",
            status_code=403,
        )
