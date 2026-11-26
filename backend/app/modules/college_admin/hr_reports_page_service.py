"""HR reports catalogue page (CA 11.13)."""

from __future__ import annotations

import math
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.hr_reports_settings_shared import HR_REPORTS_SETTINGS_SUB_NAV
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrReportScheduleCreate,
    HrReportTableRow,
    HrReportsPageRead,
    InstitutionFieldOption,
    PoliciesPagination,
)
from app.modules.hr.enums import HrReportExportFormat, HrScheduledReportFrequency
from app.modules.hr.hr_reports_catalog import catalog_for_scope, catalog_item
from app.modules.hr.hr_reports_models import HrReportExecutionHistory, HrScheduledReport
from app.modules.hr.hr_reports_schemas import ScheduledReportUpsert
from app.modules.hr.hr_reports_service import schedule_report

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"]


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _fmt_last_run(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return as_utc_aware(dt).astimezone(_IST).strftime("%d %b")


def _frequency_label(freq: HrScheduledReportFrequency) -> str:
    return freq.value.replace("_", " ").title()


def _format_labels(export: HrReportExportFormat, catalog_formats: tuple[str, ...]) -> str:
    labels: list[str] = []
    mapping = {"csv": "CSV", "xlsx": "Excel", "pdf": "PDF"}
    primary = mapping.get(export.value, export.value.upper())
    if primary not in labels:
        labels.append(primary)
    for fmt in catalog_formats:
        label = mapping.get(fmt, fmt.upper())
        if label not in labels:
            labels.append(label)
    return ", ".join(labels)


async def _period_label(
    tenant_id,
    *,
    filters: dict,
    frequency: HrScheduledReportFrequency,
) -> str:
    if filters.get("period_label"):
        return str(filters["period_label"])
    now = utcnow().astimezone(_IST)
    if frequency == HrScheduledReportFrequency.QUARTERLY:
        years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
        current = next((y for y in years if y.is_current), years[0] if years else None)
        if current and current.label:
            return f"FY {current.label.replace('-', '–')}"
        y = now.year
        if now.month >= 4:
            return f"FY {y}–{(y + 1) % 100:02d}"
        return f"FY {y - 1}–{y % 100:02d}"
    if frequency == HrScheduledReportFrequency.MONTHLY:
        return now.strftime("%b %Y")
    if frequency == HrScheduledReportFrequency.WEEKLY:
        return f"Week of {now.strftime('%d %b %Y')}"
    if frequency == HrScheduledReportFrequency.DAILY:
        return now.strftime("%d %b %Y")
    return now.strftime("%b %Y")


async def _build_rows(tenant_id) -> list[HrReportTableRow]:
    schedules = await HrScheduledReport.find(
        Eq(HrScheduledReport.tenant_id, tenant_id),
        Eq(HrScheduledReport.is_active, True),
    ).sort("-updated_at").to_list()

    rows: list[HrReportTableRow] = []
    for schedule in schedules:
        catalog = catalog_item(schedule.report_key)
        title = catalog.title if catalog else schedule.report_key.replace("_", " ").title()
        catalog_formats = catalog.supported_formats if catalog else ("csv",)
        period = await _period_label(tenant_id, filters=schedule.filters, frequency=schedule.frequency)
        last_run = schedule.last_run_at
        if last_run is None:
            latest = await HrReportExecutionHistory.find(
                Eq(HrReportExecutionHistory.tenant_id, tenant_id),
                Eq(HrReportExecutionHistory.report_key, schedule.report_key),
            ).sort("-created_at").first_or_none()
            if latest:
                last_run = latest.completed_at or latest.created_at
        rows.append(
            HrReportTableRow(
                row_id=str(schedule.id),
                report_key=schedule.report_key,
                report_label=title,
                period_label=period,
                format_label=_format_labels(schedule.export_format, catalog_formats),
                last_run_label=_fmt_last_run(last_run),
                schedule_label=_frequency_label(schedule.frequency),
                detail_href=f"/college-admin/hr/hr-summary-report?report_key={schedule.report_key}",
            )
        )
    return rows


async def get_hr_reports_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HrReportsPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    all_rows = await _build_rows(tenant_id)
    total = len(all_rows)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    page_rows = all_rows[start : start + page_size]

    catalog_items = catalog_for_scope(scope.effective_permissions)
    templates = [
        InstitutionFieldOption(value=item.report_key, label=item.title)
        for item in catalog_items
    ]

    showing = f"{len(page_rows)} of {total:,}" if total else "0 of 0"
    pagination = PoliciesPagination(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        page_numbers=_page_numbers(page, total_pages),
        has_previous=page > 1,
        has_next=page < total_pages,
    )

    return HrReportsPageRead(
        page_title="HR Reports",
        page_subtitle="Standard HR reports",
        create_report_label="Create report",
        sub_nav=HR_REPORTS_SETTINGS_SUB_NAV,
        reports_section_title="Reports",
        table_headers=_TABLE_HEADERS,
        report_rows=page_rows,
        create_report_templates=templates,
        showing_label=showing,
        pagination=pagination,
        footer_disclaimer="Scheduled runs use tenant data only; exports respect HR field permissions.",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )


async def create_hr_report_schedule(scope: AccessScope, payload: HrReportScheduleCreate) -> HrReportsPageRead:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    report_key = payload.report_key.strip()
    if catalog_item(report_key) is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown report type", status_code=422)
    existing = await HrScheduledReport.find_one(
        Eq(HrScheduledReport.tenant_id, tenant_id),
        Eq(HrScheduledReport.report_key, report_key),
        Eq(HrScheduledReport.is_active, True),
    )
    if existing:
        raise AppError(code="CONFLICT", message="This report is already scheduled", status_code=409)

    schedule_code = f"hr_{report_key}_{uuid.uuid4().hex[:8]}"
    await schedule_report(
        scope,
        ScheduledReportUpsert(
            schedule_code=schedule_code,
            report_key=report_key,
            frequency=HrScheduledReportFrequency.MONTHLY,
            export_format=HrReportExportFormat.CSV,
            filters={},
        ),
    )
    return await get_hr_reports_page(scope, page=1, page_size=_PAGE_SIZE)