"""Examination cell — result publication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_mixed_deps import examination_cell_or_student_user
from app.modules.examinations.exam_cell_document_service import (
    bulk_generate_documents,
    download_document,
    generate_document,
    verify_document,
)
from app.modules.examinations.exam_cell_publication_schemas import (
    ExamDocumentBulkGenerateRequest,
    ExamDocumentGenerateRequest,
    ExamDocumentRead,
    ExamDocumentVerifyRequest,
    ExamDocumentVerifyResponse,
    ExamPublicationApprove,
    ExamPublicationCreate,
    ExamPublicationHistoryRead,
    ExamPublicationProcessRequest,
    ExamPublicationRead,
    ExamPublicationReleaseRequest,
    ExamPublicationReviseRequest,
    ExamPublicationValidationReport,
    ExamPublicationWithholdRequest,
    ExamStudentPublishedResultRead,
)
from app.modules.examinations.exam_cell_publication_service import (
    approve_publication,
    create_publication,
    execute_scheduled_publications,
    list_student_published_results,
    publication_history,
    publish_results,
    release_withheld_result,
    revise_publication,
    validate_publication_ready,
    withhold_student_result,
)

router = APIRouter(tags=["examination-cell-publication"])


@router.post("/publications/validate", response_model=ApiResponse[ExamPublicationValidationReport])
async def validate_publication_route(
    payload: ExamPublicationProcessRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamPublicationValidationReport]:
    _ = user
    return success_response(await validate_publication_ready(scope, payload), request_id=get_request_id())


@router.post("/publications", response_model=ApiResponse[ExamPublicationRead])
async def create_publication_route(
    payload: ExamPublicationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamPublicationRead]:
    return success_response(await create_publication(scope, user, payload), request_id=get_request_id())


@router.post("/publications/{publication_id}/approve", response_model=ApiResponse[ExamPublicationRead])
async def approve_publication_route(
    publication_id: str,
    payload: ExamPublicationApprove,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamPublicationRead]:
    return success_response(await approve_publication(scope, user, publication_id, payload), request_id=get_request_id())


@router.post("/publications/{publication_id}/publish", response_model=ApiResponse[ExamPublicationRead])
async def publish_route(
    publication_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamPublicationRead]:
    return success_response(await publish_results(scope, user, publication_id), request_id=get_request_id())


@router.post("/publications/scheduled/execute", response_model=ApiResponse[list[ExamPublicationRead]])
async def execute_scheduled_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamPublicationRead]]:
    return success_response(await execute_scheduled_publications(scope, user), request_id=get_request_id())


@router.post("/publications/{publication_id}/withhold", response_model=ApiResponse[dict])
async def withhold_route(
    publication_id: str,
    payload: ExamPublicationWithholdRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[dict]:
    await withhold_student_result(scope, user, publication_id, payload)
    return success_response({"status": "ok"}, request_id=get_request_id())


@router.post("/publications/{publication_id}/release", response_model=ApiResponse[dict])
async def release_route(
    publication_id: str,
    payload: ExamPublicationReleaseRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[dict]:
    await release_withheld_result(scope, user, publication_id, payload)
    return success_response({"status": "ok"}, request_id=get_request_id())


@router.post("/publications/{publication_id}/revise", response_model=ApiResponse[ExamPublicationRead])
async def revise_route(
    publication_id: str,
    payload: ExamPublicationReviseRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamPublicationRead]:
    return success_response(await revise_publication(scope, user, publication_id, payload), request_id=get_request_id())


@router.get("/publications/{publication_id}/history", response_model=ApiResponse[list[ExamPublicationHistoryRead]])
async def history_route(
    publication_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamPublicationHistoryRead]]:
    _ = user
    return success_response(await publication_history(scope, publication_id), request_id=get_request_id())


@router.get("/students/me/published-results", response_model=ApiResponse[list[ExamStudentPublishedResultRead]])
async def my_published_results_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_or_student_user)],
) -> ApiResponse[list[ExamStudentPublishedResultRead]]:
    return success_response(await list_student_published_results(scope, str(user.id)), request_id=get_request_id())


@router.post("/documents/generate", response_model=ApiResponse[ExamDocumentRead])
async def generate_document_route(
    payload: ExamDocumentGenerateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamDocumentRead]:
    return success_response(await generate_document(scope, user, payload), request_id=get_request_id())


@router.post("/documents/generate/bulk", response_model=ApiResponse[list[ExamDocumentRead]])
async def bulk_generate_route(
    payload: ExamDocumentBulkGenerateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamDocumentRead]]:
    return success_response(await bulk_generate_documents(scope, user, payload), request_id=get_request_id())


@router.get("/documents/{document_id}/download")
async def download_document_route(
    document_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_or_student_user)],
) -> Response:
    data, file_name = await download_document(scope, user, document_id)
    return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{file_name}"'})


@router.post("/documents/verify", response_model=ApiResponse[ExamDocumentVerifyResponse])
async def verify_document_route(
    payload: ExamDocumentVerifyRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamDocumentVerifyResponse]:
    _ = user
    return success_response(await verify_document(scope, payload), request_id=get_request_id())