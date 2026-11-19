"""Examination integration, security and audit routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import exam_cell_sensitive_rate_limit, examination_cell_user
from app.modules.examinations.exam_cell_security_schemas import (
    ExamAccessReviewComplete,
    ExamAccessReviewCreate,
    ExamAccessReviewRead,
    ExamAuditLogRead,
    ExamAuditSearch,
    ExamIntegrationConfigRead,
    ExamIntegrationConfigUpdate,
    ExamIntegrationFailureRead,
    ExamIntegrationHealthReport,
    ExamIntegrationSyncLogRead,
    ExamIntegrationSyncRequest,
    ExamIntegrationWebhookPayload,
    ExamSecurityEventRead,
)
from app.modules.examinations.exam_cell_security_service import (
    complete_access_review,
    create_access_review,
    handle_integration_webhook,
    integration_health_report,
    list_integration_configs,
    list_security_events,
    retry_integration_failure,
    run_integration_sync,
    search_exam_audit,
    update_integration_config,
)

router = APIRouter(tags=["examination-cell-security"])


@router.get("/integrations", response_model=ApiResponse[list[ExamIntegrationConfigRead]])
async def list_integrations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamIntegrationConfigRead]]:
    _ = user
    return success_response(await list_integration_configs(scope), request_id=get_request_id())


@router.patch("/integrations/{integration_target}", response_model=ApiResponse[ExamIntegrationConfigRead])
async def update_integration_route(
    integration_target: str,
    payload: ExamIntegrationConfigUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    _: Annotated[None, Depends(exam_cell_sensitive_rate_limit)],
) -> ApiResponse[ExamIntegrationConfigRead]:
    return success_response(await update_integration_config(scope, user, integration_target, payload), request_id=get_request_id())


@router.post("/integrations/{integration_target}/sync", response_model=ApiResponse[ExamIntegrationSyncLogRead])
async def sync_integration_route(
    integration_target: str,
    payload: ExamIntegrationSyncRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    _: Annotated[None, Depends(exam_cell_sensitive_rate_limit)],
) -> ApiResponse[ExamIntegrationSyncLogRead]:
    return success_response(await run_integration_sync(scope, user, integration_target, payload), request_id=get_request_id())


@router.post("/integrations/failures/{failure_id}/retry", response_model=ApiResponse[ExamIntegrationFailureRead])
async def retry_failure_route(
    failure_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    _: Annotated[None, Depends(exam_cell_sensitive_rate_limit)],
) -> ApiResponse[ExamIntegrationFailureRead]:
    return success_response(await retry_integration_failure(scope, user, failure_id), request_id=get_request_id())


@router.get("/integrations/health", response_model=ApiResponse[ExamIntegrationHealthReport])
async def integration_health_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamIntegrationHealthReport]:
    _ = user
    return success_response(await integration_health_report(scope), request_id=get_request_id())


@router.post("/audit/search", response_model=ApiResponse[Page[ExamAuditLogRead]])
async def audit_search_route(
    filters: ExamAuditSearch,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExamAuditLogRead]]:
    _ = user
    return success_response(await search_exam_audit(scope, pagination, filters), request_id=get_request_id())


@router.get("/security/events", response_model=ApiResponse[Page[ExamSecurityEventRead]])
async def security_events_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExamSecurityEventRead]]:
    _ = user
    return success_response(await list_security_events(scope, pagination), request_id=get_request_id())


@router.post("/security/access-reviews", response_model=ApiResponse[ExamAccessReviewRead])
async def access_review_create_route(
    payload: ExamAccessReviewCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamAccessReviewRead]:
    return success_response(await create_access_review(scope, user, payload), request_id=get_request_id())


@router.post("/integrations/{integration_target}/webhooks", response_model=ApiResponse[ExamIntegrationSyncLogRead])
async def integration_webhook_route(
    integration_target: str,
    payload: ExamIntegrationWebhookPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    _: Annotated[None, Depends(exam_cell_sensitive_rate_limit)],
) -> ApiResponse[ExamIntegrationSyncLogRead]:
    return success_response(
        await handle_integration_webhook(
            scope,
            user,
            integration_target,
            ExamIntegrationSyncRequest(idempotency_key=payload.idempotency_key),
        ),
        request_id=get_request_id(),
    )


@router.post("/security/access-reviews/{review_id}/complete", response_model=ApiResponse[ExamAccessReviewRead])
async def access_review_complete_route(
    review_id: str,
    payload: ExamAccessReviewComplete,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamAccessReviewRead]:
    return success_response(await complete_access_review(scope, user, review_id, payload), request_id=get_request_id())