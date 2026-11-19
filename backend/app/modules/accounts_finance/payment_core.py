"""Authoritative payment initiation, verification and outstanding balance rules."""

from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase3_enums import OnlinePaymentMethod
from app.modules.accounts_finance.phase3_models import (
    OnlinePaymentAttempt,
    OnlinePaymentOrder,
    PaymentGatewayConfiguration,
    PaymentGatewayFailure,
    PaymentVerificationHistory,
)
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand, StudentFeeInvoice
from app.modules.finance.payment_reconciliation import reconcile_successful_payment
from app.modules.finance.payment_verification import verify_webhook_signature

_OPEN_DEMAND = frozenset({FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE})


async def verified_payments_total(tenant_id: PydanticObjectId, demand_id: str) -> float:
    txs = await PaymentTransaction.find(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.demand_id, demand_id),
        Eq(PaymentTransaction.status, PaymentTransactionStatus.SUCCESS),
    ).to_list()
    total = 0.0
    for tx in txs:
        if tx.payment_mode == "offline" or tx.webhook_verified:
            total += tx.amount
    return round_money(total)


async def demand_outstanding(tenant_id: PydanticObjectId, demand: StudentFeeDemand) -> float:
    due = round_money(demand.amount + demand.late_fee)
    paid = await verified_payments_total(tenant_id, demand.demand_id)
    return max(0.0, round_money(due - paid))


async def _log_verification(tenant_id, transaction_id, step, outcome, detail=None, actor_id=None):
    await PaymentVerificationHistory(
        tenant_id=tenant_id,
        transaction_id=transaction_id,
        step=step,
        outcome=outcome,
        detail=detail,
        actor_id=actor_id,
    ).insert()


async def _active_gateway(tenant_id: PydanticObjectId) -> PaymentGatewayConfiguration:
    doc = await PaymentGatewayConfiguration.find_one(
        Eq(PaymentGatewayConfiguration.tenant_id, tenant_id),
        Eq(PaymentGatewayConfiguration.active, True),
    )
    if doc is None:
        doc = PaymentGatewayConfiguration(
            tenant_id=tenant_id,
            config_id=f"gw_{uuid4().hex[:8]}",
            gateway_name="Stub Gateway",
            provider_code="stub",
            supported_methods=[],
            active=True,
            connection_status="stub",
        )
    return doc


async def initiate_online_payment(
    *,
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    payer_user_id: PydanticObjectId,
    demand_id: str,
    idempotency_key: str,
    amount: float | None = None,
    payment_method: OnlinePaymentMethod = OnlinePaymentMethod.OTHER,
    invoice_id: str | None = None,
) -> dict:
    dup_attempt = await OnlinePaymentAttempt.find_one(
        Eq(OnlinePaymentAttempt.tenant_id, tenant_id),
        Eq(OnlinePaymentAttempt.idempotency_key, idempotency_key),
    )
    if dup_attempt:
        tx = await PaymentTransaction.find_one(
            Eq(PaymentTransaction.tenant_id, tenant_id),
            Eq(PaymentTransaction.transaction_id, dup_attempt.transaction_id),
        )
        if tx:
            return {"transaction_id": tx.transaction_id, "status": tx.status.value, "amount": tx.amount, "duplicate": True}

    demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.tenant_id, tenant_id), Eq(StudentFeeDemand.demand_id, demand_id))
    if demand is None or demand.student_user_id != student_user_id:
        raise AppError(code="NOT_FOUND", message="Fee demand not found", status_code=404)
    if demand.status not in _OPEN_DEMAND:
        raise AppError(code="CONFLICT", message="Fee demand is not payable", status_code=409)

    outstanding = await demand_outstanding(tenant_id, demand)
    if outstanding <= 0:
        raise AppError(code="CONFLICT", message="Nothing outstanding on demand", status_code=409)

    pay_amount = round_money(amount if amount is not None else outstanding)
    if pay_amount > outstanding:
        raise AppError(code="VALIDATION_ERROR", message="Payment exceeds outstanding balance", status_code=422)
    if pay_amount <= 0:
        raise AppError(code="VALIDATION_ERROR", message="Invalid payment amount", status_code=422)

    gateway = await _active_gateway(tenant_id)
    transaction_id = f"pay_{uuid4().hex}"
    order_id = f"ord_{uuid4().hex}"
    merchant_order_id = f"M{transaction_id}"

    tx = PaymentTransaction(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        transaction_id=transaction_id,
        idempotency_key=idempotency_key,
        demand_id=demand_id,
        amount=pay_amount,
        status=PaymentTransactionStatus.INITIATED,
        gateway=gateway.provider_code,
        payment_mode="online",
        currency=gateway.currency,
    )
    await tx.insert()
    await OnlinePaymentOrder(
        tenant_id=tenant_id,
        order_id=order_id,
        student_user_id=student_user_id,
        payer_user_id=payer_user_id,
        invoice_id=invoice_id,
        demand_id=demand_id,
        merchant_order_id=merchant_order_id,
        amount=pay_amount,
        currency=gateway.currency,
        gateway_config_id=gateway.config_id,
        status="initiated",
    ).insert()
    attempt_id = f"att_{uuid4().hex[:12]}"
    await OnlinePaymentAttempt(
        tenant_id=tenant_id,
        attempt_id=attempt_id,
        order_id=order_id,
        transaction_id=transaction_id,
        payment_method=payment_method,
        idempotency_key=idempotency_key,
        status="initiated",
    ).insert()
    await _log_verification(tenant_id, transaction_id, "initiate", "ok", detail=f"order={order_id}")
    return {
        "transaction_id": transaction_id,
        "order_id": order_id,
        "merchant_order_id": merchant_order_id,
        "status": tx.status.value,
        "amount": pay_amount,
        "gateway": gateway.provider_code,
        "checkout_mode": "stub",
    }


