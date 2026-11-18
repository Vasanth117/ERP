"""Department Admin phase 5 — assessment and examination coordination."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.assessment_monitoring_service import (
    assessment_completion,
    assessment_schedule,
    list_assessments,
    marks_submission_overview,
    student_submission_statuses,
)
from app.modules.department_admin.performance_monitoring_service import (
    performance_arrears,
    performance_batches,
    performance_follow_ups,
    performance_overview,
    performance_pass_fail,
    performance_programmes,
    performance_progression,
    performance_students_requiring_support,
    performance_subjects,
    performance_trends,
)
from app.modules.department_admin.performance_schemas import (
    ArrearSummaryRead,
    BatchPerformanceRead,
    PassFailSummaryRead,
    PerformanceFilters,
    PerformanceFollowUpRead,
    PerformanceOverviewRead,
    PerformanceTrendsRead,
    ProgrammePerformanceRead,
    ProgressionStudentRead,
    StudentsRequiringSupportRead,
    SubjectPerformanceRead,
)
from app.modules.department_admin.examination_monitoring_service import (
    create_coordination_issue,
    examination_pending_tasks,
    examination_readiness,
    list_coordination_issues,
    list_examinations,
    send_coordination_reminder,
    update_coordination_issue,
)
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.phase5_schemas import (
    AssessmentCompletionRowRead,
    AssessmentMonitoringFilters,
    AssessmentScheduleItemRead,
    AssessmentSummaryRead,
    CoordinationIssueCreate,
    CoordinationIssueRead,
    CoordinationIssueUpdate,
    CoordinationReminderRead,
    ExaminationPendingTaskRead,
    ExaminationReadinessRead,
    ExaminationScheduleItemRead,
    MarksSubmissionOverviewRead,
    StudentSubmissionStatusRead,
)

phase5_router = APIRouter()


def _monitoring_filters(
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    batch_label: Annotated[str | None, Query()] = None,
    section_code: Annotated[str | None, Query()] = None,
    course_code: Annotated[str | None, Query()] = None,
    assessment_type: Annotated[str | None, Query()] = None,
    faculty_user_id: Annotated[str | None, Query()] = None,
    assessment_id: Annotated[str | None, Query()] = None,
    date_from: Annotated[str | None, Query(description="ISO-8601 datetime")] = None,
    date_to: Annotated[str | None, Query(description="ISO-8601 datetime")] = None,
) -> AssessmentMonitoringFilters:
    from datetime import datetime

    parsed_from = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
    parsed_to = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None
    return AssessmentMonitoringFilters(
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        programme_code=programme_code,
        batch_label=batch_label,
        section_code=section_code,
        course_code=course_code,
        assessment_type=assessment_type,
        faculty_user_id=faculty_user_id,
        assessment_id=assessment_id,
        date_from=parsed_from,
        date_to=parsed_to,
    )


@phase5_router.get("/assessments", response_model=ApiResponse[Page[AssessmentSummaryRead]])
async def assessments_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AssessmentMonitoringFilters, Depends(_monitoring_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AssessmentSummaryRead]]:
    data = await list_assessments(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/assessments/schedule", response_model=ApiResponse[Page[AssessmentScheduleItemRead]])
async def assessments_schedule_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AssessmentMonitoringFilters, Depends(_monitoring_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AssessmentScheduleItemRead]]:
    data = await assessment_schedule(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/assessments/completion", response_model=ApiResponse[Page[AssessmentCompletionRowRead]])
async def assessments_completion_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AssessmentMonitoringFilters, Depends(_monitoring_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AssessmentCompletionRowRead]]:
    data = await assessment_completion(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/assessments/marks-submission", response_model=ApiResponse[MarksSubmissionOverviewRead])
async def assessments_marks_submission_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AssessmentMonitoringFilters, Depends(_monitoring_filters)],
) -> ApiResponse[MarksSubmissionOverviewRead]:
    data = await marks_submission_overview(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase5_router.get(
    "/assessments/marks-submission/students",
    response_model=ApiResponse[Page[StudentSubmissionStatusRead]],
)
async def assessments_student_submission_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    assessment_id: Annotated[str, Query(min_length=1)],
    component_id: Annotated[str, Query(min_length=1)],
    section: Annotated[str, Query(min_length=1)],
    course_code: Annotated[str, Query(min_length=2)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[StudentSubmissionStatusRead]]:
    data = await student_submission_statuses(
        scope,
        user,
        assessment_id=assessment_id,
        component_id=component_id,
        section=section,
        course_code=course_code,
        pagination=pagination,
    )
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/examinations", response_model=ApiResponse[Page[ExaminationScheduleItemRead]])
async def examinations_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AssessmentMonitoringFilters, Depends(_monitoring_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[ExaminationScheduleItemRead]]:
    data = await list_examinations(scope, user, filters=filters, pagination=pagination, season_id=season_id)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/examinations/readiness", response_model=ApiResponse[ExaminationReadinessRead])
async def examinations_readiness_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    course_code: Annotated[str, Query(min_length=2)],
    section: Annotated[str | None, Query()] = None,
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ExaminationReadinessRead]:
    data = await examination_readiness(scope, user, course_code=course_code, section=section, season_id=season_id)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/examinations/pending-tasks", response_model=ApiResponse[Page[ExaminationPendingTaskRead]])
async def examinations_pending_tasks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AssessmentMonitoringFilters, Depends(_monitoring_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExaminationPendingTaskRead]]:
    data = await examination_pending_tasks(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase5_router.post("/examinations/coordination-issues", response_model=ApiResponse[CoordinationIssueRead])
async def coordination_issues_create_route(
    payload: CoordinationIssueCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[CoordinationIssueRead]:
    data = await create_coordination_issue(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/examinations/coordination-issues", response_model=ApiResponse[Page[CoordinationIssueRead]])
async def coordination_issues_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[CoordinationIssueRead]]:
    data = await list_coordination_issues(scope, user, status=status, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase5_router.patch(
    "/examinations/coordination-issues/{issue_id}",
    response_model=ApiResponse[CoordinationIssueRead],
)
async def coordination_issues_update_route(
    issue_id: str,
    payload: CoordinationIssueUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[CoordinationIssueRead]:
    data = await update_coordination_issue(scope, user, issue_id, payload)
    return success_response(data, request_id=get_request_id())


@phase5_router.post(
    "/examinations/coordination-issues/{issue_id}/remind",
    response_model=ApiResponse[CoordinationReminderRead],
)
async def coordination_issues_remind_route(
    issue_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    idempotency_key: Annotated[str | None, Query()] = None,
) -> ApiResponse[CoordinationReminderRead]:
    data = await send_coordination_reminder(scope, user, issue_id, idempotency_key=idempotency_key)
    return success_response(CoordinationReminderRead(**data), request_id=get_request_id())


def _performance_filters(
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    season_id: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    batch_label: Annotated[str | None, Query()] = None,
    section_code: Annotated[str | None, Query()] = None,
    course_code: Annotated[str | None, Query()] = None,
) -> PerformanceFilters:
    return PerformanceFilters(
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        season_id=season_id,
        programme_code=programme_code,
        batch_label=batch_label,
        section_code=section_code,
        course_code=course_code,
    )


@phase5_router.get("/performance/overview", response_model=ApiResponse[PerformanceOverviewRead])
async def performance_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[PerformanceFilters, Depends(_performance_filters)],
) -> ApiResponse[PerformanceOverviewRead]:
    data = await performance_overview(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/performance/programmes", response_model=ApiResponse[list[ProgrammePerformanceRead]])
async def performance_programmes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[PerformanceFilters, Depends(_performance_filters)],
) -> ApiResponse[list[ProgrammePerformanceRead]]:
    data = await performance_programmes(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/performance/batches", response_model=ApiResponse[list[BatchPerformanceRead]])
async def performance_batches_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[PerformanceFilters, Depends(_performance_filters)],
) -> ApiResponse[list[BatchPerformanceRead]]:
    data = await performance_batches(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/performance/subjects", response_model=ApiResponse[list[SubjectPerformanceRead]])
async def performance_subjects_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[PerformanceFilters, Depends(_performance_filters)],
) -> ApiResponse[list[SubjectPerformanceRead]]:
    data = await performance_subjects(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/performance/pass-fail", response_model=ApiResponse[PassFailSummaryRead])
async def performance_pass_fail_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[PerformanceFilters, Depends(_performance_filters)],
) -> ApiResponse[PassFailSummaryRead]:
    data = await performance_pass_fail(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/performance/arrears", response_model=ApiResponse[ArrearSummaryRead])
async def performance_arrears_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[PerformanceFilters, Depends(_performance_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[ArrearSummaryRead]:
    data = await performance_arrears(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/performance/progression", response_model=ApiResponse[Page[ProgressionStudentRead]])
async def performance_progression_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[PerformanceFilters, Depends(_performance_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ProgressionStudentRead]]:
    data = await performance_progression(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase5_router.get(
    "/performance/students-requiring-support",
    response_model=ApiResponse[StudentsRequiringSupportRead],
)
async def performance_support_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[PerformanceFilters, Depends(_performance_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[StudentsRequiringSupportRead]:
    data = await performance_students_requiring_support(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/performance/trends", response_model=ApiResponse[PerformanceTrendsRead])
async def performance_trends_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    season_ids: Annotated[list[str], Query(min_length=1)],
) -> ApiResponse[PerformanceTrendsRead]:
    data = await performance_trends(scope, user, season_ids=season_ids)
    return success_response(data, request_id=get_request_id())


@phase5_router.get("/performance/follow-ups", response_model=ApiResponse[Page[PerformanceFollowUpRead]])
async def performance_follow_ups_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    category: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[PerformanceFollowUpRead]]:
    data = await performance_follow_ups(scope, user, category=category, pagination=pagination)
    return success_response(data, request_id=get_request_id())