"""Examination cell — hall ticket routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_hall_ticket_schemas import (
    ExamHallTicketBulkGenerateRequest,
    ExamHallTicketGenerateRequest,
    ExamHallTicketHistoryRead,
    ExamHallTicketRead,
    ExamHallTicketReissueRequest,
    ExamHallTicketVerifyRequest,
    ExamHallTicketVerifyResponse,
)
from app.modules.examinations.exam_cell_hall_ticket_service import (
    bulk_generate_hall_tickets,
    download_hall_ticket_pdf,
    generate_hall_ticket,
    get_hall_ticket,
    hall_ticket_history,
    publish_hall_ticket,
    reissue_hall_ticket,
    revoke_hall_ticket,
    verify_hall_ticket,
)

router = APIRouter(prefix="/hall-tickets", tags=["examination-cell-hall-tickets"])


@router.post("/generate", response_model=ApiResponse[ExamHallTicketRead])
async def generate_hall_ticket_route(
    payload: ExamHallTicketGenerateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamHallTicketRead]:
    return success_response(await generate_hall_ticket(scope, user, payload), request_id=get_request_id())


@router.post("/generate/bulk", response_model=ApiResponse[list[ExamHallTicketRead]])
async def bulk_generate_hall_ticket_route(
    payload: ExamHallTicketBulkGenerateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamHallTicketRead]]:
    return success_response(await bulk_generate_hall_tickets(scope, user, payload), request_id=get_request_id())


@router.get("/{hall_ticket_id}", response_model=ApiResponse[ExamHallTicketRead])
async def get_hall_ticket_route(
    hall_ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamHallTicketRead]:
    _ = user
    return success_response(await get_hall_ticket(scope, hall_ticket_id), request_id=get_request_id())


@router.post("/{hall_ticket_id}/publish", response_model=ApiResponse[ExamHallTicketRead])
async def publish_hall_ticket_route(
    hall_ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamHallTicketRead]:
    return success_response(await publish_hall_ticket(scope, user, hall_ticket_id), request_id=get_request_id())


@router.post("/{hall_ticket_id}/revoke", response_model=ApiResponse[ExamHallTicketRead])
async def revoke_hall_ticket_route(
    hall_ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamHallTicketRead]:
    return success_response(await revoke_hall_ticket(scope, user, hall_ticket_id), request_id=get_request_id())


@router.post("/{hall_ticket_id}/reissue", response_model=ApiResponse[ExamHallTicketRead])
async def reissue_hall_ticket_route(
    hall_ticket_id: str,
    payload: ExamHallTicketReissueRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamHallTicketRead]:
    return success_response(await reissue_hall_ticket(scope, user, hall_ticket_id, payload), request_id=get_request_id())


@router.get("/{hall_ticket_id}/download")
async def download_hall_ticket_route(
    hall_ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> Response:
    data, name = await download_hall_ticket_pdf(scope, user, hall_ticket_id)
    return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.post("/verify", response_model=ApiResponse[ExamHallTicketVerifyResponse])
async def verify_hall_ticket_route(
    payload: ExamHallTicketVerifyRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamHallTicketVerifyResponse]:
    _ = user
    return success_response(await verify_hall_ticket(scope, payload), request_id=get_request_id())


@router.get("/{hall_ticket_id}/history", response_model=ApiResponse[list[ExamHallTicketHistoryRead]])
async def hall_ticket_history_route(
    hall_ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamHallTicketHistoryRead]]:
    _ = user
    return success_response(await hall_ticket_history(scope, hall_ticket_id), request_id=get_request_id())