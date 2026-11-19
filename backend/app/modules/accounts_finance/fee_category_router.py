"""Fee category routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.fee_category_service import get_fee_category, list_fee_categories, upsert_fee_category
from app.modules.accounts_finance.schemas import FeeCategoryRead, FeeCategoryUpsert
from app.modules.auth.models import User

router = APIRouter(prefix="/fee-categories", tags=["accounts-finance-fee-categories"])


@router.put("", response_model=ApiResponse[FeeCategoryRead])
async def fee_category_upsert_route(
    payload: FeeCategoryUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[FeeCategoryRead]:
    return success_response(await upsert_fee_category(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[FeeCategoryRead]])
async def fee_category_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    active_only: Annotated[bool, Query()] = False,
) -> ApiResponse[Page[FeeCategoryRead]]:
    return success_response(await list_fee_categories(scope, pagination, active_only=active_only), request_id=get_request_id())


@router.get("/{fee_code}", response_model=ApiResponse[FeeCategoryRead])
async def fee_category_get_route(
    fee_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[FeeCategoryRead]:
    return success_response(await get_fee_category(scope, fee_code), request_id=get_request_id())