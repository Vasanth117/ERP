"""Library reports listing (CA 12.12)."""

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
    LibraryReportsPageRead,
    LibraryReportsTableRow,
    PoliciesPagination,
)
from app.modules.library.report_access import can_view_finance_reports
from app.modules.library.report_catalog import catalog_for_role
from app.modules.library.report_models import LibraryReportJob, LibraryReportJobStatus

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"]
_FORMAT_LABELS = {"json": "PDF", "csv": "CSV", "xlsx": "Excel", "pdf": "PDF"}

_SCHEDULE_BY_TYPE: dict[str, str] = {
    "circulation_summary": "Monthly",
    "overdue_books": "Daily",
    "acquisition_procurement": "Monthly",
    "fine_summary": "Monthly",
    "member_activity": "Weekly",
}


def _format_label(supported: list[str]) -> str:
    labels: list[str] = []
    for fmt in supported:
        key = (fmt or "").lower()
        label = _FORMAT_LABELS.get(key, key.upper())
        if label not in labels:
            labels.append(label)
    return ", ".join(labels) if labels else "—"


def _short_day(value: date) -> str:
    return value.strftime("%d %b")


def _period_label(report_type: str, filters: dict | None, today: date) -> str:
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
    if report_type == "overdue_books":
        return f"As on {_short_day(today)}"
    if report_type == "circulation_summary":
        month = today.month - 1 or 12
        year = today.year if today.month > 1 else today.year - 1
        return f"{month_name[month][:3]} {year}"
    if report_type == "acquisition_procurement":
        start = today.year if today.month >= 4 else today.year - 1
        end = start + 1
        return f"FY {start}–{str(end)[-2:]}"
    return "—"


async def get_library_reports_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryReportsPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    catalog = catalog_for_role(can_finance=can_view_finance_reports(scope))
    total = len(catalog)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    page_catalog = catalog[offset : offset + page_size]

    latest = await LibraryReportJob.find(
        Eq(LibraryReportJob.tenant_id, tenant_id),
        Eq(LibraryReportJob.status, LibraryReportJobStatus.COMPLETED),
    ).sort("-completed_at").to_list()
    latest_by_type: dict[str, LibraryReportJob] = {}
    for job in latest:
        if job.report_type not in latest_by_type:
            latest_by_type[job.report_type] = job

    table_rows: list[LibraryReportsTableRow] = []
    for item in page_catalog:
        job = latest_by_type.get(item.report_type)
        last_run = "—"
        period = _period_label(item.report_type, job.filters if job else None, today)
        if job and job.completed_at:
            last_run = _short_day(job.completed_at.astimezone(_IST).date())
        elif job and job.created_at:
            last_run = _short_day(job.created_at.astimezone(_IST).date())
        table_rows.append(
            LibraryReportsTableRow(
                report_type=item.report_type,
                report_label=item.name,
                period_label=period,
                format_label=_format_label(item.supported_formats),
                last_run_label=last_run,
                schedule_label=_SCHEDULE_BY_TYPE.get(item.report_type, "On demand"),
                detail_href=f"/college-admin/library/library-reports?report_type={item.report_type}",
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(table_rows))
    showing_label = f"{showing_end:,} of {total:,}"

    return LibraryReportsPageRead(
        page_title="Library Reports",
        page_subtitle="Circulation and usage reports",
        create_report_label="Create report",
        create_report_href="/college-admin/library/library-reports?action=create",
        reports_section_title="Reports",
        table_headers=_TABLE_HEADERS,
        report_rows=table_rows,
        empty_table_message="No report templates available.",
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