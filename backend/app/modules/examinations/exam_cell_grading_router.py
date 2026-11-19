"""Examination cell — grading and GPA routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_grading_schemas import (
    ExamGradeBoundaryRead,
    ExamGradingPolicyActivate,
    ExamGradingPolicyCreate,
    ExamGradingPolicyRead,
    ExamGradingPolicyVersionRead,
    ExamProvisionalCalculateRequest,
    ExamProvisionalCalculateSummary,
    ExamSemesterResultRead,
    ExamStudentSubjectResultRead,
)
from app.modules.examinations.exam_cell_grading_service import (
    activate_grading_policy,
    calculate_provisional_results,
    create_grading_policy,
    list_grade_boundaries,
    list_semester_results,
    list_subject_results,
    recalculate_for_student_course,
)

router = APIRouter(tags=["examination-cell-grading"])


@router.post("/grading-policies", response_model=ApiResponse[ExamGradingPolicyRead])
async def create_policy_route(
    payload: ExamGradingPolicyCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamGradingPolicyRead]:
    return success_response(await create_grading_policy(scope, user, payload), request_id=get_request_id())


@router.get("/grading-policies/{policy_id}/boundaries", response_model=ApiResponse[list[ExamGradeBoundaryRead]])
async def list_boundaries_route(
    policy_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamGradeBoundaryRead]]:
    _ = user
    return success_response(await list_grade_boundaries(scope, policy_id), request_id=get_request_id())


@router.post("/grading-policies/{policy_id}/activate", response_model=ApiResponse[ExamGradingPolicyVersionRead])
async def activate_policy_route(
    policy_id: str,
    payload: ExamGradingPolicyActivate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamGradingPolicyVersionRead]:
    return success_response(await activate_grading_policy(scope, user, policy_id, payload), request_id=get_request_id())


@router.post("/results/provisional/calculate", response_model=ApiResponse[ExamProvisionalCalculateSummary])
async def calculate_provisional_route(
    payload: ExamProvisionalCalculateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamProvisionalCalculateSummary]:
    return success_response(await calculate_provisional_results(scope, user, payload), request_id=get_request_id())


@router.get("/sessions/{session_id}/subject-results", response_model=ApiResponse[list[ExamStudentSubjectResultRead]])
async def subject_results_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamStudentSubjectResultRead]]:
    _ = user
    return success_response(await list_subject_results(scope, session_id), request_id=get_request_id())


@router.get("/sessions/{session_id}/semester-results", response_model=ApiResponse[list[ExamSemesterResultRead]])
async def semester_results_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamSemesterResultRead]]:
    _ = user
    return success_response(await list_semester_results(scope, session_id), request_id=get_request_id())


@router.post("/sessions/{session_id}/students/{student_id}/courses/{course_code}/recalculate", response_model=ApiResponse[ExamStudentSubjectResultRead])
async def recalculate_route(
    session_id: str,
    student_id: str,
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamStudentSubjectResultRead]:
    data = await recalculate_for_student_course(scope, user, exam_session_id=session_id, student_user_id=student_id, course_code=course_code)
    return success_response(data, request_id=get_request_id())