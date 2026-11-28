"""Finance payment monitoring pages (online, offline, all transactions)."""

from __future__ import annotations

import math
import re
from datetime import date

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.finance_payment_page_shared import (
    build_transaction_rows,
    counter_label,
    current_month_start,
    format_inr,
    format_inr_compact,
    gateway_success_rates,
    is_offline_tx,
    is_online_tx,
    method_label,
    month_label,
    offline_reference,
    offline_status,
    page_numbers,
    payment_sub_nav,
    transaction_status,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FinanceOfflinePaymentTableRow,
    FinancePaymentGatewayItem,
    OfflinePaymentCollectionPageRead,
    OnlinePaymentMonitoringPageRead,
    PaymentTransactionsPageRead,
    PoliciesPagination,
    StudentAdminDashboardFilterOption,
    UserDashboardKpi,
)
from app.modules.accounts_finance.phase3_enums import PaymentGatewayEnvironment
from app.modules.accounts_finance.phase3_models import PaymentGatewayConfiguration
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction
from app.modules.finance.payment_verification import apply_verified_payment

_ONLINE_PAGE_SIZE = 4
_OFFLINE_PAGE_SIZE = 10
_TRANSACTIONS_PAGE_SIZE = 10
_TABLE_HEADERS_ONLINE = ["Transaction", "Student", "Invoice", "Method", "Amount", "Status"]
_TABLE_HEADERS_OFFLINE = ["Reference", "Student", "Method", "Amount", "Counter", "Status"]


def _format_count(n: int) -> str:
    return f"{n:,}"


def _pagination(total: int, page: int, page_size: int) -> tuple[PoliciesPagination, int, int]:
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
        min(start + page_size, total),
    )


def _showing_slice(start: int, end: int, total: int) -> str:
    if total <= 0:
        return "Showing 0 of 0"
    shown = end - start
    return f"Showing {shown} of {total:,}"


def _month_bounds(month_code: str | None) -> tuple[date, date]:
    now = utcnow()
    if month_code and re.match(r"^\d{4}-\d{2}$", month_code):
        year, month = (int(x) for x in month_code.split("-"))
    else:
        year, month = now.year, now.month
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def _tx_in_month(tx: PaymentTransaction, start: date, end: date) -> bool:
    local = tx.created_at
    if local.tzinfo:
        local = local.replace(tzinfo=None)
    day = local.date()
    return start <= day < end


def _online_success(tx: PaymentTransaction) -> bool:
    if not is_online_tx(tx):
        return False
    label, _ = transaction_status(tx)
    return label == "Verified"


def _online_pending(tx: PaymentTransaction) -> bool:
    if not is_online_tx(tx):
        return False
    label, _ = transaction_status(tx)
    return label == "Pending"


def _online_failed(tx: PaymentTransaction) -> bool:
    if not is_online_tx(tx):
        return False
    label, _ = transaction_status(tx)
    return label == "Failed"


def _provider_rate_key(provider_code: str | None) -> str:
    return (provider_code or "unknown").strip().lower().replace(" ", "_")


def _gateway_detail_line(
    gw: PaymentGatewayConfiguration,
    rates: dict[str, float],
) -> str:
    code_key = _provider_rate_key(gw.provider_code)
    rate = rates.get(code_key)
    if rate is None:
        for tx_key, tx_rate in rates.items():
            if tx_key in code_key or code_key in tx_key:
                rate = tx_rate
                break
    if rate is not None:
        return f"{rate}% success today"
    if gw.connection_status and gw.connection_status not in {"unknown", "stub"}:
        return str(gw.connection_status).replace("_", " ").title()
    env = gw.environment.value if hasattr(gw.environment, "value") else str(gw.environment)
    if env == PaymentGatewayEnvironment.SANDBOX.value:
        return "Sandbox environment"
    return "No attempts today"


def _gateway_status(gw: PaymentGatewayConfiguration) -> tuple[str, str, str]:
    if not gw.active:
        return "Inactive", "muted", "info"
    env = gw.environment.value if hasattr(gw.environment, "value") else str(gw.environment)
    if env == PaymentGatewayEnvironment.PRODUCTION.value:
        return "Live", "success", "check"
    return "Test", "warning", "info"


