"""General Ledger REST API."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.coa_service import deactivate_account, list_accounts, seed_default_chart, upsert_account
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.gl_posting_service import reverse_journal
from app.modules.accounts_finance.gl_report_service import account_ledger, balance_sheet, income_expenditure_statement, trial_balance
from app.modules.accounts_finance.journal_service import (
    approve_journal,
    create_manual_journal,
    get_journal,
    list_journals,
    post_journal,
    submit_journal,
)
from app.modules.accounts_finance.mapping_service import (
    activate_mapping_version,
    add_mapping_rule,
    create_mapping_version,
    list_mapping_versions,
    seed_default_mappings,
)
from app.modules.accounts_finance.phase9_models import AccountOpeningBalance, JournalLineInput
from app.modules.accounts_finance.policy import authorize_finance_gl_manage, require_finance_tenant_scope
from app.modules.auth.models import User

router = APIRouter(prefix="/general-ledger", tags=["accounts-finance-gl"])


class AccountInput(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    normal_balance: str
    classification: str | None = None
    parent_account_code: str | None = None
    account_group: str | None = None
    description: str | None = None
    currency: str = "INR"
    active: bool = True


class ManualJournalInput(BaseModel):
    journal_date: date
    narration: str
    lines: list[JournalLineInput]
    financial_period_code: str | None = None
    document_refs: list[str] = Field(default_factory=list)


class MappingRuleInput(BaseModel):
    event_type: str
    debit_account_code: str
    credit_account_code: str
    description: str | None = None


class OpeningBalanceInput(BaseModel):
    financial_year_id: str
    account_code: str
    debit: float = 0
    credit: float = 0
    as_of_date: date


class ReverseJournalInput(BaseModel):
    reason: str = Field(min_length=5)


@router.post("/chart/seed")
async def seed_chart_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)]) -> ApiResponse[dict]:
    return success_response(await seed_default_chart(scope), request_id=get_request_id())


@router.get("/chart/accounts")
async def list_accounts_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)]) -> ApiResponse[list]:
    return success_response(await list_accounts(scope), request_id=get_request_id())


@router.put("/chart/accounts")
async def upsert_account_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: AccountInput,
) -> ApiResponse[dict]:
    return success_response(await upsert_account(scope, body.model_dump()), request_id=get_request_id())


@router.post("/chart/accounts/{account_code}/deactivate")
async def deactivate_account_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    account_code: str,
) -> ApiResponse[dict]:
    return success_response(await deactivate_account(scope, account_code), request_id=get_request_id())


@router.post("/mappings/versions")
async def create_mapping_version_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    label: Annotated[str, Query()] = "Custom mappings",
) -> ApiResponse[dict]:
    return success_response(await create_mapping_version(scope, label), request_id=get_request_id())


@router.post("/mappings/seed-default")
async def seed_mappings_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)]) -> ApiResponse[dict]:
    return success_response(await seed_default_mappings(scope), request_id=get_request_id())


@router.get("/mappings/versions")
async def list_mappings_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)]) -> ApiResponse[list]:
    return success_response(await list_mapping_versions(scope), request_id=get_request_id())


@router.post("/mappings/versions/{version_id}/rules")
async def add_rule_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    version_id: str,
    body: MappingRuleInput,
) -> ApiResponse[dict]:
    return success_response(await add_mapping_rule(scope, version_id, body.model_dump()), request_id=get_request_id())


@router.post("/mappings/versions/{version_id}/activate")
async def activate_mapping_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    version_id: str,
) -> ApiResponse[dict]:
    return success_response(await activate_mapping_version(scope, version_id), request_id=get_request_id())


@router.post("/journals")
async def create_journal_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: ManualJournalInput,
) -> ApiResponse[dict]:
    payload = body.model_dump()
    payload["lines"] = [line.model_dump() for line in body.lines]
    return success_response(await create_manual_journal(scope, payload), request_id=get_request_id())


@router.get("/journals")
async def list_journals_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    status: Annotated[str | None, Query()] = None,
) -> ApiResponse[list]:
    return success_response(await list_journals(scope, status=status), request_id=get_request_id())


@router.get("/journals/{journal_id}")
async def get_journal_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    journal_id: str,
) -> ApiResponse[dict]:
    return success_response(await get_journal(scope, journal_id), request_id=get_request_id())


@router.post("/journals/{journal_id}/submit")
async def submit_journal_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    journal_id: str,
) -> ApiResponse[dict]:
    return success_response(await submit_journal(scope, journal_id), request_id=get_request_id())


@router.post("/journals/{journal_id}/approve")
async def approve_journal_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    journal_id: str,
) -> ApiResponse[dict]:
    return success_response(await approve_journal(scope, journal_id), request_id=get_request_id())


@router.post("/journals/{journal_id}/post")
async def post_journal_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    journal_id: str,
) -> ApiResponse[dict]:
    return success_response(await post_journal(scope, journal_id), request_id=get_request_id())


@router.post("/journals/{journal_id}/reverse")
async def reverse_journal_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    journal_id: str,
    body: ReverseJournalInput,
) -> ApiResponse[dict]:
    return success_response(await reverse_journal(scope, journal_id, body.reason), request_id=get_request_id())


@router.get("/reports/trial-balance")
async def trial_balance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    financial_year_id: Annotated[str | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await trial_balance(scope, financial_year_id=financial_year_id, date_from=date_from, date_to=date_to), request_id=get_request_id())


@router.get("/reports/ledger/{account_code}")
async def account_ledger_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    account_code: str,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await account_ledger(scope, account_code, date_from=date_from, date_to=date_to), request_id=get_request_id())


@router.get("/reports/income-expenditure")
async def income_statement_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await income_expenditure_statement(scope, date_from=date_from, date_to=date_to), request_id=get_request_id())


@router.get("/reports/balance-sheet")
async def balance_sheet_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    financial_year_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await balance_sheet(scope, financial_year_id=financial_year_id), request_id=get_request_id())


@router.post("/opening-balances")
async def opening_balance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: OpeningBalanceInput,
) -> ApiResponse[dict]:
    import uuid

    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = AccountOpeningBalance(
        tenant_id=tenant_id,
        balance_id=f"ob_{uuid.uuid4().hex[:10]}",
        financial_year_id=body.financial_year_id,
        account_code=body.account_code,
        debit=body.debit,
        credit=body.credit,
        as_of_date=body.as_of_date,
        created_by=scope.user_id,
    )
    await doc.insert()
    return success_response({"balance_id": doc.balance_id}, request_id=get_request_id())