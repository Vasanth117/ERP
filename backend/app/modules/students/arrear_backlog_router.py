"""Arrear and supplementary examination routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.arrear_backlog_schemas import (
    ArrearEligibilityRead,
    ArrearSubjectRead,
    BacklogSummaryRead,
    ExamAttemptHistoryRead,
    SupplementaryFeeRead,
    SupplementaryRegistrationInput,
    SupplementaryRegistrationRead,
    SupplementaryResultRead,
    SupplementaryScheduleRead,
)
from app.modules.students.arrear_backlog_service import (
    get_arrear_eligibility,
    get_arrear_subjects,
    get_attempt_history,
    get_backlog_summary,
    get_supplementary_fee,
    get_supplementary_results,
    get_supplementary_schedules,
    list_supplementary_registrations,
    register_supplementary,
)
from app.modules.students.deps import exam_review_rate_limit, student_user

arrear_backlog_router = APIRouter()


@arrear_backlog_router.get("/me/arrears/subjects", response_model=ApiResponse[list[ArrearSubjectRead]])
async def student_arrear_subjects_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ArrearSubjectRead]]:
    data = await get_arrear_subjects(scope, user)
    return success_response(data, request_id=get_request_id())


@arrear_backlog_router.get("/me/arrears/attempt-history", response_model=ApiResponse[Page[ExamAttemptHistoryRead]])
async def student_attempt_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExamAttemptHistoryRead]]:
    data = await get_attempt_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@arrear_backlog_router.get(
    "/me/arrears/supplementary/{supplementary_season_id}/eligibility",
    response_model=ApiResponse[ArrearEligibilityRead],
)
async def student_arrear_eligibility_route(
    supplementary_season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ArrearEligibilityRead]:
    data = await get_arrear_eligibility(scope, user, supplementary_season_id)
    return success_response(data, request_id=get_request_id())


@arrear_backlog_router.get("/me/arrears/supplementary/schedules", response_model=ApiResponse[list[SupplementaryScheduleRead]])
async def student_supplementary_schedules_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SupplementaryScheduleRead]]:
    data = await get_supplementary_schedules(scope, user)
    return success_response(data, request_id=get_request_id())


@arrear_backlog_router.get(
    "/me/arrears/supplementary/{supplementary_season_id}/fees",
    response_model=ApiResponse[SupplementaryFeeRead],
)
async def student_supplementary_fee_route(
    supplementary_season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[SupplementaryFeeRead]:
    data = await get_supplementary_fee(scope, user, supplementary_season_id)
    return success_response(data, request_id=get_request_id())


@arrear_backlog_router.post(
    "/me/arrears/supplementary/registrations",
    response_model=ApiResponse[SupplementaryRegistrationRead],
)
async def student_supplementary_register_route(
    payload: SupplementaryRegistrationInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(exam_review_rate_limit)],
) -> ApiResponse[SupplementaryRegistrationRead]:
    data = await register_supplementary(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@arrear_backlog_router.get(
    "/me/arrears/supplementary/registrations",
    response_model=ApiResponse[list[SupplementaryRegistrationRead]],
)
async def student_supplementary_registrations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SupplementaryRegistrationRead]]:
    data = await list_supplementary_registrations(scope, user)
    return success_response(data, request_id=get_request_id())


@arrear_backlog_router.get("/me/arrears/backlog-summary", response_model=ApiResponse[BacklogSummaryRead])
async def student_backlog_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[BacklogSummaryRead]:
    data = await get_backlog_summary(scope, user)
    return success_response(data, request_id=get_request_id())


@arrear_backlog_router.get(
    "/me/arrears/supplementary/{supplementary_season_id}/results",
    response_model=ApiResponse[list[SupplementaryResultRead]],
)
async def student_supplementary_results_route(
    supplementary_season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SupplementaryResultRead]]:
    data = await get_supplementary_results(scope, user, supplementary_season_id)
    return success_response(data, request_id=get_request_id())
