"""Finance staff dashboard service."""

from datetime import datetime, timezone

from app.common.access import AccessScope
from app.modules.accounts_finance.dashboard_filters import build_dashboard_context
from app.modules.accounts_finance.dashboard_repository import (
    build_accounting_section,
    build_financial_overview,
    build_invoice_overview,
    build_payment_overview,
    build_refund_section,
    build_scholarship_section,
    build_student_fee_overview,
)
from app.modules.accounts_finance.dashboard_schemas import DrillDownLink, FinanceDashboardFilters, FinanceDashboardOverview
from app.modules.accounts_finance.policy import authorize_finance_dashboard, require_finance_tenant_scope


async def get_finance_dashboard(
    scope: AccessScope,
    *,
    financial_year: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    programme_code: str | None = None,
    department_id: str | None = None,
    fee_category_code: str | None = None,
    invoice_status: str | None = None,
    payment_status: str | None = None,
    payment_method: str | None = None,
    campus_id: str | None = None,
    date_from=None,
    date_to=None,
) -> FinanceDashboardOverview:
    authorize_finance_dashboard(scope)
    tenant_id = require_finance_tenant_scope(scope)
    ctx = build_dashboard_context(
        tenant_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        programme_code=programme_code,
        department_id=department_id,
        campus_id=campus_id,
        date_from=date_from,
        date_to=date_to,
        payment_status=payment_status,
        payment_method=payment_method,
    )
    filters = FinanceDashboardFilters(
        financial_year=financial_year,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        programme_code=programme_code,
        department_id=department_id,
        fee_category_code=fee_category_code,
        invoice_status=invoice_status,
        payment_status=payment_status,
        payment_method=payment_method,
        campus_id=campus_id,
        date_from=date_from,
        date_to=date_to,
    )
    drill_downs = [
        DrillDownLink(
            resource="payment_transactions",
            path="/accounts-finance/transactions",
            query={"payment_status": payment_status, "payment_method": payment_method},
        ),
        DrillDownLink(
            resource="fee_structures",
            path="/accounts-finance/fee-structures",
            query={"programme_code": programme_code},
        ),
    ]
    return FinanceDashboardOverview(
        generated_at=datetime.now(timezone.utc),
        filters=filters,
        financial=await build_financial_overview(ctx),
        student_fees=await build_student_fee_overview(ctx),
        payments=await build_payment_overview(ctx),
        invoices=await build_invoice_overview(ctx),
        scholarships=await build_scholarship_section(ctx),
        refunds=await build_refund_section(ctx),
        accounting=await build_accounting_section(ctx),
        drill_downs=drill_downs,
    )