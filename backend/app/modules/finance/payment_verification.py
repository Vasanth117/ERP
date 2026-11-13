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
    doc = await PaymentTransaction.find_one({"transaction_id": transaction_id})
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Payment transaction not found", status_code=404)
    if doc.status == PaymentTransactionStatus.SUCCESS:
        return doc
    doc.status = PaymentTransactionStatus.SUCCESS
    doc.gateway_reference = gateway_reference
    doc.webhook_verified = True
    await doc.save()
    await reconcile_successful_payment(doc)
    return doc
