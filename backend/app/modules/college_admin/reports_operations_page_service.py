"""Operations reports module pages (CA 16 Operations)."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, In, LTE

from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.college_admin.finance_overview_service import _verified_payment
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.reports_academic_page_service import (
    _academic_year_label,
    _department_options,
    _fmt_last_run,
    _fmt_updated,
    _format_labels,
    _period_for,
    _sync_last_runs,
)
from app.modules.college_admin.reports_admin_models import InstitutionReportsAcademicDefinition
from app.modules.college_admin.reports_operations_catalog import page_meta, page_rows
from app.modules.college_admin.schemas import (
    InstitutionFieldOption,
    PoliciesPagination,
    ReportsAcademicHighlightBar,
    ReportsAcademicModulePageRead,
    ReportsAcademicTableRow,
    UserDashboardKpi,
)
from app.modules.finance.finance_enums import FeeDemandStatus, RefundStatus
from app.modules.finance.finance_models import PaymentTransaction, RefundRecord, StudentFeeDemand
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus
from app.modules.hostel.infrastructure_models import InstitutionHostel
from app.modules.hostel.maintenance_models import HostelComplaint, HostelComplaintStatus
from app.modules.hostel.rules_incident_models import HostelIncident, HostelIncidentStatus
from app.modules.library.dashboard_filters import build_dashboard_context
from app.modules.library.dashboard_repository import LibraryDashboardRepository
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryDashboardDateRange
from app.modules.library.library_models import LibraryCirculation
from app.modules.students.models import StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"]
_HIGHLIGHT_TONES = ("success", "success", "info", "warning")
_lib_dashboard = LibraryDashboardRepository()


def _fmt_inr(amount: float) -> str:
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f} Cr"
    if amount >= 100_000:
        lakhs = amount / 100_000
        return f"₹{lakhs:.1f} L" if lakhs < 10 else f"₹{lakhs:.0f} L"
    return f"₹{amount:,.0f}"


def _norm_ay(label: str) -> str:
    return label.replace("-", "–").strip()


def _matches_ay(record_label: str | None, ay_label: str) -> bool:
    if not record_label:
        return False
    return _norm_ay(record_label) == _norm_ay(ay_label)


def _student_user_ids_for_department(
    profiles: list[StudentProfile],
    department_id: PydanticObjectId | None,
) -> set[PydanticObjectId] | None:
    if department_id is None:
        return None
    return {p.user_id for p in profiles if p.department_id == department_id}


async def _ensure_definitions(
    tenant_id: PydanticObjectId,
    page_key: str,
    ay_label: str,
) -> list[InstitutionReportsAcademicDefinition]:
    existing = await InstitutionReportsAcademicDefinition.find(
        Eq(InstitutionReportsAcademicDefinition.tenant_id, tenant_id),
        Eq(InstitutionReportsAcademicDefinition.page_key, page_key),
        Eq(InstitutionReportsAcademicDefinition.is_active, True),
    ).sort("+sort_order").to_list()
    if existing:
        changed = False
        for row in existing:
            seed = next((s for s in page_rows(page_key) if s.report_key == row.report_key), None)
            period = await _period_for(seed.period_kind if seed else "month", tenant_id, ay_label)
            if row.period_label != period:
                row.period_label = period
                row.updated_at = utcnow()
                changed = True
        if changed:
            for row in existing:
                await row.save()
        return existing

    seeds = page_rows(page_key)
    created: list[InstitutionReportsAcademicDefinition] = []
    for index, seed in enumerate(seeds):
        period = await _period_for(seed.period_kind, tenant_id, ay_label)
        doc = InstitutionReportsAcademicDefinition(
            tenant_id=tenant_id,
            page_key=page_key,
            report_key=seed.report_key,
            title=seed.title,
            period_label=period,
            export_formats=list(seed.export_formats),
            schedule_label=seed.schedule_label,
            last_run_at=None,
            sort_order=index,
        )
        await doc.insert()
        created.append(doc)
    return created


async def _finance_metrics(
    tenant_id: PydanticObjectId,
    ay_label: str,
    department_id: PydanticObjectId | None,
) -> tuple[float, float, float, float, float | None]:
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    allowed = _student_user_ids_for_department(profiles, department_id)

    assessments = await StudentFeeAssessment.find(Eq(StudentFeeAssessment.tenant_id, tenant_id)).to_list()
    assessments = [a for a in assessments if _matches_ay(a.academic_year_label, ay_label)]
    if allowed is not None:
        assessments = [a for a in assessments if a.student_user_id in allowed]

    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    demands = [d for d in demands if _matches_ay(d.academic_year_label, ay_label)]
    if allowed is not None:
        demands = [d for d in demands if d.student_user_id in allowed]

    billed = sum(a.net_amount or a.assessed_amount for a in assessments)
    if billed <= 0:
        billed = sum(d.amount + d.late_fee for d in demands)

    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()
    if allowed is not None:
        txs = [t for t in txs if t.student_user_id in allowed]
    collected = sum(t.amount for t in txs if _verified_payment(t))
    collected_pct = round((collected / billed) * 100, 1) if billed > 0 else None

    outstanding = 0.0
    for d in demands:
        if d.status in (FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE):
            outstanding += d.amount + d.late_fee

    refunds = await RefundRecord.find(Eq(RefundRecord.tenant_id, tenant_id)).to_list()
    if allowed is not None:
        refunds = [r for r in refunds if r.student_user_id in allowed]
    refund_amount = sum(
        r.amount for r in refunds if r.status in (RefundStatus.PROCESSED, RefundStatus.APPROVED, RefundStatus.REQUESTED)
    )

    scholarships = sum(a.scholarship_amount + (a.concession_amount or 0) for a in assessments)
    return collected, outstanding, refund_amount, scholarships, collected_pct


async def _finance_kpis(
    tenant_id: PydanticObjectId,
    ay_label: str,
    department_id: PydanticObjectId | None,
) -> list[UserDashboardKpi]:
    collected, outstanding, refunds, scholarships, collected_pct = await _finance_metrics(tenant_id, ay_label, department_id)
    return [
        UserDashboardKpi(
            key="collected",
            label="Collected",
            value=_fmt_inr(collected),
            hint_line=f"{collected_pct:.1f}%" if collected_pct is not None else "",
            hint_tone="success" if collected_pct and collected_pct >= 75 else "warning",
        ),
        UserDashboardKpi(key="outstanding", label="Outstanding", value=_fmt_inr(outstanding), hint_line="", hint_tone="warning" if outstanding else "success"),
        UserDashboardKpi(key="refunds", label="Refunds", value=_fmt_inr(refunds), hint_line="", hint_tone="info"),
        UserDashboardKpi(key="scholarships", label="Scholarships", value=_fmt_inr(scholarships), hint_line="", hint_tone="info"),
    ]


async def _finance_highlights(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
) -> list[ReportsAcademicHighlightBar]:
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    if department_id:
        profiles = [p for p in profiles if p.department_id == department_id]
    profile_by_user = {p.user_id: p for p in profiles}

    assessments = await StudentFeeAssessment.find(Eq(StudentFeeAssessment.tenant_id, tenant_id)).to_list()
    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()

    dept_billed: dict[PydanticObjectId, float] = defaultdict(float)
    dept_collected: dict[PydanticObjectId, float] = defaultdict(float)
    for a in assessments:
        profile = profile_by_user.get(a.student_user_id)
        if profile and profile.department_id:
            dept_billed[profile.department_id] += a.net_amount or a.assessed_amount
    for tx in txs:
        if not _verified_payment(tx):
            continue
        profile = profile_by_user.get(tx.student_user_id)
        if profile and profile.department_id:
            dept_collected[profile.department_id] += tx.amount

    depts = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    if department_id:
        depts = [d for d in depts if d.id == department_id]

    metrics: list[tuple[InstitutionDepartment, int]] = []
    for dept in depts:
        billed = dept_billed.get(dept.id, 0)
        collected = dept_collected.get(dept.id, 0)
        pct = int(round((collected / billed) * 100)) if billed > 0 else 0
        metrics.append((dept, min(100, pct)))
    metrics.sort(key=lambda x: x[1], reverse=True)

    return [
        ReportsAcademicHighlightBar(
            bar_key=str(dept.id),
            department_label=dept.name or dept.code or "Department",
            percent_value=pct,
            tone=_HIGHLIGHT_TONES[i % len(_HIGHLIGHT_TONES)],
        )
        for i, (dept, pct) in enumerate(metrics[:4])
    ]


async def _library_kpis(tenant_id: PydanticObjectId, department_id: PydanticObjectId | None) -> list[UserDashboardKpi]:
    today = utcnow().astimezone(_IST).date()
    ctx = await build_dashboard_context(
        tenant_id,
        branch_code=None,
        category=None,
        copy_status=None,
        anchor_date=today,
        date_range=LibraryDashboardDateRange.MONTH,
    )
    copies = await _lib_dashboard.copy_inventory(ctx)
    fines = await _lib_dashboard.outstanding_fines(ctx)
    digital = await _lib_dashboard.digital_stats(ctx)
    members = await _lib_dashboard.member_stats(ctx)

    month_start = datetime.combine(today.replace(day=1), datetime.min.time(), tzinfo=timezone.utc)
    if today.month == 12:
        month_end = datetime(today.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        month_end = datetime(today.year, today.month + 1, 1, tzinfo=timezone.utc)

    circ_query: dict = {
        "tenant_id": tenant_id,
        "issued_at": {"$gte": month_start, "$lt": month_end},
    }
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    allowed = _student_user_ids_for_department(profiles, department_id)
    if allowed is not None:
        circ_query["student_user_id"] = {"$in": list(allowed)}

    issued = await LibraryCirculation.find(circ_query).count()
    overdue_match: dict = {
        "tenant_id": tenant_id,
        "status": {"$in": [LibraryCirculationStatus.OVERDUE.value, LibraryCirculationStatus.ACTIVE.value]},
        "due_at": {"$lt": today},
    }
    if allowed is not None:
        overdue_match["student_user_id"] = {"$in": list(allowed)}
    overdue = await LibraryCirculation.find(overdue_match).count()

    fine_amount = fines.total_amount
    digital_users = members.active if members.active else digital.published

    return [
        UserDashboardKpi(key="issued", label="Issued this month", value=f"{issued:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(key="overdue", label="Overdue", value=f"{overdue:,}", hint_line="", hint_tone="warning" if overdue else "success"),
        UserDashboardKpi(
            key="fines",
            label="Fines",
            value=_fmt_inr(float(fine_amount or 0)),
            hint_line="",
            hint_tone="warning" if fine_amount else "success",
        ),
        UserDashboardKpi(
            key="digital_users",
            label="Digital users",
            value=f"{digital_users:,}",
            hint_line="",
            hint_tone="info",
        ),
    ]


async def _library_highlights(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
) -> list[ReportsAcademicHighlightBar]:
    today = utcnow().astimezone(_IST).date()
    month_start = datetime.combine(today.replace(day=1), datetime.min.time(), tzinfo=timezone.utc)
    if today.month == 12:
        month_end = datetime(today.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        month_end = datetime(today.year, today.month + 1, 1, tzinfo=timezone.utc)

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    circs = await LibraryCirculation.find(
        {"tenant_id": tenant_id, "issued_at": {"$gte": month_start, "$lt": month_end}},
    ).to_list()

    counts: dict[PydanticObjectId, int] = defaultdict(int)
    for c in circs:
        profile = profile_by_user.get(c.student_user_id)
        if profile and profile.department_id:
            if department_id and profile.department_id != department_id:
                continue
            counts[profile.department_id] += 1

    depts = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    if department_id:
        depts = [d for d in depts if d.id == department_id]

    max_count = max(counts.values()) if counts else 1
    metrics = [(d, int(round((counts.get(d.id, 0) / max_count) * 100))) for d in depts]
    metrics.sort(key=lambda x: x[1], reverse=True)

    return [
        ReportsAcademicHighlightBar(
            bar_key=str(dept.id),
            department_label=dept.name or dept.code or "Department",
            percent_value=min(100, pct),
            tone=_HIGHLIGHT_TONES[i % len(_HIGHLIGHT_TONES)],
        )
        for i, (dept, pct) in enumerate(metrics[:4])
    ]


async def _hostel_kpis(tenant_id: PydanticObjectId) -> list[UserDashboardKpi]:
    beds = await HostelBed.find(Eq(HostelBed.tenant_id, tenant_id)).to_list()
    total_beds = len(beds)
    occupied = sum(1 for b in beds if b.status == HostelBedStatus.ALLOCATED)
    occupancy_pct = round((occupied / total_beds) * 100, 1) if total_beds else 0.0

    hostel_demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        In(StudentFeeDemand.status, [FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE]),
    ).to_list()
    pattern = re.compile(r"(hostel|mess|boarding)", re.I)
    defaulter_ids: set[PydanticObjectId] = set()
    for d in hostel_demands:
        if pattern.search(d.description or ""):
            defaulter_ids.add(d.student_user_id)

    open_complaints = await HostelComplaint.find(
        Eq(HostelComplaint.tenant_id, tenant_id),
        In(
            HostelComplaint.status,
            [
                HostelComplaintStatus.SUBMITTED,
                HostelComplaintStatus.ASSIGNED,
                HostelComplaintStatus.IN_PROGRESS,
            ],
        ),
    ).count()
    open_incidents = await HostelIncident.find(
        Eq(HostelIncident.tenant_id, tenant_id),
        In(
            HostelIncident.status,
            [
                HostelIncidentStatus.REPORTED,
                HostelIncidentStatus.UNDER_REVIEW,
                HostelIncidentStatus.UNDER_INVESTIGATION,
                HostelIncidentStatus.ACTION_REQUIRED,
            ],
        ),
    ).count()

    return [
        UserDashboardKpi(
            key="occupancy",
            label="Occupancy",
            value=f"{occupancy_pct:.1f}%",
            hint_line="",
            hint_tone="success" if occupancy_pct >= 80 else "info",
        ),
        UserDashboardKpi(
            key="fee_defaulters",
            label="Fee defaulters",
            value=f"{len(defaulter_ids):,}",
            hint_line="",
            hint_tone="warning" if defaulter_ids else "success",
        ),
        UserDashboardKpi(
            key="complaints",
            label="Open complaints",
            value=f"{open_complaints:,}",
            hint_line="",
            hint_tone="warning" if open_complaints else "success",
        ),
        UserDashboardKpi(
            key="incidents",
            label="Incidents",
            value=f"{open_incidents:,}",
            hint_line="",
            hint_tone="warning" if open_incidents else "success",
        ),
    ]


async def _hostel_highlights(tenant_id: PydanticObjectId) -> list[ReportsAcademicHighlightBar]:
    hostels = await InstitutionHostel.find(Eq(InstitutionHostel.tenant_id, tenant_id)).to_list()
    metrics: list[tuple[str, str, int]] = []
    for h in hostels:
        beds = await HostelBed.find(
            Eq(HostelBed.tenant_id, tenant_id),
            Eq(HostelBed.hostel_code, h.hostel_code),
        ).to_list()
        if not beds:
            continue
        occ = sum(1 for b in beds if b.status == HostelBedStatus.ALLOCATED)
        pct = int(round((occ / len(beds)) * 100))
        metrics.append((h.hostel_code, h.name or h.hostel_code, min(100, pct)))
    metrics.sort(key=lambda x: x[2], reverse=True)

    return [
        ReportsAcademicHighlightBar(bar_key=key, department_label=label, percent_value=pct, tone=_HIGHLIGHT_TONES[i % len(_HIGHLIGHT_TONES)])
        for i, (key, label, pct) in enumerate(metrics[:4])
    ]


async def get_reports_operations_module_page(
    scope: AccessScope,
    *,
    page_key: str,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    academic_year: str | None = None,
    department_id: str | None = None,
) -> ReportsAcademicModulePageRead:
    meta = page_meta(page_key)
    if meta is None:
        raise AppError(code="NOT_FOUND", message="Unknown reports page", status_code=404)
    authorize(scope, meta.permission)
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    now = utcnow()
    ay_label = await _academic_year_label(tenant_id, academic_year)

    definitions = await _ensure_definitions(tenant_id, page_key, ay_label)
    await _sync_last_runs(tenant_id, definitions, meta.run_report_key)

    total = len(definitions)
    page = max(1, page)
    page_size = max(1, min(page_size, 20))
    start = (page - 1) * page_size
    visible = definitions[start : start + page_size]

    table_rows = [
        ReportsAcademicTableRow(
            row_key=row.report_key,
            report_label=row.title,
            period_label=row.period_label,
            format_label=_format_labels(row.export_formats),
            last_run_label=_fmt_last_run(row.last_run_at),
            schedule_label=row.schedule_label,
        )
        for row in visible
    ]

    if page_key == "finance":
        kpis = await _finance_kpis(tenant_id, ay_label, dept_oid)
        highlights = await _finance_highlights(tenant_id, dept_oid)
    elif page_key == "library":
        kpis = await _library_kpis(tenant_id, dept_oid)
        highlights = await _library_highlights(tenant_id, dept_oid)
    else:
        kpis = await _hostel_kpis(tenant_id)
        highlights = await _hostel_highlights(tenant_id)

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, start + len(table_rows))

    return ReportsAcademicModulePageRead(
        page_key=page_key,
        page_title=meta.page_title,
        page_subtitle=meta.page_subtitle,
        export_label="Export",
        run_report_label="Run report",
        academic_year_label=f"AY {ay_label}",
        academic_year_options=[InstitutionFieldOption(value=ay_label, label=f"AY {ay_label}")],
        department_filter_label="All departments",
        department_options=await _department_options(tenant_id),
        selected_department_id=department_id or "",
        scope_badge_label="College scope" if not dept_oid else "Department scope",
        updated_at_label=_fmt_updated(now),
        kpis=kpis,
        reports_section_title="Reports",
        highlights_section_title="Highlights",
        table_headers=_TABLE_HEADERS,
        report_rows=table_rows,
        highlight_bars=highlights,
        empty_table_message="No reports configured yet.",
        empty_highlights_message="No highlights yet.",
        showing_label=f"Showing {showing_end} of {total}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        run_report_key=meta.run_report_key,
        generated_at=now,
    )