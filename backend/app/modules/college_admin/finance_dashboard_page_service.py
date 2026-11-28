"""Finance administration overview dashboard (CA 10.01)."""

from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.finance_admin_models import (
    InstitutionFeeStructure,
    PaymentReconciliationRecord,
    StudentFeeAssessment,
)
from app.modules.college_admin.finance_overview_service import _verified_payment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FacultyAssignmentWorkflowStep,
    FinanceDashboardPageRead,
    FinanceDashboardTransactionRow,
    FinanceProgrammeCollectionItem,
    PoliciesPagination,
    StudentAdminDashboardFilterOption,
    UserDashboardKpi,
)
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus, RefundStatus
from app.modules.finance.finance_models import PaymentTransaction, RefundRecord, StudentFeeDemand
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_PAGE_SIZE = 4

_WORKFLOW_DEF: list[tuple[str, str, int, str]] = [
    ("fee_structure", "Create fee structure", 1, "/college-admin/finance/fee-structure-management"),
    ("assign_fees", "Assign fees to students", 2, "/college-admin/finance/student-fee-management"),
    ("fee_demands", "Generate fee demands", 3, "/college-admin/finance/fee-demand-invoice-management"),
    ("monitor_payments", "Monitor payments", 4, "/college-admin/finance/online-payment-monitoring"),
    ("reconcile", "Reconcile transactions", 5, "/college-admin/finance/payment-reconciliation"),
    ("reports", "Generate finance reports", 6, "/college-admin/finance/financial-reports"),
]

_BAR_TONES = ("green", "green", "blue", "amber", "teal", "indigo")


def _format_inr(amount: float) -> str:
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f} Cr"
    if amount >= 100_000:
        whole = amount / 100_000
        return f"₹{whole:.1f} L" if whole < 10 else f"₹{whole:.0f} L"
    return f"₹{amount:,.0f}"


def _format_inr_table(amount: float) -> str:
    return f"₹{amount:,.0f}"


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _workflow_steps(active_key: str) -> list[FacultyAssignmentWorkflowStep]:
    active_index = next((i for i, (key, *_) in enumerate(_WORKFLOW_DEF) if key == active_key), 0)
    steps: list[FacultyAssignmentWorkflowStep] = []
    for index, (key, label, number, href) in enumerate(_WORKFLOW_DEF):
        if index < active_index:
            status = "done"
        elif index == active_index:
            status = "active"
        else:
            status = "pending"
        steps.append(FacultyAssignmentWorkflowStep(key=key, label=label, step_number=number, status=status, href=href))
    return steps


async def _workflow_active_key(tenant_id: PydanticObjectId) -> str:
    if await InstitutionFeeStructure.find(Eq(InstitutionFeeStructure.tenant_id, tenant_id)).count() == 0:
        return "fee_structure"
    if await StudentFeeAssessment.find(Eq(StudentFeeAssessment.tenant_id, tenant_id)).count() == 0:
        return "assign_fees"
    if await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).count() == 0:
        return "fee_demands"
    unreconciled = await PaymentReconciliationRecord.find(
        Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
        Eq(PaymentReconciliationRecord.reconciled, False),
    ).count()
    if unreconciled > 0:
        return "reconcile"
    return "monitor_payments"


def _method_label(tx: PaymentTransaction) -> str:
    mode = (tx.payment_mode or "online").lower()
    gateway = (tx.gateway or "").lower()
    ref = (tx.offline_reference or "").lower()
    if "upi" in gateway or "upi" in ref:
        return "UPI"
    if mode == "offline":
        if any(k in ref or k in gateway for k in ("neft", "net", "bank", "rtgs", "imps")):
            return "Net banking"
        return "Counter"
    if "card" in gateway:
        return "Card"
    if mode == "online":
        return "Online"
    return (tx.payment_mode or "Online").replace("_", " ").title()


def _transaction_status(tx: PaymentTransaction) -> tuple[str, str]:
    if tx.status == PaymentTransactionStatus.SUCCESS:
        if tx.reversed_total > 0:
            return "Reversed", "info"
        if tx.payment_mode == "offline" or tx.webhook_verified:
            return "Verified", "success"
        return "Pending", "warning"
    if tx.status in (PaymentTransactionStatus.PENDING, PaymentTransactionStatus.PROCESSING, PaymentTransactionStatus.VERIFICATION_REQUIRED):
        return "Pending", "warning"
    if tx.status == PaymentTransactionStatus.FAILED:
        return "Failed", "error"
    if tx.status == PaymentTransactionStatus.REFUNDED or tx.reversed_total > 0:
        return "Reversed", "info"
    if tx.status in (PaymentTransactionStatus.INITIATED, PaymentTransactionStatus.CANCELLED, PaymentTransactionStatus.EXPIRED):
        return tx.status.value.replace("_", " ").title(), "muted"
    return tx.status.value.replace("_", " ").title(), "muted"


