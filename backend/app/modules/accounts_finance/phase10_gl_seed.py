"""Seed GL accounts and mappings for procurement and expenses."""

from app.common.access import AccessScope
from app.modules.accounts_finance.coa_service import upsert_account
from app.modules.accounts_finance.mapping_service import add_mapping_rule, create_mapping_version, activate_mapping_version


async def seed_procurement_gl(scope: AccessScope) -> dict:
    for code, name, atype, normal in (
        ("2100", "Vendor Payables", "liability", "credit"),
        ("5300", "Institutional Operating Expense", "expense", "debit"),
    ):
        await upsert_account(
            scope,
            {
                "account_code": code,
                "account_name": name,
                "account_type": atype,
                "normal_balance": normal,
            },
        )
    ver = await create_mapping_version(scope, "Procurement and expense mappings")
    version_id = ver["version_id"]
    for event, debit, credit in (
        ("vendor_invoice", "5300", "2100"),
        ("vendor_payment", "2100", "1000"),
        ("expense_reimbursement", "5300", "2100"),
        ("expense_payment", "2100", "1000"),
    ):
        await add_mapping_rule(scope, version_id, {"event_type": event, "debit_account_code": debit, "credit_account_code": credit})
    await activate_mapping_version(scope, version_id)
    return {"mapping_version_id": version_id}