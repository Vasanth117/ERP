"""Hostel leave and outpass routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus
from app.modules.hostel.leave_outpass_schemas import ApprovalDecision, GateMovementInput, LeaveOutpassOverview, LeaveOutpassRead, LeaveTypeUpsert
from app.modules.hostel.leave_outpass_service import (
    leave_outpass_overview,
    list_leave_requests,
    list_outpass_requests,
    record_gate_movement,
    review_request,
    upsert_leave_type,
)

router = APIRouter(prefix="/me", tags=["hostel-leave-outpass"])


@router.get("/leave-outpass/overview", response_model=ApiResponse[LeaveOutpassOverview])
async def overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await leave_outpass_overview(scope), request_id=get_request_id())


@router.put("/leave/types", response_model=ApiResponse[dict])
async def leave_type_route(
    payload: LeaveTypeUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_leave_type(scope, payload), request_id=get_request_id())


@router.get("/leave/requests", response_model=ApiResponse[Page[LeaveOutpassRead]])
async def list_leave_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[HostelLeaveOutpassStatus | None, Query()] = None,
):
    return success_response(await list_leave_requests(scope, pagination, status=status), request_id=get_request_id())


@router.get("/outpass/requests", response_model=ApiResponse[Page[LeaveOutpassRead]])
async def list_outpass_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[HostelLeaveOutpassStatus | None, Query()] = None,
):
    return success_response(await list_outpass_requests(scope, pagination, status=status), request_id=get_request_id())


@router.post("/leave-outpass/review", response_model=ApiResponse[LeaveOutpassRead])
async def review_route(
    payload: ApprovalDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await review_request(scope, payload), request_id=get_request_id())


@router.post("/leave-outpass/gate", response_model=ApiResponse[dict])
async def gate_route(
    payload: GateMovementInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await record_gate_movement(scope, payload), request_id=get_request_id())