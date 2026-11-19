"""Accounts / Finance Staff — Phase 10 procurement and expenses."""

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
from app.modules.accounts_finance.budget_service import approve_budget, create_budget, submit_budget
from app.modules.accounts_finance.coa_service import seed_default_chart
from app.modules.accounts_finance.expense_claim_service import approve_expense_claim, create_expense_claim, seed_expense_categories
from app.modules.accounts_finance.mapping_service import seed_default_mappings
from app.modules.accounts_finance.phase10_gl_seed import seed_procurement_gl
from app.modules.accounts_finance.procurement_service import (
    approve_purchase_request,
    confirm_vendor_payment,
    create_purchase_order,
    create_purchase_request,
    record_vendor_invoice,
    verify_vendor_invoice,
)
from app.modules.accounts_finance.vendor_service import register_vendor, verify_vendor
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


async def _seed(suffix: str):
    tenant = Tenant(name=f"Fin P10 {suffix}", code=f"fp10_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p10+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    approver = User(
        email=f"mgr+p10+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Approver",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await approver.insert()
    scope = AccessScope(
        role=Role.FINANCE_STAFF,
        user_id=staff.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FINANCE_STAFF),
    )
    approver_scope = AccessScope(
        role=Role.FINANCE_STAFF,
        user_id=approver.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FINANCE_STAFF),
    )
    await seed_default_chart(scope)
    await seed_default_mappings(scope)
    await seed_procurement_gl(scope)
    return tenant, scope, approver_scope


@pytest.mark.asyncio
async def test_vendor_and_procurement_flow(db_ready):
    _, scope, approver_scope = await _seed(uuid4().hex[:8])
    vid = f"ven_{uuid4().hex[:6]}"
    await register_vendor(scope, {"vendor_id": vid, "name": "Lab Supplies", "vendor_code": "LAB01", "category": "laboratory"})
    await verify_vendor(approver_scope, vid, approved=True)
    budget = await create_budget(
        scope,
        {"budget_code": "CAP", "budget_name": "Cap", "financial_year_id": "FY25", "total_amount": 500000},
    )
    await submit_budget(scope, budget["budget_id"])
    await approve_budget(approver_scope, budget["budget_id"])
    rid = f"pr_{uuid4().hex[:6]}"
    await create_purchase_request(
        scope,
        {
            "request_id": rid,
            "description": "Microscope",
            "estimated_amount": 10000,
            "finance_budget_id": budget["budget_id"],
            "submit": True,
        },
    )
    with pytest.raises(AppError):
        await approve_purchase_request(scope, rid, approved=True)
    await approve_purchase_request(approver_scope, rid, approved=True)
    oid = f"po_{uuid4().hex[:6]}"
    await create_purchase_order(
        scope,
        {
            "order_id": oid,
            "vendor_id": vid,
            "request_id": rid,
            "finance_budget_id": budget["budget_id"],
            "items": [{"description": "Microscope", "quantity": 1, "unit_price": 10000}],
        },
    )
    iid = f"vinv_{uuid4().hex[:6]}"
    await record_vendor_invoice(
        scope,
        {"invoice_id": iid, "vendor_id": vid, "order_id": oid, "amount": 10000, "vendor_invoice_number": "V-1001", "invoice_date": date.today()},
    )
    await verify_vendor_invoice(approver_scope, iid)
    pay = await confirm_vendor_payment(
        approver_scope,
        {"invoice_id": iid, "amount": 10000, "payment_reference": "NEFT-12345"},
    )
    assert pay["outstanding"] == 0


@pytest.mark.asyncio
async def test_expense_self_approval_and_duplicate_bill(db_ready):
    _, scope, approver_scope = await _seed(uuid4().hex[:8])
    await seed_expense_categories(scope)
    claim = await create_expense_claim(
        scope,
        {
            "description": "Travel",
            "category_code": "travel",
            "expense_date": date.today(),
            "amount": 1500,
            "document_refs": ["bill-scan-1"],
            "submit": True,
        },
    )
    with pytest.raises(AppError):
        await approve_expense_claim(scope, claim["claim_id"], approved=True)
    await approve_expense_claim(approver_scope, claim["claim_id"], approved=True)
    with pytest.raises(AppError):
        await create_expense_claim(
            scope,
            {
                "description": "Duplicate",
                "category_code": "travel",
                "expense_date": date.today(),
                "amount": 1500,
                "document_refs": ["bill-scan-1"],
            },
        )