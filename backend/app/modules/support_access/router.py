"""Controlled support access routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AccessScope, get_access_scope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.modules.support_access.schemas import (
    SupportAccessApprovalRequest,
    SupportAccessRequestCreate,
    SupportAccessRequestRead,
    SupportAccessSessionRead,
    SupportActivityRead,
)
from app.modules.support_access.service import (
    decide_support_request,
    get_support_request,
    get_support_session,
    list_support_activity,
    list_support_requests,
    request_support_access,
    revoke_support_session,
    start_support_session,
    terminate_support_session,
)

router = APIRouter(prefix="/support-access", tags=["support-access"])


@router.post("/requests", response_model=ApiResponse[SupportAccessRequestRead])
async def request_support_route(
    payload: SupportAccessRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SupportAccessRequestRead]:
    data = await request_support_access(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/requests", response_model=ApiResponse[list[SupportAccessRequestRead]])
async def list_support_requests_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[SupportAccessRequestRead]]:
    data = await list_support_requests(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/requests/{request_id}", response_model=ApiResponse[SupportAccessRequestRead])
async def get_support_request_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SupportAccessRequestRead]:
    data = await get_support_request(scope, to_object_id(request_id, "request id"))
    return success_response(data, request_id=get_request_id())


@router.post("/requests/{request_id}/decision", response_model=ApiResponse[SupportAccessRequestRead])
async def decide_support_request_route(
    request_id: str,
    payload: SupportAccessApprovalRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SupportAccessRequestRead]:
    data = await decide_support_request(scope, to_object_id(request_id, "request id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/requests/{request_id}/sessions", response_model=ApiResponse[SupportAccessSessionRead])
async def start_support_session_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SupportAccessSessionRead]:
    data = await start_support_session(scope, to_object_id(request_id, "request id"))
    return success_response(data, request_id=get_request_id())


@router.get("/sessions/{session_id}", response_model=ApiResponse[SupportAccessSessionRead])
async def get_support_session_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SupportAccessSessionRead]:
    data = await get_support_session(scope, to_object_id(session_id, "session id"))
    return success_response(data, request_id=get_request_id())


@router.post("/sessions/{session_id}/revoke", response_model=ApiResponse[SupportAccessSessionRead])
async def revoke_support_session_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    reason: Annotated[str, Query(min_length=3, max_length=500)],
) -> ApiResponse[SupportAccessSessionRead]:
    data = await revoke_support_session(scope, to_object_id(session_id, "session id"), reason=reason)
    return success_response(data, request_id=get_request_id())


@router.post("/sessions/{session_id}/terminate", response_model=ApiResponse[SupportAccessSessionRead])
async def terminate_support_session_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SupportAccessSessionRead]:
    data = await terminate_support_session(scope, to_object_id(session_id, "session id"))
    return success_response(data, request_id=get_request_id())


@router.get("/sessions/{session_id}/activity", response_model=ApiResponse[list[SupportActivityRead]])
async def support_activity_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[SupportActivityRead]]:
    data = await list_support_activity(scope, to_object_id(session_id, "session id"))
    return success_response(data, request_id=get_request_id())
