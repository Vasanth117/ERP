"""Hostel resident management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.resident_models import HostelResidentStatus
from app.modules.hostel.resident_schemas import ResidentCheckinInput, ResidentCheckoutInput, ResidentNoShowInput, ResidentOperationalView
from app.modules.hostel.resident_service import (
    check_in_resident,
    check_out_resident,
    get_resident,
    list_awaiting_checkin,
    list_residents,
    mark_no_show,
)

router = APIRouter(prefix="/me", tags=["hostel-residents"])


@router.get("/residents", response_model=ApiResponse[Page[ResidentOperationalView]])
async def list_residents_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    hostel_code: Annotated[str | None, Query()] = None,
    status: Annotated[HostelResidentStatus | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
):
    return success_response(await list_residents(scope, pagination, hostel_code=hostel_code, status=status, search=search), request_id=get_request_id())


@router.get("/residents/awaiting-checkin", response_model=ApiResponse[Page[ResidentOperationalView]])
async def awaiting_checkin_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_awaiting_checkin(scope, pagination), request_id=get_request_id())


@router.get("/residents/{resident_id}", response_model=ApiResponse[ResidentOperationalView])
async def get_resident_route(
    resident_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await get_resident(scope, resident_id), request_id=get_request_id())


@router.post("/residents/check-in", response_model=ApiResponse[ResidentOperationalView])
async def check_in_route(
    payload: ResidentCheckinInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await check_in_resident(scope, payload), request_id=get_request_id())


@router.post("/residents/check-out", response_model=ApiResponse[ResidentOperationalView])
async def check_out_route(
    payload: ResidentCheckoutInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await check_out_resident(scope, payload), request_id=get_request_id())


@router.post("/residents/no-show", response_model=ApiResponse[dict])
async def no_show_route(
    payload: ResidentNoShowInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await mark_no_show(scope, payload), request_id=get_request_id())