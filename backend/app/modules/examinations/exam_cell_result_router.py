"""Examination cell — result review and approval routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_result_schemas import (
    ExamResultReviewComment,
    ExamResultReviewDecision,
    ExamResultReviewHistoryRead,
    ExamResultReviewStart,
    ExamResultSessionSummary,
    ExamResultWorkflowRead,
)
from app.modules.examinations.exam_cell_result_service import (
    approve_results,
    department_review_comment,
    exam_cell_verify,
    get_session_summary,
    resubmit_after_rejection,
    review_history,
    start_result_review,
)

router = APIRouter(tags=["examination-cell-results"])


@router.post("/results/review/start", response_model=ApiResponse[ExamResultWorkflowRead])
async def start_review_route(
    payload: ExamResultReviewStart,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamResultWorkflowRead]:
    return success_response(await start_result_review(scope, user, payload), request_id=get_request_id())


@router.post("/results/workflows/{workflow_id}/department-comment", response_model=ApiResponse)
async def department_comment_route(
    workflow_id: str,
    payload: ExamResultReviewComment,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse:
    data = await department_review_comment(scope, user, workflow_id, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/results/workflows/{workflow_id}/verify", response_model=ApiResponse[ExamResultWorkflowRead])
async def verify_route(
    workflow_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamResultWorkflowRead]:
    return success_response(await exam_cell_verify(scope, user, workflow_id), request_id=get_request_id())


@router.post("/results/workflows/{workflow_id}/approve", response_model=ApiResponse[ExamResultWorkflowRead])
async def approve_route(
    workflow_id: str,
    payload: ExamResultReviewDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamResultWorkflowRead]:
    return success_response(await approve_results(scope, user, workflow_id, payload), request_id=get_request_id())


@router.post("/results/workflows/{workflow_id}/resubmit", response_model=ApiResponse[ExamResultWorkflowRead])
async def resubmit_route(
    workflow_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamResultWorkflowRead]:
    return success_response(await resubmit_after_rejection(scope, user, workflow_id), request_id=get_request_id())


@router.get("/sessions/{session_id}/results/summary", response_model=ApiResponse[ExamResultSessionSummary])
async def session_summary_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamResultSessionSummary]:
    _ = user
    return success_response(await get_session_summary(scope, session_id), request_id=get_request_id())


@router.get("/sessions/{session_id}/results/review-history", response_model=ApiResponse[list[ExamResultReviewHistoryRead]])
async def review_history_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamResultReviewHistoryRead]]:
    _ = user
    return success_response(await review_history(scope, session_id), request_id=get_request_id())