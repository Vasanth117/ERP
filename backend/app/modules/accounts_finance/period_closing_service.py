"""Financial period management, pre-closing validation, and controlled closing."""

import uuid
from datetime import date
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.finance_report_repository import report_fee_collections, report_refund_reconciliation
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase2_enums import StudentInvoiceStatus
from app.modules.accounts_finance.phase3_enums import OfflinePaymentStatus
from app.modules.accounts_finance.phase3_models import OfflinePaymentRecord
from app.modules.accounts_finance.phase7_enums import RefundWorkflowStatus
from app.modules.accounts_finance.phase7_models import PaymentReconciliationException, StudentRefundRequest
from app.modules.accounts_finance.phase8_enums import ClosingRunStatus, PeriodLifecycleStatus
from app.modules.accounts_finance.phase8_models import (
    FinancialPeriodClosingCheck,
    FinancialPeriodClosingRun,
    FinancialPeriodClosingSummary,
    FinancialPeriodReopeningRequest,
    FinancialPeriodStatusHistory,
    FinancialYear,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_period_close,
    authorize_finance_period_manage,
    authorize_finance_period_read,
    authorize_finance_period_reopen_approve,
    require_finance_tenant_scope,
)
from app.modules.college_admin.finance_admin_models import FinancialPeriod, FinancialPeriodStatus, PaymentReconciliationRecord
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeInvoice


