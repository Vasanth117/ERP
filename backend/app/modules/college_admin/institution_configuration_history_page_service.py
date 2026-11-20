"""Campus / institution configuration history dashboard (CA 02.x)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.college_admin.enums import InstitutionActivityKind
from app.modules.college_admin.models import InstitutionActivityLog, InstitutionConfigurationVersion
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ConfigurationAreaSummary,
    ConfigurationChangeDetail,
    ConfigurationChangeRow,
    ConfigurationHistoryFilterOption,
    ConfigurationHistoryPageRead,
    PoliciesPagination,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 7

_AREA_LABELS: dict[str, str] = {
    "institution_information": "Institution information",
    "academic_rules": "Academic rules",
    "branding": "Branding",
    "calendar": "Calendar",
    "campus_contacts": "Campus & contacts",
    "general": "General",
}

_SCOPE_TO_AREA: dict[str, str] = {
    "institution_profile": "institution_information",
    "institution_settings": "institution_information",
    "institution_information": "institution_information",
    "institution_branding": "branding",
    "institution_academic_defaults": "academic_rules",
    "institution_calendar_settings": "calendar",
    "campus": "campus_contacts",
    "campus_contact": "campus_contacts",
}

_AUDIT_ACTION_AREA: dict[str, str] = {
    "institution.settings.updated": "institution_information",
    "institution.academic_settings.updated": "academic_rules",
    "institution.academic_settings.reset": "academic_rules",
    "institution.calendar_settings.updated": "calendar",
    "institution.calendar_holidays.imported": "calendar",
}

_ACTIVITY_AREA: dict[InstitutionActivityKind, str] = {
    InstitutionActivityKind.PROFILE_UPDATED: "institution_information",
    InstitutionActivityKind.SETTINGS_UPDATED: "institution_information",
    InstitutionActivityKind.BRANDING_UPDATED: "branding",
    InstitutionActivityKind.CAMPUS_CREATED: "campus_contacts",
    InstitutionActivityKind.CAMPUS_UPDATED: "campus_contacts",
}

_DATE_RANGE_OPTIONS: list[tuple[str, str, int | None]] = [
    ("last_90_days", "Last 90 days", 90),
    ("last_30_days", "Last 30 days", 30),
    ("last_7_days", "Last 7 days", 7),
    ("all_time", "All time", None),
]


@dataclass
class _UnifiedChange:
    change_id: str
    created_at: datetime
    actor_id: PydanticObjectId | None
    area_key: str
    setting_label: str
    change_summary: str
    status_code: str
    status_label: str
    status_tone: str
    detail_setting_line: str | None = None
    previous_value: str | None = None
    new_value: str | None = None
    approved_by_label: str | None = None
    ip_line: str | None = None
    open_href: str | None = None


def _status_tone(code: str) -> str:
    if code == "applied":
        return "success"
    if code == "rejected":
        return "error"
    if code == "draft":
        return "warning"
    return "muted"


def _format_when(created_at: datetime) -> str:
    local = as_utc_aware(created_at).astimezone(_IST)
    return local.strftime("%d %b • %H:%M")


def _area_key(scope_or_type: str) -> str:
    return _SCOPE_TO_AREA.get(scope_or_type, "general")


def _human_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _stringify(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def _summarize_key_change(key: str, new_val: object, old_val: object | None) -> str:
    label = _human_key(key)
    new_s = _stringify(new_val)
    if key in {"official_website", "website"} and new_s != "—":
        return f"Website updated to {new_s}"
    if old_val is not None and _stringify(old_val) != new_s:
        return f"{label} updated"
    if new_s != "—":
        return f"{label} set to {new_s}"
    return f"{label} updated"


async def _actor_label(actor_id: PydanticObjectId | None, cache: dict[str, str]) -> str:
    if actor_id is None:
        return "System"
    key = str(actor_id)
    if key in cache:
        return cache[key]
    user = await User.get(actor_id)
    label = user.full_name if user and user.full_name else key
    cache[key] = label
    return label


def _area_open_href(area_key: str) -> str | None:
    routes = {
        "institution_information": "/college-admin/institution/information",
        "academic_rules": "/college-admin/institution/academic-settings",
        "branding": "/college-admin/institution/branding",
        "calendar": "/college-admin/institution/calendar",
        "campus_contacts": "/college-admin/institution/campuses",
    }
    return routes.get(area_key)


async def _collect_changes(tenant_id: PydanticObjectId) -> list[_UnifiedChange]:
    changes: list[_UnifiedChange] = []

    versions = (
        await InstitutionConfigurationVersion.find(Eq(InstitutionConfigurationVersion.tenant_id, tenant_id))
        .sort("-created_at")
        .to_list()
    )
    version_index: dict[tuple[str, int], InstitutionConfigurationVersion] = {
        (row.scope, row.version_number): row for row in versions
    }

    for row in versions:
        area = _area_key(row.scope)
        area_label = _AREA_LABELS.get(area, _human_key(area))
        primary_key = row.changed_keys[0] if row.changed_keys else row.scope
        prev_doc = version_index.get((row.scope, row.version_number - 1))
        old_val: object | None = None
        new_val: object | None = None
        if prev_doc and primary_key:
            old_val = prev_doc.snapshot.get(primary_key)
            new_val = row.snapshot.get(primary_key)
        elif primary_key:
            new_val = row.snapshot.get(primary_key)
        summary = (
            _summarize_key_change(primary_key, new_val, old_val)
            if primary_key
            else f"{area_label} configuration updated"
        )
        status_code = "draft" if "draft" in row.scope.lower() else "applied"
        changes.append(
            _UnifiedChange(
                change_id=f"ver-{row.id}",
                created_at=row.created_at,
                actor_id=row.created_by,
                area_key=area,
                setting_label=area_label,
                change_summary=summary,
                status_code=status_code,
                status_label=status_code.title(),
                status_tone=_status_tone(status_code),
                detail_setting_line=f"{area_label} • {_human_key(primary_key)}" if primary_key else area_label,
                previous_value=_stringify(old_val) if old_val is not None else None,
                new_value=_stringify(new_val) if new_val is not None else None,
                approved_by_label="Auto-approved (configuration snapshot)" if status_code == "applied" else None,
                open_href=_area_open_href(area),
            )
        )

    activities = (
        await InstitutionActivityLog.find(Eq(InstitutionActivityLog.tenant_id, tenant_id))
        .sort("-created_at")
        .to_list()
    )
    for row in activities:
        if row.activity_kind == InstitutionActivityKind.DASHBOARD_VIEW:
            continue
        area = _ACTIVITY_AREA.get(row.activity_kind, "general")
        area_label = _AREA_LABELS.get(area, _human_key(area))
        meta = row.metadata or {}
        status_code = str(meta.get("status", "applied")).lower()
        if status_code not in {"applied", "rejected", "draft"}:
            status_code = "applied"
        changes.append(
            _UnifiedChange(
                change_id=f"act-{row.id}",
                created_at=row.created_at,
                actor_id=row.actor_id,
                area_key=area,
                setting_label=area_label,
                change_summary=row.summary,
                status_code=status_code,
                status_label=status_code.title(),
                status_tone=_status_tone(status_code),
                detail_setting_line=area_label,
                approved_by_label=meta.get("approved_by"),
                ip_line=meta.get("ip_line"),
                open_href=_area_open_href(area),
            )
        )

    audits = (
        await AuditLog.find(Eq(AuditLog.tenant_id, tenant_id))
        .sort("-created_at")
        .to_list()
    )
    for row in audits:
        if not row.action.startswith("institution."):
            continue
        area = _AUDIT_ACTION_AREA.get(row.action, "general")
        area_label = _AREA_LABELS.get(area, _human_key(area))
        status_code = "applied" if row.outcome == "success" else "rejected"
        summary = row.action.replace("institution.", "").replace("_", " ").replace(".", " · ").title()
        meta = row.metadata or {}
        ip = meta.get("ip_address")
        ip_line = f"{ip} · {meta.get('location', '—')}" if ip else meta.get("ip_line")
        changes.append(
            _UnifiedChange(
                change_id=f"aud-{row.id}",
                created_at=row.created_at,
                actor_id=row.actor_id,
                area_key=area,
                setting_label=area_label,
                change_summary=summary,
                status_code=status_code,
                status_label=status_code.title(),
                status_tone=_status_tone(status_code),
                detail_setting_line=area_label,
                approved_by_label=meta.get("approved_by"),
                ip_line=ip_line,
                open_href=_area_open_href(area),
            )
        )

    changes.sort(key=lambda item: item.created_at, reverse=True)
    return changes


def _apply_filters(
    rows: list[_UnifiedChange],
    *,
    date_range: str,
    setting_area: str | None,
    actor_id: str | None,
    search: str | None,
) -> list[_UnifiedChange]:
    days = next((d for key, _, d in _DATE_RANGE_OPTIONS if key == date_range), 90)
    cutoff: datetime | None = None
    if days is not None:
        cutoff = utcnow() - timedelta(days=days)

    filtered: list[_UnifiedChange] = []
    needle = (search or "").strip().lower()
    for row in rows:
        if cutoff and as_utc_aware(row.created_at) < cutoff:
            continue
        if setting_area and row.area_key != setting_area:
            continue
        if actor_id and (row.actor_id is None or str(row.actor_id) != actor_id):
            continue
        if needle:
            hay = f"{row.change_summary} {row.setting_label}".lower()
            if needle not in hay:
                continue
        filtered.append(row)
    return filtered


async def get_institution_configuration_history_page(
    scope: AccessScope,
    *,
    page: int = 1,
    date_range: str = "last_90_days",
    setting_area: str | None = None,
    actor_id: str | None = None,
    search: str | None = None,
    selected_change_id: str | None = None,
) -> ConfigurationHistoryPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_READ)
    tenant_id = require_college_tenant_scope(scope)

    all_rows = await _collect_changes(tenant_id)
    filtered = _apply_filters(
        all_rows,
        date_range=date_range,
        setting_area=setting_area or None,
        actor_id=actor_id or None,
        search=search,
    )

    actor_cache: dict[str, str] = {}
    actor_ids = {str(r.actor_id) for r in filtered if r.actor_id}
    user_options: list[ConfigurationHistoryFilterOption] = [
        ConfigurationHistoryFilterOption(value="", label="All users"),
    ]
    for aid in sorted(actor_ids):
        user_options.append(
            ConfigurationHistoryFilterOption(value=aid, label=await _actor_label(PydanticObjectId(aid), actor_cache))
        )

    area_counts: dict[str, int] = {}
    for row in filtered:
        area_counts[row.area_key] = area_counts.get(row.area_key, 0) + 1
    max_area = max(area_counts.values()) if area_counts else 0
    area_summaries = [
        ConfigurationAreaSummary(
            area_key=key,
            title=_AREA_LABELS.get(key, _human_key(key)),
            count=count,
            progress_percent=round((count / max_area) * 100) if max_area else 0,
        )
        for key, count in sorted(area_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    total = len(filtered)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = filtered[start : start + _PAGE_SIZE]

    table_rows: list[ConfigurationChangeRow] = []
    for row in page_slice:
        table_rows.append(
            ConfigurationChangeRow(
                change_id=row.change_id,
                change_summary=row.change_summary,
                setting_label=row.setting_label,
                changed_by_label=await _actor_label(row.actor_id, actor_cache),
                when_label=_format_when(row.created_at),
                status_code=row.status_code,
                status_label=row.status_label,
                status_tone=row.status_tone,
            )
        )

    selected: ConfigurationChangeDetail | None = None
    selected_row = None
    if selected_change_id:
        selected_row = next((r for r in filtered if r.change_id == selected_change_id), None)
    if selected_row is None and filtered:
        selected_row = filtered[0]
    if selected_row:
        selected = ConfigurationChangeDetail(
            change_id=selected_row.change_id,
            setting_line=selected_row.detail_setting_line or selected_row.setting_label,
            previous_value=selected_row.previous_value,
            new_value=selected_row.new_value,
            approved_by_label=selected_row.approved_by_label,
            ip_line=selected_row.ip_line,
            open_href=selected_row.open_href or "/college-admin/institution/configuration-history",
            open_label="Open",
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    setting_options = [
        ConfigurationHistoryFilterOption(value="", label="All settings"),
    ] + [
        ConfigurationHistoryFilterOption(value=key, label=label)
        for key, label in sorted(_AREA_LABELS.items(), key=lambda item: item[1])
    ]

    return ConfigurationHistoryPageRead(
        page_title="Campus Configuration History",
        page_subtitle="Every change made to institution, campus and academic settings",
        export_label="Export log",
        date_range_filter_label="Date range",
        setting_filter_label="Settings",
        user_filter_label="Users",
        scope_indicator_label="College scope",
        updated_at_label=_format_when(utcnow()),
        date_range_options=[
            ConfigurationHistoryFilterOption(value=key, label=label) for key, label, _ in _DATE_RANGE_OPTIONS
        ],
        setting_options=setting_options,
        user_options=user_options,
        change_log_title="Change log",
        table_headers=["Change", "Setting", "Changed by", "When", "Status"],
        changes=table_rows,
        showing_label=f"Showing {len(table_rows)} of {total} change{'s' if total != 1 else ''}",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        selected_change=selected,
        change_details_title="Change details",
        changes_by_area_title="Changes by area",
        changes_by_area=area_summaries,
        footer_disclaimer=(
            "Live configuration and audit records · Merged from snapshots, activity and audit logs · All times IST"
        ),
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )