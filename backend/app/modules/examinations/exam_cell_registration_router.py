"""Examination cell — eligibility and registration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_mixed_deps import examination_cell_or_student_user
from app.modules.examinations.exam_cell_eligibility_service import evaluate_student_eligibility, get_student_eligibility
from app.modules.examinations.exam_cell_registration_schemas import (
    ExamBulkRegistrationCreate,
    ExamEligibilityEvaluateRequest,
    ExamEligibilityRead,
    ExamRegistrationCorrection,
    ExamRegistrationCreate,
    ExamRegistrationHistoryRead,
    ExamRegistrationRead,
    ExamRegistrationSummaryRead,
)
from app.modules.examinations.exam_cell_registration_service import (
    bulk_register_students,
    cancel_registration,
    correct_registration,
    get_registration,
    list_registrations_for_session,
    register_student,
    registration_history,
    registration_summary,
)

router = APIRouter(tags=["examination-cell-registration"])


@router.post("/eligibility/evaluate", response_model=ApiResponse[ExamEligibilityRead])
async def evaluate_eligibility_route(
    payload: ExamEligibilityEvaluateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamEligibilityRead]:
    return success_response(await evaluate_student_eligibility(scope, user, payload), request_id=get_request_id())


@router.get("/eligibility/sessions/{session_id}/students/{student_id}", response_model=ApiResponse[ExamEligibilityRead])
async def get_eligibility_route(
    session_id: str,
    student_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamEligibilityRead]:
    _ = user
    data = await get_student_eligibility(
        scope,
        exam_session_id=to_object_id(session_id, "exam session id"),
        student_user_id=to_object_id(student_id, "student id"),
    )
    return success_response(data, request_id=get_request_id())


@router.post("/registrations", response_model=ApiResponse[ExamRegistrationRead], status_code=status.HTTP_201_CREATED)
async def register_route(
    payload: ExamRegistrationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_or_student_user)],
) -> ApiResponse[ExamRegistrationRead]:
    return success_response(await register_student(scope, user, payload), request_id=get_request_id())


@router.post("/registrations/bulk", response_model=ApiResponse[list[ExamRegistrationRead]], status_code=status.HTTP_201_CREATED)
async def bulk_register_route(
    payload: ExamBulkRegistrationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamRegistrationRead]]:
    return success_response(await bulk_register_students(scope, user, payload), request_id=get_request_id())


@router.get("/registrations/{registration_id}", response_model=ApiResponse[ExamRegistrationRead])
async def get_registration_route(
    registration_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_or_student_user)],
) -> ApiResponse[ExamRegistrationRead]:
    return success_response(await get_registration(scope, user, registration_id), request_id=get_request_id())


@router.post("/registrations/{registration_id}/cancel", response_model=ApiResponse[ExamRegistrationRead])
async def cancel_registration_route(
    registration_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_or_student_user)],
) -> ApiResponse[ExamRegistrationRead]:
    return success_response(await cancel_registration(scope, user, registration_id), request_id=get_request_id())


@router.post("/registrations/{registration_id}/corrections", response_model=ApiResponse[ExamRegistrationRead])
async def correct_registration_route(
    registration_id: str,
    payload: ExamRegistrationCorrection,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamRegistrationRead]:
    return success_response(await correct_registration(scope, user, registration_id, payload), request_id=get_request_id())


@router.get("/sessions/{session_id}/registrations", response_model=ApiResponse[Page[ExamRegistrationRead]])
async def list_session_registrations_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExamRegistrationRead]]:
    _ = user
    data = await list_registrations_for_session(scope, to_object_id(session_id, "exam session id"), pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/sessions/{session_id}/registrations/summary", response_model=ApiResponse[ExamRegistrationSummaryRead])
async def registration_summary_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamRegistrationSummaryRead]:
    _ = user
    return success_response(await registration_summary(scope, to_object_id(session_id, "exam session id")), request_id=get_request_id())


@router.get("/registrations/{registration_id}/history", response_model=ApiResponse[Page[ExamRegistrationHistoryRead]])
async def registration_history_route(
    registration_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExamRegistrationHistoryRead]]:
    _ = user
    return success_response(await registration_history(scope, registration_id, pagination), request_id=get_request_id())