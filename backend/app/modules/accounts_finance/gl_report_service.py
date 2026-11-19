"""Trial balance, account ledger, and financial statements."""

from collections import defaultdict
from datetime import date

from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.common.access import AccessScope
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase9_enums import AccountType
from app.modules.accounts_finance.phase9_models import AccountOpeningBalance, ChartOfAccount, GeneralLedgerEntry
from app.modules.accounts_finance.policy import authorize_finance_gl_read, require_finance_tenant_scope


async def account_ledger(scope: AccessScope, account_code: str, *, date_from: date | None = None, date_to: date | None = None) -> dict:
    authorize_finance_gl_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    acct = await ChartOfAccount.find_one(Eq(ChartOfAccount.tenant_id, tenant_id), Eq(ChartOfAccount.account_code, account_code))
    if acct is None:
        return {"account_code": account_code, "available": False}
    query = GeneralLedgerEntry.find(
        Eq(GeneralLedgerEntry.tenant_id, tenant_id),
        Eq(GeneralLedgerEntry.account_code, account_code),
    )
    if date_from:
        query = query.find(GTE(GeneralLedgerEntry.journal_date, date_from))
    if date_to:
        query = query.find(LTE(GeneralLedgerEntry.journal_date, date_to))
    rows = await query.sort("journal_date").to_list()
    running = 0.0
    movements = []
    for row in rows:
        delta = row.debit - row.credit
        running = round_money(running + delta)
        movements.append(
            {
                "journal_date": row.journal_date.isoformat(),
                "journal_id": row.journal_id,
                "debit": row.debit,
                "credit": row.credit,
                "balance_after": running,
                "source_reference": row.source_reference,
            }
        )
    return {
        "account_code": account_code,
        "account_name": acct.account_name,
        "opening_balance_note": "Period opening from account_opening_balances when configured",
        "movements": movements,
        "closing_balance": running,
    }


async def trial_balance(
    scope: AccessScope,
    *,
    financial_year_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    authorize_finance_gl_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    accounts = await ChartOfAccount.find(Eq(ChartOfAccount.tenant_id, tenant_id), Eq(ChartOfAccount.active, True)).to_list()
    openings: dict[str, tuple[float, float]] = {}
    if financial_year_id:
        ob_rows = await AccountOpeningBalance.find(
            Eq(AccountOpeningBalance.tenant_id, tenant_id),
            Eq(AccountOpeningBalance.financial_year_id, financial_year_id),
        ).to_list()
        for ob in ob_rows:
            openings[ob.account_code] = (ob.debit, ob.credit)

    query = GeneralLedgerEntry.find(Eq(GeneralLedgerEntry.tenant_id, tenant_id))
    if date_from:
        query = query.find(GTE(GeneralLedgerEntry.journal_date, date_from))
    if date_to:
        query = query.find(LTE(GeneralLedgerEntry.journal_date, date_to))
    gl_rows = await query.to_list()

    period_debit: dict[str, float] = defaultdict(float)
    period_credit: dict[str, float] = defaultdict(float)
    for row in gl_rows:
        period_debit[row.account_code] += row.debit
        period_credit[row.account_code] += row.credit

    lines = []
    total_debit = total_credit = 0.0
    for acct in accounts:
        od, oc = openings.get(acct.account_code, (0.0, 0.0))
        pd = round_money(period_debit.get(acct.account_code, 0))
        pc = round_money(period_credit.get(acct.account_code, 0))
        cd = round_money(od + pd)
        cc = round_money(oc + pc)
        lines.append(
            {
                "account_code": acct.account_code,
                "account_name": acct.account_name,
                "opening_debit": round_money(od),
                "opening_credit": round_money(oc),
                "period_debit": pd,
                "period_credit": pc,
                "closing_debit": cd,
                "closing_credit": cc,
            }
        )
        total_debit += cd
        total_credit += cc

    balanced = round_money(total_debit) == round_money(total_credit)
    return {
        "lines": lines,
        "total_closing_debit": round_money(total_debit),
        "total_closing_credit": round_money(total_credit),
        "balanced": balanced,
        "financial_year_id": financial_year_id,
    }


async def income_expenditure_statement(scope: AccessScope, *, date_from: date | None = None, date_to: date | None = None) -> dict:
    tb = await trial_balance(scope, date_from=date_from, date_to=date_to)
    income = expense = 0.0
    tenant_id = require_finance_tenant_scope(scope)
    acct_types = {a.account_code: a.account_type for a in await ChartOfAccount.find(Eq(ChartOfAccount.tenant_id, tenant_id)).to_list()}
    for line in tb["lines"]:
        atype = acct_types.get(line["account_code"])
        net = line["period_credit"] - line["period_debit"]
        if atype == AccountType.INCOME.value:
            income += net
        elif atype == AccountType.EXPENSE.value:
            expense += line["period_debit"] - line["period_credit"]
    income = round_money(income)
    expense = round_money(expense)
    return {
        "income": income,
        "expenses": expense,
        "surplus_deficit": round_money(income - expense),
        "complete": bool(tb["lines"]),
        "warning": None if income or expense else "No posted income/expense activity in range",
    }


async def balance_sheet(scope: AccessScope, *, financial_year_id: str | None = None) -> dict:
    tb = await trial_balance(scope, financial_year_id=financial_year_id)
    assets = liabilities = equity = 0.0
    tenant_id = require_finance_tenant_scope(scope)
    acct_types = {a.account_code: a.account_type for a in await ChartOfAccount.find(Eq(ChartOfAccount.tenant_id, tenant_id)).to_list()}
    for line in tb["lines"]:
        atype = acct_types.get(line["account_code"])
        net_debit = line["closing_debit"] - line["closing_credit"]
        if atype == AccountType.ASSET.value:
            assets += net_debit
        elif atype == AccountType.LIABILITY.value:
            liabilities += -net_debit
        elif atype == AccountType.EQUITY.value:
            equity += -net_debit
    missing_opening = financial_year_id is None
    return {
        "assets": round_money(assets),
        "liabilities": round_money(liabilities),
        "equity": round_money(equity),
        "balanced": round_money(assets) == round_money(liabilities + equity),
        "warning": "Opening balances may be incomplete" if missing_opening else None,
    }