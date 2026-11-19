"""Payment reconciliation periods, imports, matching and settlements."""

import csv
import io
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase7_enums import ReconciliationMatchStatus, ReconciliationPeriodStatus
from app.modules.accounts_finance.phase7_models import (
    PaymentReconciliationBatch,
    PaymentReconciliationException,
    PaymentReconciliationHistory,
    PaymentReconciliationImport,
    PaymentReconciliationMatch,
    PaymentReconciliationPeriod,
    PaymentReconciliationSourceRecord,
    PaymentSettlementRecord,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_reconciliation_confirm,
    authorize_finance_reconciliation_manage,
    authorize_finance_reconciliation_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.finance_admin_models import PaymentReconciliationRecord
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction


async def create_reconciliation_period(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_reconciliation_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    period_id = f"reconp_{uuid4().hex[:10]}"
    row = await PaymentReconciliationPeriod(
        tenant_id=tenant_id,
        period_id=period_id,
        label=payload["label"],
        period_start=payload["period_start"],
        period_end=payload["period_end"],
        status=ReconciliationPeriodStatus.NOT_STARTED,
    ).insert()
    return {"period_id": row.period_id, "status": row.status.value}


async def create_batch(scope: AccessScope, period_id: str, source_type: str) -> dict[str, Any]:
    authorize_finance_reconciliation_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    period = await PaymentReconciliationPeriod.find_one(
        Eq(PaymentReconciliationPeriod.tenant_id, tenant_id),
        Eq(PaymentReconciliationPeriod.period_id, period_id),
    )
    if period is None:
        raise AppError(code="NOT_FOUND", message="Reconciliation period not found", status_code=404)
    batch_id = f"reconb_{uuid4().hex[:10]}"
    batch = await PaymentReconciliationBatch(
        tenant_id=tenant_id,
        batch_id=batch_id,
        period_id=period_id,
        source_type=source_type,
        status=ReconciliationPeriodStatus.IMPORTED,
    ).insert()
    return {"batch_id": batch.batch_id, "period_id": period_id}


def _parse_csv(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise AppError(code="VALIDATION_ERROR", message="CSV missing header row", status_code=422)
    return list(reader)


async def import_statement(scope: AccessScope, batch_id: str, *, file_name: str, content: str, file_format: str = "csv") -> dict[str, Any]:
    authorize_finance_reconciliation_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    batch = await PaymentReconciliationBatch.find_one(
        Eq(PaymentReconciliationBatch.tenant_id, tenant_id),
        Eq(PaymentReconciliationBatch.batch_id, batch_id),
    )
    if batch is None:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    if file_format != "csv":
        raise AppError(code="VALIDATION_ERROR", message="Only CSV import supported in Phase 7", status_code=422)
    rows = _parse_csv(content)
    required = {"amount", "transaction_date"}
    id_cols = {"gateway_reference", "bank_reference", "external_reference", "transaction_id"}
    import_id = f"reconi_{uuid4().hex[:10]}"
    quarantined = 0
    saved = 0
    for idx, row in enumerate(rows):
        missing = required - set(row.keys())
        has_id = any(row.get(c) for c in id_cols if c in row)
        quarantine = bool(missing) or not has_id
        try:
            amount = round_money(float(row.get("amount", 0)))
        except (TypeError, ValueError):
            quarantine = True
            amount = 0.0
        dt = None
        raw_date = row.get("transaction_date") or row.get("date")
        if raw_date:
            try:
                dt = date.fromisoformat(str(raw_date)[:10])
            except ValueError:
                quarantine = True
        source_record_id = f"src_{uuid4().hex[:12]}"
        await PaymentReconciliationSourceRecord(
            tenant_id=tenant_id,
            source_record_id=source_record_id,
            batch_id=batch_id,
            external_reference=row.get("external_reference") or row.get("transaction_id"),
            gateway_reference=row.get("gateway_reference"),
            bank_reference=row.get("bank_reference") or row.get("utr"),
            transaction_date=dt,
            amount=amount,
            currency=row.get("currency", "INR"),
            payment_method=row.get("payment_method"),
            settlement_reference=row.get("settlement_reference"),
            gross_amount=float(row["gross_amount"]) if row.get("gross_amount") else amount,
            provider_fee=float(row["provider_fee"]) if row.get("provider_fee") else None,
            net_settlement=float(row["net_settlement"]) if row.get("net_settlement") else None,
            quarantined=quarantine,
            raw=row,
        ).insert()
        saved += 1
        if quarantine:
            quarantined += 1
            await PaymentReconciliationException(
                tenant_id=tenant_id,
                exception_id=f"rex_{uuid4().hex[:10]}",
                batch_id=batch_id,
                exception_type="quarantined_import_row",
                detail=f"Row {idx + 1} failed validation",
                source_record_id=source_record_id,
            ).insert()
    await PaymentReconciliationImport(
        tenant_id=tenant_id,
        import_id=import_id,
        batch_id=batch_id,
        file_name=file_name,
        format=file_format,
        row_count=saved,
        quarantined_count=quarantined,
        actor_id=scope.user_id,
    ).insert()
    batch.status = ReconciliationPeriodStatus.IMPORTED
    batch.updated_at = utcnow()
    await batch.save()
    await PaymentReconciliationHistory(
        tenant_id=tenant_id,
        history_id=f"rh_{uuid4().hex[:10]}",
        batch_id=batch_id,
        action="import",
        actor_id=scope.user_id,
        note=f"rows={saved}, quarantined={quarantined}",
    ).insert()
    return {"import_id": import_id, "row_count": saved, "quarantined_count": quarantined}


async def auto_match_batch(scope: AccessScope, batch_id: str) -> dict[str, Any]:
    authorize_finance_reconciliation_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    batch = await PaymentReconciliationBatch.find_one(
        Eq(PaymentReconciliationBatch.tenant_id, tenant_id),
        Eq(PaymentReconciliationBatch.batch_id, batch_id),
    )
    if batch is None:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    sources = await PaymentReconciliationSourceRecord.find(
        Eq(PaymentReconciliationSourceRecord.tenant_id, tenant_id),
        Eq(PaymentReconciliationSourceRecord.batch_id, batch_id),
        Eq(PaymentReconciliationSourceRecord.quarantined, False),
    ).to_list()
    exact = suggested = unmatched = 0
    batch.status = ReconciliationPeriodStatus.PROCESSING
    await batch.save()
    for src in sources:
        existing = await PaymentReconciliationMatch.find_one(
            Eq(PaymentReconciliationMatch.tenant_id, tenant_id),
            Eq(PaymentReconciliationMatch.source_record_id, src.source_record_id),
        )
        if existing:
            continue
        tx = None
        rule = None
        if src.external_reference:
            tx = await PaymentTransaction.find_one(
                Eq(PaymentTransaction.tenant_id, tenant_id),
                Eq(PaymentTransaction.transaction_id, src.external_reference),
            )
            if tx:
                rule = "transaction_id"
        if tx is None and src.gateway_reference:
            tx = await PaymentTransaction.find_one(
                Eq(PaymentTransaction.tenant_id, tenant_id),
                Eq(PaymentTransaction.gateway_reference, src.gateway_reference),
            )
            if tx:
                rule = "gateway_reference"
        if tx is None and src.bank_reference:
            tx = await PaymentTransaction.find_one(
                Eq(PaymentTransaction.tenant_id, tenant_id),
                Eq(PaymentTransaction.offline_reference, src.bank_reference),
            )
            if tx:
                rule = "bank_reference"
        match_id = f"match_{uuid4().hex[:10]}"
        if tx is None:
            await PaymentReconciliationMatch(
                tenant_id=tenant_id,
                match_id=match_id,
                batch_id=batch_id,
                source_record_id=src.source_record_id,
                match_status=ReconciliationMatchStatus.UNMATCHED,
            ).insert()
            await PaymentReconciliationException(
                tenant_id=tenant_id,
                exception_id=f"rex_{uuid4().hex[:10]}",
                batch_id=batch_id,
                exception_type="erp_missing",
                detail="No ERP transaction for source record",
                source_record_id=src.source_record_id,
            ).insert()
            unmatched += 1
            continue
        amount_delta = round_money(src.amount - tx.amount)
        status = ReconciliationMatchStatus.CONFIRMED if rule and amount_delta == 0 else ReconciliationMatchStatus.SUGGESTED
        if status == ReconciliationMatchStatus.CONFIRMED:
            exact += 1
        else:
            suggested += 1
            if amount_delta != 0:
                await PaymentReconciliationException(
                    tenant_id=tenant_id,
                    exception_id=f"rex_{uuid4().hex[:10]}",
                    batch_id=batch_id,
                    exception_type="amount_mismatch",
                    detail=f"delta={amount_delta}",
                    source_record_id=src.source_record_id,
                    erp_transaction_id=tx.transaction_id,
                ).insert()
        await PaymentReconciliationMatch(
            tenant_id=tenant_id,
            match_id=match_id,
            batch_id=batch_id,
            source_record_id=src.source_record_id,
            erp_transaction_id=tx.transaction_id,
            match_status=status,
            match_rule=rule,
            amount_delta=amount_delta,
        ).insert()
    if exact and not suggested and not unmatched:
        batch.status = ReconciliationPeriodStatus.MATCHED
    elif exact or suggested:
        batch.status = ReconciliationPeriodStatus.PARTIALLY_MATCHED
    else:
        batch.status = ReconciliationPeriodStatus.UNMATCHED
    batch.updated_at = utcnow()
    await batch.save()
    await PaymentReconciliationHistory(
        tenant_id=tenant_id,
        history_id=f"rh_{uuid4().hex[:10]}",
        batch_id=batch_id,
        action="auto_match",
        actor_id=scope.user_id,
        note=f"exact={exact}, suggested={suggested}, unmatched={unmatched}",
    ).insert()
    return {"batch_id": batch_id, "exact_matches": exact, "suggested_matches": suggested, "unmatched": unmatched, "status": batch.status.value}


async def confirm_match(scope: AccessScope, match_id: str, remark: str | None = None) -> dict[str, Any]:
    authorize_finance_reconciliation_confirm(scope)
    tenant_id = require_finance_tenant_scope(scope)
    match = await PaymentReconciliationMatch.find_one(
        Eq(PaymentReconciliationMatch.tenant_id, tenant_id),
        Eq(PaymentReconciliationMatch.match_id, match_id),
    )
    if match is None:
        raise AppError(code="NOT_FOUND", message="Match not found", status_code=404)
    if not match.erp_transaction_id:
        raise AppError(code="CONFLICT", message="Cannot confirm match without ERP transaction", status_code=409)
    match.match_status = ReconciliationMatchStatus.CONFIRMED
    match.confirmed_by = scope.user_id
    match.remark = remark
    match.updated_at = utcnow()
    await match.save()
    existing = await PaymentReconciliationRecord.find_one(
        Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
        Eq(PaymentReconciliationRecord.transaction_id, match.erp_transaction_id),
    )
    if existing:
        existing.reconciled = True
        existing.actor_id = scope.user_id
        await existing.save()
    else:
        tx = await PaymentTransaction.find_one(
            Eq(PaymentTransaction.tenant_id, tenant_id),
            Eq(PaymentTransaction.transaction_id, match.erp_transaction_id),
        )
        await PaymentReconciliationRecord(
            tenant_id=tenant_id,
            transaction_id=match.erp_transaction_id,
            gateway_reference=tx.gateway_reference if tx else None,
            reconciled=True,
            actor_id=scope.user_id,
        ).insert()
    await PaymentReconciliationHistory(
        tenant_id=tenant_id,
        history_id=f"rh_{uuid4().hex[:10]}",
        batch_id=match.batch_id,
        action="confirm_match",
        actor_id=scope.user_id,
        note=remark,
    ).insert()
    return {"match_id": match_id, "status": match.match_status.value}


async def unmatch(scope: AccessScope, match_id: str, reason: str) -> dict[str, Any]:
    authorize_finance_reconciliation_confirm(scope)
    tenant_id = require_finance_tenant_scope(scope)
    match = await PaymentReconciliationMatch.find_one(
        Eq(PaymentReconciliationMatch.tenant_id, tenant_id),
        Eq(PaymentReconciliationMatch.match_id, match_id),
    )
    if match is None:
        raise AppError(code="NOT_FOUND", message="Match not found", status_code=404)
    if match.erp_transaction_id:
        rec = await PaymentReconciliationRecord.find_one(
            Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
            Eq(PaymentReconciliationRecord.transaction_id, match.erp_transaction_id),
        )
        if rec:
            rec.reconciled = False
            rec.discrepancy_note = reason
            await rec.save()
    match.match_status = ReconciliationMatchStatus.REJECTED
    match.remark = reason
    match.updated_at = utcnow()
    await match.save()
    await PaymentReconciliationHistory(
        tenant_id=tenant_id,
        history_id=f"rh_{uuid4().hex[:10]}",
        batch_id=match.batch_id,
        action="unmatch",
        actor_id=scope.user_id,
        note=reason,
    ).insert()
    return {"match_id": match_id, "status": match.match_status.value}


async def confirm_batch(scope: AccessScope, batch_id: str) -> dict[str, Any]:
    authorize_finance_reconciliation_confirm(scope)
    tenant_id = require_finance_tenant_scope(scope)
    batch = await PaymentReconciliationBatch.find_one(
        Eq(PaymentReconciliationBatch.tenant_id, tenant_id),
        Eq(PaymentReconciliationBatch.batch_id, batch_id),
    )
    if batch is None:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    pending = await PaymentReconciliationMatch.find(
        Eq(PaymentReconciliationMatch.tenant_id, tenant_id),
        Eq(PaymentReconciliationMatch.batch_id, batch_id),
        Eq(PaymentReconciliationMatch.match_status, ReconciliationMatchStatus.SUGGESTED),
    ).count()
    if pending > 0:
        raise AppError(code="CONFLICT", message="Batch has unconfirmed suggested matches", status_code=409)
    batch.status = ReconciliationPeriodStatus.RECONCILED
    batch.updated_at = utcnow()
    await batch.save()
    period = await PaymentReconciliationPeriod.find_one(
        Eq(PaymentReconciliationPeriod.tenant_id, tenant_id),
        Eq(PaymentReconciliationPeriod.period_id, batch.period_id),
    )
    if period:
        period.status = ReconciliationPeriodStatus.RECONCILED
        period.updated_at = utcnow()
        await period.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="reconciliation_batch_confirmed",
        module="accounts_finance",
        resource_type="payment_reconciliation_batch",
        resource_id=batch_id,
    )
    return {"batch_id": batch_id, "status": batch.status.value}


async def record_settlement(scope: AccessScope, batch_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_reconciliation_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    settlement_id = f"stl_{uuid4().hex[:10]}"
    gross = round_money(payload["gross_amount"])
    fee = round_money(payload.get("provider_fee", 0))
    tax = round_money(payload.get("tax_on_fee", 0))
    net = round_money(payload.get("net_amount", gross - fee - tax))
    row = await PaymentSettlementRecord(
        tenant_id=tenant_id,
        settlement_id=settlement_id,
        batch_id=batch_id,
        settlement_reference=payload["settlement_reference"],
        settlement_date=payload.get("settlement_date"),
        gross_amount=gross,
        provider_fee=fee,
        tax_on_fee=tax,
        net_amount=net,
    ).insert()
    return {"settlement_id": row.settlement_id, "net_amount": net}


async def reconciliation_dashboard(scope: AccessScope) -> dict[str, Any]:
    authorize_finance_reconciliation_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    txs = await PaymentTransaction.find(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.status, PaymentTransactionStatus.SUCCESS),
    ).to_list()
    verified = [t for t in txs if t.payment_mode == "offline" or t.webhook_verified]
    records = await PaymentReconciliationRecord.find(Eq(PaymentReconciliationRecord.tenant_id, tenant_id)).to_list()
    reconciled_ids = {r.transaction_id for r in records if r.reconciled}
    awaiting = sum(1 for t in verified if t.transaction_id not in reconciled_ids)
    matched = len(reconciled_ids)
    exceptions = await PaymentReconciliationException.find(
        Eq(PaymentReconciliationException.tenant_id, tenant_id),
        Eq(PaymentReconciliationException.resolved, False),
    ).count()
    suggested = await PaymentReconciliationMatch.find(
        Eq(PaymentReconciliationMatch.tenant_id, tenant_id),
        Eq(PaymentReconciliationMatch.match_status, ReconciliationMatchStatus.SUGGESTED),
    ).count()
    unmatched = await PaymentReconciliationMatch.find(
        Eq(PaymentReconciliationMatch.tenant_id, tenant_id),
        Eq(PaymentReconciliationMatch.match_status, ReconciliationMatchStatus.UNMATCHED),
    ).count()
    total = len(verified) or 1
    pct = round(100.0 * matched / total, 2)
    return {
        "awaiting_reconciliation": awaiting,
        "matched_transactions": matched,
        "suggested_matches": suggested,
        "unmatched_records": unmatched,
        "open_exceptions": exceptions,
        "completion_percent": pct,
    }


async def list_exceptions(scope: AccessScope, pagination: Pagination, batch_id: str | None = None) -> Page[dict[str, Any]]:
    authorize_finance_reconciliation_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query: dict[str, Any] = {"tenant_id": tenant_id, "resolved": False}
    if batch_id:
        query["batch_id"] = batch_id
    total = await PaymentReconciliationException.find(query).count()
    rows = (
        await PaymentReconciliationException.find(query).sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    )
    items = [
        {
            "exception_id": r.exception_id,
            "batch_id": r.batch_id,
            "exception_type": r.exception_type,
            "detail": r.detail,
            "source_record_id": r.source_record_id,
            "erp_transaction_id": r.erp_transaction_id,
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)