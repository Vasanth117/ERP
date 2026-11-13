"""Data export and offboarding HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import AccessScope, get_access_scope, pagination_params
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.data_governance.export_service import (
    create_export_request,
    get_export_artifacts,
    get_export_progress,
    get_export_request,
    issue_download_access,
    list_export_requests,
    retry_export_job,
    review_export_request,
    start_export_job,
    stream_authorized_download,
)
from app.modules.data_governance.offboarding_service import (
    advance_export_preparation,
    approve_deletion,
    approve_offboarding,
    create_deletion_request,
    create_legal_hold,
    enter_retention_period,
    execute_deletion,
    get_archival_status,
    get_deletion_manifest,
    get_offboarding_report,
    get_offboarding_workflow,
    get_retention_policy,
    initiate_offboarding_workflow,
    reject_offboarding,
    run_offboarding_export,
    start_archival,
    update_retention_policy,
)
from app.modules.data_governance.schemas import (
    DeletionRequestCreate,
    ExportArtifactRead,
    ExportDownloadIssueResponse,
    ExportJobRead,
    ExportRequestCreate,
    ExportRequestRead,
    ExportReviewRequest,
    LegalHoldCreate,
    OffboardingInitiate,
    OffboardingRead,
    RetentionPolicyRead,
    RetentionPolicyUpdate,
)

router = APIRouter(tags=["data-governance"])


@router.post("/tenants/{tenant_id}/exports", response_model=ApiResponse[ExportRequestRead])
async def create_export_route(
    tenant_id: str,
    payload: ExportRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ExportRequestRead]:
    data = await create_export_request(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/exports", response_model=ApiResponse[Page[ExportRequestRead]])
async def list_exports_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ExportRequestRead]]:
    data = await list_export_requests(scope, to_object_id(tenant_id, "tenant id"), pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/exports/{request_id}", response_model=ApiResponse[ExportRequestRead])
async def get_export_route(
    tenant_id: str,
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ExportRequestRead]:
    data = await get_export_request(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
    )
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/exports/{request_id}/review", response_model=ApiResponse[ExportRequestRead])
async def review_export_route(
    tenant_id: str,
    request_id: str,
    payload: ExportReviewRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ExportRequestRead]:
    data = await review_export_request(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
        payload,
    )
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/exports/{request_id}/start", response_model=ApiResponse[ExportJobRead])
async def start_export_route(
    tenant_id: str,
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ExportJobRead]:
    data = await start_export_job(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
    )
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/exports/{request_id}/progress", response_model=ApiResponse[ExportJobRead])
async def export_progress_route(
    tenant_id: str,
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ExportJobRead]:
    data = await get_export_progress(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
    )
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/exports/{request_id}/retry", response_model=ApiResponse[ExportJobRead])
async def retry_export_route(
    tenant_id: str,
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ExportJobRead]:
    data = await retry_export_job(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
    )
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/exports/{request_id}/artifacts", response_model=ApiResponse[list[ExportArtifactRead]])
async def export_artifacts_route(
    tenant_id: str,
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ExportArtifactRead]]:
    data = await get_export_artifacts(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
    )
    return success_response(data, request_id=get_request_id())


@router.post(
    "/tenants/{tenant_id}/exports/artifacts/{artifact_id}/download",
    response_model=ApiResponse[ExportDownloadIssueResponse],
)
async def issue_download_route(
    tenant_id: str,
    artifact_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ExportDownloadIssueResponse]:
    data = await issue_download_access(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(artifact_id, "artifact id"),
    )
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/exports/artifacts/{artifact_id}/content")
async def download_export_route(
    tenant_id: str,
    artifact_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    token: Annotated[str, Query()],
    signature: Annotated[str, Query()],
) -> Response:
    data, filename = await stream_authorized_download(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(artifact_id, "artifact id"),
        token,
        signature,
    )
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/tenants/{tenant_id}/offboarding", response_model=ApiResponse[OffboardingRead])
async def initiate_offboarding_route(
    tenant_id: str,
    payload: OffboardingInitiate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingRead]:
    data = await initiate_offboarding_workflow(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/offboarding/report", response_model=ApiResponse[dict])
async def offboarding_report_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await get_offboarding_report(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/offboarding", response_model=ApiResponse[OffboardingRead])
async def offboarding_status_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingRead]:
    data = await get_offboarding_workflow(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/offboarding/approve", response_model=ApiResponse[OffboardingRead])
async def approve_offboarding_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingRead]:
    data = await approve_offboarding(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/offboarding/reject", response_model=ApiResponse[OffboardingRead])
async def reject_offboarding_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    note: Annotated[str, Query()] = "",
) -> ApiResponse[OffboardingRead]:
    data = await reject_offboarding(scope, to_object_id(tenant_id, "tenant id"), note)
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/offboarding/export/prepare", response_model=ApiResponse[OffboardingRead])
async def offboarding_prepare_export_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingRead]:
    data = await advance_export_preparation(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/offboarding/export/run", response_model=ApiResponse[OffboardingRead])
async def offboarding_run_export_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingRead]:
    data = await run_offboarding_export(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/offboarding/retention", response_model=ApiResponse[OffboardingRead])
async def offboarding_retention_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingRead]:
    data = await enter_retention_period(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/offboarding/archival/start", response_model=ApiResponse[OffboardingRead])
async def offboarding_archival_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[OffboardingRead]:
    data = await start_archival(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/offboarding/archival", response_model=ApiResponse[dict])
async def archival_status_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await get_archival_status(scope, to_object_id(tenant_id, "tenant id"))
    return success_response(data, request_id=get_request_id())


@router.get("/retention/policies", response_model=ApiResponse[RetentionPolicyRead])
async def global_retention_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[RetentionPolicyRead]:
    data = await get_retention_policy(scope, None)
    return success_response(data, request_id=get_request_id())


@router.patch("/retention/policies", response_model=ApiResponse[RetentionPolicyRead])
async def update_global_retention_route(
    payload: RetentionPolicyUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[RetentionPolicyRead]:
    data = await update_retention_policy(scope, None, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/retention/policy", response_model=ApiResponse[RetentionPolicyRead])
async def tenant_retention_route(
    tenant_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[RetentionPolicyRead]:
    data = await get_retention_policy(scope, tenant_id)
    return success_response(data, request_id=get_request_id())


@router.patch("/tenants/{tenant_id}/retention/policy", response_model=ApiResponse[RetentionPolicyRead])
async def update_tenant_retention_route(
    tenant_id: str,
    payload: RetentionPolicyUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[RetentionPolicyRead]:
    data = await update_retention_policy(scope, tenant_id, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/legal-holds", response_model=ApiResponse[dict])
async def legal_hold_route(
    tenant_id: str,
    payload: LegalHoldCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await create_legal_hold(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/deletion-requests", response_model=ApiResponse[dict])
async def deletion_request_route(
    tenant_id: str,
    payload: DeletionRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await create_deletion_request(scope, to_object_id(tenant_id, "tenant id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/deletion-requests/{request_id}/approve", response_model=ApiResponse[dict])
async def approve_deletion_route(
    tenant_id: str,
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await approve_deletion(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
    )
    return success_response(data, request_id=get_request_id())


@router.post("/tenants/{tenant_id}/deletion-requests/{request_id}/execute", response_model=ApiResponse[dict])
async def execute_deletion_route(
    tenant_id: str,
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await execute_deletion(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
    )
    return success_response(data, request_id=get_request_id())


@router.get("/tenants/{tenant_id}/deletion-requests/{request_id}/manifest", response_model=ApiResponse[dict])
async def deletion_manifest_route(
    tenant_id: str,
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await get_deletion_manifest(
        scope,
        to_object_id(tenant_id, "tenant id"),
        to_object_id(request_id, "request id"),
    )
    return success_response(data, request_id=get_request_id())
