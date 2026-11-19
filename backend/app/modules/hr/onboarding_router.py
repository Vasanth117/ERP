"""HR onboarding routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope, pagination_params
from app.common.schemas import Page, Pagination
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.onboarding_schemas import (
    OnboardingInitiate,
    OnboardingOverviewStats,
    OnboardingProcessRead,
    OnboardingProgressRead,
    OnboardingTaskRead,
    OnboardingTaskUpdate,
    OnboardingTemplateRead,
    OnboardingTemplateUpsert,
    OnboardingWaiverCreate,
)
from app.modules.hr.onboarding_service import (
    complete_onboarding,
    compute_onboarding_progress,
    get_onboarding_process,
    initiate_onboarding,
    list_my_onboarding_tasks,
    list_onboarding_processes,
    list_onboarding_templates,
    list_process_tasks,
    onboarding_overview,
    record_onboarding_waiver,
    submit_onboarding_for_completion,
    update_onboarding_task,
    upsert_onboarding_template,
)

router = APIRouter(prefix="/onboarding", tags=["hr-onboarding"])


@router.get("/overview", response_model=ApiResponse[OnboardingOverviewStats])
async def onboarding_overview_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await onboarding_overview(scope), request_id=get_request_id())


@router.get("/templates", response_model=ApiResponse[list[OnboardingTemplateRead]])
async def list_templates_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_onboarding_templates(scope), request_id=get_request_id())


@router.put("/templates", response_model=ApiResponse[OnboardingTemplateRead])
async def upsert_template_route(
    payload: OnboardingTemplateUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_onboarding_template(scope, payload), request_id=get_request_id())


@router.get("/processes", response_model=ApiResponse[Page[OnboardingProcessRead]])
async def list_processes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_onboarding_processes(scope, pagination), request_id=get_request_id())


@router.get("/processes/{process_id}", response_model=ApiResponse[OnboardingProcessRead])
async def get_process_route(
    process_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_onboarding_process(scope, process_id), request_id=get_request_id())


@router.get("/processes/{process_id}/tasks", response_model=ApiResponse[list[OnboardingTaskRead]])
async def list_tasks_route(
    process_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await list_process_tasks(scope, process_id), request_id=get_request_id())


@router.get("/tasks/mine", response_model=ApiResponse[list[OnboardingTaskRead]])
async def my_tasks_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_my_onboarding_tasks(scope), request_id=get_request_id())


@router.post("/processes", response_model=ApiResponse[OnboardingProcessRead])
async def initiate_onboarding_route(
    payload: OnboardingInitiate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await initiate_onboarding(scope, payload), request_id=get_request_id())


@router.get("/processes/{process_id}/progress", response_model=ApiResponse[OnboardingProgressRead])
async def onboarding_progress_route(
    process_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await compute_onboarding_progress(scope, process_id), request_id=get_request_id())


@router.patch("/tasks/{task_id}", response_model=ApiResponse[OnboardingTaskRead])
async def update_task_route(
    task_id: str,
    payload: OnboardingTaskUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_onboarding_task(scope, task_id, payload), request_id=get_request_id())


@router.post("/processes/{process_id}/waivers")
async def waiver_route(
    process_id: str,
    payload: OnboardingWaiverCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await record_onboarding_waiver(scope, process_id, payload), request_id=get_request_id())


@router.post("/processes/{process_id}/submit-completion", response_model=ApiResponse[OnboardingProcessRead])
async def submit_completion_route(
    process_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await submit_onboarding_for_completion(scope, process_id), request_id=get_request_id())


@router.post("/processes/{process_id}/complete", response_model=ApiResponse[OnboardingProcessRead])
async def complete_onboarding_route(
    process_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await complete_onboarding(scope, process_id), request_id=get_request_id())