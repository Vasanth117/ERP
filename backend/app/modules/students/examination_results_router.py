"""Published semester examination results routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.deps import student_user
from app.modules.students.examination_results_schemas import (
    ArrearResultRead,
    ResultAttemptHistoryRead,
    ResultNotificationRead,
    ResultPublicationStatusRead,
    SemesterResultSummaryRead,
    SubjectWiseMarksRead,
)
from app.modules.students.examination_results_service import (
    get_arrear_results,
    get_attempt_history,
    get_published_semester_results,
    get_result_notifications,
    get_result_publication_status,
    get_subject_wise_marks,
)

examination_results_router = APIRouter()


@examination_results_router.get(
    "/me/exam-results/seasons/{season_id}",
    response_model=ApiResponse[SemesterResultSummaryRead],
)
async def student_semester_results_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[SemesterResultSummaryRead]:
    data = await get_published_semester_results(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@examination_results_router.get("/me/exam-results/marks", response_model=ApiResponse[list[SubjectWiseMarksRead]])
async def student_subject_wise_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[SubjectWiseMarksRead]]:
    data = await get_subject_wise_marks(scope, user, season_id=season_id)
    return success_response(data, request_id=get_request_id())


@examination_results_router.get(
    "/me/exam-results/attempt-history",
    response_model=ApiResponse[Page[ResultAttemptHistoryRead]],
)
async def student_exam_attempt_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ResultAttemptHistoryRead]]:
    data = await get_attempt_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@examination_results_router.get("/me/exam-results/arrears", response_model=ApiResponse[list[ArrearResultRead]])
async def student_arrear_results_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ArrearResultRead]]:
    data = await get_arrear_results(scope, user)
    return success_response(data, request_id=get_request_id())


@examination_results_router.get(
    "/me/exam-results/seasons/{season_id}/publication-status",
    response_model=ApiResponse[ResultPublicationStatusRead],
)
async def student_result_publication_status_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ResultPublicationStatusRead]:
    data = await get_result_publication_status(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@examination_results_router.get(
    "/me/exam-results/notifications",
    response_model=ApiResponse[Page[ResultNotificationRead]],
)
async def student_result_notifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ResultNotificationRead]]:
    data = await get_result_notifications(scope, user, pagination)
    return success_response(data, request_id=get_request_id())
