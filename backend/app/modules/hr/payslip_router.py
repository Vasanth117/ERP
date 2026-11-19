"""Payslip routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.payroll_schemas import PayslipGenerateRequest, PayslipRead, PayslipRevise
from app.modules.hr.payslip_service import generate_payslips, list_payslips, publish_payslip, revise_payslip

router = APIRouter(prefix="/payslips", tags=["hr-payslips"])


@router.post("/generate", response_model=ApiResponse[dict])
async def generate_route(payload: PayslipGenerateRequest, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await generate_payslips(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[list[PayslipRead]])
async def list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    period_label: Annotated[str | None, Query()] = None,
    employee_user_id: Annotated[str | None, Query()] = None,
):
    return success_response(await list_payslips(scope, period_label, employee_user_id), request_id=get_request_id())


@router.post("/{payslip_id}/publish", response_model=ApiResponse[PayslipRead])
async def publish_route(payslip_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await publish_payslip(scope, payslip_id), request_id=get_request_id())


@router.post("/{payslip_id}/revise", response_model=ApiResponse[PayslipRead])
async def revise_route(payslip_id: str, payload: PayslipRevise, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await revise_payslip(scope, payslip_id, payload), request_id=get_request_id())