"""Accounts / Finance Staff — Phase 6 installments and late fees."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.accounts_finance.installment_service import apply_payment_to_installments, assign_payment_plan, upsert_payment_plan
from app.modules.accounts_finance.late_fee_service import run_late_fee_processing, upsert_late_fee_policy, waive_late_fee
from app.modules.accounts_finance.outstanding_service import outstanding_dashboard
from app.modules.accounts_finance.phase6_models import StudentInstallmentSchedule, StudentLateFeeTransaction
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import StudentFeeDemand, StudentFinancialLedgerEntry
from app.modules.finance.payment_reconciliation import reconcile_successful_payment
from app.modules.finance.finance_models import PaymentTransaction
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
    tenant = Tenant(name=f"Fin P6 {suffix}", code=f"fp6_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    student = User(
        email=f"stu+p6+{suffix}@example.com",
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
        amount=9000,
        due_date=date.today() - timedelta(days=10),
        status=FeeDemandStatus.OPEN,
    ).insert()
    return tenant, scope, student, demand_id


@pytest.mark.anyio
async def test_installment_calculation_and_payment(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student, demand_id = await _seed(suffix)
    plan = await upsert_payment_plan(
        scope,
        {
            "plan_code": f"PL3_{suffix}",
            "plan_name": "Three part",
            "plan_status": "active",
            "installment_definitions": [
                {"percent": 40, "days_offset": 0},
                {"percent": 30, "days_offset": 30},
                {"percent": 30, "days_offset": 60},
            ],
        },
    )
    assigned = await assign_payment_plan(
        scope,
        {
            "student_user_id": str(student.id),
            "plan_id": plan["plan_id"],
            "demand_id": demand_id,
            "total_obligation": 9000,
        },
    )
    total = sum(i["amount"] for i in assigned["installments"])
    assert total == 9000
    tx_id = f"pay_{suffix}"
    await apply_payment_to_installments(
        tenant.id,
        student_user_id=student.id,
        transaction_id=tx_id,
        amount=3600,
        demand_id=demand_id,
    )
    sched = await StudentInstallmentSchedule.find_one(Eq(StudentInstallmentSchedule.schedule_id, assigned["schedule_id"]))
    assert sched is not None
    paid_statuses = {i["status"] for i in sched.installments}
    assert "paid" in paid_statuses or "partially_paid" in paid_statuses


@pytest.mark.anyio
async def test_late_fee_idempotent_and_grace(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student, demand_id = await _seed(suffix)
    await upsert_late_fee_policy(
        scope,
        {
            "policy_code": f"LFP_{suffix}",
            "name": "Daily late",
            "calc_type": "daily",
            "daily_rate": 10,
            "grace_days": 5,
            "active": True,
        },
    )
    first = await run_late_fee_processing(scope)
    second = await run_late_fee_processing(scope)
    assert first["generated"] >= 1
    assert second["generated"] == 0
    txs = await StudentLateFeeTransaction.find(Eq(StudentLateFeeTransaction.tenant_id, tenant.id)).to_list()
    assert len(txs) == 1
    demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.demand_id, demand_id))
    assert demand.late_fee > 0


@pytest.mark.anyio
async def test_late_fee_waiver_and_dashboard(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student, demand_id = await _seed(suffix)
    await upsert_late_fee_policy(
        scope,
        {"policy_code": f"FIX_{suffix}", "name": "Fixed", "calc_type": "fixed", "fixed_amount": 200, "grace_days": 0, "active": True},
    )
    await run_late_fee_processing(scope)
    waiver = await waive_late_fee(
        scope,
        {"student_user_id": str(student.id), "waived_amount": 100, "reason": "Hardship", "demand_id": demand_id},
    )
    assert waiver["waived_amount"] == 100
    entry = await StudentFinancialLedgerEntry.find_one(
        Eq(StudentFinancialLedgerEntry.posting_key, f"late_fee_waiver:{waiver['waiver_id']}")
    )
    assert entry is not None
    dash = await outstanding_dashboard(scope)
    assert dash["total_overdue_amount"] >= 0


@pytest.mark.anyio
async def test_reconcile_updates_installments(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student, demand_id = await _seed(suffix)
    plan = await upsert_payment_plan(
        scope,
        {
            "plan_code": f"FULL_{suffix}",
            "plan_name": "Full",
            "plan_status": "active",
            "installment_definitions": [{"percent": 100, "days_offset": 0}],
        },
    )
    assigned = await assign_payment_plan(
        scope, {"student_user_id": str(student.id), "plan_id": plan["plan_id"], "demand_id": demand_id, "total_obligation": 9000}
    )
    tx = PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student.id,
        transaction_id=f"pay_{suffix}",
        idempotency_key=f"idem_{suffix}",
        demand_id=demand_id,
        amount=9000,
        status=PaymentTransactionStatus.SUCCESS,
        payment_mode="offline",
        webhook_verified=False,
    )
    await tx.insert()
    await reconcile_successful_payment(tx)
    sched = await StudentInstallmentSchedule.find_one(Eq(StudentInstallmentSchedule.schedule_id, assigned["schedule_id"]))
    assert sched.installments[0]["status"] == "paid"