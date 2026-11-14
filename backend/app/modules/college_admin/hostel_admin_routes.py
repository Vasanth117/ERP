"""College admin hostel administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.hostel_admin_schemas import (
    AllocationApprove,
    CheckInOut,
    HostelApplicationReview,
    HostelBedCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelRoomCreate,
    HostelRuleUpsert,
    IncidentCreate,
    MaintenanceCreate,
    MessPlanUpsert,
    OutpassDecision,
    VisitorLogCreate,
)
from app.modules.college_admin.hostel_admin_service import (
    approve_allocation,
    check_in,
    check_out,
    create_bed,
    create_block,
    create_building,
    create_incident,
    create_maintenance,
    create_room,
    decide_outpass,
    list_waiting,
    log_visitor,
    occupancy_report,
    review_application,
    upsert_mess_plan,
    upsert_rule,
)

router = APIRouter()


@router.post("/buildings", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def building_route(payload: HostelBuildingCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_building(scope, payload), request_id=get_request_id())


@router.post("/blocks", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def block_route(payload: HostelBlockCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_block(scope, payload), request_id=get_request_id())


@router.post("/rooms", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def room_route(payload: HostelRoomCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_room(scope, payload), request_id=get_request_id())


@router.post("/beds", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def bed_route(payload: HostelBedCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_bed(scope, payload), request_id=get_request_id())


@router.post("/applications/review", response_model=ApiResponse[dict])
async def application_review_route(payload: HostelApplicationReview, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await review_application(scope, payload), request_id=get_request_id())


@router.get("/waiting-list", response_model=ApiResponse[Page[dict]])
async def waiting_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)], pagination: Annotated[Pagination, Depends(pagination_params)]):
    return success_response(await list_waiting(scope, pagination), request_id=get_request_id())


@router.post("/allocations/approve", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def allocate_route(payload: AllocationApprove, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await approve_allocation(scope, payload), request_id=get_request_id())


@router.post("/check-in", response_model=ApiResponse[dict])
async def check_in_route(payload: CheckInOut, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await check_in(scope, payload), request_id=get_request_id())


@router.post("/check-out", response_model=ApiResponse[dict])
async def check_out_route(payload: CheckInOut, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await check_out(scope, payload), request_id=get_request_id())


@router.post("/visitors", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def visitor_route(payload: VisitorLogCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await log_visitor(scope, payload), request_id=get_request_id())


@router.post("/outpass/decide", response_model=ApiResponse[dict])
async def outpass_route(payload: OutpassDecision, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await decide_outpass(scope, payload), request_id=get_request_id())


@router.post("/maintenance", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def maintenance_route(payload: MaintenanceCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_maintenance(scope, payload), request_id=get_request_id())


@router.post("/incidents", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def incident_route(payload: IncidentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_incident(scope, payload), request_id=get_request_id())


@router.put("/rules", response_model=ApiResponse[dict])
async def rule_route(payload: HostelRuleUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_rule(scope, payload), request_id=get_request_id())


@router.put("/mess-plans", response_model=ApiResponse[dict])
async def mess_route(payload: MessPlanUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_mess_plan(scope, payload), request_id=get_request_id())


@router.get("/reports/occupancy", response_model=ApiResponse[dict])
async def occupancy_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)], building_code: Annotated[str | None, Query()] = None):
    return success_response(await occupancy_report(scope, building_code=building_code), request_id=get_request_id())