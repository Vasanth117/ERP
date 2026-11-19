"""Helpdesk and support routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user, helpdesk_comment_rate_limit, helpdesk_create_rate_limit
from app.modules.college_admin.helpdesk_admin_models import SupportTicketStatus
from app.modules.college_admin.helpdesk_admin_schemas import (
    SupportAssignRequest,
    SupportAttachmentCreate,
    SupportCommentCreate,
    SupportEscalateRequest,
    SupportHistoryItem,
    SupportInternalNoteCreate,
    SupportPerformanceReport,
    SupportReopenRequest,
    SupportResolveRequest,
    SupportSlaStatus,
    SupportTicketCreate,
    SupportTicketRead,
    SupportTicketUpdate,
)
from app.modules.college_admin.helpdesk_admin_schemas import SupportCategoryRead
from app.modules.college_admin.helpdesk_admin_service import (
    add_attachment,
    add_comment,
    add_internal_note,
    assign_ticket,
    create_ticket,
    escalate_ticket,
    get_sla_status,
    get_ticket_detail,
    list_categories,
    list_tickets,
    reopen_ticket,
    resolve_ticket,
    submit_feedback,
    support_performance_report,
    ticket_history,
    update_ticket,
)

router = APIRouter()


@router.get("/categories", response_model=ApiResponse[list[SupportCategoryRead]])
async def support_categories_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[SupportCategoryRead]]:
    return success_response(await list_categories(scope), request_id=get_request_id())


@router.get("/reports/performance", response_model=ApiResponse[SupportPerformanceReport])
async def support_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SupportPerformanceReport]:
    return success_response(await support_performance_report(scope), request_id=get_request_id())


@router.post("/tickets", response_model=ApiResponse[SupportTicketRead])
async def support_create_route(
    payload: SupportTicketCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    _: Annotated[None, Depends(helpdesk_create_rate_limit)],
) -> ApiResponse[SupportTicketRead]:
    return success_response(await create_ticket(scope, user, payload), request_id=get_request_id())


@router.get("/tickets", response_model=ApiResponse[Page[SupportTicketRead]])
async def support_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[SupportTicketStatus | None, Query()] = None,
    assigned_to_me: Annotated[bool, Query()] = False,
) -> ApiResponse[Page[SupportTicketRead]]:
    return success_response(
        await list_tickets(scope, pagination, status=status, assigned_to_me=assigned_to_me),
        request_id=get_request_id(),
    )


@router.get("/tickets/{ticket_id}", response_model=ApiResponse[SupportTicketRead])
async def support_detail_route(
    ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    include_internal: Annotated[bool, Query()] = False,
) -> ApiResponse[SupportTicketRead]:
    return success_response(await get_ticket_detail(scope, ticket_id, include_internal=include_internal), request_id=get_request_id())


@router.patch("/tickets/{ticket_id}", response_model=ApiResponse[SupportTicketRead])
async def support_update_route(
    ticket_id: str,
    payload: SupportTicketUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SupportTicketRead]:
    return success_response(await update_ticket(scope, user, ticket_id, payload), request_id=get_request_id())


@router.post("/tickets/{ticket_id}/assign", response_model=ApiResponse[SupportTicketRead])
async def support_assign_route(
    ticket_id: str,
    payload: SupportAssignRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SupportTicketRead]:
    return success_response(await assign_ticket(scope, user, ticket_id, payload), request_id=get_request_id())


@router.post("/tickets/{ticket_id}/comments", response_model=ApiResponse[dict])
async def support_comment_route(
    ticket_id: str,
    payload: SupportCommentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    _: Annotated[None, Depends(helpdesk_comment_rate_limit)],
) -> ApiResponse[dict]:
    return success_response(await add_comment(scope, user, ticket_id, payload), request_id=get_request_id())


@router.post("/tickets/{ticket_id}/internal-notes", response_model=ApiResponse[dict])
async def support_internal_note_route(
    ticket_id: str,
    payload: SupportInternalNoteCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await add_internal_note(scope, user, ticket_id, payload), request_id=get_request_id())


@router.post("/tickets/{ticket_id}/attachments", response_model=ApiResponse[dict])
async def support_attachment_route(
    ticket_id: str,
    payload: SupportAttachmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await add_attachment(scope, user, ticket_id, payload), request_id=get_request_id())


@router.post("/tickets/{ticket_id}/escalate", response_model=ApiResponse[SupportTicketRead])
async def support_escalate_route(
    ticket_id: str,
    payload: SupportEscalateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SupportTicketRead]:
    return success_response(await escalate_ticket(scope, user, ticket_id, payload), request_id=get_request_id())


@router.get("/tickets/{ticket_id}/sla", response_model=ApiResponse[SupportSlaStatus])
async def support_sla_route(
    ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SupportSlaStatus]:
    return success_response(await get_sla_status(scope, ticket_id), request_id=get_request_id())


@router.post("/tickets/{ticket_id}/resolve", response_model=ApiResponse[SupportTicketRead])
async def support_resolve_route(
    ticket_id: str,
    payload: SupportResolveRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SupportTicketRead]:
    return success_response(await resolve_ticket(scope, user, ticket_id, payload), request_id=get_request_id())


@router.post("/tickets/{ticket_id}/reopen", response_model=ApiResponse[SupportTicketRead])
async def support_reopen_route(
    ticket_id: str,
    payload: SupportReopenRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SupportTicketRead]:
    return success_response(await reopen_ticket(scope, user, ticket_id, payload), request_id=get_request_id())


@router.get("/tickets/{ticket_id}/history", response_model=ApiResponse[list[SupportHistoryItem]])
async def support_history_route(
    ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[SupportHistoryItem]]:
    return success_response(await ticket_history(scope, ticket_id), request_id=get_request_id())


@router.post("/tickets/{ticket_id}/feedback", response_model=ApiResponse[dict])
async def support_feedback_route(
    ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    rating: Annotated[int, Query(ge=1, le=5)] = 5,
    comment: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await submit_feedback(scope, user, ticket_id, rating, comment), request_id=get_request_id())