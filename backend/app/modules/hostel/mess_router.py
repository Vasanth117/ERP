"""Hostel mess management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.mess_models import MessEnrollmentStatus
from app.modules.hostel.mess_schemas import (
    BillingCalculateInput,
    BillingPeriodCreate,
    BillingRecordRead,
    BillingSendFinanceInput,
    HostelMessCreate,
    HostelMessRead,
    MealAttendanceRecord,
    MealCategoryUpsert,
    MenuRead,
    MenuUpsert,
    MessEnrollmentCreate,
    MessEnrollmentDecision,
    MessEnrollmentRead,
    MessEnrollmentReport,
    MessPlanRead,
    MessPlanUpsertPortal,
    BillingAdjustmentCreate,
)
from app.modules.hostel.mess_service import (
    add_billing_adjustment,
    approve_billing_record,
    calculate_billing_period,
    create_billing_period,
    create_enrollment,
    decide_enrollment,
    list_enrollments,
    list_messes,
    list_plans,
    mess_enrollment_report,
    record_meal_attendance,
    send_billing_to_finance,
    sync_billing_payments,
    upsert_meal_category,
    upsert_menu,
    upsert_mess,
    upsert_plan,
)

router = APIRouter(prefix="/me", tags=["hostel-mess"])


@router.put("/mess/facilities", response_model=ApiResponse[HostelMessRead])
async def upsert_mess_route(
    payload: HostelMessCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_mess(scope, payload), request_id=get_request_id())


@router.get("/mess/facilities", response_model=ApiResponse[list[HostelMessRead]])
async def list_messes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await list_messes(scope), request_id=get_request_id())


@router.put("/mess/plans", response_model=ApiResponse[MessPlanRead])
async def upsert_plan_route(
    payload: MessPlanUpsertPortal,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_plan(scope, payload), request_id=get_request_id())


@router.get("/mess/plans", response_model=ApiResponse[list[MessPlanRead]])
async def list_plans_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    mess_code: Annotated[str | None, Query()] = None,
):
    return success_response(await list_plans(scope, mess_code=mess_code), request_id=get_request_id())


@router.put("/mess/meal-categories", response_model=ApiResponse[dict])
async def meal_category_route(
    payload: MealCategoryUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_meal_category(scope, payload), request_id=get_request_id())


@router.put("/mess/menus", response_model=ApiResponse[MenuRead])
async def menu_route(
    payload: MenuUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_menu(scope, payload), request_id=get_request_id())


@router.post("/mess/enrollments", response_model=ApiResponse[MessEnrollmentRead])
async def create_enrollment_route(
    payload: MessEnrollmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_enrollment(scope, payload), request_id=get_request_id())


@router.post("/mess/enrollments/decide", response_model=ApiResponse[MessEnrollmentRead])
async def decide_enrollment_route(
    payload: MessEnrollmentDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await decide_enrollment(scope, payload), request_id=get_request_id())


@router.get("/mess/enrollments", response_model=ApiResponse[Page[MessEnrollmentRead]])
async def list_enrollments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    mess_code: Annotated[str | None, Query()] = None,
    plan_code: Annotated[str | None, Query()] = None,
    status: Annotated[MessEnrollmentStatus | None, Query()] = None,
):
    return success_response(
        await list_enrollments(scope, pagination, mess_code=mess_code, plan_code=plan_code, status=status),
        request_id=get_request_id(),
    )


@router.post("/mess/attendance", response_model=ApiResponse[dict])
async def meal_attendance_route(
    payload: MealAttendanceRecord,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await record_meal_attendance(scope, payload), request_id=get_request_id())


@router.post("/mess/billing/periods", response_model=ApiResponse[dict])
async def billing_period_route(
    payload: BillingPeriodCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_billing_period(scope, payload), request_id=get_request_id())


@router.post("/mess/billing/calculate", response_model=ApiResponse[dict])
async def billing_calculate_route(
    payload: BillingCalculateInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await calculate_billing_period(scope, payload), request_id=get_request_id())


@router.post("/mess/billing/records/{record_id}/approve", response_model=ApiResponse[BillingRecordRead])
async def billing_approve_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await approve_billing_record(scope, record_id), request_id=get_request_id())


@router.post("/mess/billing/send-finance", response_model=ApiResponse[dict])
async def billing_finance_route(
    payload: BillingSendFinanceInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await send_billing_to_finance(scope, payload), request_id=get_request_id())


@router.post("/mess/billing/sync-payments/{period_id}", response_model=ApiResponse[dict])
async def billing_sync_route(
    period_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await sync_billing_payments(scope, period_id), request_id=get_request_id())


@router.post("/mess/billing/adjustments", response_model=ApiResponse[dict])
async def billing_adjustment_route(
    payload: BillingAdjustmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await add_billing_adjustment(scope, payload), request_id=get_request_id())


@router.get("/mess/reports/enrollment", response_model=ApiResponse[MessEnrollmentReport])
async def mess_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    mess_code: Annotated[str | None, Query()] = None,
):
    return success_response(await mess_enrollment_report(scope, mess_code=mess_code), request_id=get_request_id())