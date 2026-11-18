"""Library acquisition routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.acquisition_schemas import (
    AcquisitionApprovalDecision,
    AcquisitionCreateRequest,
    AcquisitionHistoryEntry,
    AcquisitionRead,
    CatalogueLinkRequest,
    ProcurementSyncRequest,
    QuotationCreateRequest,
    ReceiptRecordRequest,
)
from app.modules.library.acquisition_service import (
    acquisition_history,
    add_quotation,
    create_acquisition,
    decide_acquisition_approval,
    get_acquisition,
    link_catalogue,
    record_receipt,
    request_inventory_registration,
    search_acquisitions,
    select_quotation,
    submit_acquisition,
    sync_procurement_refs,
)

router = APIRouter(prefix="/acquisitions", tags=["library-acquisitions"])


@router.post("", response_model=ApiResponse[AcquisitionRead], status_code=status.HTTP_201_CREATED)
async def create_acquisition_route(
    payload: AcquisitionCreateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[AcquisitionRead]:
    return success_response(await create_acquisition(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[AcquisitionRead]])
async def search_acquisitions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[AcquisitionRead]]:
    return success_response(await search_acquisitions(scope, pagination, branch_code=branch_code, status=status), request_id=get_request_id())


@router.get("/{acquisition_id}", response_model=ApiResponse[AcquisitionRead])
async def get_acquisition_route(
    acquisition_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[AcquisitionRead]:
    return success_response(await get_acquisition(scope, acquisition_id), request_id=get_request_id())


@router.post("/{acquisition_id}/submit", response_model=ApiResponse[AcquisitionRead])
async def submit_acquisition_route(
    acquisition_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[AcquisitionRead]:
    return success_response(await submit_acquisition(scope, acquisition_id), request_id=get_request_id())


@router.post("/{acquisition_id}/approval", response_model=ApiResponse[AcquisitionRead])
async def approval_route(
    acquisition_id: str,
    payload: AcquisitionApprovalDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[AcquisitionRead]:
    return success_response(await decide_acquisition_approval(scope, acquisition_id, payload), request_id=get_request_id())


@router.post("/{acquisition_id}/quotations", response_model=ApiResponse[dict])
async def quotation_route(
    acquisition_id: str,
    payload: QuotationCreateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[dict]:
    return success_response(await add_quotation(scope, acquisition_id, payload), request_id=get_request_id())


@router.post("/{acquisition_id}/quotations/{quotation_id}/select", response_model=ApiResponse[AcquisitionRead])
async def select_quotation_route(
    acquisition_id: str,
    quotation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[AcquisitionRead]:
    return success_response(await select_quotation(scope, acquisition_id, quotation_id), request_id=get_request_id())


@router.post("/{acquisition_id}/procurement", response_model=ApiResponse[AcquisitionRead])
async def procurement_link_route(
    acquisition_id: str,
    payload: ProcurementSyncRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[AcquisitionRead]:
    return success_response(await sync_procurement_refs(scope, acquisition_id, payload), request_id=get_request_id())


@router.post("/{acquisition_id}/receive", response_model=ApiResponse[AcquisitionRead])
async def receive_route(
    acquisition_id: str,
    payload: ReceiptRecordRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[AcquisitionRead]:
    return success_response(await record_receipt(scope, acquisition_id, payload), request_id=get_request_id())


@router.post("/{acquisition_id}/catalogue", response_model=ApiResponse[AcquisitionRead])
async def catalogue_link_route(
    acquisition_id: str,
    payload: CatalogueLinkRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[AcquisitionRead]:
    return success_response(await link_catalogue(scope, acquisition_id, payload), request_id=get_request_id())


@router.post("/{acquisition_id}/inventory-registration", response_model=ApiResponse[dict])
async def inventory_registration_route(
    acquisition_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[dict]:
    return success_response(await request_inventory_registration(scope, acquisition_id), request_id=get_request_id())


@router.get("/{acquisition_id}/history", response_model=ApiResponse[Page[AcquisitionHistoryEntry]])
async def history_route(
    acquisition_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AcquisitionHistoryEntry]]:
    return success_response(await acquisition_history(scope, acquisition_id, pagination), request_id=get_request_id())