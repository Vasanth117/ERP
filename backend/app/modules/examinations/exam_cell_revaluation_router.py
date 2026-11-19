"""Revaluation and supplementary routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope, get_current_user
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_revaluation_schemas import (
    ExamRevaluationApplicationRead,
    ExamRevaluationApply,
    ExamRevaluationApprovalDecision,
    ExamRevaluationAssignEvaluator,
    ExamRevaluationRecordEvaluation,
    ExamSupplementaryEligibilityRead,
    ExamSupplementaryRegister,
    ExamSupplementaryRegistrationRead,
)
from app.modules.examinations.exam_cell_revaluation_service import (
    apply_revaluation,
    assign_revaluation_evaluator,
    decide_revaluation,
    record_revaluation_evaluation,
    register_supplementary,
    supplementary_eligibility,
)

router = APIRouter(tags=["examination-cell-revaluation"])


@router.post("/revaluation/applications", response_model=ApiResponse[ExamRevaluationApplicationRead])
async def apply_route(
    payload: ExamRevaluationApply,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamRevaluationApplicationRead]:
    return success_response(await apply_revaluation(scope, user, payload), request_id=get_request_id())


@router.post("/revaluation/applications/{application_id}/assign-evaluator", response_model=ApiResponse[ExamRevaluationApplicationRead])
async def assign_route(
    application_id: str,
    payload: ExamRevaluationAssignEvaluator,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamRevaluationApplicationRead]:
    return success_response(await assign_revaluation_evaluator(scope, user, application_id, payload), request_id=get_request_id())


@router.post("/revaluation/applications/{application_id}/evaluation", response_model=ApiResponse[ExamRevaluationApplicationRead])
async def evaluation_route(
    application_id: str,
    payload: ExamRevaluationRecordEvaluation,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ExamRevaluationApplicationRead]:
    if user.tenant_id is None or str(user.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    return success_response(await record_revaluation_evaluation(scope, user, application_id, payload), request_id=get_request_id())


@router.post("/revaluation/applications/{application_id}/decide", response_model=ApiResponse[ExamRevaluationApplicationRead])
async def decide_route(
    application_id: str,
    payload: ExamRevaluationApprovalDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamRevaluationApplicationRead]:
    return success_response(await decide_revaluation(scope, user, application_id, payload), request_id=get_request_id())


@router.get("/supplementary/students/{student_id}/eligibility", response_model=ApiResponse[ExamSupplementaryEligibilityRead])
async def supp_eligibility_route(
    student_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSupplementaryEligibilityRead]:
    _ = user
    return success_response(await supplementary_eligibility(scope, student_id), request_id=get_request_id())


@router.post("/supplementary/registrations", response_model=ApiResponse[ExamSupplementaryRegistrationRead])
async def supp_register_route(
    payload: ExamSupplementaryRegister,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSupplementaryRegistrationRead]:
    return success_response(await register_supplementary(scope, user, payload), request_id=get_request_id())