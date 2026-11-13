"""Audit history routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import AccessScope, get_access_scope, pagination_params, require_roles
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.modules.audit.schemas import AuditLogRead
from app.modules.audit.service import list_audit_logs
from app.modules.auth.models import User

router = APIRouter()


@router.get("", response_model=ApiResponse[Page[AuditLogRead]])
async def list_audit_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.COLLEGE_ADMIN))],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AuditLogRead]]:
    data = await list_audit_logs(scope, pagination)
    return success_response(data, request_id=get_request_id())
