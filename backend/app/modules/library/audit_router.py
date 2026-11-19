"""Library audit history and inventory-control routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.audit_enums import LibraryAuditDomain, StockAdjustmentRequestStatus, StockDiscrepancyStatus
from app.modules.library.audit_schemas import (
    LibraryAuditEventRead,
    LibraryAuditReportRead,
    LibraryAuditSearch,
    LibraryAuditTimelineItem,
    StockAdjustmentDecision,
    StockAdjustmentPropose,
    StockAdjustmentRequestRead,
    StockDiscrepancyRead,
    StockDiscrepancyResolve,
)
from app.modules.library.audit_service import (
    generate_audit_report,
    resource_timeline,
    search_audit_events,
    search_institution_library_audit,
)
from app.modules.library.deps import librarian_user
from app.modules.library.inventory_control_service import (
    approve_stock_adjustment,
    list_discrepancies,
    list_stock_adjustment_requests,
    propose_stock_adjustment,
    reject_stock_adjustment,
    resolve_discrepancy,
)

router = APIRouter(prefix="/audit", tags=["library-audit"])


@router.get("/events", response_model=ApiResponse[Page[LibraryAuditEventRead]])
async def audit_events_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    domain: Annotated[LibraryAuditDomain | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
    resource_id: Annotated[str | None, Query()] = None,
    actor_id: Annotated[str | None, Query()] = None,
    action_prefix: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[LibraryAuditEventRead]]:
    filters = LibraryAuditSearch(
        domain=domain,
        branch_code=branch_code,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        action_prefix=action_prefix,
    )
    return success_response(await search_audit_events(scope, pagination, filters), request_id=get_request_id())


@router.get("/institution-logs", response_model=ApiResponse[Page[dict]])
async def institution_library_audit_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    module: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[dict]]:
    return success_response(
        await search_institution_library_audit(scope, pagination, branch_code=branch_code, module=module),
        request_id=get_request_id(),
    )


@router.get("/resources/{resource_type}/{resource_id}", response_model=ApiResponse[Page[LibraryAuditTimelineItem]])
async def resource_timeline_route(
    resource_type: str,
    resource_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[LibraryAuditTimelineItem]]:
    return success_response(
        await resource_timeline(scope, resource_type, resource_id, pagination),
        request_id=get_request_id(),
    )


@router.get("/reports/summary", response_model=ApiResponse[LibraryAuditReportRead])
async def audit_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    domain: Annotated[list[LibraryAuditDomain] | None, Query()] = None,
) -> ApiResponse[LibraryAuditReportRead]:
    return success_response(await generate_audit_report(scope, branch_code=branch_code, domains=domain), request_id=get_request_id())


@router.get("/inventory/discrepancies", response_model=ApiResponse[Page[StockDiscrepancyRead]])
async def list_discrepancies_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    status: Annotated[StockDiscrepancyStatus | None, Query()] = None,
    verification_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[StockDiscrepancyRead]]:
    return success_response(
        await list_discrepancies(scope, pagination, branch_code=branch_code, status=status, verification_id=verification_id),
        request_id=get_request_id(),
    )


@router.post("/inventory/discrepancies/{discrepancy_id}/resolve", response_model=ApiResponse[StockDiscrepancyRead])
async def resolve_discrepancy_route(
    discrepancy_id: str,
    payload: StockDiscrepancyResolve,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[StockDiscrepancyRead]:
    return success_response(await resolve_discrepancy(scope, discrepancy_id, payload), request_id=get_request_id())


@router.post(
    "/inventory/adjustment-requests",
    response_model=ApiResponse[StockAdjustmentRequestRead],
    status_code=status.HTTP_201_CREATED,
)
async def propose_adjustment_route(
    payload: StockAdjustmentPropose,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[StockAdjustmentRequestRead]:
    return success_response(await propose_stock_adjustment(scope, payload), request_id=get_request_id())


@router.get("/inventory/adjustment-requests", response_model=ApiResponse[Page[StockAdjustmentRequestRead]])
async def list_adjustment_requests_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[StockAdjustmentRequestStatus | None, Query()] = None,
) -> ApiResponse[Page[StockAdjustmentRequestRead]]:
    return success_response(await list_stock_adjustment_requests(scope, pagination, status=status), request_id=get_request_id())


@router.post("/inventory/adjustment-requests/{request_id}/approve", response_model=ApiResponse[StockAdjustmentRequestRead])
async def approve_adjustment_route(
    request_id: str,
    payload: StockAdjustmentDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[StockAdjustmentRequestRead]:
    return success_response(await approve_stock_adjustment(scope, request_id, payload), request_id=get_request_id())


@router.post("/inventory/adjustment-requests/{request_id}/reject", response_model=ApiResponse[StockAdjustmentRequestRead])
async def reject_adjustment_route(
    request_id: str,
    payload: StockAdjustmentDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[StockAdjustmentRequestRead]:
    return success_response(await reject_stock_adjustment(scope, request_id, payload), request_id=get_request_id())