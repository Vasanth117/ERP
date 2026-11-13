"""Student CIA marks and continuous assessment routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.cia_service import (
    get_assessment_components,
    get_cia_history,
    get_cia_schedules,
    get_cia_summary,
    get_marks_correction_status,
    get_published_cia_marks,
    get_published_feedback_for_component,
    get_subject_wise_internal_marks,
)
from app.modules.students.continuous_assessment_service import (
    assessment_progress,
    assignment_marks,
    get_assignment_detail,
    get_feedback,
    list_assignments,
    quiz_results,
    quiz_schedules,
    resubmission_eligibility,
    submission_status,
)
from app.modules.students.deps import student_user
from app.modules.students.assessment_schemas import (
    AssessmentComponentStudentRead,
    AssessmentProgressRead,
    AssignmentDetailRead,
    AssignmentListRead,
    CiaHistoryItemRead,
    CiaScheduleRead,
    CiaSummaryRead,
    ContinuousAssessmentMarkRead,
    FeedbackRead,
    MarksCorrectionStatusRead,
    PublishedMarkRead,
    QuizScheduleRead,
    ResubmissionEligibilityRead,
    SubmissionStatusRead,
    SubjectInternalMarksRead,
)

assessment_router = APIRouter()


@assessment_router.get("/me/cia/schedules", response_model=ApiResponse[list[CiaScheduleRead]])
async def student_cia_schedules_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[CiaScheduleRead]]:
    data = await get_cia_schedules(scope, user)
    return success_response(data, request_id=get_request_id())


@assessment_router.get(
    "/me/cia/assessments/{assessment_id}/components",
    response_model=ApiResponse[list[AssessmentComponentStudentRead]],
)
async def student_cia_components_route(
    assessment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[AssessmentComponentStudentRead]]:
    data = await get_assessment_components(scope, user, assessment_id)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/cia/marks", response_model=ApiResponse[list[PublishedMarkRead]])
async def student_cia_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[PublishedMarkRead]]:
    data = await get_published_cia_marks(scope, user)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/cia/marks/subjects", response_model=ApiResponse[list[SubjectInternalMarksRead]])
async def student_cia_subject_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SubjectInternalMarksRead]]:
    data = await get_subject_wise_internal_marks(scope, user)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/cia/summary", response_model=ApiResponse[CiaSummaryRead])
async def student_cia_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CiaSummaryRead]:
    data = await get_cia_summary(scope, user)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/cia/corrections", response_model=ApiResponse[Page[MarksCorrectionStatusRead]])
async def student_cia_corrections_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[MarksCorrectionStatusRead]]:
    data = await get_marks_correction_status(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/cia/history", response_model=ApiResponse[Page[CiaHistoryItemRead]])
async def student_cia_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[CiaHistoryItemRead]]:
    data = await get_cia_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/cia/feedback/{assessment_id}/{component_id}")
async def student_cia_feedback_route(
    assessment_id: str,
    component_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
):
    data = await get_published_feedback_for_component(scope, user, assessment_id, component_id)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/assessments/assignments", response_model=ApiResponse[list[AssignmentListRead]])
async def student_assignments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[AssignmentListRead]]:
    data = await list_assignments(scope, user)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/assessments/assignments/{assignment_id}", response_model=ApiResponse[AssignmentDetailRead])
async def student_assignment_detail_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AssignmentDetailRead]:
    data = await get_assignment_detail(scope, user, assignment_id)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/assessments/quizzes/schedules", response_model=ApiResponse[list[QuizScheduleRead]])
async def student_quiz_schedules_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[QuizScheduleRead]]:
    data = await quiz_schedules(scope, user)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/assessments/quizzes/results", response_model=ApiResponse[list[ContinuousAssessmentMarkRead]])
async def student_quiz_results_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ContinuousAssessmentMarkRead]]:
    data = await quiz_results(scope, user)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/assessments/assignments/{assignment_id}/submission", response_model=ApiResponse[SubmissionStatusRead])
async def student_submission_status_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[SubmissionStatusRead]:
    data = await submission_status(scope, user, assignment_id)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/assessments/marks", response_model=ApiResponse[list[ContinuousAssessmentMarkRead]])
async def student_assignment_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ContinuousAssessmentMarkRead]]:
    data = await assignment_marks(scope, user)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/assessments/assignments/{assignment_id}/feedback", response_model=ApiResponse[FeedbackRead])
async def student_assignment_feedback_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[FeedbackRead]:
    data = await get_feedback(scope, user, assignment_id)
    return success_response(data, request_id=get_request_id())


@assessment_router.get(
    "/me/assessments/assignments/{assignment_id}/resubmission-eligibility",
    response_model=ApiResponse[ResubmissionEligibilityRead],
)
async def student_resubmission_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ResubmissionEligibilityRead]:
    data = await resubmission_eligibility(scope, user, assignment_id)
    return success_response(data, request_id=get_request_id())


@assessment_router.get("/me/assessments/progress", response_model=ApiResponse[list[AssessmentProgressRead]])
async def student_assessment_progress_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[AssessmentProgressRead]]:
    data = await assessment_progress(scope, user)
    return success_response(data, request_id=get_request_id())
