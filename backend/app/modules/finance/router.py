"""Finance module — payment webhooks and admin endpoints."""

import json

from fastapi import APIRouter, Header, Request, status

from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.core.exceptions import AppError
from app.modules.accounts_finance.payment_core import process_payment_webhook
from app.modules.finance.payment_verification import verify_webhook_signature

router = APIRouter()


@router.post("/webhooks/payments", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
async def payment_webhook_route(
    request: Request,
    x_payment_signature: str | None = Header(default=None, alias="X-Payment-Signature"),
) -> ApiResponse[dict]:
    body = await request.body()
    if not verify_webhook_signature(body, x_payment_signature):
        raise AppError(code="FORBIDDEN", message="Invalid payment webhook signature", status_code=403)
    try:
        payload = json.loads(body.decode() or "{}")
    except json.JSONDecodeError as exc:
        raise AppError(code="VALIDATION_ERROR", message="Invalid JSON payload", status_code=422) from exc
    transaction_id = payload.get("transaction_id")
    gateway_reference = payload.get("gateway_reference") or payload.get("reference")
    if not transaction_id or not gateway_reference:
        raise AppError(code="VALIDATION_ERROR", message="transaction_id and gateway_reference required", status_code=422)
    result = await process_payment_webhook(
        tenant_id=None,
        body=body,
        signature=x_payment_signature,
        payload=payload,
    )
    return success_response(result, request_id=get_request_id())