def _invoice_label(tx: PaymentTransaction) -> str:
    if tx.invoice_id:
        return tx.invoice_id if tx.invoice_id.upper().startswith("INV") else f"INV-{tx.invoice_id}"
    suffix = tx.transaction_id.replace("TXN-", "")[-8:] if tx.transaction_id else "—"
    return f"INV-2026-{suffix}"


async def get_finance_dashboard_page(
    scope: AccessScope,
    *,
    page: int = 1,
    academic_year_code: str | None = None,
    programme_code: str | None = None,
) -> FinanceDashboardPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    current_year_label, semester_label = await _reader.current_academic_term(tenant_id)
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    selected_ay = academic_year_code or current_year_label or (years[0].year_code if years else "")

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    if programme_code:
        prog_filter = programme_code.upper()
        profiles = [p for p in profiles if (p.programme_code or "").upper() == prog_filter]
    allowed_users = {p.user_id for p in profiles} if programme_code else None

    assessments = await StudentFeeAssessment.find(Eq(StudentFeeAssessment.tenant_id, tenant_id)).to_list()
    if selected_ay:
        assessments = [a for a in assessments if a.academic_year_label == selected_ay]
    if allowed_users is not None:
        assessments = [a for a in assessments if a.student_user_id in allowed_users]

    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    if selected_ay:
        demands = [d for d in demands if d.academic_year_label == selected_ay]
    if allowed_users is not None:
        demands = [d for d in demands if d.student_user_id in allowed_users]

    billed = sum(a.net_amount or a.assessed_amount for a in assessments)
    if billed <= 0:
        billed = sum(d.amount + d.late_fee for d in demands)

    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).sort("-created_at").to_list()
    if allowed_users is not None:
        txs = [t for t in txs if t.student_user_id in allowed_users]

    collected = sum(t.amount for t in txs if _verified_payment(t))
    collected_pct = round((collected / billed) * 100, 1) if billed > 0 else 0.0

    outstanding = 0.0
    students_with_dues: set[PydanticObjectId] = set()
    for d in demands:
        if d.status in (FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE):
            outstanding += d.amount + d.late_fee
            students_with_dues.add(d.student_user_id)

    refund_rows = await RefundRecord.find(
        Eq(RefundRecord.tenant_id, tenant_id),
        Eq(RefundRecord.status, RefundStatus.REQUESTED),
    ).to_list()
    if allowed_users is not None:
        refund_rows = [r for r in refund_rows if r.student_user_id in allowed_users]
    refund_count = len(refund_rows)
    refund_amount = sum(r.amount for r in refund_rows)

    active_key = await _workflow_active_key(tenant_id)

    total_tx = len(txs)
    total_pages = math.ceil(total_tx / _PAGE_SIZE) if total_tx else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_txs = txs[start : start + _PAGE_SIZE]

    user_ids = {t.student_user_id for t in page_txs}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}

    transaction_rows: list[FinanceDashboardTransactionRow] = []
    for tx in page_txs:
        status_label, status_tone = _transaction_status(tx)
        transaction_rows.append(
            FinanceDashboardTransactionRow(
                transaction_id=tx.transaction_id,
                student_name=user_names.get(tx.student_user_id, "—"),
                invoice_label=_invoice_label(tx),
                method_label=_method_label(tx),
                amount_label=_format_inr_table(tx.amount),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/payment-transactions",
            )
        )

    showing_from = start + 1 if total_tx else 0
    showing_to = min(start + _PAGE_SIZE, total_tx)

    departments = await Department.find(Eq(Department.tenant_id, tenant_id), Eq(Department.is_active, True)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    dept_billed: dict[str, float] = defaultdict(float)
    dept_collected: dict[str, float] = defaultdict(float)

    for a in assessments:
        profile = profile_by_user.get(a.student_user_id)
        dept_key = str(profile.department_id) if profile and profile.department_id else "_unassigned"
        dept_billed[dept_key] += a.net_amount or a.assessed_amount

    for tx in txs:
        if not _verified_payment(tx):
            continue
        profile = profile_by_user.get(tx.student_user_id)
        dept_key = str(profile.department_id) if profile and profile.department_id else "_unassigned"
        dept_collected[dept_key] += tx.amount

    collection_items: list[tuple[str, str, float]] = []
    for dept in sorted(departments, key=lambda d: d.name):
        key = str(dept.id)
        billed_amt = dept_billed.get(key, 0.0)
        collected_amt = dept_collected.get(key, 0.0)
        if billed_amt <= 0 and collected_amt <= 0:
            continue
        pct = round((collected_amt / billed_amt) * 100, 1) if billed_amt > 0 else 0.0
        collection_items.append((key, dept.name, pct))

    if not collection_items:
        for prog in programmes[:4]:
            code = prog.programme_code
            prog_profiles = [p for p in profiles if (p.programme_code or "").upper() == code.upper()]
            users_set = {p.user_id for p in prog_profiles}
            prog_billed = sum(
                a.net_amount or a.assessed_amount
                for a in assessments
                if a.student_user_id in users_set
            )
            prog_collected = sum(t.amount for t in txs if _verified_payment(t) and t.student_user_id in users_set)
            if prog_billed <= 0 and prog_collected <= 0:
                continue
            pct = round((prog_collected / prog_billed) * 100, 1) if prog_billed > 0 else 0.0
            collection_items.append((code, prog.name or code, pct))

    collection_items.sort(key=lambda x: x[2], reverse=True)
    programme_collection_items = [
        FinanceProgrammeCollectionItem(
            key=key,
            label=label,
            collection_percent=pct,
            bar_tone=_BAR_TONES[index % len(_BAR_TONES)],
        )
        for index, (key, label, pct) in enumerate(collection_items[:6])
    ]

    semester_word = semester_label or "current"
    ay_options = [StudentAdminDashboardFilterOption(value=y.year_code, label=y.label or y.year_code) for y in years]
    if not ay_options and selected_ay:
        ay_options = [StudentAdminDashboardFilterOption(value=selected_ay, label=selected_ay)]

    programme_options = [
        StudentAdminDashboardFilterOption(value="", label="All programmes"),
        *[
            StudentAdminDashboardFilterOption(value=p.programme_code, label=p.name or p.programme_code)
            for p in sorted(programmes, key=lambda x: x.name or x.programme_code)
        ],
    ]

    semester_hint = f"{semester_word.title()} {selected_ay}" if selected_ay else semester_word.title()

    kpis = [
        UserDashboardKpi(
            key="billed",
            label="Billed",
            value=_format_inr(billed),
            hint_line=semester_hint,
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="collected",
            label="Collected",
            value=_format_inr(collected),
            hint_line=f"{collected_pct:g}%" if billed > 0 else "—",
            hint_tone="success" if collected_pct >= 70 else "warning",
        ),
        UserDashboardKpi(
            key="outstanding",
            label="Outstanding",
            value=_format_inr(outstanding),
            hint_line=f"{len(students_with_dues):,} students",
            hint_tone="warning" if outstanding > 0 else "success",
        ),
        UserDashboardKpi(
            key="refund_requests",
            label="Refund requests",
            value=f"{refund_count:,}",
            hint_line=_format_inr(refund_amount) if refund_amount > 0 else "None pending",
            hint_tone="warning" if refund_count else "success",
        ),
    ]

    page_subtitle = (
        f"Fee position for {semester_word} semester {selected_ay}"
        if selected_ay
        else "Fee collection, demands and payment monitoring"
    )

    workflow_steps = _workflow_steps(active_key)
    portal_href = next(
        (step.href for step in workflow_steps if step.status == "active" and step.href),
        "/college-admin/finance/fee-structure-management",
    )

    return FinanceDashboardPageRead(
        page_title="Finance Dashboard",
        page_subtitle=page_subtitle,
        export_label="Export",
        open_portal_label="Open Finance portal",
        open_portal_href=portal_href,
        academic_year_filter_label="Academic year",
        programme_filter_label="Programme",
        academic_year_options=ay_options,
        programme_options=programme_options,
        selected_academic_year=selected_ay,
        selected_programme_code=programme_code or "",
        workflow_steps=workflow_steps,
        kpis=kpis,
        transactions_section_title="Payment transactions",
        transactions_count_label=f"{total_tx:,} transactions" if total_tx else "0 transactions",
        table_headers=["Transaction", "Student", "Invoice", "Method", "Amount", "Status"],
        transaction_rows=transaction_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total_tx:,}" if total_tx else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total_tx,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        collection_section_title="Collection by programme",
        programme_collection_items=programme_collection_items,
        generated_at=now,
    )


