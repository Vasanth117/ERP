"""Chart of accounts and default institutional GL seed."""

import uuid
from datetime import date
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.phase9_enums import AccountClassification, AccountType, NormalBalance
from app.modules.accounts_finance.phase9_models import AccountGroup, ChartOfAccount
from app.modules.accounts_finance.policy import authorize_finance_gl_manage, authorize_finance_gl_read, require_finance_tenant_scope
from app.modules.college_admin.security_admin_service import append_institution_audit

DEFAULT_ACCOUNTS = [
    ("1000", "Bank and Cash", AccountType.ASSET, AccountClassification.BANK, NormalBalance.DEBIT),
    ("1100", "Student Fee Receivables", AccountType.ASSET, AccountClassification.STUDENT_RECEIVABLE, NormalBalance.DEBIT),
    ("1150", "Refund Payable", AccountType.LIABILITY, AccountClassification.OTHER, NormalBalance.CREDIT),
    ("3000", "Institutional Fund Balance", AccountType.EQUITY, AccountClassification.OTHER, NormalBalance.CREDIT),
    ("4100", "Tuition and Fee Income", AccountType.INCOME, AccountClassification.FEE_INCOME, NormalBalance.CREDIT),
    ("5100", "Scholarship and Concession Expense", AccountType.EXPENSE, AccountClassification.OPERATIONAL_EXPENSE, NormalBalance.DEBIT),
    ("5200", "Late Fee Income", AccountType.INCOME, AccountClassification.FEE_INCOME, NormalBalance.CREDIT),
]


async def seed_default_chart(scope: AccessScope, *, financial_year_id: str | None = None) -> dict:
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    created = 0
    for code, name, atype, cls, normal in DEFAULT_ACCOUNTS:
        exists = await ChartOfAccount.find_one(Eq(ChartOfAccount.tenant_id, tenant_id), Eq(ChartOfAccount.account_code, code))
        if exists:
            continue
        await ChartOfAccount(
            tenant_id=tenant_id,
            account_code=code,
            account_name=name,
            account_type=atype.value,
            classification=cls.value,
            normal_balance=normal.value,
            effective_from=date.today(),
        ).insert()
        created += 1
    group = await AccountGroup.find_one(Eq(AccountGroup.tenant_id, tenant_id), Eq(AccountGroup.group_code, "STUDENT_FEES"))
    if group is None:
        await AccountGroup(
            tenant_id=tenant_id,
            group_code="STUDENT_FEES",
            group_name="Student Fee Accounts",
            account_type=AccountType.INCOME.value,
        ).insert()
    return {"accounts_created": created, "financial_year_id": financial_year_id}


async def upsert_account(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    code = payload["account_code"].strip().upper()
    parent = payload.get("parent_account_code")
    if parent:
        parent_doc = await ChartOfAccount.find_one(Eq(ChartOfAccount.tenant_id, tenant_id), Eq(ChartOfAccount.account_code, parent))
        if parent_doc is None:
            raise AppError(code="VALIDATION_ERROR", message="Parent account not found", status_code=400)
    doc = await ChartOfAccount.find_one(Eq(ChartOfAccount.tenant_id, tenant_id), Eq(ChartOfAccount.account_code, code))
    now = utcnow()
    if doc is None:
        doc = ChartOfAccount(
            tenant_id=tenant_id,
            account_code=code,
            account_name=payload["account_name"],
            account_type=payload["account_type"],
            classification=payload.get("classification") or AccountClassification.OTHER.value,
            parent_account_code=parent,
            account_group=payload.get("account_group"),
            normal_balance=payload["normal_balance"],
            description=payload.get("description"),
            currency=payload.get("currency") or "INR",
            active=bool(payload.get("active", True)),
            effective_from=payload.get("effective_from") or date.today(),
            created_at=now,
            updated_at=now,
        )
        await doc.insert()
        action = "create"
    else:
        doc.account_name = payload["account_name"]
        doc.account_type = payload["account_type"]
        doc.classification = payload.get("classification") or doc.classification
        doc.parent_account_code = parent
        doc.account_group = payload.get("account_group")
        doc.normal_balance = payload["normal_balance"]
        doc.description = payload.get("description")
        doc.active = bool(payload.get("active", doc.active))
        doc.updated_at = now
        await doc.save()
        action = "update"
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action=f"finance.gl.account.{action}",
        module="accounts_finance",
        resource_type="chart_of_account",
        resource_id=code,
    )
    return {"account_code": doc.account_code, "account_name": doc.account_name, "active": doc.active}


async def list_accounts(scope: AccessScope, *, active_only: bool = True) -> list[dict]:
    authorize_finance_gl_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await ChartOfAccount.find(Eq(ChartOfAccount.tenant_id, tenant_id)).to_list()
    if active_only:
        rows = [r for r in rows if r.active]
    return [
        {
            "account_code": r.account_code,
            "account_name": r.account_name,
            "account_type": r.account_type,
            "classification": r.classification,
            "parent_account_code": r.parent_account_code,
            "normal_balance": r.normal_balance,
            "active": r.active,
        }
        for r in sorted(rows, key=lambda x: x.account_code)
    ]


async def deactivate_account(scope: AccessScope, account_code: str) -> dict:
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await ChartOfAccount.find_one(Eq(ChartOfAccount.tenant_id, tenant_id), Eq(ChartOfAccount.account_code, account_code))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Account not found", status_code=404)
    doc.active = False
    doc.updated_at = utcnow()
    await doc.save()
    return {"account_code": account_code, "active": False}