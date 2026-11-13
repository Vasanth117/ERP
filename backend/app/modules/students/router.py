"""Student dashboard, profile, and academic enrollment routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.academic_service import (
    get_academic_details,
    get_academic_eligibility,
    get_enrollment_history,
    get_enrollment_request_status,
    get_enrollment_status,
    list_enrollment_requests,
    submit_enrollment_request,
)
from app.modules.students.dashboard_service import (
    get_academic_notifications,
    get_dashboard_statistics,
    get_pending_tasks,
    get_recent_activities,
    get_student_dashboard,
)
from app.modules.students.deps import enrollment_request_rate_limit, profile_update_rate_limit, student_user
from app.modules.students.enums import DashboardDateRange
from app.modules.students.profile_service import get_profile_activity_history, get_student_profile, update_student_profile
from app.modules.students.schemas import (
    AcademicDetailsRead,
    AcademicEligibilityRead,
    EnrollmentHistoryRead,
    EnrollmentRequestCreate,
    EnrollmentRequestRead,
    EnrollmentStatusRead,
    NotificationSummary,
    PendingTaskSummary,
    StudentActivityRead,
    StudentDashboardRead,
    StudentDashboardStats,
    StudentProfileRead,
    StudentProfileUpdate,
)

from app.modules.students.assessment_router import assessment_router
from app.modules.students.curriculum_router import curriculum_router
from app.modules.students.timetable_attendance_router import timetable_attendance_router
from app.modules.students.practical_examination_router import practical_examination_router
from app.modules.students.semester_examination_router import semester_examination_router
from app.modules.students.examination_registration_router import examination_registration_router
from app.modules.students.examination_results_router import examination_results_router
from app.modules.students.academic_grading_router import academic_grading_router
from app.modules.students.academic_document_router import academic_document_router
from app.modules.students.arrear_backlog_router import arrear_backlog_router
from app.modules.students.exam_review_router import exam_review_router
from app.modules.students.student_finance_router import student_finance_router
from app.modules.students.student_lms_router import student_lms_router
from app.modules.students.student_portal_router import student_portal_router

router = APIRouter()
router.include_router(curriculum_router)
router.include_router(timetable_attendance_router)
router.include_router(assessment_router)
router.include_router(practical_examination_router)
router.include_router(semester_examination_router)
router.include_router(examination_registration_router)
router.include_router(examination_results_router)
router.include_router(academic_grading_router)
router.include_router(academic_document_router)
router.include_router(arrear_backlog_router)
router.include_router(exam_review_router)
router.include_router(student_lms_router)
router.include_router(student_finance_router)
router.include_router(student_portal_router)


@router.get("/me/dashboard", response_model=ApiResponse[StudentDashboardRead])
async def student_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    anchor_date: Annotated[date | None, Query(description="Dashboard anchor date (UTC calendar day)")] = None,
    date_range: Annotated[DashboardDateRange, Query(alias="range")] = DashboardDateRange.WEEK,
) -> ApiResponse[StudentDashboardRead]:
    data = await get_student_dashboard(scope, user, anchor_date=anchor_date, date_range=date_range)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/statistics", response_model=ApiResponse[StudentDashboardStats])
async def student_dashboard_statistics_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[StudentDashboardStats]:
    data = await get_dashboard_statistics(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/activities", response_model=ApiResponse[Page[StudentActivityRead]])
async def student_dashboard_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[StudentActivityRead]]:
    data = await get_recent_activities(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/pending-tasks", response_model=ApiResponse[list[PendingTaskSummary]])
async def student_pending_tasks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[PendingTaskSummary]]:
    data = await get_pending_tasks(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/notifications", response_model=ApiResponse[Page[NotificationSummary]])
async def student_notifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[NotificationSummary]]:
    data = await get_academic_notifications(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/profile", response_model=ApiResponse[StudentProfileRead])
async def student_profile_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[StudentProfileRead]:
    data = await get_student_profile(scope, user)
    return success_response(data, request_id=get_request_id())


@router.patch("/me/profile", response_model=ApiResponse[StudentProfileRead])
async def student_profile_update_route(
    payload: StudentProfileUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(profile_update_rate_limit)],
) -> ApiResponse[StudentProfileRead]:
    data = await update_student_profile(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/me/profile/activities", response_model=ApiResponse[Page[StudentActivityRead]])
async def student_profile_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[StudentActivityRead]]:
    data = await get_profile_activity_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/academics", response_model=ApiResponse[AcademicDetailsRead])
async def student_academic_details_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AcademicDetailsRead]:
    data = await get_academic_details(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/academics/enrollment-history", response_model=ApiResponse[Page[EnrollmentHistoryRead]])
async def student_enrollment_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[EnrollmentHistoryRead]]:
    data = await get_enrollment_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/academics/status", response_model=ApiResponse[EnrollmentStatusRead])
async def student_enrollment_status_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[EnrollmentStatusRead]:
    data = await get_enrollment_status(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/me/academics/eligibility", response_model=ApiResponse[AcademicEligibilityRead])
async def student_academic_eligibility_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AcademicEligibilityRead]:
    data = await get_academic_eligibility(scope, user)
    return success_response(data, request_id=get_request_id())


@router.post("/me/academics/enrollment-requests", response_model=ApiResponse[EnrollmentRequestRead])
async def student_submit_enrollment_request_route(
    payload: EnrollmentRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(enrollment_request_rate_limit)],
) -> ApiResponse[EnrollmentRequestRead]:
    data = await submit_enrollment_request(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/me/academics/enrollment-requests", response_model=ApiResponse[Page[EnrollmentRequestRead]])
async def student_list_enrollment_requests_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[EnrollmentRequestRead]]:
    data = await list_enrollment_requests(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/me/academics/enrollment-requests/{request_id}", response_model=ApiResponse[EnrollmentRequestRead])
async def student_enrollment_request_status_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[EnrollmentRequestRead]:
    data = await get_enrollment_request_status(scope, user, request_id)
    return success_response(data, request_id=get_request_id())
