"""HR attendance and work schedule routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.attendance_schedule_schemas import (
    AttendanceCorrectionCreate,
    AttendanceCorrectionReview,
    AttendanceEventIngest,
    AttendanceManualDay,
    AttendanceOverview,
    AttendanceRecordRead,
    MonthlyAttendanceAction,
    RosterAssign,
    RosterRead,
    ShiftRead,
    ShiftSwapCreate,
    ShiftUpsert,
    WorkScheduleRead,
    WorkScheduleUpsert,
)
from app.modules.hr.attendance_schedule_service import (
    approve_shift_swap,
    assign_roster,
    attendance_overview,
    close_monthly_attendance,
    ingest_attendance_event,
    list_attendance_records,
    list_roster,
    list_shifts,
    list_work_schedules,
    lock_monthly_attendance,
    manual_attendance_entry,
    reopen_monthly_attendance,
    request_shift_swap,
    review_attendance_correction,
    submit_attendance_correction,
    upsert_shift,
    upsert_work_schedule,
)
from app.modules.hr.deps import hr_staff_user

router = APIRouter(prefix="/attendance", tags=["hr-attendance"])


@router.get("/overview", response_model=ApiResponse[AttendanceOverview])
async def overview_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await attendance_overview(scope), request_id=get_request_id())


@router.put("/schedules", response_model=ApiResponse[WorkScheduleRead])
async def upsert_schedule_route(payload: WorkScheduleUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_work_schedule(scope, payload), request_id=get_request_id())


@router.get("/schedules", response_model=ApiResponse[list[WorkScheduleRead]])
async def list_schedules_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_work_schedules(scope), request_id=get_request_id())


@router.put("/shifts", response_model=ApiResponse[ShiftRead])
async def upsert_shift_route(payload: ShiftUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_shift(scope, payload), request_id=get_request_id())


@router.get("/shifts", response_model=ApiResponse[list[ShiftRead]])
async def list_shifts_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_shifts(scope), request_id=get_request_id())


@router.post("/roster", response_model=ApiResponse[RosterRead])
async def assign_roster_route(payload: RosterAssign, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await assign_roster(scope, payload), request_id=get_request_id())


@router.get("/roster", response_model=ApiResponse[list[RosterRead]])
async def list_roster_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
    employee_user_id: Annotated[str | None, Query()] = None,
):
    return success_response(await list_roster(scope, start_date, end_date, employee_user_id), request_id=get_request_id())


@router.post("/shift-swaps", response_model=ApiResponse[dict])
async def shift_swap_route(payload: ShiftSwapCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await request_shift_swap(scope, payload), request_id=get_request_id())


@router.post("/shift-swaps/{swap_request_id}/approve", response_model=ApiResponse[dict])
async def approve_swap_route(swap_request_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await approve_shift_swap(scope, swap_request_id), request_id=get_request_id())


@router.post("/events", response_model=ApiResponse[AttendanceRecordRead])
async def ingest_event_route(payload: AttendanceEventIngest, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await ingest_attendance_event(scope, payload), request_id=get_request_id())


@router.post("/manual", response_model=ApiResponse[AttendanceRecordRead])
async def manual_day_route(payload: AttendanceManualDay, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await manual_attendance_entry(scope, payload), request_id=get_request_id())


@router.get("/records", response_model=ApiResponse[Page[AttendanceRecordRead]])
async def list_records_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    employee_user_id: Annotated[str | None, Query()] = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
):
    return success_response(await list_attendance_records(scope, pagination, employee_user_id, start_date, end_date), request_id=get_request_id())


@router.post("/corrections", response_model=ApiResponse[dict])
async def correction_create_route(payload: AttendanceCorrectionCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await submit_attendance_correction(scope, payload), request_id=get_request_id())


@router.post("/corrections/{correction_id}/review", response_model=ApiResponse[dict])
async def correction_review_route(
    correction_id: str,
    payload: AttendanceCorrectionReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await review_attendance_correction(scope, correction_id, payload), request_id=get_request_id())


@router.post("/monthly/close", response_model=ApiResponse[dict])
async def monthly_close_route(payload: MonthlyAttendanceAction, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await close_monthly_attendance(scope, payload), request_id=get_request_id())


@router.post("/monthly/lock", response_model=ApiResponse[dict])
async def monthly_lock_route(payload: MonthlyAttendanceAction, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await lock_monthly_attendance(scope, payload), request_id=get_request_id())


@router.post("/monthly/reopen", response_model=ApiResponse[dict])
async def monthly_reopen_route(payload: MonthlyAttendanceAction, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await reopen_monthly_attendance(scope, payload), request_id=get_request_id())