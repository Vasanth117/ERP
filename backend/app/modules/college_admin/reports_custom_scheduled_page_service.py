"""Custom & scheduled reports pages (CA 16)."""

from __future__ import annotations

import json
import math
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.reports_custom_builder_catalog import builder_sources
from app.modules.college_admin.reports_academic_page_service import _academic_year_label
from app.modules.college_admin.reports_admin_models import (
    InstitutionAnalyticsSnapshot,
    InstitutionReportDefinition,
    InstitutionReportExport,
    InstitutionReportFilter,
    InstitutionReportJob,
)
from app.modules.college_admin.reports_admin_schemas import ReportFilterCreate
from app.modules.college_admin.reports_admin_service import (
    _ensure_definitions,
    _permission_allowed,
    list_report_definitions,
    save_report_filter,
)
from app.modules.college_admin.reports_custom_builder_catalog import (
    default_source_key,
    source_config,
)
from app.modules.college_admin.schemas import (
    InstitutionFieldOption,
    PoliciesPagination,
    ReportsCustomBuilderPageRead,
    ReportsCustomBuilderPreviewRow,
    ReportsCustomBuilderSave,
    ReportsCustomBuilderStep,
    ReportsExportHistoryPageRead,
    ReportsExportHistoryTableRow,
    ReportsScheduledPageRead,
    ReportsScheduledTableRow,
)

_IST = ZoneInfo("Asia/Kolkata")
_SCHEDULED_PAGE_SIZE = 4
_EXPORT_PAGE_SIZE = 3
_FORMAT_LABELS = {"json": "JSON", "csv": "CSV", "excel": "Excel", "xlsx": "Excel", "pdf": "PDF"}


def _fmt_format(fmt: str) -> str:
    return _FORMAT_LABELS.get((fmt or "").lower(), (fmt or "—").upper())


def _fmt_frequency(job: InstitutionReportJob) -> str:
    if job.schedule_frequency_label:
        return job.schedule_frequency_label
    cron = (job.schedule_cron or "").lower()
    if "0 0 * * 0" in cron or "weekly" in cron:
        return "Weekly"
    if "* * *" in cron or "daily" in cron:
        return "Daily"
    if "month" in cron or "28" in cron:
        return "Monthly"
    return "Scheduled"


def _fmt_next_run(dt) -> str:
    if dt is None:
        return "—"
    local = as_utc_aware(dt).astimezone(_IST)
    return local.strftime("%d %b %H:%M")


def _fmt_day(dt) -> str:
    if dt is None:
        return "—"
    return as_utc_aware(dt).astimezone(_IST).strftime("%d %b")


def _export_file_label(report_key: str, export_id: str, fmt: str) -> str:
    ext = {"excel": "xlsx", "xlsx": "xlsx", "pdf": "pdf", "csv": "csv", "json": "json"}.get(fmt.lower(), fmt.lower())
    slug = report_key.replace("_", "-")
    return f"{slug}-{export_id[-6:]}.{ext}"


def _human_size(byte_count: int | None) -> str:
    if not byte_count or byte_count <= 0:
        return "—"
    if byte_count >= 1_000_000:
        return f"{byte_count / 1_000_000:.1f} MB"
    if byte_count >= 1_000:
        return f"{byte_count / 1_000:.0f} KB"
    return f"{byte_count} B"


async def _definition_titles(tenant_id: PydanticObjectId) -> dict[str, str]:
    await _ensure_definitions(tenant_id)
    rows = await InstitutionReportDefinition.find(Eq(InstitutionReportDefinition.tenant_id, tenant_id)).to_list()
    return {r.report_key: r.title for r in rows}


async def _user_labels(tenant_id: PydanticObjectId, user_ids: set[PydanticObjectId]) -> dict[PydanticObjectId, str]:
    if not user_ids:
        return {}
    users = await User.find(In(User.id, list(user_ids))).to_list()
    labels: dict[PydanticObjectId, str] = {}
    for u in users:
        name = (u.full_name or u.email or "User").strip()
        labels[u.id] = name if u.tenant_id == tenant_id or True else name
    return labels


