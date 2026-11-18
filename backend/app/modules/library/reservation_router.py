"""Reservation queue routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.library_enums import LibraryReservationStatus
from app.modules.library.reservation_schemas import (
    ReservationAllocateRequest,
    ReservationCancelRequest,
    ReservationCreateRequest,
    ReservationHistoryEntry,
    ReservationPolicyUpsert,
    ReservationRead,
)
from app.modules.library.reservation_service import (
    cancel_reservation,
    create_reservation,
    fulfill_reservation_record,
    get_reservation,
    manual_allocate,
    queue_for_book,
    reservation_history,
    search_reservations,
    upsert_reservation_policy,
)

router = APIRouter(prefix="/reservations", tags=["library-reservations"])


@router.post("", response_model=ApiResponse[ReservationRead], status_code=status.HTTP_201_CREATED)
async def create_reservation_route(
    payload: ReservationCreateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[ReservationRead]:
    return success_response(await create_reservation(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[ReservationRead]])
async def search_reservations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    member_user_id: Annotated[str | None, Query()] = None,
    book_id: Annotated[str | None, Query()] = None,
    status: Annotated[LibraryReservationStatus | None, Query()] = None,
) -> ApiResponse[Page[ReservationRead]]:
    return success_response(
        await search_reservations(
            scope,
            pagination,
            branch_code=branch_code,
            member_user_id=member_user_id,
            book_id=book_id,
            status=status,
        ),
        request_id=get_request_id(),
    )


@router.get("/queue/{book_id}", response_model=ApiResponse[list[ReservationRead]])
async def reservation_queue_route(
    book_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[ReservationRead]]:
    return success_response(await queue_for_book(scope, book_id, branch_code=branch_code), request_id=get_request_id())


@router.post("/policy", response_model=ApiResponse[dict])
async def reservation_policy_route(
    payload: ReservationPolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_reservation_policy(scope, payload), request_id=get_request_id())


@router.get("/{reservation_id}", response_model=ApiResponse[ReservationRead])
async def get_reservation_route(
    reservation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[ReservationRead]:
    return success_response(await get_reservation(scope, reservation_id), request_id=get_request_id())


@router.post("/{reservation_id}/cancel", response_model=ApiResponse[ReservationRead])
async def cancel_reservation_route(
    reservation_id: str,
    payload: ReservationCancelRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[ReservationRead]:
    return success_response(await cancel_reservation(scope, reservation_id, payload), request_id=get_request_id())


@router.post("/{reservation_id}/allocate", response_model=ApiResponse[ReservationRead])
async def allocate_reservation_route(
    reservation_id: str,
    payload: ReservationAllocateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[ReservationRead]:
    return success_response(await manual_allocate(scope, reservation_id, payload), request_id=get_request_id())


@router.post("/{reservation_id}/fulfill", response_model=ApiResponse[ReservationRead])
async def fulfill_reservation_route(
    reservation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[ReservationRead]:
    return success_response(await fulfill_reservation_record(scope, reservation_id), request_id=get_request_id())


@router.get("/{reservation_id}/history", response_model=ApiResponse[Page[ReservationHistoryEntry]])
async def reservation_history_route(
    reservation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ReservationHistoryEntry]]:
    return success_response(await reservation_history(scope, reservation_id, pagination), request_id=get_request_id())