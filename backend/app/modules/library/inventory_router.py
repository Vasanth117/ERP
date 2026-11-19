"""Book copy inventory routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.inventory_schemas import (
    CopyDuplicateMatch,
    CopyInventoryRead,
    CopyRegisterRequest,
    CopyTransferRequest,
    CopyUpdateRequest,
    InventoryAdjustmentRequest,
    InventoryHistoryRead,
    MissingCopySummary,
    StockVerificationCreate,
    StockVerificationRead,
    StockVerificationScan,
)
from app.modules.library.inventory_enums import StockVerificationStatus
from app.modules.library.inventory_service import (
    apply_adjustment,
    complete_stock_verification,
    copy_inventory_history,
    find_duplicates,
    get_copy,
    list_copies,
    list_missing_copies,
    list_stock_verifications,
    register_copy,
    scan_stock_verification,
    start_stock_verification,
    transfer_copy,
    update_copy,
)
from app.modules.library.library_enums import LibraryCopyStatus

router = APIRouter(prefix="/inventory", tags=["library-inventory"])


@router.post("/copies", response_model=ApiResponse[CopyInventoryRead], status_code=status.HTTP_201_CREATED)
async def register_copy_route(
    payload: CopyRegisterRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CopyInventoryRead]:
    return success_response(await register_copy(scope, payload), request_id=get_request_id())


@router.get("/copies", response_model=ApiResponse[Page[CopyInventoryRead]])
async def list_copies_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    book_id: Annotated[str | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
    status: Annotated[LibraryCopyStatus | None, Query()] = None,
) -> ApiResponse[Page[CopyInventoryRead]]:
    return success_response(
        await list_copies(scope, pagination, book_id=book_id, branch_code=branch_code, status=status),
        request_id=get_request_id(),
    )


@router.get("/copies/{copy_id}", response_model=ApiResponse[CopyInventoryRead])
async def get_copy_route(
    copy_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CopyInventoryRead]:
    return success_response(await get_copy(scope, copy_id), request_id=get_request_id())


@router.patch("/copies/{copy_id}", response_model=ApiResponse[CopyInventoryRead])
async def update_copy_route(
    copy_id: str,
    payload: CopyUpdateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CopyInventoryRead]:
    return success_response(await update_copy(scope, copy_id, payload), request_id=get_request_id())


@router.post("/copies/{copy_id}/transfer", response_model=ApiResponse[CopyInventoryRead])
async def transfer_copy_route(
    copy_id: str,
    payload: CopyTransferRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CopyInventoryRead]:
    return success_response(await transfer_copy(scope, copy_id, payload), request_id=get_request_id())


@router.post("/adjustments", response_model=ApiResponse[CopyInventoryRead])
async def adjustment_route(
    payload: InventoryAdjustmentRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CopyInventoryRead]:
    return success_response(await apply_adjustment(scope, payload), request_id=get_request_id())


@router.get("/duplicates", response_model=ApiResponse[list[CopyDuplicateMatch]])
async def duplicates_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[list[CopyDuplicateMatch]]:
    return success_response(await find_duplicates(scope), request_id=get_request_id())


@router.get("/missing", response_model=ApiResponse[list[MissingCopySummary]])
async def missing_copies_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[MissingCopySummary]]:
    return success_response(await list_missing_copies(scope, branch_code=branch_code), request_id=get_request_id())


@router.get("/verifications", response_model=ApiResponse[Page[StockVerificationRead]])
async def list_verifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    status: Annotated[StockVerificationStatus | None, Query()] = None,
) -> ApiResponse[Page[StockVerificationRead]]:
    return success_response(
        await list_stock_verifications(scope, pagination, branch_code=branch_code, status=status),
        request_id=get_request_id(),
    )


@router.post("/verifications", response_model=ApiResponse[StockVerificationRead], status_code=status.HTTP_201_CREATED)
async def start_verification_route(
    payload: StockVerificationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[StockVerificationRead]:
    return success_response(await start_stock_verification(scope, payload), request_id=get_request_id())


@router.post("/verifications/{verification_id}/scan", response_model=ApiResponse[StockVerificationRead])
async def scan_verification_route(
    verification_id: str,
    payload: StockVerificationScan,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[StockVerificationRead]:
    return success_response(await scan_stock_verification(scope, verification_id, payload), request_id=get_request_id())


@router.post("/verifications/{verification_id}/complete", response_model=ApiResponse[StockVerificationRead])
async def complete_verification_route(
    verification_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[StockVerificationRead]:
    return success_response(await complete_stock_verification(scope, verification_id), request_id=get_request_id())


@router.get("/copies/{copy_id}/history", response_model=ApiResponse[Page[InventoryHistoryRead]])
async def copy_history_route(
    copy_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[InventoryHistoryRead]]:
    return success_response(await copy_inventory_history(scope, copy_id, pagination), request_id=get_request_id())