"""Reports & analytics overview dashboard (CA 16.01)."""

from __future__ import annotations

import math
from calendar import month_name
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.reports_admin_models import (
    InstitutionReportExport,
    InstitutionReportJob,
    ReportJobStatus,
)
from app.modules.college_admin.reports_admin_service import _ensure_definitions, _permission_allowed
from app.modules.college_admin.reports_hub_catalog import group_meta, hub_items
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    ReportsDashboardGroupRow,
    ReportsDashboardPageRead,
    ReportsDashboardTableRow,
    UserDashboardKpi,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"]
_FORMAT_LABELS = {"csv": "CSV", "excel": "Excel", "pdf": "PDF", "json": "JSON", "xlsx": "Excel"}

_reader = OperationalDataReader()


def _format_label(formats: tuple[str, ...] | list[str]) -> str:
    labels: list[str] = []
    for fmt in formats:
        key = (fmt or "").lower()
        label = _FORMAT_LABELS.get(key, key.upper())
        if label not in labels:
            labels.append(label)
    return ", ".join(labels) if labels else "—"


def _short_day(value: datetime) -> str:
    return value.astimezone(_IST).strftime("%d %b")


def _schedule_label(job: InstitutionReportJob | None, default: str) -> str:
    if job and job.schedule_cron:
        if "week" in job.schedule_cron.lower() or job.schedule_cron.startswith("0 0 * * 1"):
            return "Weekly"
        if "day" in job.schedule_cron.lower() or job.schedule_cron == "0 6 * * *":
            return "Daily"
        return "Monthly"
    return default


async def _period_label(
    tenant_id,
    *,
    report_key: str,
    item_title: str,
    job: InstitutionReportJob | None,
) -> str:
    now = utcnow().astimezone(_IST)
    if job and job.completed_at:
        dt = as_utc_aware(job.completed_at).astimezone(_IST)
        if report_key == "finance":
            start = dt.year if dt.month >= 4 else dt.year - 1
            end = start + 1
            return f"FY {start}–{str(end)[-2:]}"
        if report_key in ("examination",) and "Odd" in item_title:
            return f"Odd {dt.year}"
        return f"{month_name[dt.month][:3]} {dt.year}"
    year, _sem = await _reader.current_academic_term(tenant_id)
    if report_key == "finance" and year:
        parts = year.replace("–", "-").split("-")
        if len(parts) >= 2:
            return f"FY {parts[0]}–{parts[1][-2:]}"
        return f"FY {year}"
    if report_key == "attendance":
        return now.strftime("%b %Y")
    return now.strftime("%b %Y")


async def get_reports_dashboard_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> ReportsDashboardPageRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    await _ensure_definitions(tenant_id)

    visible = [item for item in hub_items() if _permission_allowed(scope, item.required_permission)]
    module_labels = {item.module_label for item in visible}

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    jobs = await InstitutionReportJob.find(Eq(InstitutionReportJob.tenant_id, tenant_id)).sort("-created_at").to_list()
    completed = [j for j in jobs if j.status == ReportJobStatus.COMPLETED]
    runs_month = sum(1 for j in jobs if j.created_at >= month_start)
    scheduled = sum(1 for j in jobs if j.schedule_cron)
    failed = sum(1 for j in jobs if j.status == ReportJobStatus.FAILED)

    latest_job_by_key: dict[str, InstitutionReportJob] = {}
    for job in completed:
        if job.report_key not in latest_job_by_key:
            latest_job_by_key[job.report_key] = job

    scheduled_job_by_key: dict[str, InstitutionReportJob] = {}
    for job in jobs:
        if job.schedule_cron and job.report_key not in scheduled_job_by_key:
            scheduled_job_by_key[job.report_key] = job

    exports = await InstitutionReportExport.find(Eq(InstitutionReportExport.tenant_id, tenant_id)).sort("-created_at").to_list()
    format_by_job: dict[str, str] = {}
    for ex in exports:
        if ex.job_id not in format_by_job:
            format_by_job[ex.job_id] = ex.format

    total = len(visible)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    page_items = visible[offset : offset + page_size]

    rows: list[ReportsDashboardTableRow] = []
    for item in page_items:
        job = latest_job_by_key.get(item.report_key)
        sched = scheduled_job_by_key.get(item.report_key)
        last_run = "—"
        if job and job.completed_at:
            last_run = _short_day(as_utc_aware(job.completed_at))
        formats = list(item.export_formats)
        if job and job.job_id in format_by_job:
            fmt = format_by_job[job.job_id]
            if fmt and fmt not in formats:
                formats = [fmt, *formats]
        rows.append(
            ReportsDashboardTableRow(
                row_id=item.catalog_id,
                report_label=item.title,
                period_label=await _period_label(
                    tenant_id,
                    report_key=item.report_key,
                    item_title=item.title,
                    job=job,
                ),
                format_label=_format_label(formats),
                last_run_label=last_run,
                schedule_label=_schedule_label(sched, item.schedule_label),
                detail_href=item.detail_href,
            )
        )

    groups: list[ReportsDashboardGroupRow] = []
    meta = group_meta()
    for group_key, (label, icon_key, href) in meta.items():
        count = sum(1 for item in visible if item.group_key == group_key)
        groups.append(
            ReportsDashboardGroupRow(
                group_key=group_key,
                label=label,
                count_label=f"{count} reports",
                count_badge=str(count),
                icon_key=icon_key,
                detail_href=href,
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(rows))
    showing_label = f"Showing {showing_end} of {total}" if total else "Showing 0 of 0"

    kpis = [
        UserDashboardKpi(
            key="reports_available",
            label="Reports available",
            value=f"{total:,}",
            hint_line=f"Across {len(module_labels)} modules",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="runs_this_month",
            label="Run this month",
            value=f"{runs_month:,}",
            hint_line=now.astimezone(_IST).strftime("%b %Y"),
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="scheduled",
            label="Scheduled",
            value=f"{scheduled:,}",
            hint_line="Active schedules",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="failed_runs",
            label="Failed runs",
            value=f"{failed:,}",
            hint_line="Requires attention" if failed else "All clear",
            hint_tone="error" if failed else "success",
        ),
    ]

    return ReportsDashboardPageRead(
        page_title="Reports Dashboard",
        page_subtitle="Institution-wide reporting hub",
        create_report_label="Create report",
        create_report_href="/college-admin/reports/custom-report-builder",
        reports_section_title="Reports",
        groups_section_title="Report groups",
        table_headers=_TABLE_HEADERS,
        report_rows=rows,
        group_rows=groups,
        empty_table_message="No reports available for your role.",
        empty_groups_message="No report groups to show.",
        showing_label=showing_label,
        kpis=kpis,
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