"""Payment gateway verification (server-side only)."""

import hashlib
import hmac

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction
from app.modules.finance.payment_reconciliation import reconcile_successful_payment


def verify_webhook_signature(payload: bytes, signature: str | None) -> bool:
    settings = get_settings()
    secret = getattr(settings, "payment_webhook_secret", None) or ""
    if not secret:
        return False
    if not signature:
        return False
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


async def apply_verified_payment(transaction_id: str, *, gateway_reference: str) -> PaymentTransaction:
    from app.modules.accounts_finance.payment_core import process_payment_webhook

    result = await process_payment_webhook(
        tenant_id=None,
        body=f'{{"transaction_id":"{transaction_id}","gateway_reference":"{gateway_reference}"}}'.encode(),
        signature=None,
        payload={"transaction_id": transaction_id, "gateway_reference": gateway_reference},
        trusted_internal=True,
    )
    doc = await PaymentTransaction.find_one({"transaction_id": transaction_id})
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Payment transaction not found", status_code=404)
    _ = result
    return doc
