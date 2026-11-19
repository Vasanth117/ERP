"""Hostel visitor management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.visitor_models import HostelVisitorStatus
from app.modules.hostel.visitor_schemas import (
    VisitorApprovalInput,
    VisitorDenyInput,
    VisitorEntryInput,
    VisitorEntryRead,
    VisitorExitInput,
    VisitorRegisterInput,
    VisitorRestrictionUpsert,
)
from app.modules.hostel.visitor_service import (
    approve_visitor,
    deny_visitor_entry,
    list_visitors,
    record_visitor_entry,
    record_visitor_exit,
    register_visitor,
    upsert_visitor_restrictions,
    visitor_daily_report,
    visitors_inside,
)

router = APIRouter(prefix="/me", tags=["hostel-visitors"])


@router.post("/visitors", response_model=ApiResponse[VisitorEntryRead], status_code=status.HTTP_201_CREATED)
async def register_visitor_route(
    payload: VisitorRegisterInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await register_visitor(scope, payload), request_id=get_request_id())


@router.post("/visitors/approve", response_model=ApiResponse[VisitorEntryRead])
async def approve_visitor_route(
    payload: VisitorApprovalInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await approve_visitor(scope, payload), request_id=get_request_id())


@router.post("/visitors/entry", response_model=ApiResponse[VisitorEntryRead])
async def visitor_entry_route(
    payload: VisitorEntryInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await record_visitor_entry(scope, payload), request_id=get_request_id())


@router.post("/visitors/exit", response_model=ApiResponse[VisitorEntryRead])
async def visitor_exit_route(
    payload: VisitorExitInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await record_visitor_exit(scope, payload), request_id=get_request_id())


@router.post("/visitors/deny", response_model=ApiResponse[VisitorEntryRead])
async def deny_visitor_route(
    payload: VisitorDenyInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await deny_visitor_entry(scope, payload), request_id=get_request_id())


@router.get("/visitors", response_model=ApiResponse[Page[VisitorEntryRead]])
async def list_visitors_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[HostelVisitorStatus | None, Query()] = None,
    hostel_code: Annotated[str | None, Query()] = None,
    resident_user_id: Annotated[str | None, Query()] = None,
):
    return success_response(
        await list_visitors(scope, pagination, status=status, hostel_code=hostel_code, resident_user_id=resident_user_id),
        request_id=get_request_id(),
    )


@router.get("/visitors/inside", response_model=ApiResponse[Page[VisitorEntryRead]])
async def visitors_inside_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await visitors_inside(scope, pagination), request_id=get_request_id())


@router.get("/visitors/reports/daily", response_model=ApiResponse[dict])
async def visitor_daily_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await visitor_daily_report(scope), request_id=get_request_id())


@router.put("/visitors/restrictions", response_model=ApiResponse[dict])
async def visitor_restrictions_route(
    payload: VisitorRestrictionUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_visitor_restrictions(scope, payload), request_id=get_request_id())