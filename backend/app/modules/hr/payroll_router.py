"""Payroll processing routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.payroll_schemas import (
    PaymentConfirm,
    PayrollAdjustmentCreate,
    PayrollPeriodCreate,
    PayrollPeriodRead,
    PayrollPreview,
    PayrollReports,
    PayrollRunCreate,
    PayrollRunRead,
    PayrollTransition,
)
from app.modules.hr.payroll_service import (
    calculate_payroll_run,
    confirm_employee_payment,
    create_payroll_adjustment,
    create_payroll_period,
    create_payroll_run,
    get_payroll_preview,
    list_payroll_periods,
    payroll_reports,
    submit_payroll_for_payment,
    transition_payroll_run,
)

router = APIRouter(prefix="/payroll", tags=["hr-payroll"])


@router.post("/periods", response_model=ApiResponse[PayrollPeriodRead])
async def create_period_route(payload: PayrollPeriodCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_payroll_period(scope, payload), request_id=get_request_id())


@router.get("/periods", response_model=ApiResponse[list[PayrollPeriodRead]])
async def list_periods_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_payroll_periods(scope), request_id=get_request_id())


@router.post("/runs", response_model=ApiResponse[PayrollRunRead])
async def create_run_route(payload: PayrollRunCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_payroll_run(scope, payload), request_id=get_request_id())


@router.post("/runs/{run_id}/calculate", response_model=ApiResponse[PayrollRunRead])
async def calculate_route(run_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await calculate_payroll_run(scope, run_id), request_id=get_request_id())


@router.get("/runs/{run_id}/preview", response_model=ApiResponse[PayrollPreview])
async def preview_route(run_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_payroll_preview(scope, run_id), request_id=get_request_id())


@router.post("/runs/{run_id}/transition", response_model=ApiResponse[PayrollRunRead])
async def transition_route(run_id: str, payload: PayrollTransition, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await transition_payroll_run(scope, run_id, payload), request_id=get_request_id())


@router.post("/runs/{run_id}/submit-payment", response_model=ApiResponse[dict])
async def submit_payment_route(run_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await submit_payroll_for_payment(scope, run_id), request_id=get_request_id())


@router.post("/runs/{run_id}/confirm-payment", response_model=ApiResponse[dict])
async def confirm_payment_route(run_id: str, payload: PaymentConfirm, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await confirm_employee_payment(scope, run_id, payload), request_id=get_request_id())


@router.post("/adjustments", response_model=ApiResponse[dict])
async def adjustment_route(payload: PayrollAdjustmentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_payroll_adjustment(scope, payload), request_id=get_request_id())


@router.get("/runs/{run_id}/reports", response_model=ApiResponse[PayrollReports])
async def reports_route(run_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await payroll_reports(scope, run_id), request_id=get_request_id())