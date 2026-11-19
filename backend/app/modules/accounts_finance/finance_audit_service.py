"""Finance audit dashboard, search, trace and export via institution audit."""

import csv
import io
import uuid
from datetime import date, datetime, time, timezone
from typing import Any

from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.accounts_finance.finance_trace_service import trace_from_root
from app.modules.accounts_finance.phase12_models import FinanceAuditExportHistory
from app.modules.accounts_finance.phase2_models import StudentInvoiceHistory
from app.modules.accounts_finance.phase4_models import StudentLedgerPostingHistory
from app.modules.accounts_finance.policy import authorize_finance_audit_export, authorize_finance_audit_read, require_finance_tenant_scope
from app.modules.college_admin.security_admin_models import InstitutionAuditLog


MODULE_PREFIX = "accounts_finance"


async def audit_dashboard(scope: AccessScope) -> dict:
    authorize_finance_audit_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    logs = await InstitutionAuditLog.find(Eq(InstitutionAuditLog.tenant_id, tenant_id)).to_list()
    finance_logs = [l for l in logs if l.module in (MODULE_PREFIX, "finance_ext", "accounts_finance")]
    actions = {}
    for row in finance_logs:
        actions[row.action] = actions.get(row.action, 0) + 1
    return {
        "total_finance_activities": len(finance_logs),
        "top_actions": dict(sorted(actions.items(), key=lambda x: -x[1])[:15]),
        "invoice_history_count": await StudentInvoiceHistory.find(Eq(StudentInvoiceHistory.tenant_id, tenant_id)).count(),
        "ledger_posting_history_count": await StudentLedgerPostingHistory.find(Eq(StudentLedgerPostingHistory.tenant_id, tenant_id)).count(),
        "immutable_note": "Institution audit logs are append-only",
    }


async def search_finance_audit(
    scope: AccessScope,
    *,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
) -> list[dict]:
    authorize_finance_audit_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query = InstitutionAuditLog.find(Eq(InstitutionAuditLog.tenant_id, tenant_id))
    if date_from:
        query = query.find(GTE(InstitutionAuditLog.created_at, datetime.combine(date_from, time.min, tzinfo=timezone.utc)))
    if date_to:
        query = query.find(LTE(InstitutionAuditLog.created_at, datetime.combine(date_to, time.max, tzinfo=timezone.utc)))
    rows = await query.sort("-created_at").limit(limit).to_list()
    rows = [r for r in rows if r.module in (MODULE_PREFIX, "finance_ext", "accounts_finance")]
    if action:
        rows = [r for r in rows if r.action == action]
    if resource_type:
        rows = [r for r in rows if r.resource_type == resource_type]
    if resource_id:
        rows = [r for r in rows if r.resource_id == resource_id]
    return [
        {
            "created_at": r.created_at.isoformat(),
            "action": r.action,
            "module": r.module,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "actor_id": str(r.actor_id) if r.actor_id else None,
            "outcome": r.outcome,
        }
        for r in rows
    ]


async def trace_transaction(scope: AccessScope, root_type: str, root_id: str) -> dict:
    authorize_finance_audit_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    edges = await trace_from_root(tenant_id, root_type, root_id)
    module_histories: list[dict] = []
    if root_type == "invoice":
        inv_hist = await StudentInvoiceHistory.find(
            Eq(StudentInvoiceHistory.tenant_id, tenant_id),
            Eq(StudentInvoiceHistory.invoice_id, root_id),
        ).to_list()
        module_histories.extend({"source": "student_invoice_history", **h.model_dump()} for h in inv_hist)
    if root_type in ("payment", "payment_transaction"):
        led = await StudentLedgerPostingHistory.find(
            Eq(StudentLedgerPostingHistory.tenant_id, tenant_id),
            Eq(StudentLedgerPostingHistory.source_reference, root_id),
        ).to_list()
        module_histories.extend({"source": "ledger_posting_history", **h.model_dump()} for h in led)
    audit = await search_finance_audit(scope, resource_id=root_id, limit=50)
    return {"root_type": root_type, "root_id": root_id, "relationships": edges, "module_histories": module_histories, "audit_events": audit}


async def export_finance_audit_csv(scope: AccessScope, filters: dict[str, Any] | None = None) -> tuple[str, str]:
    authorize_finance_audit_export(scope)
    tenant_id = require_finance_tenant_scope(scope)
    filters = filters or {}
    rows = await search_finance_audit(
        scope,
        action=filters.get("action"),
        resource_type=filters.get("resource_type"),
        resource_id=filters.get("resource_id"),
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        limit=int(filters.get("limit") or 500),
    )
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    export_id = f"fae_{uuid.uuid4().hex[:10]}"
    await FinanceAuditExportHistory(
        tenant_id=tenant_id,
        export_id=export_id,
        export_type=filters.get("export_type") or "audit_csv",
        filters=filters,
        row_count=len(rows),
        actor_id=scope.user_id,
    ).insert()
    filename = f"finance_audit_{utcnow().strftime('%Y%m%d')}.csv"
    return filename, buffer.getvalue()