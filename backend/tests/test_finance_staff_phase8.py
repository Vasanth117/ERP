"""Accounts / Finance Staff — Phase 8 reports and period closing."""

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
from app.modules.accounts_finance.finance_report_service import export_report_csv, preview_report, save_report
from app.modules.accounts_finance.period_closing_service import (
    approve_period_close,
    approve_period_reopen,
    initiate_closing_run,
    request_period_reopen,
    upsert_accounting_period,
)
from app.modules.accounts_finance.period_lock_service import assert_period_open_for_date
from app.modules.accounts_finance.refund_service import create_refund_request
from app.modules.auth.models import User
from app.modules.college_admin.finance_admin_models import FinancialPeriod, FinancialPeriodStatus
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand
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
    tenant = Tenant(name=f"Fin P8 {suffix}", code=f"fp8_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p8+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    student = User(
        email=f"stu+p8+{suffix}@example.com",
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
        amount=3000,
        due_date=date.today() + timedelta(days=30),
        status=FeeDemandStatus.OPEN,
    ).insert()
    tx_id = f"pay_{suffix}"
    await PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student.id,
        transaction_id=tx_id,
        idempotency_key=f"idem_{suffix}",
        demand_id=demand_id,
        amount=1000,
        status=PaymentTransactionStatus.SUCCESS,
        payment_mode="offline",
        webhook_verified=True,
        gateway_reference=f"gw_{suffix}",
    ).insert()
    return tenant, staff, student, scope, tx_id


@pytest.mark.asyncio
async def test_report_preview_collections(db_ready):
    _, _, _, scope, _ = await _seed(uuid4().hex[:8])
    preview = await preview_report(scope, "fee_collections", {"group_by": "day"})
    assert preview.row_count >= 1
    assert preview.totals.get("amount", 0) >= 1000


@pytest.mark.asyncio
async def test_saved_report_and_csv_export(db_ready):
    _, _, _, scope, _ = await _seed(uuid4().hex[:8])
    saved = await save_report(
        scope,
        {"name": "Daily collections", "category": "fee_collections", "config": {"filters": {"group_by": "day"}}},
    )
    assert saved.report_id.startswith("srpt_")
    filename, csv_body = await export_report_csv(scope, "fee_collections", {"group_by": "day"})
    assert filename.endswith(".csv")
    assert "group_key" in csv_body or "amount" in csv_body


@pytest.mark.asyncio
async def test_period_close_locks_mutations(db_ready):
    tenant, _, student, scope, tx_id = await _seed(uuid4().hex[:8])
    period_code = "2025-11"
    await upsert_accounting_period(
        scope,
        {
            "period_code": period_code,
            "label": "Nov 2025",
            "start_date": date.today().replace(day=1),
            "end_date": date.today(),
            "period_type": "monthly",
        },
    )
    closing = await initiate_closing_run(scope, period_code)
    await approve_period_close(scope, closing["closing_run_id"])
    with pytest.raises(AppError) as exc:
        await assert_period_open_for_date(tenant.id)
    assert exc.value.status_code == 409
    with pytest.raises(AppError):
        await create_refund_request(
            scope,
            {
                "student_user_id": str(student.id),
                "transaction_id": tx_id,
                "requested_amount": 100,
                "reason": "Test refund in closed period",
            },
        )


@pytest.mark.asyncio
async def test_period_reopen_allows_writes(db_ready):
    tenant, _, student, scope, tx_id = await _seed(uuid4().hex[:8])
    period_code = "2025-12"
    await upsert_accounting_period(
        scope,
        {
            "period_code": period_code,
            "label": "Dec 2025",
            "start_date": date.today().replace(day=1),
            "end_date": date.today(),
        },
    )
    closing = await initiate_closing_run(scope, period_code)
    await approve_period_close(scope, closing["closing_run_id"])
    reopen = await request_period_reopen(scope, period_code, "Correction for late posting")
    await approve_period_reopen(scope, reopen["request_id"])
    period = await FinancialPeriod.find_one(Eq(FinancialPeriod.period_code, period_code))
    assert period.status == FinancialPeriodStatus.OPEN
    assert period.locked is False
    await assert_period_open_for_date(tenant.id)