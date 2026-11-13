"""Student timetable and attendance routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.attendance_portal_service import (
    attendance_history,
    export_attendance_summary,
    get_attendance_eligibility,
    get_attendance_summary,
    get_daily_attendance,
    get_discrepancy_status,
    get_shortage_details,
    get_subject_wise_attendance,
    list_discrepancy_requests,
    submit_discrepancy_request,
)
from app.modules.students.deps import enrollment_request_rate_limit, student_user
from app.modules.students.student_schedule_schemas import (
    AttendanceEligibilityRead,
    AttendanceMarkRead,
    AttendanceSemesterSummaryRead,
    AttendanceShortageRead,
    AttendanceSummaryExportRead,
    CalendarEventStudentRead,
    ClassSessionStudentRead,
    DiscrepancyRequestCreate,
    DiscrepancyRequestRead,
    ExaminationScheduleStudentRead,
    StudentTimetableDayRead,
    StudentTimetableSemesterRead,
    StudentTimetableWeekRead,
    SubjectAttendanceDetailRead,
    TimetableChangeStudentRead,
    TimetableNotificationStudentRead,
)
from app.modules.students.timetable_service import (
    calendar_deadlines,
    get_academic_calendar,
    get_daily_timetable,
    get_examination_schedule,
    get_semester_timetable,
    get_timetable_changes,
    get_timetable_notifications,
    get_weekly_timetable,
    list_cancelled_rescheduled_sessions,
)

timetable_attendance_router = APIRouter()


@timetable_attendance_router.get("/me/timetable/daily", response_model=ApiResponse[StudentTimetableDayRead])
async def student_daily_timetable_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    anchor_date: Annotated[date | None, Query()] = None,
    course_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[StudentTimetableDayRead]:
    data = await get_daily_timetable(scope, user, anchor_date=anchor_date, course_code=course_code)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/timetable/weekly", response_model=ApiResponse[StudentTimetableWeekRead])
async def student_weekly_timetable_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    anchor_date: Annotated[date | None, Query()] = None,
    course_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[StudentTimetableWeekRead]:
    data = await get_weekly_timetable(scope, user, anchor_date=anchor_date, course_code=course_code)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/timetable/semester", response_model=ApiResponse[StudentTimetableSemesterRead])
async def student_semester_timetable_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    course_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[StudentTimetableSemesterRead]:
    data = await get_semester_timetable(scope, user, course_code=course_code)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/timetable/calendar", response_model=ApiResponse[list[CalendarEventStudentRead]])
async def student_academic_calendar_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ApiResponse[list[CalendarEventStudentRead]]:
    data = await get_academic_calendar(scope, user, limit=limit)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/timetable/calendar/deadlines", response_model=ApiResponse[Page[CalendarEventStudentRead]])
async def student_calendar_deadlines_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[CalendarEventStudentRead]]:
    data = await calendar_deadlines(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/timetable/examinations", response_model=ApiResponse[list[ExaminationScheduleStudentRead]])
async def student_examination_schedule_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ExaminationScheduleStudentRead]]:
    data = await get_examination_schedule(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/timetable/changes", response_model=ApiResponse[list[TimetableChangeStudentRead]])
async def student_timetable_changes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[TimetableChangeStudentRead]]:
    data = await get_timetable_changes(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/timetable/notifications", response_model=ApiResponse[list[TimetableNotificationStudentRead]])
async def student_timetable_notifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[TimetableNotificationStudentRead]]:
    data = await get_timetable_notifications(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/timetable/sessions/cancelled-rescheduled", response_model=ApiResponse[list[ClassSessionStudentRead]])
async def student_cancelled_sessions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ClassSessionStudentRead]]:
    data = await list_cancelled_rescheduled_sessions(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/attendance/summary", response_model=ApiResponse[AttendanceSemesterSummaryRead])
async def student_attendance_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AttendanceSemesterSummaryRead]:
    data = await get_attendance_summary(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/attendance/subjects", response_model=ApiResponse[list[SubjectAttendanceDetailRead]])
async def student_subject_attendance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SubjectAttendanceDetailRead]]:
    data = await get_subject_wise_attendance(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/attendance/daily", response_model=ApiResponse[list[AttendanceMarkRead]])
async def student_daily_attendance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    session_date: Annotated[date, Query()],
) -> ApiResponse[list[AttendanceMarkRead]]:
    data = await get_daily_attendance(scope, user, session_date)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/attendance/history", response_model=ApiResponse[Page[AttendanceMarkRead]])
async def student_attendance_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AttendanceMarkRead]]:
    data = await attendance_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/attendance/shortages", response_model=ApiResponse[list[AttendanceShortageRead]])
async def student_attendance_shortages_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[AttendanceShortageRead]]:
    data = await get_shortage_details(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/attendance/eligibility", response_model=ApiResponse[AttendanceEligibilityRead])
async def student_attendance_eligibility_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AttendanceEligibilityRead]:
    data = await get_attendance_eligibility(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/attendance/export", response_model=ApiResponse[AttendanceSummaryExportRead])
async def student_attendance_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AttendanceSummaryExportRead]:
    data = await export_attendance_summary(scope, user)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.post("/me/attendance/discrepancy-requests", response_model=ApiResponse[DiscrepancyRequestRead])
async def student_submit_discrepancy_route(
    payload: DiscrepancyRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(enrollment_request_rate_limit)],
) -> ApiResponse[DiscrepancyRequestRead]:
    data = await submit_discrepancy_request(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get("/me/attendance/discrepancy-requests", response_model=ApiResponse[Page[DiscrepancyRequestRead]])
async def student_list_discrepancy_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[DiscrepancyRequestRead]]:
    data = await list_discrepancy_requests(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@timetable_attendance_router.get(
    "/me/attendance/discrepancy-requests/{request_id}",
    response_model=ApiResponse[DiscrepancyRequestRead],
)
async def student_discrepancy_status_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[DiscrepancyRequestRead]:
    data = await get_discrepancy_status(scope, user, request_id)
    return success_response(data, request_id=get_request_id())
