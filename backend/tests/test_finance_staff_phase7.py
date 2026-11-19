"""Accounts / Finance Staff — Phase 7 refunds and reconciliation."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.accounts_finance.reconciliation_service import (
    auto_match_batch,
    confirm_batch,
    confirm_match,
    create_batch,
    create_reconciliation_period,
    import_statement,
)
from app.modules.accounts_finance.refund_service import (
    approve_payment_reversal,
    approve_refund_request,
    complete_refund,
    create_payment_reversal,
    create_refund_request,
    refundable_amount,
)
from app.modules.accounts_finance.phase7_models import PaymentReconciliationMatch, StudentRefundRequest
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand, StudentFinancialLedgerEntry
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


async def _seed_payment(suffix: str):
    tenant = Tenant(name=f"Fin P7 {suffix}", code=f"fp7_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p7+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    student = User(
        email=f"stu+p7+{suffix}@example.com",
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
        description="Fees",
        amount=5000,
        due_date=date.today() + timedelta(days=30),
        status=FeeDemandStatus.OPEN,
    ).insert()
    tx_id = f"pay_{suffix}"
    tx = PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student.id,
        transaction_id=tx_id,
        idempotency_key=f"idem_{suffix}",
        demand_id=demand_id,
        amount=5000,
        status=PaymentTransactionStatus.SUCCESS,
        payment_mode="offline",
        webhook_verified=False,
        gateway_reference=f"gw_{suffix}",
    )
    await tx.insert()
    await reconcile_successful_payment(tx)
    return tenant, scope, student, tx_id


@pytest.mark.anyio
async def test_partial_refund_and_limit(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, student, tx_id = await _seed_payment(suffix)
    elig = await refundable_amount(scope.tenant_id, tx_id)
    assert elig["refundable"] == 5000
    req = await create_refund_request(
        scope,
        {
            "student_user_id": str(student.id),
            "transaction_id": tx_id,
            "requested_amount": 2000,
            "reason": "Excess payment",
            "category": "excess_payment",
        },
    )
    await approve_refund_request(scope, req["refund_request_id"], approved_amount=2000)
    done = await complete_refund(scope, req["refund_request_id"], payout_reference="NEFT-123")
    assert done["status"] == "successful"
    with pytest.raises(AppError):
        await create_refund_request(
            scope,
            {
                "student_user_id": str(student.id),
                "transaction_id": tx_id,
                "requested_amount": 4000,
                "reason": "Too much",
                "category": "other",
            },
        )
    second = await create_refund_request(
        scope,
        {
            "student_user_id": str(student.id),
            "transaction_id": tx_id,
            "requested_amount": 3000,
            "reason": "Remaining",
            "category": "other",
        },
    )
    await approve_refund_request(scope, second["refund_request_id"])
    await complete_refund(scope, second["refund_request_id"], payout_reference="NEFT-124")
    entry = await StudentFinancialLedgerEntry.find_one(
        Eq(StudentFinancialLedgerEntry.posting_key, f"refund:{req['refund_request_id']}")
    )
    assert entry is not None


@pytest.mark.anyio
async def test_payment_reversal_ledger(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, student, tx_id = await _seed_payment(suffix)
    rev = await create_payment_reversal(
        scope,
        {"student_user_id": str(student.id), "transaction_id": tx_id, "amount": 1000, "reason": "Duplicate posting"},
    )
    posted = await approve_payment_reversal(scope, rev["reversal_request_id"])
    assert posted["ledger_entry_id"]
    ledger = await StudentFinancialLedgerEntry.find_one(
        Eq(StudentFinancialLedgerEntry.posting_key, f"payment_reversal:{rev['reversal_request_id']}")
    )
    assert ledger.debit == 1000


@pytest.mark.anyio
async def test_reconciliation_csv_match(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, student, tx_id = await _seed_payment(suffix)
    period = await create_reconciliation_period(
        scope, {"label": "Nov", "period_start": date.today().replace(day=1), "period_end": date.today()}
    )
    batch = await create_batch(scope, period["period_id"], "bank")
    csv_content = (
        "transaction_id,amount,transaction_date,gateway_reference\n"
        f"{tx_id},5000,{date.today().isoformat()},gw_{suffix}\n"
    )
    imp = await import_statement(scope, batch["batch_id"], file_name="stmt.csv", content=csv_content)
    assert imp["row_count"] == 1
    matched = await auto_match_batch(scope, batch["batch_id"])
    assert matched["exact_matches"] == 1
    row = await PaymentReconciliationMatch.find_one(Eq(PaymentReconciliationMatch.batch_id, batch["batch_id"]))
    await confirm_match(scope, row.match_id)
    await confirm_batch(scope, batch["batch_id"])


@pytest.mark.anyio
async def test_duplicate_refund_complete(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, student, tx_id = await _seed_payment(suffix)
    req = await create_refund_request(
        scope,
        {
            "student_user_id": str(student.id),
            "transaction_id": tx_id,
            "requested_amount": 1000,
            "reason": "Dup",
            "category": "duplicate_payment",
        },
    )
    await approve_refund_request(scope, req["refund_request_id"])
    await complete_refund(scope, req["refund_request_id"], payout_reference="P1")
    with pytest.raises(AppError):
        await complete_refund(scope, req["refund_request_id"], payout_reference="P2")