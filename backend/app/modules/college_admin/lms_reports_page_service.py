"""LMS reports listing page (CA 15.11)."""

from __future__ import annotations

import math
import uuid
from calendar import month_name
from datetime import date
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.lms_admin_models import LmsScheduledReport, LmsScheduledReportFrequency
from app.modules.college_admin.lms_reports_catalog import (
    catalog_item,
    catalog_items,
    default_frequency_for,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionFieldOption,
    LmsReportScheduleCreate,
    LmsReportsPageRead,
    LmsReportsTableRow,
    PoliciesPagination,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"]
_FORMAT_LABELS = {"csv": "CSV", "excel": "Excel", "pdf": "PDF", "xlsx": "Excel"}


def _format_label(formats: list[str] | tuple[str, ...]) -> str:
    labels: list[str] = []
    for fmt in formats:
        key = (fmt or "").lower()
        label = _FORMAT_LABELS.get(key, key.upper())
        if label not in labels:
            labels.append(label)
    return ", ".join(labels) if labels else "—"


def _short_day(value: date) -> str:
    return value.strftime("%d %b")


def _frequency_label(freq: LmsScheduledReportFrequency) -> str:
    if freq == LmsScheduledReportFrequency.WEEKLY:
        return "Weekly"
    if freq == LmsScheduledReportFrequency.QUARTERLY:
        return "Quarterly"
    return "Monthly"


def _period_label(report_key: str, filters: dict | None, today: date) -> str:
    if filters and filters.get("period_label"):
        return str(filters["period_label"])
    if report_key == "content_usage":
        month = today.month - 1 or 12
        year = today.year if today.month > 1 else today.year - 1
        return f"{month_name[month][:3]} {year}"
    return f"{month_name[today.month][:3]} {today.year}"


async def _schedule_by_key(tenant_id) -> dict[str, LmsScheduledReport]:
    schedules = await LmsScheduledReport.find(
        Eq(LmsScheduledReport.tenant_id, tenant_id),
        Eq(LmsScheduledReport.is_active, True),
    ).to_list()
    return {s.report_key: s for s in schedules}


async def create_lms_report_schedule(
    scope: AccessScope,
    payload: LmsReportScheduleCreate,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LmsReportsPageRead:
    authorize(scope, Permission.LMS_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    report_key = payload.report_key.strip().lower()
    item = catalog_item(report_key)
    if item is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown report type", status_code=422)
    existing = await LmsScheduledReport.find_one(
        Eq(LmsScheduledReport.tenant_id, tenant_id),
        Eq(LmsScheduledReport.report_key, report_key),
        Eq(LmsScheduledReport.is_active, True),
    )
    if existing:
        raise AppError(code="CONFLICT", message="This report is already scheduled", status_code=409)

    schedule_code = f"lms_{report_key}_{uuid.uuid4().hex[:8]}"
    await LmsScheduledReport(
        tenant_id=tenant_id,
        schedule_code=schedule_code,
        report_key=report_key,
        title=item.title,
        export_formats=list(item.export_formats),
        frequency=default_frequency_for(item),
        filters={},
        actor_id=scope.user_id,
    ).insert()
    return await get_lms_reports_page(scope, page=page, page_size=page_size)


async def get_lms_reports_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LmsReportsPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    catalog = catalog_items()
    total = len(catalog)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    page_catalog = catalog[offset : offset + page_size]
    schedules = await _schedule_by_key(tenant_id)

    table_rows: list[LmsReportsTableRow] = []
    for item in page_catalog:
        schedule = schedules.get(item.report_key)
        formats = schedule.export_formats if schedule and schedule.export_formats else item.export_formats
        period = _period_label(item.report_key, schedule.filters if schedule else None, today)
        last_run = "—"
        if schedule and schedule.last_run_at:
            last_run = _short_day(as_utc_aware(schedule.last_run_at).astimezone(_IST).date())
        schedule_label = (
            _frequency_label(schedule.frequency) if schedule else item.schedule_label
        )
        table_rows.append(
            LmsReportsTableRow(
                report_key=item.report_key,
                report_label=item.title,
                period_label=period,
                format_label=_format_label(formats),
                last_run_label=last_run,
                schedule_label=schedule_label,
                detail_href=f"/college-admin/lms/lms-reports?report_key={item.report_key}",
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(table_rows))
    showing_label = f"{showing_end} of {total:,}" if total else "0 of 0"

    templates = [InstitutionFieldOption(value=item.report_key, label=item.title) for item in catalog]
    unscheduled = [
        InstitutionFieldOption(value=item.report_key, label=item.title)
        for item in catalog
        if item.report_key not in schedules
    ]

    return LmsReportsPageRead(
        page_title="LMS Reports",
        page_subtitle="Usage and completion reports",
        create_report_label="Create report",
        reports_section_title="Reports",
        table_headers=_TABLE_HEADERS,
        report_rows=table_rows,
        create_report_templates=unscheduled or templates,
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