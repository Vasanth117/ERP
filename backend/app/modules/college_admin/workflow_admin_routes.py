"""Workflow and approval administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.workflow_admin_schemas import (
    ApprovalDecision,
    ApprovalHistoryItem,
    ApprovalInfoRequest,
    ApprovalReject,
    ApprovalTaskRead,
    WorkflowDefinitionRead,
    WorkflowDefinitionUpsert,
    WorkflowDelegationCreate,
    WorkflowDelegationRead,
    WorkflowEscalationRead,
    WorkflowInstanceRead,
    WorkflowInstanceStart,
)
from app.modules.college_admin.workflow_admin_service import (
    approve_task,
    cancel_workflow_instance,
    create_delegation,
    list_escalations,
    list_pending_approval_tasks,
    list_workflow_definitions,
    list_workflow_history,
    process_escalations,
    reject_task,
    request_additional_info,
    resubmit_workflow_instance,
    start_workflow_instance,
    upsert_workflow_definition,
)

router = APIRouter()


@router.get("/definitions", response_model=ApiResponse[list[WorkflowDefinitionRead]])
async def workflow_definitions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[WorkflowDefinitionRead]]:
    return success_response(await list_workflow_definitions(scope), request_id=get_request_id())


@router.put("/definitions", response_model=ApiResponse[WorkflowDefinitionRead])
async def workflow_definition_upsert_route(
    payload: WorkflowDefinitionUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[WorkflowDefinitionRead]:
    return success_response(await upsert_workflow_definition(scope, user, payload), request_id=get_request_id())


@router.post("/instances", response_model=ApiResponse[WorkflowInstanceRead])
async def workflow_start_route(
    payload: WorkflowInstanceStart,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[WorkflowInstanceRead]:
    return success_response(await start_workflow_instance(scope, user, payload), request_id=get_request_id())


@router.post("/instances/{instance_id}/cancel", response_model=ApiResponse[WorkflowInstanceRead])
async def workflow_cancel_route(
    instance_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[WorkflowInstanceRead]:
    return success_response(await cancel_workflow_instance(scope, user, instance_id), request_id=get_request_id())


@router.post("/instances/{instance_id}/resubmit", response_model=ApiResponse[WorkflowInstanceRead])
async def workflow_resubmit_route(
    instance_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[WorkflowInstanceRead]:
    return success_response(await resubmit_workflow_instance(scope, user, instance_id), request_id=get_request_id())


@router.get("/pending", response_model=ApiResponse[Page[ApprovalTaskRead]])
async def workflow_pending_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ApprovalTaskRead]]:
    return success_response(await list_pending_approval_tasks(scope, pagination), request_id=get_request_id())


@router.post("/tasks/{task_id}/approve", response_model=ApiResponse[ApprovalTaskRead])
async def workflow_approve_route(
    task_id: str,
    payload: ApprovalDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ApprovalTaskRead]:
    return success_response(await approve_task(scope, user, task_id, payload), request_id=get_request_id())


@router.post("/tasks/{task_id}/reject", response_model=ApiResponse[ApprovalTaskRead])
async def workflow_reject_route(
    task_id: str,
    payload: ApprovalReject,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ApprovalTaskRead]:
    return success_response(await reject_task(scope, user, task_id, payload), request_id=get_request_id())


@router.post("/tasks/{task_id}/request-info", response_model=ApiResponse[ApprovalTaskRead])
async def workflow_request_info_route(
    task_id: str,
    payload: ApprovalInfoRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ApprovalTaskRead]:
    return success_response(await request_additional_info(scope, user, task_id, payload), request_id=get_request_id())


@router.get("/instances/{instance_id}/history", response_model=ApiResponse[list[ApprovalHistoryItem]])
async def workflow_history_route(
    instance_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[ApprovalHistoryItem]]:
    return success_response(await list_workflow_history(scope, instance_id), request_id=get_request_id())


@router.put("/delegations", response_model=ApiResponse[WorkflowDelegationRead])
async def workflow_delegation_route(
    payload: WorkflowDelegationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[WorkflowDelegationRead]:
    return success_response(await create_delegation(scope, user, payload), request_id=get_request_id())


@router.get("/escalations", response_model=ApiResponse[list[WorkflowEscalationRead]])
async def workflow_escalations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    instance_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[WorkflowEscalationRead]]:
    return success_response(await list_escalations(scope, instance_id), request_id=get_request_id())


@router.post("/escalations/process", response_model=ApiResponse[dict])
async def workflow_process_escalations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await process_escalations(scope), request_id=get_request_id())