"""Platform operations HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import AccessScope, get_access_scope, pagination_params
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.platform_ops.health_service import (
    get_background_job_summary,
    get_dependency_health,
    get_platform_health,
    get_queue_statistics,
    get_service_health,
    get_worker_statistics,
    list_failed_jobs,
    retry_background_job,
)
from app.modules.platform_ops.incident_service import (
    add_incident_note,
    assign_incident,
    create_incident,
    get_incident,
    get_incident_history,
    list_incidents,
    update_incident_status,
)
from app.modules.platform_ops.schemas import (
    IncidentAssignRequest,
    IncidentCreate,
    IncidentNote,
    IncidentRead,
    IncidentStatusUpdate,
    PlatformHealthOverview,
)

router = APIRouter(prefix="/operations", tags=["platform-operations"])


@router.get("/health", response_model=ApiResponse[PlatformHealthOverview])
async def platform_health_route(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> ApiResponse[PlatformHealthOverview]:
    data = await get_platform_health(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/health/services", response_model=ApiResponse[dict])
async def service_health_route(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> ApiResponse[dict]:
    data = await get_service_health(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/health/dependencies", response_model=ApiResponse[list])
async def dependency_health_route(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> ApiResponse[list]:
    data = await get_dependency_health(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/queues", response_model=ApiResponse[dict])
async def queue_stats_route(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> ApiResponse[dict]:
    data = await get_queue_statistics(scope)
    return success_response(data.model_dump(), request_id=get_request_id())


@router.get("/workers", response_model=ApiResponse[dict])
async def worker_stats_route(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> ApiResponse[dict]:
    data = await get_worker_statistics(scope)
    return success_response(data.model_dump(), request_id=get_request_id())


@router.get("/jobs/summary", response_model=ApiResponse[dict])
async def job_summary_route(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> ApiResponse[dict]:
    data = await get_background_job_summary(scope)
    return success_response(data.model_dump(), request_id=get_request_id())


@router.get("/jobs/failed", response_model=ApiResponse[list])
async def failed_jobs_route(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> ApiResponse[list]:
    data = await list_failed_jobs(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/jobs/{registry_id}/retry", response_model=ApiResponse[dict])
async def retry_job_route(
    registry_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    data = await retry_background_job(scope, registry_id)
    return success_response(data, request_id=get_request_id())


@router.post("/incidents", response_model=ApiResponse[IncidentRead])
async def create_incident_route(
    payload: IncidentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[IncidentRead]:
    data = await create_incident(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/incidents", response_model=ApiResponse[Page[IncidentRead]])
async def list_incidents_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[IncidentRead]]:
    data = await list_incidents(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/incidents/{incident_id}", response_model=ApiResponse[IncidentRead])
async def get_incident_route(
    incident_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[IncidentRead]:
    data = await get_incident(scope, to_object_id(incident_id, "incident id"))
    return success_response(data, request_id=get_request_id())


@router.post("/incidents/{incident_id}/assign", response_model=ApiResponse[IncidentRead])
async def assign_incident_route(
    incident_id: str,
    payload: IncidentAssignRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[IncidentRead]:
    data = await assign_incident(scope, to_object_id(incident_id, "incident id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/incidents/{incident_id}/status", response_model=ApiResponse[IncidentRead])
async def update_incident_status_route(
    incident_id: str,
    payload: IncidentStatusUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[IncidentRead]:
    data = await update_incident_status(scope, to_object_id(incident_id, "incident id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/incidents/{incident_id}/notes", response_model=ApiResponse[IncidentRead])
async def add_incident_note_route(
    incident_id: str,
    payload: IncidentNote,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[IncidentRead]:
    data = await add_incident_note(scope, to_object_id(incident_id, "incident id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/incidents/{incident_id}/history", response_model=ApiResponse[list])
async def incident_history_route(
    incident_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list]:
    data = await get_incident_history(scope, to_object_id(incident_id, "incident id"))
    return success_response(data, request_id=get_request_id())
