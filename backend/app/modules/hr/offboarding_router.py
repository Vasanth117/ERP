"""Offboarding and resignation routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.offboarding_schemas import (
    ExitInterviewUpsert,
    NoticePeriodUpdate,
    OffboardingInitiate,
    OffboardingProcessRead,
    OffboardingTaskUpdate,
    OffboardingTemplateUpsert,
    ResignationCreate,
    ResignationRead,
    ResignationReview,
)
from app.modules.hr.offboarding_service import (
    complete_offboarding,
    create_resignation,
    initiate_offboarding,
    list_resignations,
    review_resignation,
    update_notice_period,
    update_offboarding_task,
    upsert_exit_interview,
    upsert_offboarding_template,
)

router = APIRouter(prefix="/offboarding", tags=["hr-offboarding"])


@router.get("/resignations", response_model=ApiResponse[Page[ResignationRead]])
async def list_resignations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_resignations(scope, pagination), request_id=get_request_id())


@router.post("/resignations", response_model=ApiResponse[ResignationRead])
async def create_resignation_route(
    payload: ResignationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_resignation(scope, payload), request_id=get_request_id())


@router.post("/resignations/{resignation_id}/notice-period", response_model=ApiResponse[dict])
async def notice_period_route(
    resignation_id: str,
    payload: NoticePeriodUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_notice_period(scope, resignation_id, payload), request_id=get_request_id())


@router.post("/resignations/{resignation_id}/review", response_model=ApiResponse[ResignationRead])
async def review_resignation_route(
    resignation_id: str,
    payload: ResignationReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await review_resignation(scope, resignation_id, payload), request_id=get_request_id())


@router.put("/templates", response_model=ApiResponse[dict])
async def template_upsert_route(
    payload: OffboardingTemplateUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_offboarding_template(scope, payload), request_id=get_request_id())


@router.post("/processes", response_model=ApiResponse[OffboardingProcessRead])
async def initiate_route(
    payload: OffboardingInitiate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await initiate_offboarding(scope, payload), request_id=get_request_id())


@router.post("/tasks/{task_id}", response_model=ApiResponse[dict])
async def task_update_route(
    task_id: str,
    payload: OffboardingTaskUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_offboarding_task(scope, task_id, payload), request_id=get_request_id())


@router.put("/processes/{process_id}/exit-interview", response_model=ApiResponse[dict])
async def exit_interview_route(
    process_id: str,
    payload: ExitInterviewUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_exit_interview(scope, process_id, payload), request_id=get_request_id())


@router.post("/processes/{process_id}/complete", response_model=ApiResponse[OffboardingProcessRead])
async def complete_route(
    process_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await complete_offboarding(scope, process_id), request_id=get_request_id())