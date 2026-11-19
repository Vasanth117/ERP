# Finance Staff — Phase 3 (Online + Offline Payments)

Aligned with `backend_and_frontend.md`. Reuses authoritative `payment_transactions`, `payment_receipts`, `student_fee_demands`, `student_financial_ledger`; receipt creation stays in `payment_reconciliation.reconcile_successful_payment` only.

## APIs

### Gateway (`/accounts-finance/payments/gateway-config`)
- `PUT` / `GET` — tenant config, **secret refs only** (`env://…`), never plaintext keys

### Online
- Student portal: existing `POST /students/me/finance/payments/initiate` now calls `payment_core.initiate_online_payment` (optional partial `amount`)
- Webhook: `POST /api/v1/finance/webhooks/payments` → `process_payment_webhook` (signature, amount, idempotent events)
- Staff history: `GET /accounts-finance/payments/transactions`

### Offline (`/accounts-finance/payments/offline`)
- `POST` record (pending / cheque_pending)
- `POST …/verify` posts via reconciliation (receipt + ledger)
- `POST …/reverse`, batches, handover, daily report

## Collections (new)

`payment_gateway_configurations`, `online_payment_orders`, `online_payment_attempts`, `payment_gateway_webhook_events`, `payment_verification_history`, `payment_gateway_failures`, `offline_payment_records`, `offline_payment_verification_history`, `offline_collection_batches`, `offline_collection_handover_records`, `offline_payment_instruments`, `offline_payment_reversals`

## Partial payments

`reconcile_successful_payment` sums verified tx per demand → `partially_paid` or `paid`.

## Limitations

- Stub gateway only (no live Razorpay/Stripe client).
- Refunds remain in existing refund modules.
- Webhook requires `PAYMENT_WEBHOOK_SECRET` env for signature validation in production.

## Tests

```bash
cd backend
py -m pytest tests/test_finance_staff_phase3.py -q --disable-warnings
```