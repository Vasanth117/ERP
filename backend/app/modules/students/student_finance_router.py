"""Student finance routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.students.deps import finance_payment_rate_limit, finance_scholarship_rate_limit, student_user
from app.modules.students.student_finance_schemas import (
    ConcessionRead,
    FeeDemandRead,
    FeeStructureRead,
    InstallmentScheduleRead,
    LedgerEntryRead,
    OutstandingDuesRead,
    PaymentHistoryRead,
    PaymentInitiateInput,
    PaymentInitiateRead,
    PaymentStatusRead,
    ReceiptRead,
    RefundStatusRead,
    ScholarshipApplicationInput,
    ScholarshipApplicationRead,
    ScholarshipEligibilityRead,
)
from app.modules.students.student_finance_service import (
    financial_ledger,
    get_fee_demands,
    get_fee_structure,
    get_invoices,
    get_outstanding_dues,
    get_payment_status,
    initiate_payment,
    installment_schedule,
    list_concessions,
    list_refunds,
    list_receipts,
    payment_history,
    payment_reminders,
    refresh_payment_reconciliation,
    scholarship_eligibility,
    scholarship_status,
    submit_scholarship,
    track_receipt_view,
    get_fee_view_preferences,
    update_fee_view_preferences,
)


class FeeViewPreferencesUpdate(BaseModel):
    show_installments: bool

    model_config = {"extra": "forbid"}

student_finance_router = APIRouter()


@student_finance_router.get("/me/finance/fee-structure", response_model=ApiResponse[list[FeeStructureRead]])
async def student_fee_structure_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[FeeStructureRead]]:
    return success_response(await get_fee_structure(scope, user), request_id=get_request_id())


@student_finance_router.get("/me/finance/demands", response_model=ApiResponse[list[FeeDemandRead]])
async def student_fee_demands_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[FeeDemandRead]]:
    return success_response(await get_fee_demands(scope, user), request_id=get_request_id())


@student_finance_router.get("/me/finance/invoices", response_model=ApiResponse[list[dict]])
async def student_fee_invoices_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[dict]]:
    return success_response(await get_invoices(scope, user), request_id=get_request_id())


@student_finance_router.get("/me/finance/outstanding", response_model=ApiResponse[OutstandingDuesRead])
async def student_outstanding_dues_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[OutstandingDuesRead]:
    return success_response(await get_outstanding_dues(scope, user), request_id=get_request_id())


@student_finance_router.post("/me/finance/payments/initiate", response_model=ApiResponse[PaymentInitiateRead])
async def student_payment_initiate_route(
    payload: PaymentInitiateInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(finance_payment_rate_limit)],
) -> ApiResponse[PaymentInitiateRead]:
    return success_response(await initiate_payment(scope, user, payload), request_id=get_request_id())


@student_finance_router.get("/me/finance/payments/history", response_model=ApiResponse[list[PaymentHistoryRead]])
async def student_payment_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[PaymentHistoryRead]]:
    return success_response(await payment_history(scope, user), request_id=get_request_id())


@student_finance_router.get(
    "/me/finance/payments/{transaction_id}/status",
    response_model=ApiResponse[PaymentStatusRead],
)
async def student_payment_status_route(
    transaction_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[PaymentStatusRead]:
    return success_response(await get_payment_status(scope, user, transaction_id), request_id=get_request_id())


@student_finance_router.post(
    "/me/finance/payments/{transaction_id}/refresh",
    response_model=ApiResponse[PaymentStatusRead],
)
async def student_payment_refresh_route(
    transaction_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[PaymentStatusRead]:
    return success_response(await refresh_payment_reconciliation(scope, user, transaction_id), request_id=get_request_id())


@student_finance_router.get("/me/finance/receipts", response_model=ApiResponse[list[ReceiptRead]])
async def student_receipts_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ReceiptRead]]:
    return success_response(await list_receipts(scope, user), request_id=get_request_id())


@student_finance_router.post("/me/finance/receipts/{receipt_id}/viewed", response_model=ApiResponse[dict])
async def student_receipt_viewed_route(
    receipt_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[dict]:
    await track_receipt_view(scope, user, receipt_id)
    return success_response({"receipt_id": receipt_id, "viewed": True}, request_id=get_request_id())


@student_finance_router.get("/me/finance/installments", response_model=ApiResponse[list[InstallmentScheduleRead]])
async def student_installments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[InstallmentScheduleRead]]:
    return success_response(await installment_schedule(scope, user), request_id=get_request_id())


@student_finance_router.get(
    "/me/finance/scholarships/eligibility",
    response_model=ApiResponse[list[ScholarshipEligibilityRead]],
)
async def student_scholarship_eligibility_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ScholarshipEligibilityRead]]:
    return success_response(await scholarship_eligibility(scope, user), request_id=get_request_id())


@student_finance_router.post(
    "/me/finance/scholarships/applications",
    response_model=ApiResponse[ScholarshipApplicationRead],
)
async def student_scholarship_apply_route(
    payload: ScholarshipApplicationInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(finance_scholarship_rate_limit)],
) -> ApiResponse[ScholarshipApplicationRead]:
    return success_response(await submit_scholarship(scope, user, payload), request_id=get_request_id())


@student_finance_router.get(
    "/me/finance/scholarships/applications/{application_id}",
    response_model=ApiResponse[ScholarshipApplicationRead],
)
async def student_scholarship_status_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[ScholarshipApplicationRead]:
    return success_response(await scholarship_status(scope, user, application_id), request_id=get_request_id())


@student_finance_router.get("/me/finance/concessions", response_model=ApiResponse[list[ConcessionRead]])
async def student_concessions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ConcessionRead]]:
    return success_response(await list_concessions(scope, user), request_id=get_request_id())


@student_finance_router.get("/me/finance/refunds", response_model=ApiResponse[list[RefundStatusRead]])
async def student_refunds_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[RefundStatusRead]]:
    return success_response(await list_refunds(scope, user), request_id=get_request_id())


@student_finance_router.get("/me/finance/ledger", response_model=ApiResponse[list[LedgerEntryRead]])
async def student_ledger_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[LedgerEntryRead]]:
    return success_response(await financial_ledger(scope, user), request_id=get_request_id())


@student_finance_router.get("/me/finance/reminders", response_model=ApiResponse[list[dict]])
async def student_payment_reminders_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[dict]]:
    return success_response(await payment_reminders(scope, user), request_id=get_request_id())


@student_finance_router.get("/me/finance/preferences", response_model=ApiResponse[dict])
async def student_fee_preferences_get_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[dict]:
    return success_response(await get_fee_view_preferences(scope, user), request_id=get_request_id())


@student_finance_router.patch("/me/finance/preferences", response_model=ApiResponse[dict])
async def student_fee_preferences_patch_route(
    payload: FeeViewPreferencesUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[dict]:
    return success_response(await update_fee_view_preferences(scope, user, show_installments=payload.show_installments), request_id=get_request_id())
