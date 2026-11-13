"""Student semester examination routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.deps import student_user
from app.modules.students.examination_portal_schemas import (
    ExaminationAnnouncementRead,
    ExaminationCalendarEventRead,
    ExaminationCentreRead,
    ExaminationEligibilityRead,
    ExaminationHistoryItemRead,
    ExaminationInstructionsRead,
    ExaminationNotificationRead,
    ExaminationRegulationRead,
    ExaminationScheduleChangeRead,
    SemesterExaminationOverviewRead,
    SemesterExamSeasonRead,
    SemesterExamSessionRead,
)
from app.modules.students.semester_examination_service import (
    get_examination_announcements,
    get_examination_calendar,
    get_examination_centres,
    get_examination_eligibility,
    get_examination_history,
    get_examination_instructions,
    get_examination_notifications,
    get_examination_regulations,
    get_examination_schedule_changes,
    get_examination_session_details,
    get_semester_examination_overview,
    get_semester_examination_schedules,
    list_examination_seasons,
)

semester_examination_router = APIRouter()


@semester_examination_router.get("/me/semester-examinations/overview", response_model=ApiResponse[SemesterExaminationOverviewRead])
async def student_semester_exam_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[SemesterExaminationOverviewRead]:
    data = await get_semester_examination_overview(scope, user)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/seasons", response_model=ApiResponse[list[SemesterExamSeasonRead]])
async def student_semester_exam_seasons_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SemesterExamSeasonRead]]:
    data = await list_examination_seasons(scope, user)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/calendar", response_model=ApiResponse[list[ExaminationCalendarEventRead]])
async def student_semester_exam_calendar_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ExaminationCalendarEventRead]]:
    data = await get_examination_calendar(scope, user)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/schedules", response_model=ApiResponse[list[SemesterExamSessionRead]])
async def student_semester_exam_schedules_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SemesterExamSessionRead]]:
    data = await get_semester_examination_schedules(scope, user)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get(
    "/me/semester-examinations/sessions/{season_id}/{session_code}",
    response_model=ApiResponse[SemesterExamSessionRead],
)
async def student_semester_exam_session_route(
    season_id: str,
    session_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[SemesterExamSessionRead]:
    data = await get_examination_session_details(scope, user, season_id, session_code)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/centres", response_model=ApiResponse[list[ExaminationCentreRead]])
async def student_semester_exam_centres_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ExaminationCentreRead]]:
    data = await get_examination_centres(scope, user)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/instructions", response_model=ApiResponse[list[ExaminationInstructionsRead]])
async def student_semester_exam_instructions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ExaminationInstructionsRead]]:
    data = await get_examination_instructions(scope, user)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/eligibility", response_model=ApiResponse[ExaminationEligibilityRead])
async def student_semester_exam_eligibility_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ExaminationEligibilityRead]:
    data = await get_examination_eligibility(scope, user, season_id=season_id)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/regulations", response_model=ApiResponse[list[ExaminationRegulationRead]])
async def student_semester_exam_regulations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[ExaminationRegulationRead]]:
    data = await get_examination_regulations(scope, user, season_id=season_id)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/announcements", response_model=ApiResponse[list[ExaminationAnnouncementRead]])
async def student_semester_exam_announcements_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ExaminationAnnouncementRead]]:
    data = await get_examination_announcements(scope, user)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get(
    "/me/semester-examinations/schedule-changes",
    response_model=ApiResponse[list[ExaminationScheduleChangeRead]],
)
async def student_semester_exam_changes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ExaminationScheduleChangeRead]]:
    data = await get_examination_schedule_changes(scope, user)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/history", response_model=ApiResponse[Page[ExaminationHistoryItemRead]])
async def student_semester_exam_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExaminationHistoryItemRead]]:
    data = await get_examination_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@semester_examination_router.get("/me/semester-examinations/notifications", response_model=ApiResponse[Page[ExaminationNotificationRead]])
async def student_semester_exam_notifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExaminationNotificationRead]]:
    data = await get_examination_notifications(scope, user, pagination)
    return success_response(data, request_id=get_request_id())
