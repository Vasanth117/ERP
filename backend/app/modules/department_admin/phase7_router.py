"""Department Admin phase 7 — requests hub and resources."""

from typing import Annotated
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.phase7_schemas import (
    RequestDecisionBody,
    RequestDetailRead,
    RequestEscalateBody,
    RequestFilters,
    RequestForwardBody,
    RequestHistoryRead,
    RequestRejectBody,
    RequestSummaryRead,
    ResourceAvailabilityRead,
    ResourceDirectoryItemRead,
    ResourceIssueCreate,
    ResourceIssueRead,
    ResourceRequestCreate,
    ResourceRequestRead,
    ResourceUtilizationRead,
    UnifiedRequestListItem,
    UnifiedRequestStatus,
)
from app.modules.department_admin.requests_workflow_service import (
    approve_request,
    escalate_request,
    forward_request,
    get_request,
    list_requests,
    reject_request,
    request_history,
    request_more_information,
    requests_summary,
)
from app.modules.department_admin.resource_service import (
    create_resource_request,
    get_resource,
    list_classrooms,
    list_equipment,
    list_laboratories,
    list_resource_requests,
    list_resources,
    report_resource_issue,
    resource_availability,
    resource_utilization,
)

phase7_router = APIRouter()


def _request_filters(
    category: Annotated[str | None, Query()] = None,
    status: Annotated[UnifiedRequestStatus | None, Query()] = None,
    requester_user_id: Annotated[str | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> RequestFilters:
    return RequestFilters(
        category=category,
        status=status,
        requester_user_id=requester_user_id,
        date_from=date_from,
        date_to=date_to,
    )


@phase7_router.get("/requests", response_model=ApiResponse[Page[UnifiedRequestListItem]])
async def department_requests_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[RequestFilters, Depends(_request_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[UnifiedRequestListItem]]:
    data = await list_requests(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/requests/summary", response_model=ApiResponse[RequestSummaryRead])
async def department_requests_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[RequestFilters, Depends(_request_filters)],
) -> ApiResponse[RequestSummaryRead]:
    data = await requests_summary(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/requests/{request_id}", response_model=ApiResponse[RequestDetailRead])
async def department_request_get_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[RequestDetailRead]:
    data = await get_request(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@phase7_router.post("/requests/{request_id}/approve", response_model=ApiResponse[RequestDetailRead])
async def department_request_approve_route(
    request_id: str,
    payload: RequestDecisionBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[RequestDetailRead]:
    data = await approve_request(scope, user, request_id, payload)
    return success_response(data, request_id=get_request_id())


@phase7_router.post("/requests/{request_id}/reject", response_model=ApiResponse[RequestDetailRead])
async def department_request_reject_route(
    request_id: str,
    payload: RequestRejectBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[RequestDetailRead]:
    data = await reject_request(scope, user, request_id, payload)
    return success_response(data, request_id=get_request_id())


@phase7_router.post("/requests/{request_id}/request-information", response_model=ApiResponse[RequestDetailRead])
async def department_request_information_route(
    request_id: str,
    payload: RequestDecisionBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[RequestDetailRead]:
    data = await request_more_information(scope, user, request_id, payload)
    return success_response(data, request_id=get_request_id())


@phase7_router.post("/requests/{request_id}/forward", response_model=ApiResponse[RequestDetailRead])
async def department_request_forward_route(
    request_id: str,
    payload: RequestForwardBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[RequestDetailRead]:
    data = await forward_request(scope, user, request_id, payload)
    return success_response(data, request_id=get_request_id())


@phase7_router.post("/requests/{request_id}/escalate", response_model=ApiResponse[RequestDetailRead])
async def department_request_escalate_route(
    request_id: str,
    payload: RequestEscalateBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[RequestDetailRead]:
    data = await escalate_request(scope, user, request_id, payload)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/requests/{request_id}/history", response_model=ApiResponse[RequestHistoryRead])
async def department_request_history_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[RequestHistoryRead]:
    data = await request_history(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/resources", response_model=ApiResponse[Page[ResourceDirectoryItemRead]])
async def department_resources_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    resource_type: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[ResourceDirectoryItemRead]]:
    data = await list_resources(scope, user, resource_type=resource_type, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/resources/utilization", response_model=ApiResponse[ResourceUtilizationRead])
async def department_resources_utilization_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ResourceUtilizationRead]:
    data = await resource_utilization(scope, user)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/resources/availability", response_model=ApiResponse[ResourceAvailabilityRead])
async def department_resources_availability_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    resource_id: Annotated[str, Query()],
    day: Annotated[date | None, Query()] = None,
) -> ApiResponse[ResourceAvailabilityRead]:
    data = await resource_availability(scope, user, resource_id=resource_id, day=day)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/resources/classrooms", response_model=ApiResponse[Page[ResourceDirectoryItemRead]])
async def department_classrooms_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ResourceDirectoryItemRead]]:
    data = await list_classrooms(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/resources/laboratories", response_model=ApiResponse[Page[ResourceDirectoryItemRead]])
async def department_laboratories_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ResourceDirectoryItemRead]]:
    data = await list_laboratories(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/resources/equipment", response_model=ApiResponse[Page[ResourceDirectoryItemRead]])
async def department_equipment_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ResourceDirectoryItemRead]]:
    data = await list_equipment(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase7_router.post("/resources/requests", response_model=ApiResponse[ResourceRequestRead])
async def department_resource_request_create_route(
    payload: ResourceRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ResourceRequestRead]:
    data = await create_resource_request(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/resources/requests", response_model=ApiResponse[Page[ResourceRequestRead]])
async def department_resource_requests_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ResourceRequestRead]]:
    data = await list_resource_requests(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase7_router.post("/resources/issues", response_model=ApiResponse[ResourceIssueRead])
async def department_resource_issue_route(
    payload: ResourceIssueCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ResourceIssueRead]:
    data = await report_resource_issue(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase7_router.get("/resources/{resource_id}", response_model=ApiResponse[ResourceDirectoryItemRead])
async def department_resource_get_route(
    resource_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ResourceDirectoryItemRead]:
    data = await get_resource(scope, user, resource_id)
    return success_response(data, request_id=get_request_id())