async def _gateway_items(tenant_id, txs: list[PaymentTransaction], today: date) -> tuple[list[FinancePaymentGatewayItem], str | None]:
    rates = gateway_success_rates(txs, day=today)
    gateways = await PaymentGatewayConfiguration.find(
        Eq(PaymentGatewayConfiguration.tenant_id, tenant_id),
    ).sort("-active", "+gateway_name").to_list()
    if not gateways:
        return [], "Configure payment gateways in Finance settings to monitor providers here."

    items: list[FinancePaymentGatewayItem] = []
    for gw in gateways:
        status_label, status_tone, icon_variant = _gateway_status(gw)
        items.append(
            FinancePaymentGatewayItem(
                gateway_key=gw.config_id,
                gateway_label=gw.gateway_name or gw.provider_code,
                detail_line=_gateway_detail_line(gw, rates),
                status_label=status_label,
                status_tone=status_tone,
                icon_variant=icon_variant,
            )
        )
    return items, None


async def _load_tenant_transactions(scope: AccessScope) -> list[PaymentTransaction]:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    return await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).sort("-created_at").to_list()


async def verify_pending_online_payments(scope: AccessScope) -> dict[str, int]:
    authorize(scope, Permission.FINANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()
    pending = [
        t
        for t in txs
        if is_online_tx(t)
        and t.status in (PaymentTransactionStatus.PENDING, PaymentTransactionStatus.VERIFICATION_REQUIRED)
    ]
    attempted = 0
    verified = 0
    for tx in pending:
        attempted += 1
        reference = (tx.gateway_reference or tx.transaction_id or "").strip()
        if not reference:
            continue
        try:
            await apply_verified_payment(tx.transaction_id, gateway_reference=reference)
            verified += 1
        except Exception:  # noqa: BLE001
            continue
    return {"attempted": attempted, "verified": verified}


async def get_online_payment_monitoring_page(scope: AccessScope, *, page: int = 1) -> OnlinePaymentMonitoringPageRead:
    now = utcnow()
    today = now.date()
    month_start = current_month_start()
    _, month_end = _month_bounds(month_start.strftime("%Y-%m"))
    tenant_id = require_college_tenant_scope(scope)
    txs = await _load_tenant_transactions(scope)
    online = [t for t in txs if is_online_tx(t)]
    month_online = [t for t in online if _tx_in_month(t, month_start, month_end)]

    success_n = sum(1 for t in month_online if _online_success(t))
    pending_n = sum(1 for t in month_online if _online_pending(t))
    failed_n = sum(1 for t in month_online if _online_failed(t))
    success_pct = round((success_n / len(month_online)) * 100, 1) if month_online else 0.0

    kpis = [
        UserDashboardKpi(
            key="online_tx",
            label="Online transactions",
            value=_format_count(len(month_online)),
            hint_line=month_label(month_start),
            hint_tone="blue",
        ),
        UserDashboardKpi(
            key="successful",
            label="Successful",
            value=_format_count(success_n),
            hint_line=f"{success_pct}%",
            hint_tone="green",
        ),
        UserDashboardKpi(
            key="pending",
            label="Pending",
            value=_format_count(pending_n),
            hint_line=f"{pending_n:,} awaiting verification" if pending_n else "None awaiting",
            hint_tone="amber" if pending_n else "success",
        ),
        UserDashboardKpi(
            key="failed",
            label="Failed",
            value=_format_count(failed_n),
            hint_line="",
            hint_tone="muted",
        ),
    ]

    total = len(online)
    pagination, start, end = _pagination(total, page, _ONLINE_PAGE_SIZE)
    page_slice = online[start : start + _ONLINE_PAGE_SIZE]
    transaction_rows = await build_transaction_rows(page_slice)

    gateway_items, gateways_empty_message = await _gateway_items(tenant_id, txs, today)

    return OnlinePaymentMonitoringPageRead(
        page_title="Online Payment Monitoring",
        page_subtitle="Gateway transactions and settlements",
        verify_pending_label="Verify pending",
        verify_pending_href="/college-admin/finance/online-payment-monitoring?verify=1",
        verify_pending_count=pending_n,
        kpis=kpis,
        sub_nav=payment_sub_nav("online"),
        transactions_section_title="Payment transactions",
        table_headers=_TABLE_HEADERS_ONLINE,
        transaction_rows=transaction_rows,
        showing_label=_showing_slice(start, min(start + len(page_slice), total), total),
        pagination=pagination,
        gateways_section_title="Gateways",
        gateway_items=gateway_items,
        gateways_empty_message=gateways_empty_message,
        generated_at=now,
    )


async def get_offline_payment_collection_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> OfflinePaymentCollectionPageRead:
    now = utcnow()
    today = now.date()
    txs = await _load_tenant_transactions(scope)
    offline = [t for t in txs if is_offline_tx(t)]

    today_collected = 0.0
    today_receipts = 0
    pending_verify_n = 0
    pending_verify_amt = 0.0
    clearing_n = 0
    clearing_amt = 0.0
    unallocated_n = 0
    unallocated_amt = 0.0

    for tx in offline:
        local_day = tx.created_at.date() if not tx.created_at.tzinfo else tx.created_at.replace(tzinfo=None).date()
        status_label, _ = offline_status(tx)
        if status_label == "Verified" and local_day == today:
            today_collected += tx.amount
            today_receipts += 1
        if status_label == "Verifying":
            pending_verify_n += 1
            pending_verify_amt += tx.amount
        if status_label == "Clearing":
            clearing_n += 1
            clearing_amt += tx.amount
        if not tx.invoice_id and not tx.demand_id:
            unallocated_n += 1
            unallocated_amt += tx.amount

    kpis = [
        UserDashboardKpi(
            key="collected_today",
            label="Collected today",
            value=format_inr_compact(today_collected),
            hint_line=f"{today_receipts} receipts",
            hint_tone="green",
        ),
        UserDashboardKpi(
            key="pending_verification",
            label="Pending verification",
            value=str(pending_verify_n),
            hint_line=format_inr_compact(pending_verify_amt),
            hint_tone="amber",
        ),
        UserDashboardKpi(
            key="cheques_clearing",
            label="Cheques clearing",
            value=str(clearing_n),
            hint_line=format_inr_compact(clearing_amt),
            hint_tone="amber",
        ),
        UserDashboardKpi(
            key="unallocated",
            label="Unallocated",
            value=str(unallocated_n),
            hint_line=format_inr_compact(unallocated_amt),
            hint_tone="rose",
        ),
    ]

    total = len(offline)
    pagination, start, _ = _pagination(total, page, _OFFLINE_PAGE_SIZE)
    page_slice = offline[start : start + _OFFLINE_PAGE_SIZE]

    from app.modules.auth.models import User
    from beanie.odm.operators.find.comparison import In

    user_ids = {t.student_user_id for t in page_slice}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}

    offline_rows: list[FinanceOfflinePaymentTableRow] = []
    for tx in page_slice:
        status_label, status_tone = offline_status(tx)
        offline_rows.append(
            FinanceOfflinePaymentTableRow(
                reference=offline_reference(tx),
                student_name=user_names.get(tx.student_user_id, "—"),
                method_label=method_label(tx),
                amount_label=format_inr(tx.amount),
                counter_label=counter_label(tx),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/offline-payment-collection",
            )
        )

    return OfflinePaymentCollectionPageRead(
        page_title="Offline Payment Collection",
        page_subtitle="Counter, cheque and bank collections",
        record_payment_label="Record payment",
        record_payment_href="/college-admin/finance/offline-payment-collection?record=1",
        kpis=kpis,
        sub_nav=payment_sub_nav("offline"),
        payments_section_title="Offline payments",
        table_headers=_TABLE_HEADERS_OFFLINE,
        payment_rows=offline_rows,
        showing_label=_showing_slice(start, min(start + len(page_slice), total), total),
        pagination=pagination,
        generated_at=now,
    )


