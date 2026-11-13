"""College admin HR administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.hr_admin_schemas import (
    HrPolicyRead,
    HrPolicyUpsert,
    LeaveDecision,
    LeavePolicyUpsert,
    OffboardingCreate,
    OnboardingCreate,
    PayrollConfigRead,
    PayrollConfigUpsert,
    RecruitmentCreate,
)
from app.modules.college_admin.hr_admin_service import (
    complete_onboarding,
    create_recruitment,
    decide_leave,
    hr_report,
    list_pending_leave,
    payroll_status,
    publish_hr_policy,
    record_offboarding,
    start_onboarding,
    upsert_hr_policy,
    upsert_leave_policy,
    upsert_payroll_config,
    workforce_statistics,
)

router = APIRouter()


@router.put("/policies", response_model=ApiResponse[HrPolicyRead])
async def hr_policy_route(
    payload: HrPolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HrPolicyRead]:
    return success_response(await upsert_hr_policy(scope, payload), request_id=get_request_id())


@router.post("/policies/{policy_code}/publish", response_model=ApiResponse[HrPolicyRead])
async def publish_policy_route(
    policy_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HrPolicyRead]:
    return success_response(await publish_hr_policy(scope, policy_code), request_id=get_request_id())


@router.post("/recruitment", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def recruitment_route(
    payload: RecruitmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_recruitment(scope, payload), request_id=get_request_id())


@router.post("/onboarding", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def onboarding_route(
    payload: OnboardingCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await start_onboarding(scope, payload), request_id=get_request_id())


@router.post("/onboarding/{user_id}/complete", response_model=ApiResponse[dict])
async def complete_onboarding_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await complete_onboarding(scope, user_id), request_id=get_request_id())


@router.post("/offboarding", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def offboarding_route(
    payload: OffboardingCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await record_offboarding(scope, payload), request_id=get_request_id())


@router.put("/leave-policies", response_model=ApiResponse[dict])
async def leave_policy_route(
    payload: LeavePolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_leave_policy(scope, payload), request_id=get_request_id())


@router.get("/leave/pending", response_model=ApiResponse[Page[dict]])
async def pending_leave_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_pending_leave(scope, pagination), request_id=get_request_id())


@router.post("/leave/decide", response_model=ApiResponse[dict])
async def leave_decide_route(
    payload: LeaveDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_leave(scope, payload), request_id=get_request_id())


@router.put("/payroll/configuration", response_model=ApiResponse[PayrollConfigRead])
async def payroll_config_route(
    payload: PayrollConfigUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[PayrollConfigRead]:
    return success_response(await upsert_payroll_config(scope, payload), request_id=get_request_id())


@router.get("/payroll/status", response_model=ApiResponse[dict])
async def payroll_status_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await payroll_status(scope), request_id=get_request_id())


@router.get("/statistics", response_model=ApiResponse[dict])
async def workforce_stats_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await workforce_statistics(scope), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[dict])
async def hr_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await hr_report(scope), request_id=get_request_id())