async def process_payment_webhook(
    *,
    tenant_id: PydanticObjectId | None,
    body: bytes,
    signature: str | None,
    payload: dict,
    trusted_internal: bool = False,
) -> dict:
    from app.modules.accounts_finance.phase3_models import PaymentGatewayWebhookEvent

    if not trusted_internal and not verify_webhook_signature(body, signature):
        if signature:
            await PaymentGatewayFailure(
                tenant_id=tenant_id,
                failure_id=f"pf_{uuid4().hex[:10]}",
                code="invalid_signature",
                message="Webhook signature validation failed",
            ).insert()
        raise AppError(code="FORBIDDEN", message="Invalid payment webhook signature", status_code=403)

    transaction_id = payload.get("transaction_id")
    gateway_reference = payload.get("gateway_reference") or payload.get("reference")
    provider_event_id = payload.get("event_id") or hashlib.sha256(body).hexdigest()
    amount = float(payload.get("amount") or 0)
    if not transaction_id or not gateway_reference:
        raise AppError(code="VALIDATION_ERROR", message="transaction_id and gateway_reference required", status_code=422)

    tx = await PaymentTransaction.find_one(Eq(PaymentTransaction.transaction_id, transaction_id))
    if tx is None:
        raise AppError(code="NOT_FOUND", message="Payment transaction not found", status_code=404)
    tenant_id = tx.tenant_id

    existing_event = await PaymentGatewayWebhookEvent.find_one(
        Eq(PaymentGatewayWebhookEvent.tenant_id, tenant_id),
        Eq(PaymentGatewayWebhookEvent.provider_event_id, provider_event_id),
    )
    if existing_event:
        return {"transaction_id": transaction_id, "status": tx.status.value, "duplicate": True}

    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    await PaymentGatewayWebhookEvent(
        tenant_id=tenant_id,
        event_id=f"evt_{uuid4().hex[:12]}",
        provider_event_id=provider_event_id,
        transaction_id=transaction_id,
        signature_valid=bool(signature),
        processed=False,
        payload_hash=payload_hash,
    ).insert()

    if round_money(amount) != round_money(tx.amount) and amount > 0:
        await PaymentGatewayFailure(
            tenant_id=tenant_id,
            failure_id=f"pf_{uuid4().hex[:10]}",
            transaction_id=transaction_id,
            code="amount_mismatch",
            message=f"Expected {tx.amount} got {amount}",
        ).insert()
        tx.status = PaymentTransactionStatus.VERIFICATION_REQUIRED
        await tx.save()
        await _log_verification(tenant_id, transaction_id, "amount_check", "failed", detail=str(amount))
        raise AppError(code="VALIDATION_ERROR", message="Payment amount mismatch", status_code=422)

    if tx.status == PaymentTransactionStatus.SUCCESS and tx.webhook_verified:
        return {"transaction_id": transaction_id, "status": tx.status.value, "duplicate": True}

    tx.status = PaymentTransactionStatus.SUCCESS
    tx.gateway_reference = str(gateway_reference)
    tx.webhook_verified = True
    tx.updated_at = utcnow()
    await tx.save()

    attempt = await OnlinePaymentAttempt.find_one(
        Eq(OnlinePaymentAttempt.tenant_id, tenant_id),
        Eq(OnlinePaymentAttempt.transaction_id, transaction_id),
    )
    if attempt:
        attempt.status = "verified"
        attempt.verified_at = utcnow()
        await attempt.save()

    await _log_verification(tenant_id, transaction_id, "webhook", "verified", detail=str(gateway_reference))
    await reconcile_successful_payment(tx)

    event_doc = await PaymentGatewayWebhookEvent.find_one(
        Eq(PaymentGatewayWebhookEvent.tenant_id, tenant_id),
        Eq(PaymentGatewayWebhookEvent.provider_event_id, provider_event_id),
    )
    if event_doc:
        event_doc.processed = True
        await event_doc.save()

    return {"transaction_id": transaction_id, "status": tx.status.value, "verified": True}


async def mark_payment_failed(tenant_id: PydanticObjectId, transaction_id: str, *, code: str, message: str) -> None:
    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, transaction_id),
    )
    if tx is None:
        return
    if tx.status == PaymentTransactionStatus.SUCCESS:
        return
    tx.status = PaymentTransactionStatus.FAILED
    tx.updated_at = utcnow()
    await tx.save()
    await PaymentGatewayFailure(
        tenant_id=tenant_id,
        failure_id=f"pf_{uuid4().hex[:10]}",
        transaction_id=transaction_id,
        code=code,
        message=message,
    ).insert()
    attempt = await OnlinePaymentAttempt.find_one(
        Eq(OnlinePaymentAttempt.tenant_id, tenant_id),
        Eq(OnlinePaymentAttempt.transaction_id, transaction_id),
    )
    if attempt:
        attempt.status = "failed"
        attempt.failure_code = code
        attempt.failure_detail = message
        await attempt.save()