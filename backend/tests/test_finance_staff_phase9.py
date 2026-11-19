"""Accounts / Finance Staff — Phase 9 GL and budget."""

import uuid
from datetime import date
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.accounts_finance.budget_service import approve_budget, budget_utilization, create_budget, record_commitment, submit_budget
from app.modules.accounts_finance.coa_service import seed_default_chart, upsert_account
from app.modules.accounts_finance.gl_report_service import trial_balance
from app.modules.accounts_finance.journal_service import approve_journal, create_manual_journal, post_journal, submit_journal
from app.modules.accounts_finance.ledger_posting_service import post_fee_invoice
from app.modules.accounts_finance.mapping_service import seed_default_mappings
from app.modules.accounts_finance.phase9_models import GeneralLedgerEntry, JournalEntry
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_mongo()


async def _seed_scope(suffix: str):
    tenant = Tenant(name=f"Fin P9 {suffix}", code=f"fp9_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p9+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    student = User(
        email=f"stu+p9+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    scope = AccessScope(
        role=Role.FINANCE_STAFF,
        user_id=staff.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FINANCE_STAFF),
    )
    return tenant, staff, student, scope


@pytest.mark.asyncio
async def test_coa_unique_and_manual_journal(db_ready):
    _, _, _, scope = await _seed_scope(uuid4().hex[:8])
    await seed_default_chart(scope)
    await upsert_account(
        scope,
        {
            "account_code": "9999",
            "account_name": "Test",
            "account_type": "expense",
            "normal_balance": "debit",
        },
    )
    with pytest.raises(AppError) as dup:
        await create_manual_journal(
            scope,
            {
                "journal_date": date.today(),
                "narration": "Unbalanced test",
                "lines": [{"account_code": "1000", "debit": 100, "credit": 0}, {"account_code": "4100", "debit": 0, "credit": 50}],
            },
        )
    assert dup.value.code == "UNBALANCED_JOURNAL"
    j = await create_manual_journal(
        scope,
        {
            "journal_date": date.today(),
            "narration": "Balanced test",
            "lines": [{"account_code": "1000", "debit": 100, "credit": 0}, {"account_code": "4100", "debit": 0, "credit": 100}],
        },
    )
    await submit_journal(scope, j["journal_id"])
    await approve_journal(scope, j["journal_id"])
    posted = await post_journal(scope, j["journal_id"])
    assert posted["status"] == "posted"
    tb = await trial_balance(scope)
    assert tb["balanced"] is True


@pytest.mark.asyncio
async def test_system_gl_idempotent_from_invoice(db_ready):
    tenant, staff, student, scope = await _seed_scope(uuid4().hex[:8])
    await seed_default_chart(scope)
    await seed_default_mappings(scope)
    inv_id = f"inv_{uuid4().hex[:8]}"
    await post_fee_invoice(
        tenant_id=tenant.id,
        student_user_id=student.id,
        invoice_id=inv_id,
        invoice_number="INV-001",
        amount=5000,
        posted_by=staff.id,
    )
    journals = await JournalEntry.find(Eq(JournalEntry.tenant_id, tenant.id)).to_list()
    assert len(journals) == 1
    await post_fee_invoice(
        tenant_id=tenant.id,
        student_user_id=student.id,
        invoice_id=inv_id,
        invoice_number="INV-001",
        amount=5000,
        posted_by=staff.id,
    )
    journals = await JournalEntry.find(Eq(JournalEntry.tenant_id, tenant.id)).to_list()
    assert len(journals) == 1
    gl = await GeneralLedgerEntry.find(Eq(GeneralLedgerEntry.tenant_id, tenant.id)).to_list()
    assert sum(e.debit for e in gl) == sum(e.credit for e in gl)


@pytest.mark.asyncio
async def test_budget_approval_and_commitment(db_ready):
    _, _, _, scope = await _seed_scope(uuid4().hex[:8])
    budget = await create_budget(
        scope,
        {
            "budget_code": "OPS-2025",
            "budget_name": "Operations",
            "financial_year_id": "FY2025",
            "total_amount": 100000,
        },
    )
    await submit_budget(scope, budget["budget_id"])
    await approve_budget(scope, budget["budget_id"])
    await record_commitment(
        scope,
        budget["budget_id"],
        {"reference_type": "purchase_order", "reference_id": "po_1", "amount": 20000},
    )
    util = await budget_utilization(scope, budget["budget_id"])
    assert util["committed"] == 20000
    assert util["available"] == 80000
    dup = await record_commitment(
        scope,
        budget["budget_id"],
        {"reference_type": "purchase_order", "reference_id": "po_1", "amount": 1000},
    )
    assert dup.get("idempotent") is True