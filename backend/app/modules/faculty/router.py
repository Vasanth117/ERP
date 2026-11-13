"""Faculty dashboard and profile routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.faculty.dashboard_service import (
    get_dashboard_statistics,
    get_faculty_dashboard,
    get_pending_tasks,
    get_recent_activities,
    get_upcoming_deadlines,
)
from app.modules.faculty.deps import faculty_user, profile_update_rate_limit
from app.modules.faculty.enums import DashboardDateRange
from app.modules.faculty.course_content_service import (
    get_approved_syllabus,
    get_course_coverage,
    get_course_details,
    get_enrolled_students,
    get_learning_outcomes,
    get_sections_batches,
    list_assigned_courses,
    list_assigned_subjects,
    update_course_coverage,
)
from app.modules.faculty.content_schemas import (
    AssignedCourseListItem,
    AssignedSubjectItem,
    CalendarEventRead,
    ClassSessionRead,
    ClassroomSummary,
    CourseCoverageRead,
    CourseCoverageUpdate,
    CourseDetailRead,
    ExaminationScheduleRead,
    LearningOutcomesRead,
    EnrolledStudentRead,
    SectionBatchRead,
    SessionUpdateRequestCreate,
    SessionUpdateRequestRead,
    SyllabusRead,
    TimetableChangeRead,
    TimetableDayRead,
    TimetableNotificationRead,
    TimetableWeekRead,
)
from app.modules.faculty.timetable_service import (
    get_academic_calendar,
    get_daily_timetable,
    get_examination_schedules,
    get_session_history,
    get_timetable_changes,
    get_timetable_notifications,
    get_weekly_timetable,
    list_cancelled_rescheduled_sessions,
    list_class_sessions,
    list_classrooms,
    submit_session_update_request,
)
from app.common.ids import to_object_id
from app.modules.faculty.profile_service import (
    get_assigned_courses,
    get_assignment_history,
    get_faculty_profile,
    get_profile_activity_history,
    get_teaching_responsibilities,
    get_workload_summary,
    update_faculty_profile,
)
from app.modules.faculty.schemas import (
    DeadlineSummary,
    FacultyActivityRead,
    FacultyDashboardRead,
    FacultyDashboardStats,
    FacultyProfileRead,
    FacultyProfileUpdate,
    PendingTaskSummary,
    TeachingResponsibilityRead,
    WorkloadDetailRead,
)

from app.modules.faculty.phase3_router import phase3_router
from app.modules.faculty.phase4_router import phase4_router
from app.modules.faculty.phase5_router import phase5_router

router = APIRouter()
router.include_router(phase3_router)
router.include_router(phase4_router)
router.include_router(phase5_router)


@router.get("/me/dashboard", response_model=ApiResponse[FacultyDashboardRead])
async def faculty_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    anchor_date: Annotated[date | None, Query(description="Dashboard anchor date (UTC calendar day)")] = None,
    date_range: Annotated[DashboardDateRange, Query(alias="range")] = DashboardDateRange.WEEK,
) -> ApiResponse[FacultyDashboardRead]:
    data = await get_faculty_dashboard(scope, user, anchor_date=anchor_date, date_range=date_range)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/statistics", response_model=ApiResponse[FacultyDashboardStats])
async def faculty_dashboard_statistics_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[FacultyDashboardStats]:
    data = await get_dashboard_statistics(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/pending-tasks", response_model=ApiResponse[list[PendingTaskSummary]])
async def faculty_pending_tasks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[PendingTaskSummary]]:
    data = await get_pending_tasks(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/deadlines", response_model=ApiResponse[Page[DeadlineSummary]])
async def faculty_deadlines_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[DeadlineSummary]]:
    data = await get_upcoming_deadlines(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/activities", response_model=ApiResponse[Page[FacultyActivityRead]])
async def faculty_dashboard_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[FacultyActivityRead]]:
    data = await get_recent_activities(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/profile", response_model=ApiResponse[FacultyProfileRead])
async def faculty_profile_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[FacultyProfileRead]:
    data = await get_faculty_profile(scope, user)
    return success_response(data, request_id=get_request_id())


@router.patch("/me/profile", response_model=ApiResponse[FacultyProfileRead])
async def faculty_profile_update_route(
    payload: FacultyProfileUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    _: Annotated[None, Depends(profile_update_rate_limit)],
) -> ApiResponse[FacultyProfileRead]:
    data = await update_faculty_profile(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/me/teaching-responsibilities", response_model=ApiResponse[list[TeachingResponsibilityRead]])
async def teaching_responsibilities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[TeachingResponsibilityRead]]:
    data = await get_teaching_responsibilities(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/courses", response_model=ApiResponse[list[TeachingResponsibilityRead]])
async def assigned_courses_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[TeachingResponsibilityRead]]:
    data = await get_assigned_courses(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/workload", response_model=ApiResponse[WorkloadDetailRead])
async def workload_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[WorkloadDetailRead]:
    data = await get_workload_summary(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/profile/activity-history", response_model=ApiResponse[Page[FacultyActivityRead]])
async def profile_activity_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[FacultyActivityRead]]:
    data = await get_profile_activity_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/teaching-responsibilities/history", response_model=ApiResponse[Page[TeachingResponsibilityRead]])
async def teaching_assignment_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[TeachingResponsibilityRead]]:
    data = await get_assignment_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/academic-content/courses", response_model=ApiResponse[list[AssignedCourseListItem]])
async def faculty_assigned_courses_v2_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[AssignedCourseListItem]]:
    data = await list_assigned_courses(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/me/academic-content/courses/{course_code}/subjects",
    response_model=ApiResponse[list[AssignedSubjectItem]],
)
async def faculty_course_subjects_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    section: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[AssignedSubjectItem]]:
    data = await list_assigned_subjects(scope, user, course_code, section=section)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/me/academic-content/courses/{course_code}",
    response_model=ApiResponse[CourseDetailRead],
)
async def faculty_course_detail_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    section: Annotated[str | None, Query()] = None,
) -> ApiResponse[CourseDetailRead]:
    data = await get_course_details(scope, user, course_code, section=section)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/me/academic-content/courses/{course_code}/syllabus",
    response_model=ApiResponse[SyllabusRead],
)
async def faculty_syllabus_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    section: Annotated[str | None, Query()] = None,
    subject_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[SyllabusRead]:
    data = await get_approved_syllabus(scope, user, course_code, section=section, subject_id=subject_id)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/me/academic-content/courses/{course_code}/learning-outcomes",
    response_model=ApiResponse[LearningOutcomesRead],
)
async def faculty_outcomes_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    section: Annotated[str | None, Query()] = None,
) -> ApiResponse[LearningOutcomesRead]:
    data = await get_learning_outcomes(scope, user, course_code, section=section)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/me/academic-content/courses/{course_code}/sections/{section}/students",
    response_model=ApiResponse[list[EnrolledStudentRead]],
)
async def faculty_enrolled_students_route(
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    subject_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[EnrolledStudentRead]]:
    data = await get_enrolled_students(scope, user, course_code, section=section, subject_id=subject_id)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/me/academic-content/courses/{course_code}/sections",
    response_model=ApiResponse[list[SectionBatchRead]],
)
async def faculty_sections_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[SectionBatchRead]]:
    data = await get_sections_batches(scope, user, course_code)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/me/academic-content/courses/{course_code}/sections/{section}/coverage",
    response_model=ApiResponse[CourseCoverageRead],
)
async def faculty_coverage_get_route(
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[CourseCoverageRead]:
    data = await get_course_coverage(scope, user, course_code, section=section)
    return success_response(data, request_id=get_request_id())


@router.patch(
    "/me/academic-content/courses/{course_code}/sections/{section}/coverage",
    response_model=ApiResponse[CourseCoverageRead],
)
async def faculty_coverage_patch_route(
    course_code: str,
    section: str,
    payload: CourseCoverageUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[CourseCoverageRead]:
    data = await update_course_coverage(scope, user, course_code, section=section, payload=payload)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/daily", response_model=ApiResponse[TimetableDayRead])
async def faculty_daily_timetable_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    anchor_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[TimetableDayRead]:
    data = await get_daily_timetable(scope, user, anchor_date=anchor_date)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/weekly", response_model=ApiResponse[TimetableWeekRead])
async def faculty_weekly_timetable_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    anchor_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[TimetableWeekRead]:
    data = await get_weekly_timetable(scope, user, anchor_date=anchor_date)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/sessions", response_model=ApiResponse[list[ClassSessionRead]])
async def faculty_class_sessions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    from_date: Annotated[date | None, Query()] = None,
    to_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[list[ClassSessionRead]]:
    data = await list_class_sessions(scope, user, from_date=from_date, to_date=to_date)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/classrooms", response_model=ApiResponse[list[ClassroomSummary]])
async def faculty_classrooms_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[ClassroomSummary]]:
    data = await list_classrooms(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/calendar", response_model=ApiResponse[list[CalendarEventRead]])
async def faculty_calendar_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[CalendarEventRead]]:
    data = await get_academic_calendar(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/examinations", response_model=ApiResponse[list[ExaminationScheduleRead]])
async def faculty_exam_schedule_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[ExaminationScheduleRead]]:
    data = await get_examination_schedules(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/changes", response_model=ApiResponse[list[TimetableChangeRead]])
async def faculty_timetable_changes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[TimetableChangeRead]]:
    data = await get_timetable_changes(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/notifications", response_model=ApiResponse[list[TimetableNotificationRead]])
async def faculty_timetable_notifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[TimetableNotificationRead]]:
    data = await get_timetable_notifications(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/me/timetable/sessions/cancelled-rescheduled",
    response_model=ApiResponse[list[ClassSessionRead]],
)
async def faculty_cancelled_sessions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[ClassSessionRead]]:
    data = await list_cancelled_rescheduled_sessions(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/timetable/sessions/history", response_model=ApiResponse[Page[ClassSessionRead]])
async def faculty_session_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ClassSessionRead]]:
    data = await get_session_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.post(
    "/me/timetable/sessions/{session_id}/update-requests",
    response_model=ApiResponse[SessionUpdateRequestRead],
    status_code=status.HTTP_201_CREATED,
)
async def faculty_session_update_request_route(
    session_id: str,
    payload: SessionUpdateRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[SessionUpdateRequestRead]:
    data = await submit_session_update_request(
        scope, user, to_object_id(session_id, "session id"), payload
    )
    return success_response(data, request_id=get_request_id())
