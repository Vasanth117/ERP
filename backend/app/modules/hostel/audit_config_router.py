"""Hostel audit history and configuration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.audit_config_schemas import (
    HostelAuditDashboard,
    HostelAuditLogRead,
    HostelAuditSearch,
    HostelConfigRead,
    HostelConfigTransition,
    HostelConfigUpsert,
    HostelPolicyApprovalInput,
    HostelPolicyDefinitionUpsert,
    HostelPolicyRead,
)
from app.modules.hostel.audit_config_service import (
    approve_policy,
    audit_dashboard,
    export_audit,
    get_config,
    list_configurations,
    list_policy_definitions,
    search_audit,
    transition_config,
    upsert_config,
    upsert_policy_definition,
)
from app.modules.hostel.deps import hostel_admin_user

router = APIRouter(prefix="/me", tags=["hostel-audit-config"])


@router.get("/audit/dashboard", response_model=ApiResponse[HostelAuditDashboard])
async def audit_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await audit_dashboard(scope), request_id=get_request_id())


@router.post("/audit/search", response_model=ApiResponse[Page[HostelAuditLogRead]])
async def audit_search_route(
    filters: HostelAuditSearch,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    return success_response(
        await search_audit(scope, Pagination(page=page, page_size=page_size), filters),
        request_id=get_request_id(),
    )


@router.post("/audit/export", response_model=ApiResponse[dict])
async def audit_export_route(
    filters: HostelAuditSearch,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await export_audit(scope, filters), request_id=get_request_id())


@router.get("/configuration", response_model=ApiResponse[list[HostelConfigRead]])
async def config_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    hostel_code: str | None = None,
):
    return success_response(await list_configurations(scope, hostel_code), request_id=get_request_id())


@router.put("/configuration", response_model=ApiResponse[HostelConfigRead])
async def config_upsert_route(
    payload: HostelConfigUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_config(scope, payload), request_id=get_request_id())


@router.post("/configuration/transition", response_model=ApiResponse[HostelConfigRead])
async def config_transition_route(
    payload: HostelConfigTransition,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await transition_config(scope, payload), request_id=get_request_id())


@router.get("/configuration/{policy_section}", response_model=ApiResponse[HostelConfigRead | None])
async def config_get_route(
    policy_section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    hostel_code: str | None = None,
):
    return success_response(await get_config(scope, policy_section, hostel_code), request_id=get_request_id())


@router.get("/policies/definitions", response_model=ApiResponse[list[HostelPolicyRead]])
async def policy_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await list_policy_definitions(scope), request_id=get_request_id())


@router.put("/policies/definitions", response_model=ApiResponse[HostelPolicyRead])
async def policy_upsert_route(
    payload: HostelPolicyDefinitionUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_policy_definition(scope, payload), request_id=get_request_id())


@router.post("/policies/approve", response_model=ApiResponse[HostelPolicyRead])
async def policy_approve_route(
    payload: HostelPolicyApprovalInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await approve_policy(scope, payload), request_id=get_request_id())