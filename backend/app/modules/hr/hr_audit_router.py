"""HR audit and access management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, get_pagination
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.hr_audit_schemas import (
    AccessReviewCreate,
    AccessReviewRead,
    AccessScopeAssignmentRead,
    AccessScopeAssignmentUpsert,
    AuditExportRead,
    AuditExportRequest,
    HrAuditDashboard,
    HrAuditEntryRead,
    HrAuditSearch,
    RoleProfileRead,
    RoleProfileUpsert,
    TemporaryAccessCreate,
    TemporaryAccessRead,
)
from app.modules.hr.hr_audit_service import (
    approve_temporary_access,
    audit_dashboard,
    create_access_review,
    create_temporary_access,
    employee_audit_timeline,
    export_audit,
    expire_temporary_grants,
    get_access_scope_assignment,
    list_access_reviews,
    list_role_profiles,
    search_audit,
    upsert_access_scope,
    upsert_role_profile,
)

router = APIRouter(prefix="/audit", tags=["hr-audit"])


@router.get("/dashboard", response_model=ApiResponse[HrAuditDashboard])
async def dashboard_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await audit_dashboard(scope), request_id=get_request_id())


@router.post("/search", response_model=ApiResponse[Page[HrAuditEntryRead]])
async def search_route(
    filters: HrAuditSearch,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await search_audit(scope, pagination, filters), request_id=get_request_id())


@router.get("/employees/{employee_user_id}/timeline", response_model=ApiResponse[Page[HrAuditEntryRead]])
async def timeline_route(
    employee_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await employee_audit_timeline(scope, employee_user_id, pagination), request_id=get_request_id())


@router.post("/export", response_model=ApiResponse[AuditExportRead])
async def export_route(payload: AuditExportRequest, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await export_audit(scope, payload), request_id=get_request_id())


@router.get("/role-profiles", response_model=ApiResponse[list[RoleProfileRead]])
async def role_profiles_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_role_profiles(scope), request_id=get_request_id())


@router.put("/role-profiles", response_model=ApiResponse[RoleProfileRead])
async def role_profiles_upsert(payload: RoleProfileUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_role_profile(scope, payload), request_id=get_request_id())


@router.put("/access-scopes", response_model=ApiResponse[AccessScopeAssignmentRead])
async def access_scope_put(payload: AccessScopeAssignmentUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_access_scope(scope, payload), request_id=get_request_id())


@router.get("/access-scopes/{user_id}", response_model=ApiResponse[AccessScopeAssignmentRead | None])
async def access_scope_get(user_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_access_scope_assignment(scope, user_id), request_id=get_request_id())


@router.post("/temporary-access", response_model=ApiResponse[TemporaryAccessRead])
async def temp_access_create(payload: TemporaryAccessCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_temporary_access(scope, payload), request_id=get_request_id())


@router.post("/temporary-access/{grant_id}/approve", response_model=ApiResponse[TemporaryAccessRead])
async def temp_access_approve(grant_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await approve_temporary_access(scope, grant_id), request_id=get_request_id())


@router.post("/temporary-access/expire-due", response_model=ApiResponse[dict])
async def temp_access_expire(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    count = await expire_temporary_grants(scope)
    return success_response({"expired_count": count}, request_id=get_request_id())


@router.get("/access-reviews", response_model=ApiResponse[list[AccessReviewRead]])
async def access_reviews_list(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_access_reviews(scope), request_id=get_request_id())


@router.post("/access-reviews", response_model=ApiResponse[AccessReviewRead])
async def access_reviews_create(payload: AccessReviewCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_access_review(scope, payload), request_id=get_request_id())