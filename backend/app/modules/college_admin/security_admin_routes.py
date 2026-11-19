"""Audit and security administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.security_admin_schemas import (
    AccessReviewCreate,
    AuditExportRead,
    AuditLogSearch,
    IntegrityCheckRead,
    InstitutionAuditLogRead,
    LoginActivityRead,
    SecurityEventRead,
    SecurityPolicyRead,
    SecurityPolicyUpdate,
    SecurityReportRead,
    SessionRevokeRequest,
)
from app.modules.college_admin.security_admin_service import (
    create_access_review,
    download_audit_export,
    export_audit_records,
    list_login_activity,
    list_security_events,
    read_security_policy,
    revoke_authorized_sessions,
    search_institution_audit_logs,
    security_report,
    update_security_policy,
    verify_audit_integrity,
)

router = APIRouter()


@router.get("/audit-logs", response_model=ApiResponse[Page[InstitutionAuditLogRead]])
async def audit_logs_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    actor_id: Annotated[str | None, Query()] = None,
    module: Annotated[str | None, Query()] = None,
    action_prefix: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[InstitutionAuditLogRead]]:
    filters = AuditLogSearch(actor_id=actor_id, module=module, action_prefix=action_prefix, resource_type=resource_type)
    data = await search_institution_audit_logs(scope, filters, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/security-events", response_model=ApiResponse[Page[SecurityEventRead]])
async def security_events_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[SecurityEventRead]]:
    return success_response(await list_security_events(scope, pagination), request_id=get_request_id())


@router.get("/login-activity", response_model=ApiResponse[Page[LoginActivityRead]])
async def login_activity_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    success_only: Annotated[bool | None, Query()] = None,
) -> ApiResponse[Page[LoginActivityRead]]:
    return success_response(await list_login_activity(scope, success_only=success_only, pagination=pagination), request_id=get_request_id())


@router.get("/policies", response_model=ApiResponse[SecurityPolicyRead])
async def security_policy_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SecurityPolicyRead]:
    return success_response(await read_security_policy(scope), request_id=get_request_id())


@router.patch("/policies", response_model=ApiResponse[SecurityPolicyRead])
async def security_policy_update_route(
    payload: SecurityPolicyUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SecurityPolicyRead]:
    return success_response(await update_security_policy(scope, user, payload), request_id=get_request_id())


@router.post("/sessions/revoke", response_model=ApiResponse[dict])
async def session_revoke_route(
    payload: SessionRevokeRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await revoke_authorized_sessions(scope, payload.user_id), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[SecurityReportRead])
async def security_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SecurityReportRead]:
    return success_response(await security_report(scope), request_id=get_request_id())


@router.get("/audit-integrity", response_model=ApiResponse[IntegrityCheckRead])
async def audit_integrity_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[IntegrityCheckRead]:
    return success_response(await verify_audit_integrity(scope), request_id=get_request_id())


@router.post("/audit-exports", response_model=ApiResponse[AuditExportRead])
async def audit_export_route(
    filters: AuditLogSearch,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AuditExportRead]:
    return success_response(await export_audit_records(scope, user, filters), request_id=get_request_id())


@router.get("/audit-exports/download", response_model=ApiResponse[dict])
async def audit_export_download_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    token: Annotated[str, Query(min_length=8)],
) -> ApiResponse[dict]:
    return success_response(await download_audit_export(scope, user, token), request_id=get_request_id())


@router.post("/access-reviews", response_model=ApiResponse[dict])
async def access_review_route(
    payload: AccessReviewCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_access_review(scope, user, payload), request_id=get_request_id())