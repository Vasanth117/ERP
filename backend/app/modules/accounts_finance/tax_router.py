"""Tax and regulatory reporting API."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.tax_service import (
    approve_regulatory_report,
    approve_tax_adjustment,
    export_tax_register,
    prepare_regulatory_report,
    record_regulatory_filing,
    request_tax_adjustment,
    sync_tax_from_sources,
    tax_overview,
    upsert_tax_config_reference,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/tax", tags=["accounts-finance-tax"])


class TaxConfigInput(BaseModel):
    tax_category: str
    transaction_type: str
    component_code: str
    effective_from: date
    tax_treatment: str | None = None
    registration_ref: str | None = None


class TaxAdjustmentInput(BaseModel):
    tax_record_id: str
    adjustment_type: str
    amount: float
    reason: str = Field(min_length=3)


class RegulatoryReportInput(BaseModel):
    period_start: date
    period_end: date
    report_type: str | None = None
    financial_year_id: str | None = None


class FilingRecordInput(BaseModel):
    external_acknowledgment: str = Field(min_length=3)
    filing_type: str | None = None
    actual_filing_date: date | None = None
    note: str | None = None


@router.get("/overview")
async def tax_overview_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)]) -> ApiResponse[dict]:
    return success_response(await tax_overview(scope), request_id=get_request_id())


@router.put("/config-references")
async def tax_config_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: TaxConfigInput,
) -> ApiResponse[dict]:
    return success_response(await upsert_tax_config_reference(scope, body.model_dump()), request_id=get_request_id())


@router.post("/sync-transactions")
async def sync_tax_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    date_from: Annotated[date, Query()],
    date_to: Annotated[date, Query()],
) -> ApiResponse[dict]:
    return success_response(await sync_tax_from_sources(scope, date_from=date_from, date_to=date_to), request_id=get_request_id())


@router.get("/register")
async def tax_register_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> ApiResponse[list]:
    return success_response(await export_tax_register(scope, date_from=date_from, date_to=date_to), request_id=get_request_id())


@router.post("/adjustments")
async def tax_adjustment_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: TaxAdjustmentInput,
) -> ApiResponse[dict]:
    return success_response(await request_tax_adjustment(scope, body.model_dump()), request_id=get_request_id())


@router.post("/adjustments/{adjustment_id}/approve")
async def approve_adjustment_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    adjustment_id: str,
) -> ApiResponse[dict]:
    return success_response(await approve_tax_adjustment(scope, adjustment_id), request_id=get_request_id())


@router.post("/regulatory-reports")
async def prepare_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: RegulatoryReportInput,
) -> ApiResponse[dict]:
    return success_response(await prepare_regulatory_report(scope, body.model_dump()), request_id=get_request_id())


@router.post("/regulatory-reports/{report_id}/approve")
async def approve_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    report_id: str,
) -> ApiResponse[dict]:
    return success_response(await approve_regulatory_report(scope, report_id), request_id=get_request_id())


@router.post("/regulatory-reports/{report_id}/filing")
async def record_filing_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    report_id: str,
    body: FilingRecordInput,
) -> ApiResponse[dict]:
    return success_response(await record_regulatory_filing(scope, report_id, body.model_dump()), request_id=get_request_id())