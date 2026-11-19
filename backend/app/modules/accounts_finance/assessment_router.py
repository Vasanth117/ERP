"""Fee assessment routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.assessment_service import (
    create_bulk_assessment,
    create_individual_assessment,
    get_assessment,
    list_assessments,
    preview_bulk_assessment,
    transition_assessment,
)
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.phase2_schemas import (
    AssessmentPreviewResult,
    AssessmentRead,
    AssessmentScopeFilter,
    AssessmentTransition,
    BulkAssessmentCreate,
    IndividualAssessmentCreate,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/assessments", tags=["accounts-finance-assessments"])


@router.post("/preview", response_model=ApiResponse[AssessmentPreviewResult])
async def assessment_preview_route(
    payload: AssessmentScopeFilter,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[AssessmentPreviewResult]:
    return success_response(await preview_bulk_assessment(scope, payload), request_id=get_request_id())


@router.post("", response_model=ApiResponse[AssessmentRead])
async def assessment_create_individual_route(
    payload: IndividualAssessmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[AssessmentRead]:
    return success_response(await create_individual_assessment(scope, payload), request_id=get_request_id())


@router.post("/bulk", response_model=ApiResponse[AssessmentPreviewResult])
async def assessment_bulk_route(
    payload: BulkAssessmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[AssessmentPreviewResult]:
    return success_response(await create_bulk_assessment(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[AssessmentRead]])
async def assessment_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    workflow_status: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[AssessmentRead]]:
    return success_response(
        await list_assessments(scope, pagination, workflow_status=workflow_status, academic_year_label=academic_year_label),
        request_id=get_request_id(),
    )


@router.get("/{assessment_id}", response_model=ApiResponse[AssessmentRead])
async def assessment_get_route(
    assessment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[AssessmentRead]:
    return success_response(await get_assessment(scope, assessment_id), request_id=get_request_id())


@router.post("/{assessment_id}/transitions", response_model=ApiResponse[AssessmentRead])
async def assessment_transition_route(
    assessment_id: str,
    payload: AssessmentTransition,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[AssessmentRead]:
    return success_response(await transition_assessment(scope, assessment_id, payload), request_id=get_request_id())