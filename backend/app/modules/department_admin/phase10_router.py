"""Department Admin phase 10 — helpdesk and placement/research."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.helpdesk_service import (
    add_comment,
    assign_ticket,
    create_ticket,
    escalate_ticket,
    get_ticket,
    helpdesk_summary,
    list_comments,
    list_helpdesk_categories,
    list_tickets,
    reopen_ticket,
    resolve_ticket,
    ticket_history,
    update_ticket,
)
from app.modules.department_admin.models import DepartmentHelpdeskPriority, DepartmentHelpdeskStatus
from app.modules.department_admin.phase10_schemas import (
    HelpdeskAssignBody,
    HelpdeskCommentBody,
    HelpdeskCommentRead,
    HelpdeskEscalateBody,
    HelpdeskFilters,
    HelpdeskHistoryRead,
    HelpdeskReopenBody,
    HelpdeskResolveBody,
    HelpdeskSummaryRead,
    HelpdeskTicketCreate,
    HelpdeskTicketRead,
    HelpdeskTicketUpdate,
    InternshipCreate,
    InternshipRead,
    PlacementActivityCreate,
    PlacementActivityRead,
    PlacementOverviewRead,
    PlacementResearchReportRead,
    PlacementStudentRead,
    ProjectCoordinationRead,
    ProjectReviewCreate,
    ProjectReviewRead,
    ResearchEventRead,
    ResearchOverviewRead,
    ResearchProjectCreate,
    ResearchProjectRead,
)
from app.modules.department_admin.placement_research_service import (
    create_internship,
    create_placement_activity,
    create_research_project,
    get_project,
    list_internships,
    list_placement_activities,
    list_placement_students,
    list_projects,
    list_research_events,
    list_research_projects,
    placement_overview,
    placement_research_report,
    research_overview,
    schedule_project_review,
)

phase10_router = APIRouter()


def _helpdesk_filters(
    q: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    priority: Annotated[DepartmentHelpdeskPriority | None, Query()] = None,
    status: Annotated[DepartmentHelpdeskStatus | None, Query()] = None,
    assigned_user_id: Annotated[str | None, Query()] = None,
    requester_user_id: Annotated[str | None, Query()] = None,
    overdue_only: Annotated[bool, Query()] = False,
    escalated_only: Annotated[bool, Query()] = False,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> HelpdeskFilters:
    return HelpdeskFilters(
        q=q,
        category=category,
        priority=priority,
        status=status,
        assigned_user_id=assigned_user_id,
        requester_user_id=requester_user_id,
        overdue_only=overdue_only,
        escalated_only=escalated_only,
        date_from=date_from,
        date_to=date_to,
    )


@phase10_router.get("/helpdesk/categories", response_model=ApiResponse[list[str]])
async def helpdesk_categories_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[str]]:
    return success_response(list_helpdesk_categories(scope), request_id=get_request_id())


@phase10_router.get("/helpdesk/summary", response_model=ApiResponse[HelpdeskSummaryRead])
async def helpdesk_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[HelpdeskFilters, Depends(_helpdesk_filters)],
) -> ApiResponse[HelpdeskSummaryRead]:
    return success_response(await helpdesk_summary(scope, user, filters), request_id=get_request_id())


@phase10_router.get("/helpdesk", response_model=ApiResponse[Page[HelpdeskTicketRead]])
async def helpdesk_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    filters: Annotated[HelpdeskFilters, Depends(_helpdesk_filters)],
) -> ApiResponse[Page[HelpdeskTicketRead]]:
    return success_response(await list_tickets(scope, user, pagination, filters), request_id=get_request_id())


@phase10_router.post("/helpdesk", response_model=ApiResponse[HelpdeskTicketRead])
async def helpdesk_create_route(
    payload: HelpdeskTicketCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[HelpdeskTicketRead]:
    return success_response(await create_ticket(scope, user, payload), request_id=get_request_id())


@phase10_router.get("/helpdesk/{ticket_id}", response_model=ApiResponse[HelpdeskTicketRead])
async def helpdesk_get_route(
    ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[HelpdeskTicketRead]:
    return success_response(await get_ticket(scope, user, ticket_id), request_id=get_request_id())


@phase10_router.patch("/helpdesk/{ticket_id}", response_model=ApiResponse[HelpdeskTicketRead])
async def helpdesk_patch_route(
    ticket_id: str,
    payload: HelpdeskTicketUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[HelpdeskTicketRead]:
    return success_response(await update_ticket(scope, user, ticket_id, payload), request_id=get_request_id())


@phase10_router.post("/helpdesk/{ticket_id}/assign", response_model=ApiResponse[HelpdeskTicketRead])
async def helpdesk_assign_route(
    ticket_id: str,
    body: HelpdeskAssignBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[HelpdeskTicketRead]:
    return success_response(await assign_ticket(scope, user, ticket_id, body), request_id=get_request_id())


@phase10_router.post("/helpdesk/{ticket_id}/comments", response_model=ApiResponse[HelpdeskCommentRead])
async def helpdesk_comment_route(
    ticket_id: str,
    body: HelpdeskCommentBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[HelpdeskCommentRead]:
    return success_response(await add_comment(scope, user, ticket_id, body), request_id=get_request_id())


@phase10_router.get("/helpdesk/{ticket_id}/comments", response_model=ApiResponse[Page[HelpdeskCommentRead]])
async def helpdesk_comments_list_route(
    ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[HelpdeskCommentRead]]:
    return success_response(await list_comments(scope, user, ticket_id, pagination), request_id=get_request_id())


@phase10_router.post("/helpdesk/{ticket_id}/escalate", response_model=ApiResponse[HelpdeskTicketRead])
async def helpdesk_escalate_route(
    ticket_id: str,
    body: HelpdeskEscalateBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[HelpdeskTicketRead]:
    return success_response(await escalate_ticket(scope, user, ticket_id, body), request_id=get_request_id())


@phase10_router.post("/helpdesk/{ticket_id}/resolve", response_model=ApiResponse[HelpdeskTicketRead])
async def helpdesk_resolve_route(
    ticket_id: str,
    body: HelpdeskResolveBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[HelpdeskTicketRead]:
    return success_response(await resolve_ticket(scope, user, ticket_id, body), request_id=get_request_id())


@phase10_router.post("/helpdesk/{ticket_id}/reopen", response_model=ApiResponse[HelpdeskTicketRead])
async def helpdesk_reopen_route(
    ticket_id: str,
    body: HelpdeskReopenBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[HelpdeskTicketRead]:
    return success_response(await reopen_ticket(scope, user, ticket_id, body), request_id=get_request_id())


@phase10_router.get("/helpdesk/{ticket_id}/history", response_model=ApiResponse[Page[HelpdeskHistoryRead]])
async def helpdesk_history_route(
    ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[HelpdeskHistoryRead]]:
    return success_response(await ticket_history(scope, user, ticket_id, pagination), request_id=get_request_id())


@phase10_router.get("/placement/overview", response_model=ApiResponse[PlacementOverviewRead])
async def placement_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[PlacementOverviewRead]:
    return success_response(await placement_overview(scope, user), request_id=get_request_id())


@phase10_router.get("/placement/students", response_model=ApiResponse[Page[PlacementStudentRead]])
async def placement_students_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[PlacementStudentRead]]:
    return success_response(await list_placement_students(scope, user, pagination), request_id=get_request_id())


@phase10_router.get("/placement/activities", response_model=ApiResponse[Page[PlacementActivityRead]])
async def placement_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[PlacementActivityRead]]:
    return success_response(await list_placement_activities(scope, user, pagination), request_id=get_request_id())


@phase10_router.post("/placement/activities", response_model=ApiResponse[PlacementActivityRead])
async def placement_activity_create_route(
    payload: PlacementActivityCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[PlacementActivityRead]:
    return success_response(await create_placement_activity(scope, user, payload), request_id=get_request_id())


@phase10_router.get("/internships", response_model=ApiResponse[Page[InternshipRead]])
async def internships_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[InternshipRead]]:
    return success_response(await list_internships(scope, user, pagination), request_id=get_request_id())


@phase10_router.post("/internships", response_model=ApiResponse[InternshipRead])
async def internship_create_route(
    payload: InternshipCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[InternshipRead]:
    return success_response(await create_internship(scope, user, payload), request_id=get_request_id())


@phase10_router.get("/projects", response_model=ApiResponse[Page[ProjectCoordinationRead]])
async def projects_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ProjectCoordinationRead]]:
    return success_response(await list_projects(scope, user, pagination), request_id=get_request_id())


@phase10_router.get("/projects/{project_id}", response_model=ApiResponse[ProjectCoordinationRead])
async def project_get_route(
    project_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ProjectCoordinationRead]:
    return success_response(await get_project(scope, user, project_id), request_id=get_request_id())


@phase10_router.post("/projects/{project_id}/reviews", response_model=ApiResponse[ProjectReviewRead])
async def project_review_create_route(
    project_id: str,
    payload: ProjectReviewCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ProjectReviewRead]:
    return success_response(await schedule_project_review(scope, user, project_id, payload), request_id=get_request_id())


@phase10_router.get("/research/overview", response_model=ApiResponse[ResearchOverviewRead])
async def research_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ResearchOverviewRead]:
    return success_response(await research_overview(scope, user), request_id=get_request_id())


@phase10_router.get("/research/projects", response_model=ApiResponse[Page[ResearchProjectRead]])
async def research_projects_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ResearchProjectRead]]:
    return success_response(await list_research_projects(scope, user, pagination), request_id=get_request_id())


@phase10_router.post("/research/projects", response_model=ApiResponse[ResearchProjectRead])
async def research_project_create_route(
    payload: ResearchProjectCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ResearchProjectRead]:
    return success_response(await create_research_project(scope, user, payload), request_id=get_request_id())


@phase10_router.get("/research/events", response_model=ApiResponse[Page[ResearchEventRead]])
async def research_events_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ResearchEventRead]]:
    return success_response(await list_research_events(scope, user, pagination), request_id=get_request_id())


@phase10_router.get("/placement-research/reports", response_model=ApiResponse[PlacementResearchReportRead])
async def placement_research_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[PlacementResearchReportRead]:
    return success_response(await placement_research_report(scope, user), request_id=get_request_id())