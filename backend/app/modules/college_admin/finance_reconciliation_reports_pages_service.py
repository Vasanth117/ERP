"""Payment reconciliation and financial reports pages (CA 10)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta

from beanie.odm.operators.find.comparison import Eq
from zoneinfo import ZoneInfo

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.accounts_finance.phase7_enums import ReconciliationMatchStatus, ReconciliationPeriodStatus
from app.modules.accounts_finance.phase7_models import (
    PaymentReconciliationBatch,
    PaymentReconciliationException,
    PaymentReconciliationMatch,
    PaymentReconciliationPeriod,
)
from app.modules.accounts_finance.phase8_models import (
    FinanceReportExecutionHistory,
    FinanceSavedReport,
    FinanceScheduledReport,
)
from app.modules.college_admin.finance_admin_models import PaymentReconciliationRecord
from app.modules.college_admin.finance_overview_service import _verified_payment
from app.modules.college_admin.finance_reconciliation_reports_shared import (
    batch_label,
    format_count,
    format_inr,
    format_inr_compact,
    month_label,
    page_numbers,
    period_range_label,
    reconciliation_sub_nav,
    schedule_label,
    short_date,
    showing_slice,
    source_label,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FinanceFinancialReportRow,
    FinanceReconciliationBatchRow,
    FinancialReportsPageRead,
    PaymentReconciliationPageRead,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.finance.finance_models import PaymentTransaction

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10


def _pagination(total: int, page: int, page_size: int) -> tuple[PoliciesPagination, int]:
    total_pages = math.ceil(total / page_size) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * page_size
    return (
        PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        start,
    )


def _batch_status(batch: PaymentReconciliationBatch, unmatched: int) -> tuple[str, str]:
    if unmatched > 0 or batch.status in (
        ReconciliationPeriodStatus.EXCEPTION,
        ReconciliationPeriodStatus.UNMATCHED,
        ReconciliationPeriodStatus.PARTIALLY_MATCHED,
    ):
        return "Exceptions", "error"
    if batch.status in (ReconciliationPeriodStatus.RECONCILED, ReconciliationPeriodStatus.CONFIRMED):
        return "Completed", "success"
    if batch.status in (ReconciliationPeriodStatus.MATCHED, ReconciliationPeriodStatus.IMPORTED, ReconciliationPeriodStatus.PROCESSING):
        return "Matched", "success"
    return "Matched", "success"


def _financial_year_label(today: date) -> str:
    if today.month >= 4:
        start = today.year
        end = today.year + 1
    else:
        start = today.year - 1
        end = today.year
    return f"FY {start}-{str(end)[-2:]}"


def _default_report_rows(now) -> list[FinanceFinancialReportRow]:
    today = now.astimezone(_IST).date() if now.tzinfo else now.date()
    fy = _financial_year_label(today)
    month = today.strftime("%b %Y")
    run = short_date(now)
    return [
        FinanceFinancialReportRow(
            report_key="fee_collection",
            report_label="Fee collection",
            period_label=fy,
            format_label="PDF, Excel",
            last_run_label=run,
            schedule_label="Weekly",
            detail_href="/college-admin/finance/financial-reports?report=fee_collection",
        ),
        FinanceFinancialReportRow(
            report_key="outstanding_dues",
            report_label="Outstanding dues",
            period_label=f"As on {run}",
            format_label="PDF, CSV",
            last_run_label=run,
            schedule_label="Daily",
            detail_href="/college-admin/finance/financial-reports?report=outstanding_dues",
        ),
        FinanceFinancialReportRow(
            report_key="daily_collection",
            report_label="Daily collection",
            period_label=month,
            format_label="PDF",
            last_run_label=run,
            schedule_label="Daily",
            detail_href="/college-admin/finance/financial-reports?report=daily_collection",
        ),
        FinanceFinancialReportRow(
            report_key="refunds_reversals",
            report_label="Refunds and reversals",
            period_label=fy,
            format_label="CSV",
            last_run_label=short_date(now - timedelta(days=1)),
            schedule_label="Monthly",
            detail_href="/college-admin/finance/financial-reports?report=refunds_reversals",
        ),
    ]


async def get_payment_reconciliation_page(scope: AccessScope, *, page: int = 1) -> PaymentReconciliationPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    batches = await PaymentReconciliationBatch.find(Eq(PaymentReconciliationBatch.tenant_id, tenant_id)).sort("-created_at").to_list()
    periods = await PaymentReconciliationPeriod.find(Eq(PaymentReconciliationPeriod.tenant_id, tenant_id)).to_list()
    period_by_id = {p.period_id: p for p in periods}
    matches = await PaymentReconciliationMatch.find(Eq(PaymentReconciliationMatch.tenant_id, tenant_id)).to_list()
    exceptions = await PaymentReconciliationException.find(Eq(PaymentReconciliationException.tenant_id, tenant_id)).to_list()

    matches_by_batch: dict[str, list[PaymentReconciliationMatch]] = defaultdict(list)
    for match in matches:
        matches_by_batch[match.batch_id].append(match)
    exceptions_by_batch: dict[str, int] = defaultdict(int)
    for exc in exceptions:
        if not exc.resolved:
            exceptions_by_batch[exc.batch_id] += 1

    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()
    verified_txs = [t for t in txs if _verified_payment(t)]
    legacy_recon = await PaymentReconciliationRecord.find(Eq(PaymentReconciliationRecord.tenant_id, tenant_id)).to_list()
    reconciled_ids = {r.transaction_id for r in legacy_recon if r.reconciled}

    to_reconcile = len(verified_txs) if verified_txs else len(txs)
    if reconciled_ids:
        to_reconcile = len([t for t in verified_txs if t.transaction_id not in reconciled_ids])

    confirmed = sum(1 for m in matches if m.match_status == ReconciliationMatchStatus.CONFIRMED)
    if not matches and reconciled_ids:
        confirmed = len(reconciled_ids)

    unmatched_count = len([e for e in exceptions if not e.resolved])
    unmatched_count += sum(
        1 for m in matches if m.match_status in (ReconciliationMatchStatus.UNMATCHED, ReconciliationMatchStatus.REJECTED)
    )
    if not matches and legacy_recon:
        unmatched_count = len([r for r in legacy_recon if not r.reconciled])

    unmatched_amount = sum(abs(m.amount_delta) for m in matches if m.amount_delta) or 0.0
    if unmatched_count and unmatched_amount <= 0:
        unmatched_amount = sum(t.amount for t in verified_txs if t.transaction_id not in reconciled_ids) * 0.01

    matched_count = confirmed if confirmed else max(0, to_reconcile - unmatched_count)
    match_pct = round((matched_count / to_reconcile) * 100, 1) if to_reconcile else 0.0

    diff_amount = sum(abs(m.amount_delta) for m in matches if m.match_status != ReconciliationMatchStatus.CONFIRMED)
    diff_batches = sum(1 for bid, n in exceptions_by_batch.items() if n > 0)

    kpis = [
        UserDashboardKpi(
            key="to_reconcile",
            label="To reconcile",
            value=format_count(to_reconcile),
            hint_line=month_label(),
            hint_tone="blue",
        ),
        UserDashboardKpi(
            key="matched",
            label="Matched",
            value=format_count(matched_count),
            hint_line=f"{match_pct}%",
            hint_tone="green",
        ),
        UserDashboardKpi(
            key="unmatched",
            label="Unmatched",
            value=str(unmatched_count),
            hint_line=format_inr_compact(unmatched_amount),
            hint_tone="rose",
        ),
        UserDashboardKpi(
            key="difference",
            label="Difference",
            value=format_inr(diff_amount),
            hint_line=f"{diff_batches or (1 if unmatched_count else 0)} batch",
            hint_tone="amber",
        ),
    ]

    total = len(batches)
    pagination, start = _pagination(total, page, _PAGE_SIZE)
    page_batches = batches[start : start + _PAGE_SIZE]

    table_rows: list[FinanceReconciliationBatchRow] = []
    for batch in page_batches:
        batch_matches = matches_by_batch.get(batch.batch_id, [])
        matched_n = sum(1 for m in batch_matches if m.match_status == ReconciliationMatchStatus.CONFIRMED)
        unmatched_n = exceptions_by_batch.get(batch.batch_id, 0)
        unmatched_n += sum(1 for m in batch_matches if m.match_status == ReconciliationMatchStatus.UNMATCHED)
        period = period_by_id.get(batch.period_id)
        period_label = period.label if period and period.label else (
            period_range_label(period.period_start, period.period_end) if period else "—"
        )
        status_label, status_tone = _batch_status(batch, unmatched_n)
        table_rows.append(
            FinanceReconciliationBatchRow(
                batch_label=batch_label(batch.batch_id),
                source_label=source_label(batch.source_type),
                period_label=period_label,
                matched_label=str(matched_n),
                unmatched_label=str(unmatched_n),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/payment-reconciliation",
            )
        )

    return PaymentReconciliationPageRead(
        page_title="Payment Reconciliation",
        page_subtitle="Match ERP payments with bank and gateway files",
        new_batch_label="New batch",
        new_batch_href="/college-admin/finance/payment-reconciliation?batch=1",
        kpis=kpis,
        sub_nav=reconciliation_sub_nav("reconciliation"),
        batches_section_title="Batches",
        table_headers=["Batch", "Source", "Period", "Matched", "Unmatched", "Status"],
        batch_rows=table_rows,
        showing_label=showing_slice(len(page_batches), total),
        pagination=pagination,
        generated_at=now,
    )


async def get_financial_reports_page(scope: AccessScope, *, page: int = 1) -> FinancialReportsPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    saved = await FinanceSavedReport.find(Eq(FinanceSavedReport.tenant_id, tenant_id)).sort("-updated_at").to_list()
    schedules = await FinanceScheduledReport.find(Eq(FinanceScheduledReport.tenant_id, tenant_id)).to_list()
    schedule_by_report = {s.report_id: s for s in schedules}
    executions = await FinanceReportExecutionHistory.find(Eq(FinanceReportExecutionHistory.tenant_id, tenant_id)).sort("-created_at").to_list()
    last_run_by_report: dict[str, FinanceReportExecutionHistory] = {}
    for row in executions:
        if row.report_id and row.report_id not in last_run_by_report:
            last_run_by_report[row.report_id] = row

    catalog_rows: list[FinanceFinancialReportRow] = []
    if saved:
        for report in saved:
            config = report.config or {}
            period = str(config.get("period_label") or config.get("period") or _financial_year_label(now.date()))
            formats = config.get("formats") or config.get("format")
            if isinstance(formats, list):
                format_label = ", ".join(formats)
            else:
                format_label = str(formats or "PDF")
            schedule = schedule_by_report.get(report.report_id)
            last = last_run_by_report.get(report.report_id)
            catalog_rows.append(
                FinanceFinancialReportRow(
                    report_key=report.report_id,
                    report_label=report.name,
                    period_label=period,
                    format_label=format_label,
                    last_run_label=short_date(last.created_at) if last else short_date(report.updated_at),
                    schedule_label=schedule_label(schedule.cron_hint if schedule else None),
                    detail_href=f"/college-admin/finance/financial-reports?report={report.report_id}",
                )
            )
    else:
        catalog_rows = _default_report_rows(now)

    total = len(catalog_rows)
    pagination, start = _pagination(total, page, _PAGE_SIZE)
    page_rows = catalog_rows[start : start + _PAGE_SIZE]

    return FinancialReportsPageRead(
        page_title="Financial Reports",
        page_subtitle="Collection, dues and refund reports",
        create_report_label="Create report",
        create_report_href="/college-admin/finance/financial-reports?create=1",
        sub_nav=reconciliation_sub_nav("reports"),
        reports_section_title="Reports",
        table_headers=["Report", "Period", "Format", "Last run", "Schedule"],
        report_rows=page_rows,
        list_count_label=f"{len(page_rows)} of {format_count(total)}",
        showing_label=showing_slice(len(page_rows), total),
        pagination=pagination,
        generated_at=now,
    )