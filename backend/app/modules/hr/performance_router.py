"""Performance management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import employee_self_user, hr_staff_user
from app.modules.hr.performance_schemas import (
    DevelopmentPlanUpsert,
    PerformanceCycleRead,
    PerformanceCycleUpsert,
    PerformanceGoalCreate,
    PerformanceGoalProgress,
    PerformanceGoalRead,
    PerformanceHrAction,
    PerformanceManagerAssessment,
    PerformanceReviewRead,
    PerformanceSelfAssessment,
    PipCreate,
)
from app.modules.hr.performance_service import (
    activate_performance_cycle,
    approve_goal,
    create_goal,
    create_pip,
    hr_review_action,
    list_reviews,
    submit_manager_assessment,
    submit_self_assessment,
    update_goal_progress,
    upsert_development_plan,
    upsert_performance_cycle,
)

router = APIRouter(prefix="/performance", tags=["hr-performance"])


@router.post("/cycles", response_model=ApiResponse[PerformanceCycleRead])
async def upsert_cycle_route(payload: PerformanceCycleUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_performance_cycle(scope, payload), request_id=get_request_id())


@router.post("/cycles/{cycle_id}/activate", response_model=ApiResponse)
async def activate_cycle_route(cycle_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await activate_performance_cycle(scope, cycle_id), request_id=get_request_id())


@router.post("/goals", response_model=ApiResponse[PerformanceGoalRead])
async def create_goal_route(payload: PerformanceGoalCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_goal(scope, payload), request_id=get_request_id())


@router.post("/goals/{goal_id}/approve", response_model=ApiResponse[PerformanceGoalRead])
async def approve_goal_route(goal_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await approve_goal(scope, goal_id), request_id=get_request_id())


@router.post("/goals/{goal_id}/progress", response_model=ApiResponse[PerformanceGoalRead])
async def goal_progress_hr_route(goal_id: str, payload: PerformanceGoalProgress, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await update_goal_progress(scope, goal_id, payload, self_service=False), request_id=get_request_id())


@router.get("/reviews", response_model=ApiResponse[list[PerformanceReviewRead]])
async def list_reviews_route(scope: Annotated[AccessScope, Depends(get_access_scope)], cycle_id: str | None = None, employee_user_id: str | None = None, _: Annotated[User, Depends(hr_staff_user)] = None):
    return success_response(await list_reviews(scope, cycle_id, employee_user_id), request_id=get_request_id())


@router.post("/reviews/{review_id}/manager-assessment", response_model=ApiResponse[PerformanceReviewRead])
async def manager_assessment_route(review_id: str, payload: PerformanceManagerAssessment, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await submit_manager_assessment(scope, review_id, payload), request_id=get_request_id())


@router.post("/reviews/{review_id}/hr-action", response_model=ApiResponse[PerformanceReviewRead])
async def hr_action_route(review_id: str, payload: PerformanceHrAction, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await hr_review_action(scope, review_id, payload), request_id=get_request_id())


@router.post("/pips", response_model=ApiResponse)
async def pip_route(payload: PipCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_pip(scope, payload), request_id=get_request_id())


@router.post("/development-plans", response_model=ApiResponse)
async def dev_plan_route(payload: DevelopmentPlanUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_development_plan(scope, payload), request_id=get_request_id())


@router.post("/self/reviews/{review_id}/self-assessment", response_model=ApiResponse[PerformanceReviewRead])
async def self_assessment_route(review_id: str, payload: PerformanceSelfAssessment, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await submit_self_assessment(scope, review_id, payload), request_id=get_request_id())


@router.post("/self/goals/{goal_id}/progress", response_model=ApiResponse[PerformanceGoalRead])
async def self_goal_progress_route(goal_id: str, payload: PerformanceGoalProgress, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(employee_self_user)]):
    return success_response(await update_goal_progress(scope, goal_id, payload, self_service=True), request_id=get_request_id())