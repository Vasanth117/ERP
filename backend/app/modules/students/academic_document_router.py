"""Marksheet, grade card, and transcript routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.academic_document_schemas import (
    AcademicDocumentDownloadRead,
    AcademicDocumentHistoryRead,
    AcademicDocumentRequestCreate,
    AcademicDocumentRequestRead,
    AcademicDocumentSummaryRead,
)
from app.modules.students.academic_document_service import (
    document_access_history,
    download_academic_document,
    get_document_by_id,
    get_document_request_status,
    get_transcript,
    list_grade_cards,
    list_marksheets,
    submit_document_request,
)
from app.modules.students.deps import academic_document_request_rate_limit, student_user

academic_document_router = APIRouter()


@academic_document_router.get("/me/academic-documents/grade-cards", response_model=ApiResponse[list[AcademicDocumentSummaryRead]])
async def student_grade_cards_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[AcademicDocumentSummaryRead]]:
    data = await list_grade_cards(scope, user, season_id=season_id)
    return success_response(data, request_id=get_request_id())


@academic_document_router.get("/me/academic-documents/marksheets", response_model=ApiResponse[list[AcademicDocumentSummaryRead]])
async def student_marksheets_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[AcademicDocumentSummaryRead]]:
    data = await list_marksheets(scope, user, season_id=season_id)
    return success_response(data, request_id=get_request_id())


@academic_document_router.get("/me/academic-documents/transcript", response_model=ApiResponse[AcademicDocumentSummaryRead])
async def student_transcript_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AcademicDocumentSummaryRead]:
    data = await get_transcript(scope, user)
    return success_response(data, request_id=get_request_id())


@academic_document_router.get(
    "/me/academic-documents/history",
    response_model=ApiResponse[Page[AcademicDocumentHistoryRead]],
)
async def student_academic_document_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AcademicDocumentHistoryRead]]:
    data = await document_access_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@academic_document_router.post(
    "/me/academic-documents/requests",
    response_model=ApiResponse[AcademicDocumentRequestRead],
)
async def student_academic_document_request_route(
    payload: AcademicDocumentRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(academic_document_request_rate_limit)],
) -> ApiResponse[AcademicDocumentRequestRead]:
    data = await submit_document_request(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@academic_document_router.get(
    "/me/academic-documents/requests/{request_id}",
    response_model=ApiResponse[AcademicDocumentRequestRead],
)
async def student_academic_document_request_status_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AcademicDocumentRequestRead]:
    data = await get_document_request_status(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@academic_document_router.get(
    "/me/academic-documents/{document_id}",
    response_model=ApiResponse[AcademicDocumentSummaryRead],
)
async def student_academic_document_detail_route(
    document_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AcademicDocumentSummaryRead]:
    data = await get_document_by_id(scope, user, document_id)
    return success_response(data, request_id=get_request_id())


@academic_document_router.post(
    "/me/academic-documents/{document_id}/download",
    response_model=ApiResponse[AcademicDocumentDownloadRead],
)
async def student_academic_document_download_route(
    document_id: str,
    request: Request,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AcademicDocumentDownloadRead]:
    data = await download_academic_document(
        scope,
        user,
        document_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return success_response(data, request_id=get_request_id())
