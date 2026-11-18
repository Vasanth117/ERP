"""Circulation issue / return / renew routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.circulation_schemas import CirculationHistoryEntry, CirculationRead, IssueLoanRequest, ReturnLoanRequest
from app.modules.library.circulation_service import get_loan, issue_loan, loan_history, renew_loan, return_loan, search_loans
from app.modules.library.deps import librarian_user
from app.modules.library.library_enums import LibraryCirculationStatus

router = APIRouter(prefix="/circulation", tags=["library-circulation"])


@router.post("/issue", response_model=ApiResponse[CirculationRead], status_code=status.HTTP_201_CREATED)
async def issue_loan_route(
    payload: IssueLoanRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CirculationRead]:
    return success_response(await issue_loan(scope, payload), request_id=get_request_id())


@router.post("/{circulation_id}/return", response_model=ApiResponse[CirculationRead])
async def return_loan_route(
    circulation_id: str,
    payload: ReturnLoanRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CirculationRead]:
    return success_response(await return_loan(scope, circulation_id, payload), request_id=get_request_id())


@router.post("/{circulation_id}/renew", response_model=ApiResponse[CirculationRead])
async def renew_loan_route(
    circulation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CirculationRead]:
    return success_response(await renew_loan(scope, circulation_id), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[CirculationRead]])
async def search_loans_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    member_user_id: Annotated[str | None, Query()] = None,
    status: Annotated[LibraryCirculationStatus | None, Query()] = None,
    copy_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[CirculationRead]]:
    return success_response(
        await search_loans(
            scope,
            pagination,
            branch_code=branch_code,
            member_user_id=member_user_id,
            status=status,
            copy_id=copy_id,
        ),
        request_id=get_request_id(),
    )


@router.get("/{circulation_id}", response_model=ApiResponse[CirculationRead])
async def get_loan_route(
    circulation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CirculationRead]:
    return success_response(await get_loan(scope, circulation_id), request_id=get_request_id())


@router.get("/{circulation_id}/history", response_model=ApiResponse[Page[CirculationHistoryEntry]])
async def loan_history_route(
    circulation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[CirculationHistoryEntry]]:
    return success_response(await loan_history(scope, circulation_id, pagination), request_id=get_request_id())