"""Phase 6 installment and payment plan routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.installment_service import (
    approve_assignment,
    approve_reschedule,
    assign_payment_plan,
    installment_reports,
    list_payment_plans,
    submit_reschedule,
    upsert_payment_plan,
)
from app.modules.auth.models import User


class PaymentPlanInput(BaseModel):
    plan_id: str | None = None
    plan_code: str
    plan_name: str
    description: str | None = None
    academic_year_label: str | None = None
    applicable_programmes: list[str] = Field(default_factory=list)
    installment_definitions: list[dict[str, Any]] = Field(default_factory=list)
    number_of_installments: int = 1
    requires_approval: bool = False
    plan_status: str = "active"


class AssignPlanInput(BaseModel):
    student_user_id: str
    plan_id: str
    invoice_id: str | None = None
    demand_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    special_arrangement: bool = False
    special_reason: str | None = None


class RescheduleInput(BaseModel):
    reason: str = Field(min_length=3)
    proposed_installments: list[dict[str, Any]]


router = APIRouter(prefix="/installments", tags=["accounts-finance-installments"])


@router.get("/plans", response_model=ApiResponse[Page[dict]])
async def plans_list(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_payment_plans(scope, pagination), request_id=get_request_id())


@router.post("/plans", response_model=ApiResponse[dict])
async def plans_upsert(
    payload: PaymentPlanInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_payment_plan(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/assignments", response_model=ApiResponse[dict])
async def assignments_create(
    payload: AssignPlanInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await assign_payment_plan(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/assignments/{assignment_id}/approve", response_model=ApiResponse[dict])
async def assignments_approve(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await approve_assignment(scope, assignment_id), request_id=get_request_id())


@router.post("/schedules/{schedule_id}/reschedule", response_model=ApiResponse[dict])
async def reschedule_submit(
    schedule_id: str,
    payload: RescheduleInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await submit_reschedule(scope, schedule_id, payload.reason, payload.proposed_installments),
        request_id=get_request_id(),
    )


@router.post("/reschedules/{request_id}/approve", response_model=ApiResponse[dict])
async def reschedule_approve(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await approve_reschedule(scope, request_id), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[dict])
async def reports_summary(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await installment_reports(scope), request_id=get_request_id())