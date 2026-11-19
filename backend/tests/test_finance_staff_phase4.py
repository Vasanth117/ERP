"""Accounts / Finance Staff — Phase 4 ledger and receipts."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.accounts_finance.invoice_service import issue_invoice
from app.modules.accounts_finance.ledger_posting_service import post_fee_invoice, post_verified_payment
from app.modules.accounts_finance.ledger_service import get_student_account, run_ledger_reconciliation
from app.modules.accounts_finance.phase2_enums import StudentInvoiceStatus
from app.modules.accounts_finance.receipt_service import cancel_receipt, get_receipt, issue_receipt_from_payment
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import (
    PaymentReceipt,
    PaymentTransaction,
    StudentFeeDemand,
    StudentFeeInvoice,
    StudentFinancialLedgerEntry,
)
from app.modules.finance.payment_reconciliation import reconcile_successful_payment
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
    tenant = Tenant(name=f"Fin P4 {suffix}", code=f"fp4_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    student = User(
        email=f"stu+p4+{suffix}@example.com",
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
    demand_id = f"dem_{suffix}"
    await StudentFeeDemand(
        tenant_id=tenant.id,
        student_user_id=student.id,
        demand_id=demand_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        description="Tuition",
        amount=5000,
        due_date=date.today() + timedelta(days=10),
        status=FeeDemandStatus.OPEN,
    ).insert()
    invoice_id = f"inv_{suffix}"
    await StudentFeeInvoice(
        tenant_id=tenant.id,
        student_user_id=student.id,
        invoice_id=invoice_id,
        demand_id=demand_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        amount=5000,
        due_date=date.today() + timedelta(days=10),
        issued_at=utcnow(),
        invoice_status=StudentInvoiceStatus.DRAFT.value,
    ).insert()
    return tenant, scope, student, demand_id, invoice_id


@pytest.mark.anyio
async def test_ledger_posting_idempotent(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _scope, student, _demand_id, invoice_id = await _seed(suffix)
    first = await post_fee_invoice(
        tenant_id=tenant.id,
        student_user_id=student.id,
        invoice_id=invoice_id,
        invoice_number=f"INV-TEST-{suffix}",
        amount=5000,
    )
    second = await post_fee_invoice(
        tenant_id=tenant.id,
        student_user_id=student.id,
        invoice_id=invoice_id,
        invoice_number=f"INV-TEST-{suffix}",
        amount=5000,
    )
    assert first.entry_id == second.entry_id
    count = await StudentFinancialLedgerEntry.find(
        Eq(StudentFinancialLedgerEntry.tenant_id, tenant.id),
        Eq(StudentFinancialLedgerEntry.invoice_id, invoice_id),
    ).count()
    assert count == 1
    assert first.balance_after == 5000


@pytest.mark.anyio
async def test_payment_reconcile_receipt_numbering(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student, demand_id, invoice_id = await _seed(suffix)
    await issue_invoice(scope, invoice_id)
    tx = PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student.id,
        transaction_id=f"pay_{suffix}",
        idempotency_key=f"idem_{suffix}",
        demand_id=demand_id,
        amount=2000,
        status=PaymentTransactionStatus.SUCCESS,
        payment_mode="offline",
        webhook_verified=False,
    )
    await tx.insert()
    await reconcile_successful_payment(tx)
    receipt = await PaymentReceipt.find_one(Eq(PaymentReceipt.transaction_id, tx.transaction_id))
    assert receipt is not None
    assert receipt.receipt_number is not None
    assert receipt.receipt_number.startswith("RCT-")
    account = await get_student_account(scope, str(student.id))
    assert account["outstanding_balance"] == 3000
    assert account["total_verified_payments"] == 2000


@pytest.mark.anyio
async def test_receipt_cancel_and_reconciliation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student, demand_id, _invoice_id = await _seed(suffix)
    tx = PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student.id,
        transaction_id=f"pay2_{suffix}",
        idempotency_key=f"idem2_{suffix}",
        demand_id=demand_id,
        amount=1000,
        status=PaymentTransactionStatus.SUCCESS,
        payment_mode="online",
        webhook_verified=True,
    )
    await tx.insert()
    await post_verified_payment(
        tenant_id=tenant.id,
        student_user_id=student.id,
        transaction_id=tx.transaction_id,
        amount=1000,
        demand_id=demand_id,
    )
    receipt = await issue_receipt_from_payment(tx, issuer_user_id=scope.user_id)
    assert receipt is not None
    detail = await get_receipt(scope, receipt.receipt_id)
    assert detail["amount"] == 1000
    await cancel_receipt(scope, receipt.receipt_id, "Wrong details printed")
    cancelled = await PaymentReceipt.get(receipt.id)
    assert cancelled.receipt_status == "cancelled"
    assert cancelled.published is False

    orphan_tx = PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student.id,
        transaction_id=f"pay3_{suffix}",
        idempotency_key=f"idem3_{suffix}",
        demand_id=demand_id,
        amount=500,
        status=PaymentTransactionStatus.SUCCESS,
        payment_mode="online",
        webhook_verified=True,
    )
    await orphan_tx.insert()
    report = await run_ledger_reconciliation(scope, str(student.id))
    types = {e["type"] for e in report["exceptions"]}
    assert "payment_not_posted" in types or "receipt_missing" in types