def _status_filter_match(tx: PaymentTransaction, status_code: str | None) -> bool:
    if not status_code or status_code == "all":
        return True
    label, _ = transaction_status(tx)
    normalized = label.lower().replace(" ", "_")
    return normalized == status_code.lower() or label.lower() == status_code.lower()


def _method_filter_match(tx: PaymentTransaction, method_code: str | None) -> bool:
    if not method_code or method_code == "all":
        return True
    label = method_label(tx).lower()
    code = method_code.lower().replace("_", " ")
    if code == "net banking":
        return "net" in label or "banking" in label
    if code == "card":
        return "card" in label
    if code == "upi":
        return label == "upi"
    return code in label


async def get_payment_transactions_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    month: str | None = None,
    method: str | None = None,
    status: str | None = None,
) -> PaymentTransactionsPageRead:
    now = utcnow()
    txs = await _load_tenant_transactions(scope)
    month_start, month_end = _month_bounds(month)
    month_options_months: set[tuple[int, int]] = set()
    for tx in txs:
        d = tx.created_at.date() if not tx.created_at.tzinfo else tx.created_at.replace(tzinfo=None).date()
        month_options_months.add((d.year, d.month))

    filtered = [t for t in txs if _tx_in_month(t, month_start, month_end)]
    filtered = [t for t in filtered if _method_filter_match(t, method)]
    filtered = [t for t in filtered if _status_filter_match(t, status)]

    needle = (search or "").strip().lower()
    if needle:
        from app.modules.auth.models import User
        from beanie.odm.operators.find.comparison import In

        user_ids = {t.student_user_id for t in filtered}
        users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
        user_names = {u.id: (u.full_name or "").lower() for u in users}
        filtered = [
            t
            for t in filtered
            if needle in t.transaction_id.lower()
            or needle in (t.invoice_id or "").lower()
            or needle in user_names.get(t.student_user_id, "")
        ]

    total = len(filtered)
    pagination, start, _ = _pagination(total, page, _TRANSACTIONS_PAGE_SIZE)
    page_slice = filtered[start : start + _TRANSACTIONS_PAGE_SIZE]
    transaction_rows = await build_transaction_rows(page_slice)

    month_opts: list[StudentAdminDashboardFilterOption] = []
    for year, mon in sorted(month_options_months, reverse=True):
        code = f"{year:04d}-{mon:02d}"
        month_opts.append(StudentAdminDashboardFilterOption(value=code, label=date(year, mon, 1).strftime("%b %Y")))
    if not month_opts:
        month_opts.append(
            StudentAdminDashboardFilterOption(value=month_start.strftime("%Y-%m"), label=month_label(month_start))
        )

    selected_month = month or month_start.strftime("%Y-%m")
    method_options = [
        StudentAdminDashboardFilterOption(value="all", label="All methods"),
        StudentAdminDashboardFilterOption(value="upi", label="UPI"),
        StudentAdminDashboardFilterOption(value="net_banking", label="Net banking"),
        StudentAdminDashboardFilterOption(value="card", label="Card"),
    ]
    status_options = [
        StudentAdminDashboardFilterOption(value="all", label="All statuses"),
        StudentAdminDashboardFilterOption(value="verified", label="Verified"),
        StudentAdminDashboardFilterOption(value="pending", label="Pending"),
        StudentAdminDashboardFilterOption(value="failed", label="Failed"),
        StudentAdminDashboardFilterOption(value="reversed", label="Reversed"),
    ]

    return PaymentTransactionsPageRead(
        page_title="Payment Transactions",
        page_subtitle="All verified, pending and failed payments",
        export_label="Export",
        export_href="/college-admin/finance/payment-transactions?export=1",
        search_placeholder="Search transaction, student or invoice",
        sub_nav=payment_sub_nav("all"),
        month_filter_label="Month",
        month_options=month_opts,
        selected_month=selected_month,
        method_filter_label="Method",
        method_options=method_options,
        selected_method=method or "all",
        status_filter_label="Status",
        status_options=status_options,
        selected_status=status or "all",
        transactions_section_title="Payment transactions",
        table_headers=_TABLE_HEADERS_ONLINE,
        transaction_rows=transaction_rows,
        showing_label=_showing_slice(start, min(start + len(page_slice), total), total),
        pagination=pagination,
        generated_at=now,
    )