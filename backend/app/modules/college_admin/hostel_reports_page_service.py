"""Hostel reports listing (CA 13.14)."""

from __future__ import annotations

import math
from calendar import month_name
from datetime import date
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelReportsPageRead,
    HostelReportsTableRow,
    PoliciesPagination,
)
from app.modules.hostel.reports_catalog import catalog_for_scope
from app.modules.hostel.reports_models import (
    HostelReportExecutionHistory,
    HostelReportExportFormat,
    HostelScheduledReport,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"]
_FORMAT_LABELS = {
    HostelReportExportFormat.CSV.value: "CSV",
    HostelReportExportFormat.EXCEL.value: "Excel",
    HostelReportExportFormat.PDF.value: "PDF",
    "csv": "CSV",
    "excel": "Excel",
    "xlsx": "Excel",
    "pdf": "PDF",
}

_REPORT_SHORT_LABELS: dict[str, str] = {
    "occupancy_overview": "Occupancy",
    "mess_billing_outstanding": "Fee collection",
    "maintenance_complaints": "Complaints summary",
}


def _format_labels(*, supported: tuple[str, ...], scheduled_fmt: str | None) -> str:
    labels: list[str] = []
    for fmt in supported:
        key = (fmt or "").lower()
        label = _FORMAT_LABELS.get(key, key.upper() if key else "")
        if label and label not in labels:
            labels.append(label)
    if scheduled_fmt:
        key = scheduled_fmt.lower()
        label = _FORMAT_LABELS.get(key, key.upper())
        if label and label not in labels:
            labels.append(label)
    return ", ".join(labels) if labels else "—"


def _short_day(value: date) -> str:
    return value.strftime("%d %b")


def _academic_year_label(today: date) -> str:
    start = today.year if today.month >= 4 else today.year - 1
    end = start + 1
    return f"{start}-{str(end)[-2:]}"


def _period_label(report_key: str, filters: dict | None, today: date) -> str:
    if filters:
        raw_from = filters.get("date_from")
        raw_to = filters.get("date_to")
        if raw_from and raw_to:
            try:
                d_from = date.fromisoformat(str(raw_from)[:10])
                d_to = date.fromisoformat(str(raw_to)[:10])
                if d_from.year == d_to.year and d_from.month == d_to.month:
                    return f"{month_name[d_from.month][:3]} {d_from.year}"
                return f"{_short_day(d_from)} – {_short_day(d_to)}"
            except ValueError:
                pass
        period = filters.get("period_label") or filters.get("academic_year")
        if period:
            return str(period)
    if report_key == "occupancy_overview":
        return f"{month_name[today.month][:3]} {today.year}"
    if report_key in {"mess_billing_outstanding", "residents_current", "applications_summary"}:
        return _academic_year_label(today)
    if report_key == "maintenance_complaints":
        month = today.month - 1 or 12
        year = today.year if today.month > 1 else today.year - 1
        return f"{month_name[month][:3]} {year}"
    return "—"


def _schedule_label(doc: HostelScheduledReport | None) -> str:
    if doc is None or not doc.is_active:
        return "On demand"
    freq = (doc.frequency.value if hasattr(doc.frequency, "value") else str(doc.frequency)).lower()
    return {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}.get(freq, freq.title())


def _report_label(report_key: str, fallback: str) -> str:
    return _REPORT_SHORT_LABELS.get(report_key, fallback)


async def get_hostel_reports_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HostelReportsPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    catalog = catalog_for_scope(scope.effective_permissions)
    total = len(catalog)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    page_catalog = catalog[offset : offset + page_size]

    executions = await HostelReportExecutionHistory.find(
        Eq(HostelReportExecutionHistory.tenant_id, tenant_id),
        Eq(HostelReportExecutionHistory.status, "completed"),
    ).sort("-completed_at").to_list()
    latest_by_key: dict[str, HostelReportExecutionHistory] = {}
    for row in executions:
        if row.report_key not in latest_by_key:
            latest_by_key[row.report_key] = row

    schedules = await HostelScheduledReport.find(Eq(HostelScheduledReport.tenant_id, tenant_id)).to_list()
    schedule_by_key: dict[str, HostelScheduledReport] = {}
    for sched in schedules:
        existing = schedule_by_key.get(sched.report_key)
        if existing is None or (sched.is_active and not existing.is_active):
            schedule_by_key[sched.report_key] = sched

    table_rows: list[HostelReportsTableRow] = []
    for item in page_catalog:
        execution = latest_by_key.get(item.report_key)
        schedule = schedule_by_key.get(item.report_key)
        last_run = "—"
        filters = execution.filters if execution else None
        if execution and execution.completed_at:
            last_run = _short_day(execution.completed_at.astimezone(_IST).date())
        elif execution and execution.created_at:
            last_run = _short_day(execution.created_at.astimezone(_IST).date())
        sched_fmt = None
        if schedule:
            sched_fmt = schedule.export_format.value if hasattr(schedule.export_format, "value") else str(schedule.export_format)
        table_rows.append(
            HostelReportsTableRow(
                report_key=item.report_key,
                report_label=_report_label(item.report_key, item.title),
                period_label=_period_label(item.report_key, filters, today),
                format_label=_format_labels(supported=item.supported_formats, scheduled_fmt=sched_fmt),
                last_run_label=last_run,
                schedule_label=_schedule_label(schedule),
                detail_href=f"/college-admin/hostel/hostel-reports?report_key={item.report_key}",
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(table_rows))
    showing_label = f"{showing_end:,} of {total:,}"

    return HostelReportsPageRead(
        page_title="Hostel Reports",
        page_subtitle="Occupancy, fee and incident reports",
        create_report_label="Create report",
        create_report_href="/college-admin/hostel/hostel-reports?action=create",
        reports_section_title="Reports",
        table_headers=_TABLE_HEADERS,
        report_rows=table_rows,
        empty_table_message="No report templates available for your access.",
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )