"""Examination cell — assessment configuration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_assessment_schemas import (
    ExamAssessmentConfigCreate,
    ExamAssessmentConfigRead,
    ExamAssessmentConfigUpdate,
    ExamAssessmentPolicyVersionRead,
)
from app.modules.examinations.exam_cell_assessment_service import (
    activate_assessment_config,
    create_assessment_config,
    get_assessment_config,
    list_assessment_configs,
    list_assessment_policy_versions,
    update_assessment_config,
)
from app.modules.examinations.exam_cell_deps import examination_cell_user

router = APIRouter(prefix="/assessment-configurations", tags=["examination-cell-assessment"])


@router.post("", response_model=ApiResponse[ExamAssessmentConfigRead], status_code=status.HTTP_201_CREATED)
async def create_assessment_config_route(
    payload: ExamAssessmentConfigCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamAssessmentConfigRead]:
    return success_response(await create_assessment_config(scope, user, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[ExamAssessmentConfigRead]])
async def list_assessment_configs_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    programme_code: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[ExamAssessmentConfigRead]]:
    _ = user
    return success_response(
        await list_assessment_configs(scope, programme_code=programme_code, semester_label=semester_label, pagination=pagination),
        request_id=get_request_id(),
    )


@router.get("/{config_id}", response_model=ApiResponse[ExamAssessmentConfigRead])
async def get_assessment_config_route(
    config_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamAssessmentConfigRead]:
    _ = user
    return success_response(await get_assessment_config(scope, to_object_id(config_id, "config id")), request_id=get_request_id())


@router.patch("/{config_id}", response_model=ApiResponse[ExamAssessmentConfigRead])
async def update_assessment_config_route(
    config_id: str,
    payload: ExamAssessmentConfigUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamAssessmentConfigRead]:
    return success_response(
        await update_assessment_config(scope, user, to_object_id(config_id, "config id"), payload),
        request_id=get_request_id(),
    )


@router.post("/{config_id}/activate", response_model=ApiResponse[ExamAssessmentConfigRead])
async def activate_assessment_config_route(
    config_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamAssessmentConfigRead]:
    return success_response(await activate_assessment_config(scope, user, to_object_id(config_id, "config id")), request_id=get_request_id())


@router.get("/{config_id}/versions", response_model=ApiResponse[list[ExamAssessmentPolicyVersionRead]])
async def assessment_policy_versions_route(
    config_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamAssessmentPolicyVersionRead]]:
    _ = user
    return success_response(
        await list_assessment_policy_versions(scope, to_object_id(config_id, "config id")),
        request_id=get_request_id(),
    )