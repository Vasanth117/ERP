"""Hostel infrastructure management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.infrastructure_schemas import (
    HostelBedPortalCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelBuildingUpdate,
    HostelCapacitySummary,
    HostelFacilityCreate,
    HostelFacilityUpdate,
    HostelFloorCreate,
    HostelManagementHistoryRead,
    HostelRoomCreate,
    InstitutionHostelCreate,
    InstitutionHostelRead,
    InstitutionHostelUpdate,
)
from app.modules.hostel.infrastructure_service import (
    create_bed,
    create_block,
    create_building,
    create_facility,
    create_floor,
    create_hostel,
    create_room,
    deactivate_building,
    get_hostel,
    hostel_capacity_summary,
    list_hostels,
    list_management_history,
    update_facility,
    update_hostel,
    update_building,
)

router = APIRouter(prefix="/me/infrastructure", tags=["hostel-infrastructure"])


@router.post("/hostels", response_model=ApiResponse[InstitutionHostelRead], status_code=status.HTTP_201_CREATED)
async def create_hostel_route(
    payload: InstitutionHostelCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_hostel(scope, payload), request_id=get_request_id())


@router.get("/hostels", response_model=ApiResponse[Page[InstitutionHostelRead]])
async def list_hostels_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    active_only: Annotated[bool, Query()] = False,
):
    return success_response(await list_hostels(scope, pagination, active_only=active_only), request_id=get_request_id())


@router.get("/hostels/{hostel_code}", response_model=ApiResponse[InstitutionHostelRead])
async def get_hostel_route(
    hostel_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await get_hostel(scope, hostel_code), request_id=get_request_id())


@router.patch("/hostels/{hostel_code}", response_model=ApiResponse[InstitutionHostelRead])
async def update_hostel_route(
    hostel_code: str,
    payload: InstitutionHostelUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await update_hostel(scope, hostel_code, payload), request_id=get_request_id())


@router.get("/hostels/{hostel_code}/capacity", response_model=ApiResponse[HostelCapacitySummary])
async def hostel_capacity_route(
    hostel_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await hostel_capacity_summary(scope, hostel_code), request_id=get_request_id())


@router.get("/hostels/{hostel_code}/history", response_model=ApiResponse[Page[HostelManagementHistoryRead]])
async def hostel_history_route(
    hostel_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_management_history(scope, hostel_code, pagination), request_id=get_request_id())


@router.post("/buildings", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_building_route(
    payload: HostelBuildingCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_building(scope, payload), request_id=get_request_id())


@router.patch("/buildings/{building_code}", response_model=ApiResponse[dict])
async def update_building_route(
    building_code: str,
    payload: HostelBuildingUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await update_building(scope, building_code, payload), request_id=get_request_id())


@router.post("/buildings/{building_code}/deactivate", response_model=ApiResponse[dict])
async def deactivate_building_route(
    building_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await deactivate_building(scope, building_code), request_id=get_request_id())


@router.post("/blocks", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_block_route(
    payload: HostelBlockCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_block(scope, payload), request_id=get_request_id())


@router.post("/floors", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_floor_route(
    payload: HostelFloorCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_floor(scope, payload), request_id=get_request_id())


@router.post("/rooms", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_room_route(
    payload: HostelRoomCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_room(scope, payload), request_id=get_request_id())


@router.post("/beds", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_bed_route(
    payload: HostelBedPortalCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_bed(scope, payload), request_id=get_request_id())


@router.post("/facilities", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_facility_route(
    payload: HostelFacilityCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_facility(scope, payload), request_id=get_request_id())


@router.patch("/facilities/{facility_id}", response_model=ApiResponse[dict])
async def update_facility_route(
    facility_id: str,
    payload: HostelFacilityUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await update_facility(scope, facility_id, payload), request_id=get_request_id())