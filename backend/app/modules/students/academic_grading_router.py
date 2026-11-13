"""Grades, GPA, and credit routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.academic_grading_schemas import (
    AcademicStandingRead,
    CgpaRead,
    CreditSummaryRead,
    GpaCalculationBreakdownRead,
    GradeHistoryItemRead,
    SemesterGpaRead,
    SemesterPerformanceRead,
    SubjectGradeRead,
)
from app.modules.students.academic_grading_service import (
    get_academic_standing,
    get_cgpa,
    get_credit_summary,
    get_grade_history,
    get_gpa_breakdown,
    get_semester_gpa,
    get_semester_performance,
    get_subject_grades,
)
from app.modules.students.deps import student_user

academic_grading_router = APIRouter()


@academic_grading_router.get("/me/grades/subjects", response_model=ApiResponse[list[SubjectGradeRead]])
async def student_subject_grades_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[SubjectGradeRead]]:
    data = await get_subject_grades(scope, user, season_id=season_id)
    return success_response(data, request_id=get_request_id())


@academic_grading_router.get("/me/grades/gpa/semester/{season_id}", response_model=ApiResponse[SemesterGpaRead])
async def student_semester_gpa_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[SemesterGpaRead]:
    data = await get_semester_gpa(scope, user, season_id)
    return success_response(data, request_id=get_request_id())


@academic_grading_router.get("/me/grades/gpa/cumulative", response_model=ApiResponse[CgpaRead])
async def student_cgpa_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CgpaRead]:
    data = await get_cgpa(scope, user)
    return success_response(data, request_id=get_request_id())


@academic_grading_router.get("/me/grades/performance", response_model=ApiResponse[list[SemesterPerformanceRead]])
async def student_semester_performance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SemesterPerformanceRead]]:
    data = await get_semester_performance(scope, user)
    return success_response(data, request_id=get_request_id())


@academic_grading_router.get("/me/grades/history", response_model=ApiResponse[Page[GradeHistoryItemRead]])
async def student_grade_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[GradeHistoryItemRead]]:
    data = await get_grade_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@academic_grading_router.get("/me/grades/credits", response_model=ApiResponse[CreditSummaryRead])
async def student_credit_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CreditSummaryRead]:
    data = await get_credit_summary(scope, user)
    return success_response(data, request_id=get_request_id())


@academic_grading_router.get("/me/grades/standing", response_model=ApiResponse[AcademicStandingRead])
async def student_academic_standing_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AcademicStandingRead]:
    data = await get_academic_standing(scope, user)
    return success_response(data, request_id=get_request_id())


@academic_grading_router.get("/me/grades/gpa/breakdown", response_model=ApiResponse[GpaCalculationBreakdownRead])
async def student_gpa_breakdown_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    season_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[GpaCalculationBreakdownRead]:
    data = await get_gpa_breakdown(scope, user, season_id=season_id)
    return success_response(data, request_id=get_request_id())
