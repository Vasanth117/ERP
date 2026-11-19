"""Fee structure routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.enums import FeeStructureLifecycleStatus
from app.modules.accounts_finance.fee_structure_service import (
    create_fee_structure,
    get_fee_structure,
    list_fee_structures,
    revise_fee_structure,
    transition_fee_structure,
)
from app.modules.accounts_finance.schemas import (
    FeeStructureCreate,
    FeeStructureRead,
    FeeStructureRevision,
    FeeStructureTransition,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/fee-structures", tags=["accounts-finance-fee-structures"])


@router.post("", response_model=ApiResponse[FeeStructureRead])
async def fee_structure_create_route(
    payload: FeeStructureCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[FeeStructureRead]:
    return success_response(await create_fee_structure(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[FeeStructureRead]])
async def fee_structure_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[FeeStructureLifecycleStatus | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[FeeStructureRead]]:
    return success_response(
        await list_fee_structures(scope, pagination, status=status, programme_code=programme_code),
        request_id=get_request_id(),
    )


@router.get("/{structure_id}", response_model=ApiResponse[FeeStructureRead])
async def fee_structure_get_route(
    structure_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[FeeStructureRead]:
    return success_response(await get_fee_structure(scope, structure_id), request_id=get_request_id())


@router.post("/{structure_id}/transitions", response_model=ApiResponse[FeeStructureRead])
async def fee_structure_transition_route(
    structure_id: str,
    payload: FeeStructureTransition,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[FeeStructureRead]:
    return success_response(await transition_fee_structure(scope, structure_id, payload), request_id=get_request_id())


@router.post("/{structure_id}/revisions", response_model=ApiResponse[FeeStructureRead])
async def fee_structure_revision_route(
    structure_id: str,
    payload: FeeStructureRevision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[FeeStructureRead]:
    return success_response(await revise_fee_structure(scope, structure_id, payload), request_id=get_request_id())