"""Hostel allocation and availability routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelAllocationStatus, HostelBedStatus
from app.modules.hostel.allocation_schemas import (
    AllocationCancel,
    AllocationConfirm,
    AllocationCreate,
    AllocationExtend,
    AllocationRead,
    AllocationTransferCreate,
    BedAvailabilityItem,
    RoomAvailabilityItem,
)
from app.modules.hostel.allocation_service import (
    cancel_allocation,
    complete_transfer,
    confirm_allocation,
    create_allocation,
    create_transfer,
    extend_allocation,
    get_allocation,
    list_allocations,
)
from app.modules.hostel.availability_service import list_bed_availability, list_room_availability
from app.modules.hostel.deps import hostel_admin_user

router = APIRouter(prefix="/me", tags=["hostel-allocation"])


@router.get("/availability/beds", response_model=ApiResponse[Page[BedAvailabilityItem]])
async def bed_availability_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    hostel_code: Annotated[str | None, Query()] = None,
    building_code: Annotated[str | None, Query()] = None,
    block_code: Annotated[str | None, Query()] = None,
    floor_id: Annotated[str | None, Query()] = None,
    room_type: Annotated[str | None, Query()] = None,
    status: Annotated[HostelBedStatus | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
):
    data = await list_bed_availability(
        scope,
        pagination,
        hostel_code=hostel_code,
        building_code=building_code,
        block_code=block_code,
        floor_id=floor_id,
        room_type=room_type,
        status=status,
        academic_year_label=academic_year_label,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/availability/rooms", response_model=ApiResponse[Page[RoomAvailabilityItem]])
async def room_availability_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    hostel_code: Annotated[str | None, Query()] = None,
    building_code: Annotated[str | None, Query()] = None,
    block_code: Annotated[str | None, Query()] = None,
    floor_id: Annotated[str | None, Query()] = None,
    room_type: Annotated[str | None, Query()] = None,
):
    data = await list_room_availability(
        scope,
        pagination,
        hostel_code=hostel_code,
        building_code=building_code,
        block_code=block_code,
        floor_id=floor_id,
        room_type=room_type,
    )
    return success_response(data, request_id=get_request_id())


@router.post("/allocations", response_model=ApiResponse[AllocationRead], status_code=status.HTTP_201_CREATED)
async def create_allocation_route(
    payload: AllocationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_allocation(scope, payload), request_id=get_request_id())


@router.get("/allocations", response_model=ApiResponse[Page[AllocationRead]])
async def list_allocations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    hostel_code: Annotated[str | None, Query()] = None,
    status: Annotated[HostelAllocationStatus | None, Query()] = None,
):
    return success_response(await list_allocations(scope, pagination, hostel_code=hostel_code, status=status), request_id=get_request_id())


@router.get("/allocations/{allocation_id}", response_model=ApiResponse[AllocationRead])
async def get_allocation_route(
    allocation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await get_allocation(scope, allocation_id), request_id=get_request_id())


@router.post("/allocations/confirm", response_model=ApiResponse[AllocationRead])
async def confirm_allocation_route(
    payload: AllocationConfirm,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await confirm_allocation(scope, payload), request_id=get_request_id())


@router.post("/allocations/cancel", response_model=ApiResponse[AllocationRead])
async def cancel_allocation_route(
    payload: AllocationCancel,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await cancel_allocation(scope, payload), request_id=get_request_id())


@router.post("/allocations/extend", response_model=ApiResponse[AllocationRead])
async def extend_allocation_route(
    payload: AllocationExtend,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await extend_allocation(scope, payload), request_id=get_request_id())


@router.post("/transfers", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_transfer_route(
    payload: AllocationTransferCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_transfer(scope, payload), request_id=get_request_id())


@router.post("/transfers/{transfer_id}/complete", response_model=ApiResponse[AllocationRead])
async def complete_transfer_route(
    transfer_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await complete_transfer(scope, transfer_id), request_id=get_request_id())