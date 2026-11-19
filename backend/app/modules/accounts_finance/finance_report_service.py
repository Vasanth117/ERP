"""Financial reports, analytics workspace, saved reports, and exports."""

import csv
import io
import uuid
from datetime import date
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.dashboard_service import get_finance_dashboard
from app.modules.accounts_finance.finance_report_repository import (
    report_accounting_placeholders,
    report_analytics_trends,
    report_fee_collections,
    report_invoice_register,
    report_invoice_summary_counts,
    report_outstanding,
    report_payments,
    report_refund_reconciliation,
    report_scholarship_concession,
    workspace_net_position,
)
from app.modules.accounts_finance.phase8_models import FinanceReportExecutionHistory, FinanceSavedReport
from app.modules.accounts_finance.phase8_schemas import ReportCategoryInfo, ReportPreviewResponse, SavedReportRead
from app.modules.accounts_finance.policy import (
    authorize_finance_report_export,
    authorize_finance_report_manage,
    authorize_finance_report_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit

REPORT_CATALOG: list[ReportCategoryInfo] = [
    ReportCategoryInfo(category="fee_collections", label="Fee collection reports", supported_group_by=["day", "month", "payment_method", "gateway", "academic_year"]),
    ReportCategoryInfo(category="invoice_register", label="Invoice register", supported_fields=["invoice_id", "amount", "status"]),
    ReportCategoryInfo(category="invoice_summary", label="Invoice and demand summary"),
    ReportCategoryInfo(category="outstanding", label="Student outstanding", supported_group_by=["student", "programme", "academic_year"]),
    ReportCategoryInfo(category="payments", label="Payment reports"),
    ReportCategoryInfo(category="scholarship_concession", label="Scholarship and concession"),
    ReportCategoryInfo(category="refund_reconciliation", label="Refund and reconciliation"),
    ReportCategoryInfo(category="accounting", label="Accounting reports (GL)"),
    ReportCategoryInfo(category="analytics", label="Operational analytics"),
]


def _parse_filters(raw: dict[str, Any]) -> dict[str, Any]:
    out = dict(raw)
    for key in ("date_from", "date_to"):
        if isinstance(out.get(key), str):
            out[key] = date.fromisoformat(out[key])
    return out


async def get_report_workspace(scope: AccessScope, **dashboard_kwargs) -> dict:
    authorize_finance_report_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    dashboard = await get_finance_dashboard(scope, **dashboard_kwargs)
    filters = _parse_filters({k: v for k, v in dashboard_kwargs.items() if v is not None})
    net = await workspace_net_position(tenant_id, filters)
    return {
        "dashboard": dashboard,
        "income_expense_note": net["note"],
        "net_financial_position": net,
        "catalog": REPORT_CATALOG,
    }


async def list_report_categories(scope: AccessScope) -> list[ReportCategoryInfo]:
    authorize_finance_report_read(scope)
    require_finance_tenant_scope(scope)
    return REPORT_CATALOG


async def preview_report(scope: AccessScope, category: str, filters: dict[str, Any] | None = None) -> ReportPreviewResponse:
    authorize_finance_report_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    filters = _parse_filters(filters or {})
    group_by = filters.pop("group_by", "day")
    rows: list[dict]
    totals: dict = {}
    if category == "fee_collections":
        rows = await report_fee_collections(tenant_id, filters, group_by=group_by)
        totals = {"amount": sum(r["amount"] for r in rows)}
    elif category == "invoice_register":
        rows = await report_invoice_register(tenant_id, filters)
        totals = {"amount": sum(r["amount"] for r in rows)}
    elif category == "invoice_summary":
        summary = await report_invoice_summary_counts(tenant_id, filters)
        rows = [{"metric": k, "value": v} for k, v in summary.items()]
        totals = summary
    elif category == "outstanding":
        rows = await report_outstanding(tenant_id, filters, group_by=group_by if group_by != "day" else "student")
        totals = {"outstanding": sum(r["outstanding"] for r in rows)}
    elif category == "payments":
        payload = await report_payments(tenant_id, filters)
        rows = [{"section": "summary", **payload["summary"]}]
        rows.extend({"payment_method": k, "amount": v} for k, v in payload["verified_by_method"].items())
        totals = payload["summary"]
    elif category == "scholarship_concession":
        payload = await report_scholarship_concession(tenant_id, filters)
        rows = [{"metric": k, "value": v} for k, v in payload.items()]
        totals = payload
    elif category == "refund_reconciliation":
        payload = await report_refund_reconciliation(tenant_id, filters)
        rows = [{"metric": k, "value": v} for k, v in payload.items()]
        totals = payload
    elif category == "accounting":
        payload = await report_accounting_placeholders(tenant_id)
        rows = [{"report": k, **v} for k, v in payload.items()]
        totals = {}
    elif category == "analytics":
        payload = await report_analytics_trends(tenant_id, filters)
        rows = payload.get("collection_trend", [])
        totals = {k: v for k, v in payload.items() if k != "collection_trend"}
    else:
        raise AppError(code="VALIDATION_ERROR", message=f"Unknown report category: {category}", status_code=400)
    await FinanceReportExecutionHistory(
        tenant_id=tenant_id,
        execution_id=f"rex_{uuid.uuid4().hex[:12]}",
        report_id=None,
        category=category,
        export_format=None,
        row_count=len(rows),
        actor_id=scope.user_id,
    ).insert()
    return ReportPreviewResponse(category=category, filters=filters, rows=rows, totals=totals, row_count=len(rows))


async def save_report(scope: AccessScope, payload: dict) -> SavedReportRead:
    authorize_finance_report_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    report_id = f"srpt_{uuid.uuid4().hex[:10]}"
    now = utcnow()
    doc = FinanceSavedReport(
        tenant_id=tenant_id,
        report_id=report_id,
        name=payload["name"],
        category=payload["category"],
        config=payload.get("config") or {},
        created_by=scope.user_id,
        shared=bool(payload.get("shared")),
        created_at=now,
        updated_at=now,
    )
    await doc.insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.report.save",
        module="accounts_finance",
        resource_type="saved_report",
        resource_id=report_id,
    )
    return SavedReportRead(
        report_id=doc.report_id,
        name=doc.name,
        category=doc.category,
        config=doc.config,
        shared=doc.shared,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def list_saved_reports(scope: AccessScope) -> list[SavedReportRead]:
    authorize_finance_report_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await FinanceSavedReport.find(Eq(FinanceSavedReport.tenant_id, tenant_id)).to_list()
    visible = [r for r in rows if r.shared or r.created_by == scope.user_id]
    return [
        SavedReportRead(
            report_id=r.report_id,
            name=r.name,
            category=r.category,
            config=r.config,
            shared=r.shared,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in visible
    ]


async def run_saved_report(scope: AccessScope, report_id: str) -> ReportPreviewResponse:
    authorize_finance_report_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    saved = await FinanceSavedReport.find_one(
        Eq(FinanceSavedReport.tenant_id, tenant_id),
        Eq(FinanceSavedReport.report_id, report_id),
    )
    if saved is None:
        raise AppError(code="NOT_FOUND", message="Saved report not found", status_code=404)
    if not saved.shared and saved.created_by != scope.user_id:
        raise AppError(code="FORBIDDEN", message="Saved report not accessible", status_code=403)
    filters = saved.config.get("filters") or {}
    return await preview_report(scope, saved.category, filters)


async def export_report_csv(scope: AccessScope, category: str, filters: dict[str, Any] | None = None) -> tuple[str, str]:
    authorize_finance_report_export(scope)
    preview = await preview_report(scope, category, filters)
    buffer = io.StringIO()
    if preview.rows:
        writer = csv.DictWriter(buffer, fieldnames=list(preview.rows[0].keys()))
        writer.writeheader()
        writer.writerows(preview.rows)
    else:
        buffer.write("no_rows\n")
    tenant_id = require_finance_tenant_scope(scope)
    await FinanceReportExecutionHistory(
        tenant_id=tenant_id,
        execution_id=f"rex_{uuid.uuid4().hex[:12]}",
        report_id=None,
        category=category,
        export_format="csv",
        row_count=preview.row_count,
        actor_id=scope.user_id,
    ).insert()
    filename = f"finance_{category}_{utcnow().strftime('%Y%m%d')}.csv"
    return filename, buffer.getvalue()