"""Phase 6 outstanding dues and late fee routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.late_fee_service import (
    approve_late_fee_assessment,
    list_late_fee_policies,
    run_late_fee_processing,
    upsert_late_fee_policy,
    waive_late_fee,
)
from app.modules.accounts_finance.outstanding_service import (
    list_overdue_students,
    outstanding_dashboard,
    student_outstanding_statement,
)
from app.modules.auth.models import User


class LateFeePolicyInput(BaseModel):
    policy_id: str | None = None
    policy_code: str
    name: str
    calc_type: str = "fixed"
    fixed_amount: float = 0
    percent_rate: float = 0
    daily_rate: float = 0
    max_late_fee: float | None = None
    grace_days: int = 0
    requires_approval: bool = False
    ageing_buckets: list[dict[str, Any]] = Field(default_factory=list)
    active: bool = True


class LateFeeWaiverInput(BaseModel):
    student_user_id: str
    waived_amount: float = Field(gt=0)
    original_late_fee: float | None = None
    reason: str = Field(min_length=3)
    assessment_id: str | None = None
    transaction_ref: str | None = None
    demand_id: str | None = None


router = APIRouter(prefix="/dues", tags=["accounts-finance-dues"])


@router.get("/dashboard", response_model=ApiResponse[dict])
async def dues_dashboard(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await outstanding_dashboard(scope), request_id=get_request_id())


@router.get("/students/overdue", response_model=ApiResponse[Page[dict]])
async def overdue_students(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_overdue_students(scope, pagination), request_id=get_request_id())


@router.get("/students/{student_user_id}/statement", response_model=ApiResponse[dict])
async def student_statement(
    student_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await student_outstanding_statement(scope, student_user_id), request_id=get_request_id())


@router.get("/late-fee/policies", response_model=ApiResponse[list])
async def late_fee_policies(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[list]:
    return success_response(await list_late_fee_policies(scope), request_id=get_request_id())


@router.post("/late-fee/policies", response_model=ApiResponse[dict])
async def late_fee_policy_upsert(
    payload: LateFeePolicyInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_late_fee_policy(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/late-fee/process", response_model=ApiResponse[dict])
async def late_fee_process(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await run_late_fee_processing(scope), request_id=get_request_id())


@router.post("/late-fee/assessments/{assessment_id}/approve", response_model=ApiResponse[dict])
async def late_fee_approve(
    assessment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await approve_late_fee_assessment(scope, assessment_id), request_id=get_request_id())


@router.post("/late-fee/waivers", response_model=ApiResponse[dict])
async def late_fee_waiver(
    payload: LateFeeWaiverInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await waive_late_fee(scope, payload.model_dump()), request_id=get_request_id())