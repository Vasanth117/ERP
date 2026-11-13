"""Revaluation, rechecking, and marks correction routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.deps import exam_review_rate_limit, student_user
from app.modules.students.exam_review_schemas import (
    ReviewEligibleSubjectRead,
    ReviewFeeDetailsRead,
    ReviewRequestHistoryRead,
    ReviewRequestRead,
    ReviewRequestSubmitInput,
    RevisedMarkRead,
)
from app.modules.students.exam_review_service import (
    get_eligible_review_subjects,
    get_review_fee_details,
    get_review_request_status,
    get_revised_published_marks,
    review_request_history,
    submit_marks_correction,
    submit_rechecking,
    submit_revaluation,
    withdraw_review_request,
)

exam_review_router = APIRouter()


@exam_review_router.get("/me/exam-review/eligible-subjects", response_model=ApiResponse[list[ReviewEligibleSubjectRead]])
async def student_review_eligible_subjects_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str, Query()],
) -> ApiResponse[list[ReviewEligibleSubjectRead]]:
    data = await get_eligible_review_subjects(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@exam_review_router.get("/me/exam-review/fees", response_model=ApiResponse[ReviewFeeDetailsRead])
async def student_review_fees_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str, Query()],
    review_type: Annotated[str, Query()],
) -> ApiResponse[ReviewFeeDetailsRead]:
    data = await get_review_fee_details(scope, user, season_id, review_type)
    return success_response(data, request_id=get_request_id())


@exam_review_router.post("/me/exam-review/revaluation", response_model=ApiResponse[ReviewRequestRead])
async def student_revaluation_submit_route(
    payload: ReviewRequestSubmitInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(exam_review_rate_limit)],
) -> ApiResponse[ReviewRequestRead]:
    data = await submit_revaluation(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@exam_review_router.post("/me/exam-review/rechecking", response_model=ApiResponse[ReviewRequestRead])
async def student_rechecking_submit_route(
    payload: ReviewRequestSubmitInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(exam_review_rate_limit)],
) -> ApiResponse[ReviewRequestRead]:
    data = await submit_rechecking(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@exam_review_router.post("/me/exam-review/marks-correction", response_model=ApiResponse[ReviewRequestRead])
async def student_marks_correction_submit_route(
    payload: ReviewRequestSubmitInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(exam_review_rate_limit)],
) -> ApiResponse[ReviewRequestRead]:
    data = await submit_marks_correction(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@exam_review_router.get("/me/exam-review/requests/{request_id}", response_model=ApiResponse[ReviewRequestRead])
async def student_review_request_status_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ReviewRequestRead]:
    data = await get_review_request_status(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@exam_review_router.post("/me/exam-review/requests/{request_id}/withdraw", response_model=ApiResponse[ReviewRequestRead])
async def student_review_withdraw_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ReviewRequestRead]:
    data = await withdraw_review_request(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@exam_review_router.get("/me/exam-review/history", response_model=ApiResponse[Page[ReviewRequestHistoryRead]])
async def student_review_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ReviewRequestHistoryRead]]:
    data = await review_request_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@exam_review_router.get("/me/exam-review/revised-marks", response_model=ApiResponse[list[RevisedMarkRead]])
async def student_revised_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str, Query()],
) -> ApiResponse[list[RevisedMarkRead]]:
    data = await get_revised_published_marks(scope, user, season_id)
    return success_response(data, request_id=get_request_id())