async def create_financial_year(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_period_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    if payload["end_date"] < payload["start_date"]:
        raise AppError(code="VALIDATION_ERROR", message="end_date must be on or after start_date", status_code=400)
    existing = await FinancialYear.find_one(
        Eq(FinancialYear.tenant_id, tenant_id),
        Eq(FinancialYear.financial_year_id, payload["financial_year_id"]),
    )
    if existing:
        raise AppError(code="CONFLICT", message="Financial year already exists", status_code=409)
    doc = FinancialYear(
        tenant_id=tenant_id,
        financial_year_id=payload["financial_year_id"],
        label=payload["label"],
        start_date=payload["start_date"],
        end_date=payload["end_date"],
        academic_year_labels=payload.get("academic_year_labels") or [],
    )
    await doc.insert()
    return {"financial_year_id": doc.financial_year_id, "label": doc.label}


async def upsert_accounting_period(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_period_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    period = await FinancialPeriod.find_one(
        Eq(FinancialPeriod.tenant_id, tenant_id),
        Eq(FinancialPeriod.period_code, payload["period_code"]),
    )
    now = utcnow()
    if period is None:
        period = FinancialPeriod(
            tenant_id=tenant_id,
            period_code=payload["period_code"],
            label=payload["label"],
            start_date=payload["start_date"],
            end_date=payload["end_date"],
            financial_year_id=payload.get("financial_year_id"),
            period_type=payload.get("period_type") or "monthly",
            academic_year_label=payload.get("academic_year_label"),
            lifecycle_status=PeriodLifecycleStatus.OPEN.value,
            created_at=now,
            updated_at=now,
        )
        await period.insert()
        action = "create"
    else:
        if period.locked or period.lifecycle_status in (PeriodLifecycleStatus.CLOSED.value, PeriodLifecycleStatus.LOCKED.value):
            raise AppError(code="PERIOD_LOCKED", message="Period is closed; reopen before editing", status_code=409)
        period.label = payload["label"]
        period.start_date = payload["start_date"]
        period.end_date = payload["end_date"]
        period.financial_year_id = payload.get("financial_year_id")
        period.period_type = payload.get("period_type") or period.period_type
        period.academic_year_label = payload.get("academic_year_label")
        period.updated_at = now
        await period.save()
        action = "update"
    await FinancialPeriodStatusHistory(
        tenant_id=tenant_id,
        history_id=f"psth_{uuid.uuid4().hex[:12]}",
        period_code=period.period_code,
        from_status=None,
        to_status=period.lifecycle_status,
        actor_id=scope.user_id,
        note=f"period_{action}",
    ).insert()
    return {
        "period_code": period.period_code,
        "label": period.label,
        "start_date": period.start_date.isoformat(),
        "end_date": period.end_date.isoformat(),
        "status": period.status.value,
        "lifecycle_status": period.lifecycle_status,
        "locked": period.locked,
    }


async def list_accounting_periods(scope: AccessScope) -> list[dict]:
    authorize_finance_period_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await FinancialPeriod.find(Eq(FinancialPeriod.tenant_id, tenant_id)).to_list()
    return [
        {
            "period_code": p.period_code,
            "label": p.label,
            "start_date": p.start_date.isoformat(),
            "end_date": p.end_date.isoformat(),
            "financial_year_id": p.financial_year_id,
            "period_type": p.period_type,
            "academic_year_label": p.academic_year_label,
            "status": p.status.value,
            "lifecycle_status": p.lifecycle_status,
            "locked": p.locked,
            "closed_at": p.closed_at.isoformat() if p.closed_at else None,
        }
        for p in rows
    ]


async def _period_by_code(tenant_id, period_code: str) -> FinancialPeriod:
    period = await FinancialPeriod.find_one(Eq(FinancialPeriod.tenant_id, tenant_id), Eq(FinancialPeriod.period_code, period_code))
    if period is None:
        raise AppError(code="NOT_FOUND", message="Financial period not found", status_code=404)
    return period


async def _collect_pre_closing_checks(tenant_id, period: FinancialPeriod) -> list[dict]:
    checks: list[dict] = []
    invoices = await StudentFeeInvoice.find(Eq(StudentFeeInvoice.tenant_id, tenant_id)).to_list()
    for inv in invoices:
        if period.start_date <= (inv.billing_date or inv.due_date) <= period.end_date:
            if inv.invoice_status == StudentInvoiceStatus.DRAFT.value or not inv.published:
                checks.append({"check_type": "unposted_invoice", "severity": "blocking", "detail": inv.invoice_id, "reference_id": inv.invoice_id})

    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()
    for tx in txs:
        tx_day = tx.created_at.date()
        if period.start_date <= tx_day <= period.end_date:
            if tx.status == PaymentTransactionStatus.SUCCESS and tx.payment_mode == "offline" and not tx.webhook_verified:
                checks.append({"check_type": "pending_offline_verification", "severity": "warning", "detail": tx.transaction_id, "reference_id": tx.transaction_id})
            if tx.status in (PaymentTransactionStatus.PENDING, PaymentTransactionStatus.INITIATED):
                checks.append({"check_type": "unposted_payment", "severity": "warning", "detail": tx.transaction_id, "reference_id": tx.transaction_id})

    refunds = await StudentRefundRequest.find(Eq(StudentRefundRequest.tenant_id, tenant_id)).to_list()
    for row in refunds:
        if row.status not in (RefundWorkflowStatus.SUCCESSFUL, RefundWorkflowStatus.CANCELLED, RefundWorkflowStatus.FAILED):
            checks.append(
                {
                    "check_type": "pending_refund",
                    "severity": "warning",
                    "detail": row.refund_request_id,
                    "reference_id": row.refund_request_id,
                }
            )

    offline = await OfflinePaymentRecord.find(Eq(OfflinePaymentRecord.tenant_id, tenant_id)).to_list()
    for row in offline:
        if row.status == OfflinePaymentStatus.AWAITING_VERIFICATION:
            checks.append(
                {
                    "check_type": "offline_batch_pending",
                    "severity": "warning",
                    "detail": row.record_id,
                    "reference_id": row.record_id,
                }
            )

    legacy_unreconciled = await PaymentReconciliationRecord.find(
        Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
        Eq(PaymentReconciliationRecord.reconciled, False),
    ).count()
    if legacy_unreconciled:
        checks.append({"check_type": "reconciliation_exception", "severity": "warning", "detail": f"{legacy_unreconciled} legacy unreconciled", "reference_id": None})

    phase7_exceptions = await PaymentReconciliationException.find(Eq(PaymentReconciliationException.tenant_id, tenant_id)).to_list()
    for exc in phase7_exceptions:
        if not exc.resolved:
            checks.append({"check_type": "reconciliation_exception", "severity": "warning", "detail": exc.exception_id, "reference_id": exc.exception_id})

    return checks


async def initiate_closing_run(scope: AccessScope, period_code: str) -> dict:
    authorize_finance_period_close(scope)
    tenant_id = require_finance_tenant_scope(scope)
    period = await _period_by_code(tenant_id, period_code)
    if period.locked:
        raise AppError(code="CONFLICT", message="Period already locked", status_code=409)
    closing_run_id = f"cls_{uuid.uuid4().hex[:12]}"
    run = FinancialPeriodClosingRun(
        tenant_id=tenant_id,
        closing_run_id=closing_run_id,
        period_code=period_code,
        status=ClosingRunStatus.VALIDATION,
        initiated_by=scope.user_id,
    )
    await run.insert()
    raw_checks = await _collect_pre_closing_checks(tenant_id, period)
    stored: list[dict] = []
    for item in raw_checks:
        check_id = f"chk_{uuid.uuid4().hex[:12]}"
        doc = FinancialPeriodClosingCheck(
            tenant_id=tenant_id,
            check_id=check_id,
            closing_run_id=closing_run_id,
            check_type=item["check_type"],
            severity=item["severity"],
            detail=item["detail"],
            reference_id=item.get("reference_id"),
        )
        await doc.insert()
        stored.append({"check_id": check_id, **item})
    run.exception_count = len(stored)
    run.status = ClosingRunStatus.PENDING_APPROVAL
    run.updated_at = utcnow()
    await run.save()
    period.lifecycle_status = PeriodLifecycleStatus.UNDER_REVIEW.value
    period.updated_at = utcnow()
    await period.save()
    return {"closing_run_id": closing_run_id, "period_code": period_code, "checks": stored, "exception_count": len(stored)}


async def approve_period_close(scope: AccessScope, closing_run_id: str) -> dict:
    authorize_finance_period_close(scope)
    tenant_id = require_finance_tenant_scope(scope)
    run = await FinancialPeriodClosingRun.find_one(
        Eq(FinancialPeriodClosingRun.tenant_id, tenant_id),
        Eq(FinancialPeriodClosingRun.closing_run_id, closing_run_id),
    )
    if run is None:
        raise AppError(code="NOT_FOUND", message="Closing run not found", status_code=404)
    period = await _period_by_code(tenant_id, run.period_code)
    filters = {"date_from": period.start_date, "date_to": period.end_date}
    collections = await report_fee_collections(tenant_id, filters, group_by="month")
    collection_total = round_money(sum(r["amount"] for r in collections))
    refunds = await report_refund_reconciliation(tenant_id, filters)
    summary_id = f"sum_{uuid.uuid4().hex[:12]}"
    summary = FinancialPeriodClosingSummary(
        tenant_id=tenant_id,
        summary_id=summary_id,
        closing_run_id=closing_run_id,
        period_code=period.period_code,
        period_collections=collection_total,
        period_refunds=refunds.get("refund_completed", 0),
        pending_exceptions=[c.detail for c in await FinancialPeriodClosingCheck.find(Eq(FinancialPeriodClosingCheck.closing_run_id, closing_run_id)).to_list()],
        closing_balances={"verified_collections": collection_total},
    )
    await summary.insert()
    now = utcnow()
    prev_status = period.lifecycle_status
    period.status = FinancialPeriodStatus.CLOSED
    period.lifecycle_status = PeriodLifecycleStatus.CLOSED.value
    period.locked = True
    period.closed_at = now
    period.updated_at = now
    period.updated_by = scope.user_id
    await period.save()
    run.status = ClosingRunStatus.CLOSED
    run.approved_by = scope.user_id
    run.updated_at = now
    await run.save()
    await FinancialPeriodStatusHistory(
        tenant_id=tenant_id,
        history_id=f"psth_{uuid.uuid4().hex[:12]}",
        period_code=period.period_code,
        from_status=prev_status,
        to_status=period.lifecycle_status,
        actor_id=scope.user_id,
        note="approved_close",
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.period.close",
        module="accounts_finance",
        resource_type="financial_period",
        resource_id=period.period_code,
    )
    return {"period_code": period.period_code, "closing_run_id": closing_run_id, "summary_id": summary_id, "locked": True}


async def request_period_reopen(scope: AccessScope, period_code: str, reason: str, scope_note: str | None = None) -> dict:
    authorize_finance_period_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    await _period_by_code(tenant_id, period_code)
    request_id = f"ropn_{uuid.uuid4().hex[:12]}"
    doc = FinancialPeriodReopeningRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        period_code=period_code,
        reason=reason,
        scope_note=scope_note,
        requested_by=scope.user_id,
    )
    await doc.insert()
    return {"request_id": request_id, "status": doc.status}


async def approve_period_reopen(scope: AccessScope, request_id: str) -> dict:
    authorize_finance_period_reopen_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    req = await FinancialPeriodReopeningRequest.find_one(
        Eq(FinancialPeriodReopeningRequest.tenant_id, tenant_id),
        Eq(FinancialPeriodReopeningRequest.request_id, request_id),
    )
    if req is None:
        raise AppError(code="NOT_FOUND", message="Reopen request not found", status_code=404)
    if req.status != "submitted":
        raise AppError(code="CONFLICT", message="Request already processed", status_code=409)
    period = await _period_by_code(tenant_id, req.period_code)
    prev = period.lifecycle_status
    period.status = FinancialPeriodStatus.OPEN
    period.lifecycle_status = PeriodLifecycleStatus.REOPENED.value
    period.locked = False
    period.updated_at = utcnow()
    period.updated_by = scope.user_id
    await period.save()
    req.status = "approved"
    req.approved_by = scope.user_id
    await req.save()
    await FinancialPeriodStatusHistory(
        tenant_id=tenant_id,
        history_id=f"psth_{uuid.uuid4().hex[:12]}",
        period_code=period.period_code,
        from_status=prev,
        to_status=period.lifecycle_status,
        actor_id=scope.user_id,
        note=req.reason,
    ).insert()
    return {"period_code": period.period_code, "lifecycle_status": period.lifecycle_status, "reopen_request_id": request_id}


async def get_closing_run(scope: AccessScope, closing_run_id: str) -> dict:
    authorize_finance_period_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    run = await FinancialPeriodClosingRun.find_one(
        Eq(FinancialPeriodClosingRun.tenant_id, tenant_id),
        Eq(FinancialPeriodClosingRun.closing_run_id, closing_run_id),
    )
    if run is None:
        raise AppError(code="NOT_FOUND", message="Closing run not found", status_code=404)
    checks = await FinancialPeriodClosingCheck.find(Eq(FinancialPeriodClosingCheck.closing_run_id, closing_run_id)).to_list()
    summary = await FinancialPeriodClosingSummary.find_one(Eq(FinancialPeriodClosingSummary.closing_run_id, closing_run_id))
    return {
        "closing_run_id": run.closing_run_id,
        "period_code": run.period_code,
        "status": run.status.value,
        "exception_count": run.exception_count,
        "checks": [{"check_type": c.check_type, "severity": c.severity, "detail": c.detail, "resolved": c.resolved} for c in checks],
        "summary": None if summary is None else summary.model_dump(),
    }