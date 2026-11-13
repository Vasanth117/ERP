"""Examination registration and hall ticket routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.deps import exam_registration_rate_limit, student_user
from app.modules.students.examination_registration_schemas import (
    EligibleExaminationRead,
    EligibleExamSubjectRead,
    ExamRegistrationHistoryRead,
    ExamRegistrationRead,
    ExamRegistrationSubmitInput,
    ExaminationRegistrationEligibilityRead,
    ExaminationRegistrationScheduleRead,
    HallTicketAvailabilityRead,
    HallTicketDetailsRead,
    HallTicketDownloadRead,
)
from app.modules.students.examination_registration_service import (
    cancel_registration,
    download_hall_ticket,
    get_eligible_subjects,
    get_hall_ticket_details,
    get_registration_schedule,
    get_registration_status,
    hall_ticket_availability,
    list_eligible_examinations,
    list_registrations,
    registration_history,
    submit_examination_registration,
    validate_registration_eligibility,
)

examination_registration_router = APIRouter()


@examination_registration_router.get("/me/exam-registrations/eligible", response_model=ApiResponse[list[EligibleExaminationRead]])
async def student_eligible_examinations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[EligibleExaminationRead]]:
    data = await list_eligible_examinations(scope, user)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.get(
    "/me/exam-registrations/seasons/{season_id}/schedule",
    response_model=ApiResponse[ExaminationRegistrationScheduleRead],
)
async def student_exam_registration_schedule_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ExaminationRegistrationScheduleRead]:
    data = await get_registration_schedule(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.get(
    "/me/exam-registrations/seasons/{season_id}/eligibility",
    response_model=ApiResponse[ExaminationRegistrationEligibilityRead],
)
async def student_exam_registration_eligibility_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ExaminationRegistrationEligibilityRead]:
    data = await validate_registration_eligibility(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.get(
    "/me/exam-registrations/seasons/{season_id}/subjects",
    response_model=ApiResponse[list[EligibleExamSubjectRead]],
)
async def student_exam_eligible_subjects_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[EligibleExamSubjectRead]]:
    data = await get_eligible_subjects(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.post(
    "/me/exam-registrations",
    response_model=ApiResponse[ExamRegistrationRead],
)
async def student_exam_registration_submit_route(
    payload: ExamRegistrationSubmitInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(exam_registration_rate_limit)],
) -> ApiResponse[ExamRegistrationRead]:
    data = await submit_examination_registration(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.get("/me/exam-registrations", response_model=ApiResponse[list[ExamRegistrationRead]])
async def student_exam_registrations_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ExamRegistrationRead]]:
    data = await list_registrations(scope, user)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.get(
    "/me/exam-registrations/history",
    response_model=ApiResponse[Page[ExamRegistrationHistoryRead]],
)
async def student_exam_registration_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExamRegistrationHistoryRead]]:
    data = await registration_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.get(
    "/me/exam-registrations/{registration_id}",
    response_model=ApiResponse[ExamRegistrationRead],
)
async def student_exam_registration_status_route(
    registration_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ExamRegistrationRead]:
    data = await get_registration_status(scope, user, registration_id)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.post(
    "/me/exam-registrations/{registration_id}/cancel",
    response_model=ApiResponse[ExamRegistrationRead],
)
async def student_exam_registration_cancel_route(
    registration_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ExamRegistrationRead]:
    data = await cancel_registration(scope, user, registration_id)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.get(
    "/me/hall-tickets/seasons/{season_id}/availability",
    response_model=ApiResponse[HallTicketAvailabilityRead],
)
async def student_hall_ticket_availability_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[HallTicketAvailabilityRead]:
    data = await hall_ticket_availability(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.get(
    "/me/hall-tickets/seasons/{season_id}",
    response_model=ApiResponse[HallTicketDetailsRead],
)
async def student_hall_ticket_details_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[HallTicketDetailsRead]:
    data = await get_hall_ticket_details(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@examination_registration_router.post(
    "/me/hall-tickets/seasons/{season_id}/download",
    response_model=ApiResponse[HallTicketDownloadRead],
)
async def student_hall_ticket_download_route(
    season_id: str,
    request: Request,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[HallTicketDownloadRead]:
    data = await download_hall_ticket(
        scope,
        user,
        season_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return success_response(data, request_id=get_request_id())