async def get_reports_scheduled_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _SCHEDULED_PAGE_SIZE,
) -> ReportsScheduledPageRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    titles = await _definition_titles(tenant_id)

    all_jobs = await InstitutionReportJob.find(
        Eq(InstitutionReportJob.tenant_id, tenant_id),
    ).sort("-created_at").to_list()
    scheduled = [j for j in all_jobs if j.schedule_cron]

    total = len(scheduled)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    start = (page - 1) * page_size
    visible = scheduled[start : start + page_size]

    table_rows: list[ReportsScheduledTableRow] = []
    for job in visible:
        title = titles.get(job.report_key, job.report_key.replace("_", " ").title())
        recipients = ", ".join(job.schedule_recipients) if job.schedule_recipients else "—"
        paused = bool(job.schedule_paused)
        table_rows.append(
            ReportsScheduledTableRow(
                row_key=job.job_id,
                report_label=title,
                frequency_label=_fmt_frequency(job),
                next_run_label=_fmt_next_run(job.next_run_at),
                recipients_label=recipients,
                format_label=_fmt_format(job.schedule_format),
                status_label="Paused" if paused else "Active",
                status_tone="warning" if paused else "success",
            )
        )

    definitions = await list_report_definitions(scope)
    report_options = [
        InstitutionFieldOption(value=d.report_key, label=d.title)
        for d in definitions
        if d.supports_schedule and _permission_allowed(scope, d.required_permission)
    ]

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, start + len(table_rows))

    return ReportsScheduledPageRead(
        page_title="Scheduled Reports",
        page_subtitle="Recurring report deliveries",
        schedule_action_label="Schedule report",
        schedules_section_title="Schedules",
        table_headers=["Report", "Frequency", "Next run", "Recipients", "Format", "Status"],
        schedule_rows=table_rows,
        empty_table_message="No scheduled reports yet.",
        showing_label=f"{showing_end} of {total}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        report_options=report_options,
        generated_at=now,
    )


