"""Library settings and policy routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.settings_schemas import (
    BorrowingRuleCreate,
    BorrowingRuleRead,
    BorrowingRuleUpdate,
    EffectivePolicyPreview,
    PolicyHistoryEntry,
)
from app.modules.library.settings_service import (
    activate_borrowing_rule,
    create_borrowing_rule,
    get_borrowing_rule,
    policy_change_history,
    preview_effective_policy,
    retire_borrowing_rule,
    search_borrowing_rules,
    update_borrowing_rule,
)

router = APIRouter(prefix="/settings", tags=["library-settings"])


@router.post("/policies/borrowing", response_model=ApiResponse[BorrowingRuleRead], status_code=status.HTTP_201_CREATED)
async def create_policy_route(
    payload: BorrowingRuleCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[BorrowingRuleRead]:
    return success_response(await create_borrowing_rule(scope, payload), request_id=get_request_id())


@router.get("/policies/borrowing", response_model=ApiResponse[Page[BorrowingRuleRead]])
async def search_policies_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[str | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[BorrowingRuleRead]]:
    return success_response(await search_borrowing_rules(scope, pagination, status=status, branch_code=branch_code), request_id=get_request_id())


@router.get("/policies/borrowing/preview", response_model=ApiResponse[EffectivePolicyPreview])
async def preview_policy_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    member_category: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
) -> ApiResponse[EffectivePolicyPreview]:
    return success_response(
        await preview_effective_policy(scope, branch_code=branch_code, member_category=member_category, resource_type=resource_type),
        request_id=get_request_id(),
    )


@router.get("/policies/borrowing/{policy_id}", response_model=ApiResponse[BorrowingRuleRead])
async def get_policy_route(
    policy_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[BorrowingRuleRead]:
    return success_response(await get_borrowing_rule(scope, policy_id), request_id=get_request_id())


@router.patch("/policies/borrowing/{policy_id}", response_model=ApiResponse[BorrowingRuleRead])
async def update_policy_route(
    policy_id: str,
    payload: BorrowingRuleUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[BorrowingRuleRead]:
    return success_response(await update_borrowing_rule(scope, policy_id, payload), request_id=get_request_id())


@router.post("/policies/borrowing/{policy_id}/activate", response_model=ApiResponse[BorrowingRuleRead])
async def activate_policy_route(
    policy_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[BorrowingRuleRead]:
    return success_response(await activate_borrowing_rule(scope, policy_id), request_id=get_request_id())


@router.post("/policies/borrowing/{policy_id}/retire", response_model=ApiResponse[BorrowingRuleRead])
async def retire_policy_route(
    policy_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[BorrowingRuleRead]:
    return success_response(await retire_borrowing_rule(scope, policy_id), request_id=get_request_id())


@router.get("/policies/borrowing/{policy_id}/history", response_model=ApiResponse[Page[PolicyHistoryEntry]])
async def policy_history_route(
    policy_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[PolicyHistoryEntry]]:
    return success_response(await policy_change_history(scope, policy_id, pagination), request_id=get_request_id())