"""Library member management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.member_enums import LibraryMemberCategory, LibraryMemberStatus
from app.modules.library.member_schemas import (
    MemberBorrowingSummary,
    MemberHistoryEntry,
    MemberRead,
    MemberRegisterRequest,
    MemberSuspendRequest,
    MemberUpdateRequest,
)
from app.modules.library.member_service import (
    get_member_by_number,
    get_member_by_user,
    member_borrowing_summary,
    member_history,
    reactivate_member,
    register_member,
    search_members,
    suspend_member,
    update_member,
)

router = APIRouter(prefix="/members", tags=["library-members"])


@router.post("", response_model=ApiResponse[MemberRead], status_code=status.HTTP_201_CREATED)
async def register_member_route(
    payload: MemberRegisterRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[MemberRead]:
    return success_response(await register_member(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[MemberRead]])
async def search_members_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    q: Annotated[str | None, Query(description="Search name, email, membership number")] = None,
    category: Annotated[LibraryMemberCategory | None, Query()] = None,
    status: Annotated[LibraryMemberStatus | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
    eligible: Annotated[bool | None, Query()] = None,
) -> ApiResponse[Page[MemberRead]]:
    return success_response(
        await search_members(
            scope,
            pagination,
            q=q,
            category=category,
            status=status,
            branch_code=branch_code,
            eligible=eligible,
        ),
        request_id=get_request_id(),
    )


@router.get("/by-number/{membership_number}", response_model=ApiResponse[MemberRead])
async def get_member_by_number_route(
    membership_number: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[MemberRead]:
    return success_response(await get_member_by_number(scope, membership_number), request_id=get_request_id())


@router.get("/by-user/{member_user_id}", response_model=ApiResponse[MemberRead])
async def get_member_by_user_route(
    member_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[MemberRead]:
    return success_response(await get_member_by_user(scope, member_user_id), request_id=get_request_id())


@router.patch("/{membership_number}", response_model=ApiResponse[MemberRead])
async def update_member_route(
    membership_number: str,
    payload: MemberUpdateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[MemberRead]:
    return success_response(await update_member(scope, membership_number, payload), request_id=get_request_id())


@router.post("/{membership_number}/suspend", response_model=ApiResponse[MemberRead])
async def suspend_member_route(
    membership_number: str,
    payload: MemberSuspendRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[MemberRead]:
    return success_response(await suspend_member(scope, membership_number, payload), request_id=get_request_id())


@router.post("/{membership_number}/reactivate", response_model=ApiResponse[MemberRead])
async def reactivate_member_route(
    membership_number: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[MemberRead]:
    return success_response(await reactivate_member(scope, membership_number), request_id=get_request_id())


@router.get("/{membership_number}/borrowing-summary", response_model=ApiResponse[MemberBorrowingSummary])
async def borrowing_summary_route(
    membership_number: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[MemberBorrowingSummary]:
    return success_response(await member_borrowing_summary(scope, membership_number), request_id=get_request_id())


@router.get("/{membership_number}/history", response_model=ApiResponse[Page[MemberHistoryEntry]])
async def member_history_route(
    membership_number: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[MemberHistoryEntry]]:
    return success_response(await member_history(scope, membership_number, pagination), request_id=get_request_id())