"""College admin dashboard — finance summary aggregates."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.finance_admin_models import (
    InstitutionFeeStructure,
    PaymentReconciliationRecord,
    RefundRequest,
    StudentFeeAssessment,
)
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicTermSummary,
    FinanceAttentionItem,
    FinanceMonthlyCollectionPoint,
    FinanceOverviewFilters,
    FinanceOverviewKpiRead,
    FinanceOverviewRead,
    FinancePaymentModeItem,
    FinanceProgrammeDuesRow,
    FinanceScholarshipDisbursementItem,
)
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus, RefundStatus, ScholarshipApplicationStatus
from app.modules.finance.finance_models import (
    FeeConcession,
    PaymentTransaction,
    ScholarshipProgram,
    OfficialScholarshipApplication,
    StudentFeeDemand,
)
from app.modules.students.models import StudentProfile

_reader = OperationalDataReader()
_IST = ZoneInfo("Asia/Kolkata")

_PAID_STATUSES = frozenset({FeeDemandStatus.PAID, FeeDemandStatus.WAIVED})

_PROGRAMME_BUCKETS: tuple[tuple[str, str], ...] = (
    ("be_btech", "B.E. / B.Tech"),
    ("me_mtech", "M.E. / M.Tech"),
    ("mba_mca", "MBA / MCA"),
    ("phd", "Ph.D."),
    ("hostel", "Hostel & mess"),
)

_MONTH_LABELS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _verified_payment(tx: PaymentTransaction) -> bool:
    if tx.status != PaymentTransactionStatus.SUCCESS:
        return False
    if (tx.payment_mode or "").lower() == "offline":
        return True
    return tx.webhook_verified


def _payment_mode_bucket(tx: PaymentTransaction) -> str:
    mode = (tx.payment_mode or "online").lower()
    ref = (tx.offline_reference or "").lower()
    gateway = (tx.gateway or "").lower()
    if mode == "offline":
        if any(k in ref or k in gateway for k in ("neft", "challan", "bank", "rtgs", "imps")):
            return "bank"
        return "counter"
    return "online"


def _programme_bucket(programme_code: str | None, description: str | None = None) -> str | None:
    desc = (description or "").lower()
    if "hostel" in desc or "mess" in desc:
        return "hostel"
    code = (programme_code or "").upper()
    if not code:
        return None
    if "MBA" in code or "MCA" in code:
        return "mba_mca"
    if "PHD" in code or "DOCTOR" in code:
        return "phd"
    if re.search(r"M\.?\s*E|M\.?\s*TECH|ME-|MTECH", code):
        return "me_mtech"
    if re.search(r"B\.?\s*E|B\.?\s*TECH|BE-|BTECH", code) or code.startswith("B"):
        return "be_btech"
    return "be_btech"


def _collection_status_key(pct: float | None) -> tuple[str, str]:
    if pct is None:
        return "unknown", "—"
    if pct >= 85:
        return "healthy", f"{pct:g}%"
    if pct >= 70:
        return "monitor", f"{pct:g}%"
    return "at_risk", f"{pct:g}%"


def _ay_start_year(label: str | None) -> int | None:
    if not label:
        return None
    match = re.match(r"^(\d{4})", label.strip())
    return int(match.group(1)) if match else None


def _academic_month_sequence(ay_label: str | None, anchor: date, *, limit: int = 6) -> list[tuple[int, int, str, bool]]:
    start = _ay_start_year(ay_label) or anchor.year
    sequence: list[tuple[int, int]] = []
    for month in (6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5):
        year = start if month >= 6 else start + 1
        sequence.append((year, month))
    anchor_ym = (anchor.year, anchor.month)
    eligible = [t for t in sequence if t <= anchor_ym]
    if not eligible:
        eligible = sequence[:limit]
    tail = eligible[-limit:]
    out: list[tuple[int, int, str, bool]] = []
    for year, month in tail:
        label = _MONTH_LABELS[month - 1]
        if (year, month) == anchor_ym:
            label = f"{label} (MTD)"
        out.append((year, month, label, (year, month) == anchor_ym))
    return out


def _matches_fee_head(text: str, fee_head: str | None) -> bool:
    if not fee_head:
        return True
    return fee_head.lower() in text.lower()


async def get_finance_overview(
    scope: AccessScope,
    *,
    academic_year_label: str | None = None,
    programme_code: str | None = None,
    fee_head: str | None = None,
) -> FinanceOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    anchor = now.astimezone(_IST).date()

    year, semester = await _reader.current_academic_term(tenant_id)
    ay_label = academic_year_label or year

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    if programme_code:
        prog_filter = programme_code.upper()
        profiles = [p for p in profiles if (p.programme_code or "").upper() == prog_filter]
        allowed_users = {p.user_id for p in profiles}
    else:
        allowed_users = None

    assessments = await StudentFeeAssessment.find(Eq(StudentFeeAssessment.tenant_id, tenant_id)).to_list()
    if ay_label:
        assessments = [a for a in assessments if a.academic_year_label == ay_label]
    if allowed_users is not None:
        assessments = [a for a in assessments if a.student_user_id in allowed_users]

    fee_heads: set[str] = set()
    fee_structures = await InstitutionFeeStructure.find(Eq(InstitutionFeeStructure.tenant_id, tenant_id)).to_list()
    for structure in fee_structures:
        if ay_label and structure.academic_year_label != ay_label:
            continue
        for item in structure.line_items or []:
            code = item.get("fee_head") or item.get("code") or item.get("label")
            if code:
                fee_heads.add(str(code))
    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    if ay_label:
        demands = [d for d in demands if d.academic_year_label == ay_label]
    if allowed_users is not None:
        demands = [d for d in demands if d.student_user_id in allowed_users]
    if fee_head:
        demands = [d for d in demands if _matches_fee_head(d.description, fee_head)]
        assessments = [a for a in assessments if _matches_fee_head(a.structure_id or "", fee_head)]

    for d in demands:
        head = d.description.split("-")[0].strip() if d.description else "fee"
        if head:
            fee_heads.add(head)

    total_demand = sum(a.net_amount or a.assessed_amount for a in assessments)
    if total_demand <= 0:
        total_demand = sum(d.amount + d.late_fee for d in demands)

    student_ids = {a.student_user_id for a in assessments} | {d.student_user_id for d in demands}

    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()
    collected = 0.0
    mode_totals: dict[str, float] = defaultdict(float)
    monthly: dict[tuple[int, int], float] = defaultdict(float)
    for tx in txs:
        if allowed_users is not None and tx.student_user_id not in allowed_users:
            continue
        if not _verified_payment(tx):
            continue
        collected += tx.amount
        bucket = _payment_mode_bucket(tx)
        mode_totals[bucket] += tx.amount
        local = tx.created_at.astimezone(_IST) if tx.created_at.tzinfo else tx.created_at.replace(tzinfo=timezone.utc).astimezone(_IST)
        if ay_label:
            start = _ay_start_year(ay_label)
            if start and local.year < start and local.month < 6:
                continue
        monthly[(local.year, local.month)] += tx.amount

    outstanding = 0.0
    students_with_dues: set[PydanticObjectId] = set()
    for d in demands:
        if d.status in (FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE):
            outstanding += d.amount + d.late_fee
            students_with_dues.add(d.student_user_id)

    scholarship_amount = sum(a.scholarship_amount for a in assessments)
    concession_rows = await FeeConcession.find(Eq(FeeConcession.tenant_id, tenant_id)).to_list()
    if allowed_users is not None:
        concession_rows = [c for c in concession_rows if c.student_user_id in allowed_users]
    concession_amount = sum(c.amount for c in concession_rows if c.published)
    beneficiaries: set[PydanticObjectId] = set()
    for a in assessments:
        if a.scholarship_amount > 0 or a.concession_amount > 0:
            beneficiaries.add(a.student_user_id)
    for c in concession_rows:
        if c.published and c.amount > 0:
            beneficiaries.add(c.student_user_id)

    collected_pct = round((collected / total_demand) * 100, 1) if total_demand > 0 else None

    inst_settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    target_pct = float((inst_settings.settings or {}).get("finance_collection_target_pct", 85)) if inst_settings else 85.0

    bucket_demand: dict[str, float] = defaultdict(float)
    bucket_collected: dict[str, float] = defaultdict(float)
    bucket_outstanding: dict[str, float] = defaultdict(float)
    bucket_students_due: dict[str, set[PydanticObjectId]] = defaultdict(set)

    for a in assessments:
        profile = profile_by_user.get(a.student_user_id)
        key = _programme_bucket(profile.programme_code if profile else a.programme_code)
        if key is None:
            continue
        bucket_demand[key] += a.net_amount or a.assessed_amount

    for tx in txs:
        if not _verified_payment(tx):
            continue
        if allowed_users is not None and tx.student_user_id not in allowed_users:
            continue
        profile = profile_by_user.get(tx.student_user_id)
        key = _programme_bucket(profile.programme_code if profile else None)
        if key:
            bucket_collected[key] += tx.amount

    for d in demands:
        profile = profile_by_user.get(d.student_user_id)
        key = _programme_bucket(profile.programme_code if profile else None, d.description)
        if key is None:
            continue
        if d.status not in _PAID_STATUSES:
            bucket_outstanding[key] += d.amount + d.late_fee
            bucket_students_due[key].add(d.student_user_id)

    programme_rows: list[FinanceProgrammeDuesRow] = []
    for key, label in _PROGRAMME_BUCKETS:
        demand = bucket_demand.get(key, 0) or (bucket_outstanding.get(key, 0) + bucket_collected.get(key, 0))
        if demand <= 0 and bucket_outstanding.get(key, 0) <= 0:
            continue
        collected_b = bucket_collected.get(key, 0)
        outstanding_b = bucket_outstanding.get(key, 0)
        pct = round((collected_b / demand) * 100, 1) if demand > 0 else None
        status_key, status_label = _collection_status_key(pct)
        programme_rows.append(
            FinanceProgrammeDuesRow(
                bucket_key=key,
                label=label,
                demand_amount=round(demand, 2),
                collected_amount=round(collected_b, 2),
                outstanding_amount=round(outstanding_b, 2),
                students_with_dues=len(bucket_students_due.get(key, set())),
                collection_pct=pct,
                status_key=status_key,
                status_label=status_label,
            )
        )

    month_sequence = _academic_month_sequence(ay_label, anchor)
    monthly_points = [
        FinanceMonthlyCollectionPoint(
            year=year,
            month=month,
            label=label,
            amount_inr=round(monthly.get((year, month), 0), 2),
            is_month_to_date=is_mtd,
        )
        for year, month, label, is_mtd in month_sequence
    ]

    mode_total = sum(mode_totals.values()) or 1
    payment_modes = [
        FinancePaymentModeItem(
            mode_key="online",
            label="Online gateway",
            share_pct=round((mode_totals.get("online", 0) / mode_total) * 100, 1),
            amount_inr=round(mode_totals.get("online", 0), 2),
        ),
        FinancePaymentModeItem(
            mode_key="bank",
            label="Bank challan / NEFT",
            share_pct=round((mode_totals.get("bank", 0) / mode_total) * 100, 1),
            amount_inr=round(mode_totals.get("bank", 0), 2),
        ),
        FinancePaymentModeItem(
            mode_key="counter",
            label="Counter – DD / cheque",
            share_pct=round((mode_totals.get("counter", 0) / mode_total) * 100, 1),
            amount_inr=round(mode_totals.get("counter", 0), 2),
        ),
    ]

    unreconciled = await PaymentReconciliationRecord.find(
        Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
        Eq(PaymentReconciliationRecord.reconciled, False),
    ).count()
    refund_pending = await RefundRequest.find(
        Eq(RefundRequest.tenant_id, tenant_id),
        Eq(RefundRequest.status, RefundStatus.REQUESTED),
    ).count()
    concession_pending = await OfficialScholarshipApplication.find(
        Eq(OfficialScholarshipApplication.tenant_id, tenant_id),
        Eq(OfficialScholarshipApplication.status, ScholarshipApplicationStatus.IN_REVIEW),
    ).count()
    failed_online = sum(
        1
        for tx in txs
        if tx.status == PaymentTransactionStatus.FAILED and (tx.payment_mode or "").lower() != "offline"
    )

    attention = [
        FinanceAttentionItem(item_key="unreconciled", label="Unreconciled transactions", count=unreconciled),
        FinanceAttentionItem(item_key="refunds", label="Refund requests", count=refund_pending),
        FinanceAttentionItem(item_key="concessions", label="Concession approvals", count=concession_pending),
        FinanceAttentionItem(item_key="failed_payments", label="Failed online payments", count=failed_online),
    ]

    scholarship_programs = await ScholarshipProgram.find(Eq(ScholarshipProgram.tenant_id, tenant_id)).to_list()
    program_by_id = {p.programme_id: p for p in scholarship_programs}
    approved_apps = await OfficialScholarshipApplication.find(
        Eq(OfficialScholarshipApplication.tenant_id, tenant_id),
        Eq(OfficialScholarshipApplication.status, ScholarshipApplicationStatus.APPROVED),
    ).to_list()
    if ay_label:
        approved_apps = [a for a in approved_apps if not a.academic_year_label or a.academic_year_label == ay_label]
    disbursement_map: dict[str, float] = defaultdict(float)
    for app in approved_apps:
        title = program_by_id.get(app.programme_id).title if app.programme_id in program_by_id else app.programme_id
        disbursement_map[title] += app.requested_award_amount or 0
    for c in concession_rows:
        if c.published:
            disbursement_map[c.title] += c.amount
    scholarship_items = [
        FinanceScholarshipDisbursementItem(program_label=label, amount_inr=round(amt, 2))
        for label, amt in sorted(disbursement_map.items(), key=lambda x: -x[1])[:6]
    ]

    display_year = ay_label or "Current year"
    if ay_label and "-" in ay_label:
        parts = ay_label.split("-")
        if len(parts[0]) == 4 and len(parts[1]) == 2:
            display_year = f"{parts[0]}–{parts[1]}"

    return FinanceOverviewRead(
        filters=FinanceOverviewFilters(
            academic_year_label=ay_label,
            programme_code=programme_code,
            fee_head=fee_head,
        ),
        academic_term=AcademicTermSummary(academic_year_label=ay_label, semester_label=semester),
        academic_year_display=display_year,
        kpis=FinanceOverviewKpiRead(
            total_demand_inr=round(total_demand, 2),
            student_count=len(student_ids),
            fee_head_count=len(fee_heads),
            collected_inr=round(collected, 2),
            collected_pct=collected_pct,
            outstanding_inr=round(outstanding, 2),
            students_with_dues=len(students_with_dues),
            scholarships_concessions_inr=round(scholarship_amount + concession_amount, 2),
            scholarship_beneficiaries=len(beneficiaries),
        ),
        monthly_collection=monthly_points,
        programme_dues_rows=programme_rows,
        collection_target_pct=target_pct,
        payment_modes=payment_modes,
        attention_items=attention,
        scholarship_disbursements=scholarship_items,
        fee_head_options=sorted(fee_heads),
        generated_at=utcnow(),
    )