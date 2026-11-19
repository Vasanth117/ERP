"""Library fines routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.fine_enums import LibraryFineApprovalType
from app.modules.library.fine_schemas import (
    DamageReportCreate,
    FineApprovalDecision,
    FineHistoryEntry,
    FinePaymentVerifyRequest,
    FinePolicyUpsert,
    FineRead,
    FineWaiverRequest,
)
from app.modules.library.fine_service import (
    assess_overdue_batch,
    create_damage_report,
    create_finance_demand,
    decide_approval,
    fine_history,
    get_fine,
    request_waiver,
    search_fines,
    upsert_fine_policy,
    verify_fine_payment,
)
from app.modules.library.library_enums import LibraryFineStatus

router = APIRouter(prefix="/fines", tags=["library-fines"])


@router.post("/policy", response_model=ApiResponse[dict])
async def fine_policy_route(
    payload: FinePolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_fine_policy(scope, payload), request_id=get_request_id())


@router.post("/assess-overdue", response_model=ApiResponse[dict])
async def assess_overdue_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await assess_overdue_batch(scope, branch_code=branch_code), request_id=get_request_id())


@router.post("/reports", response_model=ApiResponse[FineRead], status_code=status.HTTP_201_CREATED)
async def damage_report_route(
    payload: DamageReportCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[FineRead]:
    return success_response(await create_damage_report(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[FineRead]])
async def search_fines_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    member_user_id: Annotated[str | None, Query()] = None,
    status: Annotated[LibraryFineStatus | None, Query()] = None,
) -> ApiResponse[Page[FineRead]]:
    return success_response(
        await search_fines(scope, pagination, branch_code=branch_code, member_user_id=member_user_id, status=status),
        request_id=get_request_id(),
    )


@router.get("/{fine_id}", response_model=ApiResponse[FineRead])
async def get_fine_route(
    fine_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[FineRead]:
    return success_response(await get_fine(scope, fine_id), request_id=get_request_id())


@router.post("/{fine_id}/demand", response_model=ApiResponse[FineRead])
async def create_demand_route(
    fine_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[FineRead]:
    return success_response(await create_finance_demand(scope, fine_id), request_id=get_request_id())


@router.post("/{fine_id}/verify-payment", response_model=ApiResponse[FineRead])
async def verify_payment_route(
    fine_id: str,
    payload: FinePaymentVerifyRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[FineRead]:
    return success_response(await verify_fine_payment(scope, fine_id, payload), request_id=get_request_id())


@router.post("/{fine_id}/waiver-request", response_model=ApiResponse[FineRead])
async def waiver_request_route(
    fine_id: str,
    payload: FineWaiverRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[FineRead]:
    return success_response(
        await request_waiver(scope, fine_id, payload, approval_type=LibraryFineApprovalType.WAIVER),
        request_id=get_request_id(),
    )


@router.post("/{fine_id}/writeoff-request", response_model=ApiResponse[FineRead])
async def writeoff_request_route(
    fine_id: str,
    payload: FineWaiverRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[FineRead]:
    return success_response(
        await request_waiver(scope, fine_id, payload, approval_type=LibraryFineApprovalType.WRITEOFF),
        request_id=get_request_id(),
    )


@router.post("/{fine_id}/approval", response_model=ApiResponse[FineRead])
async def approval_decision_route(
    fine_id: str,
    payload: FineApprovalDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[FineRead]:
    return success_response(await decide_approval(scope, fine_id, payload), request_id=get_request_id())


@router.get("/{fine_id}/history", response_model=ApiResponse[Page[FineHistoryEntry]])
async def fine_history_route(
    fine_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[FineHistoryEntry]]:
    return success_response(await fine_history(scope, fine_id, pagination), request_id=get_request_id())