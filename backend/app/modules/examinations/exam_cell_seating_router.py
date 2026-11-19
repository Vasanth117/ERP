"""Examination cell — seating and logistics routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_seating_schemas import (
    ExamInvigilatorAssignRequest,
    ExamInvigilatorAssignmentRead,
    ExamRoomAttendanceSheet,
    ExamRoomCreate,
    ExamRoomRead,
    ExamSeatingAllocateRequest,
    ExamSeatingAllocationRead,
    ExamSeatingChangeRequest,
    ExamSeatingPlanCreate,
    ExamSeatingPlanRead,
    ExamSeatingPlanSummary,
    ExamVenueCreate,
    ExamVenueRead,
)
from app.modules.examinations.exam_cell_seating_service import (
    allocate_seating,
    assign_invigilator,
    change_seat_allocation,
    create_exam_room,
    create_exam_venue,
    create_seating_plan,
    list_plan_allocations,
    publish_seating_plan,
    room_attendance_sheet,
    seating_plan_summary,
    submit_seating_plan,
)

router = APIRouter(tags=["examination-cell-seating"])


@router.post("/venues", response_model=ApiResponse[ExamVenueRead])
async def create_venue_route(
    payload: ExamVenueCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamVenueRead]:
    return success_response(await create_exam_venue(scope, user, payload), request_id=get_request_id())


@router.post("/rooms", response_model=ApiResponse[ExamRoomRead])
async def create_room_route(
    payload: ExamRoomCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamRoomRead]:
    return success_response(await create_exam_room(scope, user, payload), request_id=get_request_id())


@router.post("/seating-plans", response_model=ApiResponse[ExamSeatingPlanRead])
async def create_plan_route(
    payload: ExamSeatingPlanCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSeatingPlanRead]:
    return success_response(await create_seating_plan(scope, user, payload), request_id=get_request_id())


@router.post("/seating-plans/allocate", response_model=ApiResponse[list[ExamSeatingAllocationRead]])
async def allocate_route(
    payload: ExamSeatingAllocateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamSeatingAllocationRead]]:
    return success_response(await allocate_seating(scope, user, payload), request_id=get_request_id())


@router.post("/seating-allocations/{allocation_id}/change", response_model=ApiResponse[ExamSeatingAllocationRead])
async def change_allocation_route(
    allocation_id: str,
    payload: ExamSeatingChangeRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSeatingAllocationRead]:
    return success_response(await change_seat_allocation(scope, user, allocation_id, payload), request_id=get_request_id())


@router.post("/seating-plans/{plan_id}/submit", response_model=ApiResponse[ExamSeatingPlanRead])
async def submit_plan_route(
    plan_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSeatingPlanRead]:
    return success_response(await submit_seating_plan(scope, user, plan_id), request_id=get_request_id())


@router.post("/seating-plans/{plan_id}/publish", response_model=ApiResponse[ExamSeatingPlanRead])
async def publish_plan_route(
    plan_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSeatingPlanRead]:
    return success_response(await publish_seating_plan(scope, user, plan_id), request_id=get_request_id())


@router.get("/seating-plans/{plan_id}/allocations", response_model=ApiResponse[list[ExamSeatingAllocationRead]])
async def list_allocations_route(
    plan_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamSeatingAllocationRead]]:
    _ = user
    return success_response(await list_plan_allocations(scope, plan_id), request_id=get_request_id())


@router.get("/seating-plans/{plan_id}/summary", response_model=ApiResponse[ExamSeatingPlanSummary])
async def plan_summary_route(
    plan_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSeatingPlanSummary]:
    _ = user
    return success_response(await seating_plan_summary(scope, plan_id), request_id=get_request_id())


@router.get("/seating-plans/{plan_id}/rooms/{room_id}/attendance", response_model=ApiResponse[ExamRoomAttendanceSheet])
async def attendance_sheet_route(
    plan_id: str,
    room_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamRoomAttendanceSheet]:
    _ = user
    return success_response(await room_attendance_sheet(scope, plan_id, room_id), request_id=get_request_id())


@router.post("/invigilator-assignments", response_model=ApiResponse[ExamInvigilatorAssignmentRead])
async def assign_invigilator_route(
    payload: ExamInvigilatorAssignRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamInvigilatorAssignmentRead]:
    return success_response(await assign_invigilator(scope, user, payload), request_id=get_request_id())