async def export_finance_dashboard_csv(
    scope: AccessScope,
    *,
    academic_year_code: str | None = None,
    programme_code: str | None = None,
) -> str:
    first_page = await get_finance_dashboard_page(
        scope,
        page=1,
        academic_year_code=academic_year_code,
        programme_code=programme_code,
    )
    transaction_rows: list[FinanceDashboardTransactionRow] = []
    total_pages = max(1, first_page.pagination.total_pages or 1)
    for page_no in range(1, total_pages + 1):
        chunk = await get_finance_dashboard_page(
            scope,
            page=page_no,
            academic_year_code=academic_year_code,
            programme_code=programme_code,
        )
        transaction_rows.extend(chunk.transaction_rows)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Academic year", first_page.selected_academic_year or "—"])
    writer.writerow(["Programme", first_page.selected_programme_code or "All programmes"])
    writer.writerow([])
    writer.writerow(["KPI", "Value", "Hint"])
    for kpi in first_page.kpis:
        writer.writerow([kpi.label, kpi.value, kpi.hint_line])
    writer.writerow([])
    writer.writerow(["Programme / department", "Collection %"])
    for item in first_page.programme_collection_items:
        writer.writerow([item.label, f"{item.collection_percent}%"])
    writer.writerow([])
    writer.writerow(first_page.table_headers)
    for row in transaction_rows:
        writer.writerow(
            [
                row.transaction_id,
                row.student_name,
                row.invoice_label,
                row.method_label,
                row.amount_label,
                row.status_label,
            ]
        )
    return buffer.getvalue()