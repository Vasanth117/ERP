"""Accounts / Finance Staff — Phase 3 payments."""

import hashlib
import hmac
import json
from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.config import get_settings
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.accounts_finance.offline_payment_service import record_offline_payment, verify_offline_payment
from app.modules.accounts_finance.payment_core import initiate_online_payment, process_payment_webhook
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentReceipt, PaymentTransaction, StudentFeeDemand
from app.modules.finance.payment_reconciliation import reconcile_successful_payment
from app.modules.tenants.models import Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    try:
        await connect_redis()
    except Exception:
        pass
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed(suffix: str):
    tenant = Tenant(name=f"Fin P3 {suffix}", code=f"fp3_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    student = User(
        email=f"stu+p3+{suffix}@example.com",
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
        amount=10000,
        due_date=date.today() + timedelta(days=30),
        status=FeeDemandStatus.OPEN,
    ).insert()
    return tenant, scope, student, demand_id


def _refresh_settings() -> None:
    get_settings.cache_clear()


def _sign(body: bytes) -> str:
    secret = get_settings().payment_webhook_secret or "test-webhook-secret"
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.mark.anyio
async def test_online_webhook_and_partial(db_ready, monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "test-webhook-secret")
    _refresh_settings()
    suffix = uuid4().hex[:8]
    tenant, _, student, demand_id = await _seed(suffix)
    init = await initiate_online_payment(
        tenant_id=tenant.id,
        student_user_id=student.id,
        payer_user_id=student.id,
        demand_id=demand_id,
        idempotency_key=f"idem_{suffix}a",
        amount=4000,
    )
    body_dict = {"transaction_id": init["transaction_id"], "gateway_reference": "gw_ref_1", "amount": 4000, "event_id": f"evt_{suffix}"}
    body = json.dumps(body_dict).encode()
    result = await process_payment_webhook(tenant_id=tenant.id, body=body, signature=_sign(body), payload=body_dict)
    assert result["verified"] is True
    demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.demand_id, demand_id))
    assert demand.status == FeeDemandStatus.PARTIALLY_PAID

    dup = await process_payment_webhook(tenant_id=tenant.id, body=body, signature=_sign(body), payload=body_dict)
    assert dup.get("duplicate") is True

    init2 = await initiate_online_payment(
        tenant_id=tenant.id,
        student_user_id=student.id,
        payer_user_id=student.id,
        demand_id=demand_id,
        idempotency_key=f"idem_{suffix}b",
        amount=6000,
    )
    body2 = json.dumps({"transaction_id": init2["transaction_id"], "gateway_reference": "gw_ref_2", "amount": 6000, "event_id": f"evt2_{suffix}"}).encode()
    payload2 = json.loads(body2)
    await process_payment_webhook(tenant_id=tenant.id, body=body2, signature=_sign(body2), payload=payload2)
    demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.demand_id, demand_id))
    assert demand.status == FeeDemandStatus.PAID


@pytest.mark.anyio
async def test_invalid_signature(db_ready, monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "test-webhook-secret")
    _refresh_settings()
    suffix = uuid4().hex[:8]
    tenant, _, student, demand_id = await _seed(suffix)
    init = await initiate_online_payment(
        tenant_id=tenant.id,
        student_user_id=student.id,
        payer_user_id=student.id,
        demand_id=demand_id,
        idempotency_key=f"idem_{suffix}",
    )
    body = json.dumps({"transaction_id": init["transaction_id"], "gateway_reference": "x", "amount": init["amount"]}).encode()
    with pytest.raises(AppError) as exc:
        await process_payment_webhook(tenant_id=tenant.id, body=body, signature="bad", payload=json.loads(body))
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_overpayment_prevention(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, student, demand_id = await _seed(suffix)
    with pytest.raises(AppError) as exc:
        await initiate_online_payment(
            tenant_id=tenant.id,
            student_user_id=student.id,
            payer_user_id=student.id,
            demand_id=demand_id,
            idempotency_key=f"idem_{suffix}",
            amount=20000,
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_offline_verify_posts_receipt(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student, demand_id = await _seed(suffix)
    recorded = await record_offline_payment(
        scope,
        {
            "student_user_id": str(student.id),
            "demand_id": demand_id,
            "amount": 5000,
            "payment_method": "cash",
            "idempotency_key": f"off_{suffix}",
        },
    )
    await verify_offline_payment(scope, recorded["record_id"])
    tx = await PaymentTransaction.find_one(Eq(PaymentTransaction.transaction_id, recorded["transaction_id"]))
    assert tx.status == PaymentTransactionStatus.SUCCESS
    receipt = await PaymentReceipt.find_one(Eq(PaymentReceipt.transaction_id, recorded["transaction_id"]))
    assert receipt is not None