async def get_reports_export_history_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _EXPORT_PAGE_SIZE,
) -> ReportsExportHistoryPageRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    total = await InstitutionReportExport.find(Eq(InstitutionReportExport.tenant_id, tenant_id)).count()
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    start = (page - 1) * page_size
    exports = await InstitutionReportExport.find(
        Eq(InstitutionReportExport.tenant_id, tenant_id),
    ).sort("-created_at").skip(start).limit(page_size).to_list()

    job_ids = {e.job_id for e in exports}
    jobs = await InstitutionReportJob.find(
        Eq(InstitutionReportJob.tenant_id, tenant_id),
        In(InstitutionReportJob.job_id, list(job_ids)),
    ).to_list() if job_ids else []
    job_by_id = {j.job_id: j for j in jobs}
    actor_ids = {e.actor_id for e in exports if e.actor_id}
    user_labels = await _user_labels(tenant_id, actor_ids)

    snapshot_ids = {j.snapshot_id for j in jobs if j.snapshot_id}
    snapshots = await InstitutionAnalyticsSnapshot.find(
        Eq(InstitutionAnalyticsSnapshot.tenant_id, tenant_id),
        In(InstitutionAnalyticsSnapshot.snapshot_id, list(snapshot_ids)),
    ).to_list() if snapshot_ids else []
    snap_by_id = {s.snapshot_id: s for s in snapshots}

    rows: list[ReportsExportHistoryTableRow] = []
    for export in exports:
        job = job_by_id.get(export.job_id)
        report_key = job.report_key if job else "report"
        size_bytes = None
        if job and job.snapshot_id and job.snapshot_id in snap_by_id:
            size_bytes = len(json.dumps(snap_by_id[job.snapshot_id].metrics, default=str))
        expired = export.expires_at is not None and export.expires_at < now
        rows.append(
            ReportsExportHistoryTableRow(
                row_key=export.export_id,
                file_label=_export_file_label(report_key, export.export_id, export.format),
                requested_by_label=user_labels.get(export.actor_id, "College Admin") if export.actor_id else "College Admin",
                format_label=_fmt_format(export.format),
                size_label=_human_size(size_bytes),
                date_label=_fmt_day(export.created_at),
                status_label="Expired" if expired else "Ready",
                status_tone="warning" if expired else "success",
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, start + len(rows))

    return ReportsExportHistoryPageRead(
        page_title="Export & Download History",
        page_subtitle="Exports generated by users",
        export_log_label="Export log",
        exports_section_title="Exports",
        table_headers=["File", "Requested by", "Format", "Size", "Date", "Status"],
        export_rows=rows,
        empty_table_message="No exports yet.",
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
        generated_at=now,
    )


_BUILDER_STEPS = (
    ("data", "Choose data", 1),
    ("fields", "Select fields", 2),
    ("filters", "Filters", 3),
    ("layout", "Layout", 4),
    ("run", "Run and save", 5),
)


async def _load_builder_filter(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    filter_id: str | None,
) -> InstitutionReportFilter | None:
    if filter_id:
        return await InstitutionReportFilter.find_one(
            Eq(InstitutionReportFilter.tenant_id, tenant_id),
            Eq(InstitutionReportFilter.filter_id, filter_id),
        )
    rows = await InstitutionReportFilter.find(
        Eq(InstitutionReportFilter.tenant_id, tenant_id),
        Eq(InstitutionReportFilter.owner_id, user_id),
    ).sort("-created_at").limit(1).to_list()
    return rows[0] if rows else None


async def get_reports_custom_builder_page(
    scope: AccessScope,
    user: User,
    *,
    data_source: str | None = None,
    filter_id: str | None = None,
    active_step_key: str | None = None,
) -> ReportsCustomBuilderPageRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    ay_label = await _academic_year_label(tenant_id, None)

    source_key = data_source or default_source_key()
    meta = source_config(source_key) or source_config(default_source_key())
    if meta is None:
        source_key = default_source_key()
        meta = source_config(source_key) or {}

    filt = await _load_builder_filter(tenant_id, user.id, filter_id)
    params = filt.parameters if filt and filt.parameters else {}
    if params.get("builder_source"):
        source_key = str(params["builder_source"])
        meta = source_config(source_key) or meta

    selected_fields = list(params.get("selected_fields") or [f[0] for f in meta.get("fields", ())[:5]])
    selected_group = str(params.get("group_by") or (meta.get("group_by") or (("", ""),))[0][0])
    selected_sort = str(params.get("sort_by") or (meta.get("sort_by") or (("", ""),))[0][0])
    selected_format = str(params.get("export_format") or "excel")
    selected_ay = str(params.get("academic_year") or ay_label)
    report_key = meta.get("report_key", "enrollment")
    fid = filt.filter_id if filt else f"builder_{user.id}"

    active_step = active_step_key or "filters"
    active_num = next((n for k, _, n in _BUILDER_STEPS if k == active_step), 3)
    steps: list[ReportsCustomBuilderStep] = []
    for key, label, number in _BUILDER_STEPS:
        if number < active_num:
            status = "done"
        elif number == active_num:
            status = "active"
        else:
            status = "pending"
        steps.append(ReportsCustomBuilderStep(step_key=key, step_label=label, step_number=number, status=status))

    from app.modules.students.models import StudentProfile

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).limit(3).to_list()
    user_ids = {p.user_id for p in profiles}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() for u in users}

    preview_rows: list[ReportsCustomBuilderPreviewRow] = []
    for profile in profiles:
        preview_rows.append(
            ReportsCustomBuilderPreviewRow(
                row_key=str(profile.user_id),
                name_label=user_names.get(profile.user_id, "—"),
                programme_label=profile.programme_code or profile.programme_name or "—",
                attendance_label="—",
            )
        )

    field_opts = [InstitutionFieldOption(value=k, label=lbl) for k, lbl in meta.get("fields", ())]
    group_opts = [InstitutionFieldOption(value=k, label=lbl) for k, lbl in meta.get("group_by", ())]
    sort_opts = [InstitutionFieldOption(value=k, label=lbl) for k, lbl in meta.get("sort_by", ())]

    return ReportsCustomBuilderPageRead(
        page_title="Custom Report Builder",
        page_subtitle="Pick data, filters and layout",
        save_template_label="Save template",
        run_label="Run",
        steps=steps,
        data_source_label="Data source",
        data_source_options=[InstitutionFieldOption(value=s.source_key, label=s.label) for s in builder_sources()],
        selected_data_source=source_key,
        fields_label="Fields",
        field_options=field_opts,
        selected_fields=selected_fields,
        group_by_label="Group by",
        group_by_options=group_opts,
        selected_group_by=selected_group,
        sort_by_label="Sort by",
        sort_by_options=sort_opts,
        selected_sort_by=selected_sort,
        date_range_label="Date range",
        date_range_options=[InstitutionFieldOption(value=selected_ay, label=f"AY {selected_ay}")],
        selected_date_range=selected_ay,
        format_label="Format",
        format_options=[
            InstitutionFieldOption(value="excel", label="Excel"),
            InstitutionFieldOption(value="pdf", label="PDF"),
            InstitutionFieldOption(value="csv", label="CSV"),
        ],
        selected_format=selected_format,
        preview_section_title="Preview",
        preview_headers=["Name", "Programme", "Att. %"],
        preview_rows=preview_rows,
        empty_preview_message="No preview rows for the current filters.",
        filter_id=fid,
        report_key=report_key,
        generated_at=now,
    )


async def save_reports_custom_builder(
    scope: AccessScope,
    user: User,
    payload: ReportsCustomBuilderSave,
) -> ReportsCustomBuilderPageRead:
    meta = source_config(payload.data_source) or source_config(default_source_key()) or {}
    report_key = meta.get("report_key", "enrollment")
    await save_report_filter(
        scope,
        user,
        ReportFilterCreate(
            filter_id=payload.filter_id,
            report_key=report_key,
            academic_year_label=payload.academic_year,
            parameters={
                "builder_source": payload.data_source,
                "selected_fields": payload.selected_fields,
                "group_by": payload.group_by,
                "sort_by": payload.sort_by,
                "export_format": payload.export_format,
                "academic_year": payload.academic_year,
            },
        ),
    )
    return await get_reports_custom_builder_page(
        scope,
        user,
        data_source=payload.data_source,
        filter_id=payload.filter_id,
        active_step_key="filters",
    )