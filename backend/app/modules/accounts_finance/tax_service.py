"""Tax configuration references, transaction register and regulatory reporting."""

import uuid
from datetime import date
from decimal import Decimal

from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase10_enums import VendorInvoiceVerificationStatus
from app.modules.accounts_finance.phase11_enums import FinanceTaxCategory, FilingRecordStatus, RegulatoryReportStatus
from app.modules.accounts_finance.phase11_models import (
    FinanceRegulatoryFilingHistory,
    FinanceRegulatoryReport,
    FinanceRegulatoryReportVersion,
    FinanceTaxAdjustment,
    FinanceTaxConfigReference,
    FinanceTaxException,
    FinanceTaxTransactionRecord,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_tax_approve,
    authorize_finance_tax_manage,
    authorize_finance_tax_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.finance_ext_models import InstitutionVendorInvoice
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_models import StudentFeeInvoice
from app.modules.hr.statutory_tax_models import HrStatutoryRuleVersion


async def _resolve_rule(tenant_id, component_code: str, on_date: date) -> HrStatutoryRuleVersion | None:
    rules = await HrStatutoryRuleVersion.find(
        Eq(HrStatutoryRuleVersion.tenant_id, tenant_id),
        Eq(HrStatutoryRuleVersion.component_code, component_code),
        LTE(HrStatutoryRuleVersion.effective_from, on_date),
    ).sort("-effective_from").to_list()
    for rule in rules:
        if rule.effective_to is None or rule.effective_to >= on_date:
            return rule
    return None


def _rate_percent(rule: HrStatutoryRuleVersion | None, taxable: float) -> tuple[float, str | None]:
    if rule is None:
        return 0.0, None
    try:
        pct = Decimal(rule.employee_rate_percent or rule.employer_rate_percent or "0")
    except Exception:
        pct = Decimal("0")
    tax = round_money(float(taxable) * float(pct) / 100.0)
    return tax, f"{rule.component_code}:v{rule.version_number}"


async def upsert_tax_config_reference(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_tax_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    ref_id = payload.get("reference_id") or f"ftcr_{uuid.uuid4().hex[:10]}"
    doc = await FinanceTaxConfigReference.find_one(
        Eq(FinanceTaxConfigReference.tenant_id, tenant_id),
        Eq(FinanceTaxConfigReference.reference_id, ref_id),
    )
    if doc is None:
        doc = FinanceTaxConfigReference(
            tenant_id=tenant_id,
            reference_id=ref_id,
            tax_category=payload["tax_category"],
            transaction_type=payload["transaction_type"],
            component_code=payload["component_code"],
            tax_treatment=payload.get("tax_treatment") or "collect",
            effective_from=payload["effective_from"],
            effective_to=payload.get("effective_to"),
            exemption_ref=payload.get("exemption_ref"),
            registration_ref=payload.get("registration_ref"),
        )
        await doc.insert()
    else:
        doc.component_code = payload["component_code"]
        doc.active = bool(payload.get("active", doc.active))
        await doc.save()
    return {"reference_id": ref_id}


async def capture_tax_transaction(
    tenant_id,
    *,
    source_type: str,
    source_id: str,
    tax_category: str,
    taxable_amount: float,
    transaction_date: date,
    document_tax_amount: float | None = None,
) -> FinanceTaxTransactionRecord | None:
    posting_key = f"tax:{source_type}:{source_id}:{tax_category}"
    existing = await FinanceTaxTransactionRecord.find_one(
        Eq(FinanceTaxTransactionRecord.tenant_id, tenant_id),
        Eq(FinanceTaxTransactionRecord.posting_key, posting_key),
    )
    if existing:
        return existing
    cfg = await FinanceTaxConfigReference.find_one(
        Eq(FinanceTaxConfigReference.tenant_id, tenant_id),
        Eq(FinanceTaxConfigReference.transaction_type, source_type),
        Eq(FinanceTaxConfigReference.tax_category, tax_category),
        Eq(FinanceTaxConfigReference.active, True),
    )
    tax_amount = 0.0
    rule_version = None
    component_code = None
    if cfg:
        rule = await _resolve_rule(tenant_id, cfg.component_code, transaction_date)
        calc, rule_version = _rate_percent(rule, taxable_amount)
        tax_amount = document_tax_amount if document_tax_amount is not None else calc
        component_code = cfg.component_code
    elif document_tax_amount is not None:
        tax_amount = document_tax_amount
    else:
        await FinanceTaxException(
            tenant_id=tenant_id,
            exception_id=f"tex_{uuid.uuid4().hex[:10]}",
            exception_type="missing_tax_classification",
            detail=f"No config for {source_type}/{tax_category}",
            reference_type=source_type,
            reference_id=source_id,
        ).insert()
        return None
    rec = FinanceTaxTransactionRecord(
        tenant_id=tenant_id,
        tax_record_id=f"ftx_{uuid.uuid4().hex[:12]}",
        source_type=source_type,
        source_id=source_id,
        tax_category=tax_category,
        taxable_amount=round_money(taxable_amount),
        tax_amount=round_money(tax_amount),
        rule_version_id=rule_version,
        component_code=component_code,
        transaction_date=transaction_date,
        posting_key=posting_key,
    )
    await rec.insert()
    return rec


async def sync_tax_from_sources(scope: AccessScope, *, date_from: date, date_to: date) -> dict:
    authorize_finance_tax_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    created = 0
    invoices = await StudentFeeInvoice.find(
        Eq(StudentFeeInvoice.tenant_id, tenant_id),
        GTE(StudentFeeInvoice.due_date, date_from),
        LTE(StudentFeeInvoice.due_date, date_to),
    ).to_list()
    for inv in invoices:
        if inv.published and await capture_tax_transaction(
            tenant_id,
            source_type="fee_invoice",
            source_id=inv.invoice_id,
            tax_category=FinanceTaxCategory.OUTPUT_TAX.value,
            taxable_amount=inv.amount,
            transaction_date=inv.billing_date or inv.due_date,
        ):
            created += 1
    vinv = await InstitutionVendorInvoice.find(Eq(InstitutionVendorInvoice.tenant_id, tenant_id)).to_list()
    for row in vinv:
        if row.invoice_date and date_from <= row.invoice_date <= date_to:
            if row.verification_status == VendorInvoiceVerificationStatus.VERIFIED.value and row.tax_amount > 0:
                if await capture_tax_transaction(
                    tenant_id,
                    source_type="vendor_invoice",
                    source_id=row.invoice_id,
                    tax_category=FinanceTaxCategory.INDIRECT.value,
                    taxable_amount=row.amount,
                    transaction_date=row.invoice_date,
                    document_tax_amount=row.tax_amount,
                ):
                    created += 1
    return {"tax_records_ensured": created}


async def tax_overview(scope: AccessScope) -> dict:
    authorize_finance_tax_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    records = await FinanceTaxTransactionRecord.find(Eq(FinanceTaxTransactionRecord.tenant_id, tenant_id)).to_list()
    collected = round_money(sum(r.tax_amount for r in records if r.tax_category in (FinanceTaxCategory.OUTPUT_TAX.value, FinanceTaxCategory.INDIRECT.value)))
    liabilities = round_money(sum(r.tax_amount for r in records if r.reporting_status == "pending"))
    exceptions = await FinanceTaxException.find(
        Eq(FinanceTaxException.tenant_id, tenant_id),
        Eq(FinanceTaxException.resolved, False),
    ).count()
    pending_reports = await FinanceRegulatoryReport.find(
        Eq(FinanceRegulatoryReport.tenant_id, tenant_id),
        Eq(FinanceRegulatoryReport.status, RegulatoryReportStatus.DRAFT),
    ).count()
    return {
        "configurations_active": await FinanceTaxConfigReference.find(
            Eq(FinanceTaxConfigReference.tenant_id, tenant_id),
            Eq(FinanceTaxConfigReference.active, True),
        ).count(),
        "tax_transactions": len(records),
        "tax_collected_or_accrued": collected,
        "tax_liabilities_pending_reporting": liabilities,
        "compliance_exceptions": exceptions,
        "pending_regulatory_reports": pending_reports,
    }


async def request_tax_adjustment(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_tax_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    adj_id = f"tadj_{uuid.uuid4().hex[:10]}"
    await FinanceTaxAdjustment(
        tenant_id=tenant_id,
        adjustment_id=adj_id,
        tax_record_id=payload["tax_record_id"],
        adjustment_type=payload["adjustment_type"],
        amount=payload["amount"],
        reason=payload["reason"],
        effective_period=payload.get("effective_period"),
        requested_by=scope.user_id,
    ).insert()
    return {"adjustment_id": adj_id, "status": "submitted"}


async def approve_tax_adjustment(scope: AccessScope, adjustment_id: str) -> dict:
    authorize_finance_tax_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    adj = await FinanceTaxAdjustment.find_one(
        Eq(FinanceTaxAdjustment.tenant_id, tenant_id),
        Eq(FinanceTaxAdjustment.adjustment_id, adjustment_id),
    )
    if adj is None or adj.status != "submitted":
        raise AppError(code="CONFLICT", message="Adjustment not pending", status_code=409)
    adj.status = "approved"
    adj.approved_by = scope.user_id
    await adj.save()
    rec = await FinanceTaxTransactionRecord.find_one(
        Eq(FinanceTaxTransactionRecord.tenant_id, tenant_id),
        Eq(FinanceTaxTransactionRecord.tax_record_id, adj.tax_record_id),
    )
    if rec:
        rec.tax_amount = round_money(rec.tax_amount + adj.amount)
        rec.reporting_status = "adjusted"
        await rec.save()
    return {"adjustment_id": adjustment_id, "status": "approved"}


async def prepare_regulatory_report(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_tax_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    period_start: date = payload["period_start"]
    period_end: date = payload["period_end"]
    records = await FinanceTaxTransactionRecord.find(
        Eq(FinanceTaxTransactionRecord.tenant_id, tenant_id),
        GTE(FinanceTaxTransactionRecord.transaction_date, period_start),
        LTE(FinanceTaxTransactionRecord.transaction_date, period_end),
    ).to_list()
    errors = []
    for rec in records:
        if rec.rule_version_id is None and rec.tax_amount > 0:
            errors.append({"type": "missing_rule_version", "tax_record_id": rec.tax_record_id})
    report_id = f"rpt_{uuid.uuid4().hex[:10]}"
    totals = {
        "taxable_total": round_money(sum(r.taxable_amount for r in records)),
        "tax_total": round_money(sum(r.tax_amount for r in records)),
        "transaction_count": len(records),
    }
    report = FinanceRegulatoryReport(
        tenant_id=tenant_id,
        report_id=report_id,
        report_type=payload.get("report_type") or "period_tax_summary",
        period_start=period_start,
        period_end=period_end,
        financial_year_id=payload.get("financial_year_id"),
        status=RegulatoryReportStatus.VALIDATION if errors else RegulatoryReportStatus.PENDING_REVIEW,
        totals=totals,
        validation_errors=errors,
        prepared_by=scope.user_id,
    )
    await report.insert()
    ver_id = f"rv_{uuid.uuid4().hex[:10]}"
    await FinanceRegulatoryReportVersion(
        tenant_id=tenant_id,
        version_id=ver_id,
        report_id=report_id,
        snapshot={"totals": totals, "record_ids": [r.tax_record_id for r in records]},
    ).insert()
    return {"report_id": report_id, "status": report.status.value, "validation_errors": errors}


async def approve_regulatory_report(scope: AccessScope, report_id: str) -> dict:
    authorize_finance_tax_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    report = await FinanceRegulatoryReport.find_one(
        Eq(FinanceRegulatoryReport.tenant_id, tenant_id),
        Eq(FinanceRegulatoryReport.report_id, report_id),
    )
    if report is None:
        raise AppError(code="NOT_FOUND", message="Report not found", status_code=404)
    if report.validation_errors:
        raise AppError(code="VALIDATION_ERROR", message="Resolve validation errors first", status_code=422)
    report.status = RegulatoryReportStatus.APPROVED
    report.approved_by = scope.user_id
    report.updated_at = utcnow()
    await report.save()
    return {"report_id": report_id, "status": report.status.value}


async def record_regulatory_filing(scope: AccessScope, report_id: str, payload: dict) -> dict:
    """Record actual filing only when acknowledgment reference supplied."""
    authorize_finance_tax_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    ack = payload.get("external_acknowledgment")
    if not ack:
        raise AppError(
            code="VALIDATION_ERROR",
            message="External acknowledgment reference required to mark filing",
            status_code=400,
        )
    filing_id = f"fil_{uuid.uuid4().hex[:10]}"
    filing_status = FilingRecordStatus.FILED.value
    doc = FinanceRegulatoryFilingHistory(
        tenant_id=tenant_id,
        filing_id=filing_id,
        report_id=report_id,
        filing_type=payload.get("filing_type") or "tax_return",
        preparation_date=payload.get("preparation_date") or date.today(),
        review_status="reviewed",
        approval_status="approved",
        actual_filing_date=payload.get("actual_filing_date") or date.today(),
        external_acknowledgment=ack,
        filing_status=filing_status,
        note=payload.get("note"),
        actor_id=scope.user_id,
    )
    await doc.insert()
    report = await FinanceRegulatoryReport.find_one(
        Eq(FinanceRegulatoryReport.tenant_id, tenant_id),
        Eq(FinanceRegulatoryReport.report_id, report_id),
    )
    if report:
        report.status = RegulatoryReportStatus.FILED_RECORDED
        await report.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.tax.filing.recorded",
        module="accounts_finance",
        resource_type="regulatory_filing",
        resource_id=filing_id,
    )
    return {"filing_id": filing_id, "filing_status": filing_status, "note": "Internal preparation does not equal legal filing without acknowledgment"}


async def export_tax_register(scope: AccessScope, *, date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    authorize_finance_tax_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query = FinanceTaxTransactionRecord.find(Eq(FinanceTaxTransactionRecord.tenant_id, tenant_id))
    if date_from:
        query = query.find(GTE(FinanceTaxTransactionRecord.transaction_date, date_from))
    if date_to:
        query = query.find(LTE(FinanceTaxTransactionRecord.transaction_date, date_to))
    rows = await query.to_list()
    return [
        {
            "tax_record_id": r.tax_record_id,
            "source_type": r.source_type,
            "source_id": r.source_id,
            "tax_category": r.tax_category,
            "taxable_amount": r.taxable_amount,
            "tax_amount": r.tax_amount,
            "rule_version_id": r.rule_version_id,
            "transaction_date": r.transaction_date.isoformat(),
        }
        for r in rows
    ]