"""Academic configuration history dashboard (CA — college admin academics)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicConfigurationVersion
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
    "curriculum_courses": "Curriculum & courses",
    "calendar": "Calendar",
    "batches_sections": "Batches & sections",
    "grading_credits": "Grading & credits",
    "years_programmes": "Years & programmes",
    "programmes": "Programmes",
    "courses": "Courses",
    "general": "General",
}

_AREA_TABLE_LABELS: dict[str, str] = {
    "curriculum_courses": "Curriculum",
    "calendar": "Calendar",
    "batches_sections": "Batches",
    "grading_credits": "Grading",
    "years_programmes": "Academic year",
    "programmes": "Programmes",
    "courses": "Courses",
    "general": "General",
}

_SCOPE_TO_AREA: dict[str, str] = {
    "academic_calendar": "calendar",
    "academic_year": "years_programmes",
    "academic_term": "years_programmes",
    "programme": "programmes",
    "course": "courses",
    "curriculum": "curriculum_courses",
    "grading": "grading_credits",
    "credit": "grading_credits",
    "regulation_grading": "grading_credits",
    "regulation_attendance": "grading_credits",
    "regulation_progression": "grading_credits",
    "regulation_examination": "grading_credits",
    "regulation_registration": "grading_credits",
    "batch_section_allocation": "batches_sections",
}

_DATE_RANGE_OPTIONS: list[tuple[str, str, int | None]] = [
    ("last_6_months", "Last 6 months", 180),
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
    change_summary: str
    status_code: str
    status_label: str
    status_tone: str
    detail_change_line: str
    reason_line: str | None = None
    approved_by_label: str | None = None
    applies_to_line: str | None = None
    previous_value: str | None = None
    new_value: str | None = None
    open_href: str | None = None
    actor_role: str | None = None


def _status_tone(code: str) -> str:
    if code == "applied":
        return "success"
    if code == "pending":
        return "warning"
    if code == "rejected":
        return "error"
    return "muted"


def _format_when_date(created_at: datetime) -> str:
    local = as_utc_aware(created_at).astimezone(_IST)
    return local.strftime("%d %b %Y")


def _format_when_short(created_at: datetime) -> str:
    local = as_utc_aware(created_at).astimezone(_IST)
    return local.strftime("%H:%M IST")


def _human_key(key: str) -> str:
    return key.replace("_", " ").replace(".", " ").strip().title()


def _area_key_from_scope(scope: str) -> str:
    if scope.startswith("regulation_"):
        return "grading_credits"
    return _SCOPE_TO_AREA.get(scope, "general")


def _area_for_audit(action: str, resource_type: str | None) -> str:
    blob = f"{action} {resource_type or ''}".lower()
    if "calendar" in blob:
        return "calendar"
    if "batch_section" in blob or resource_type in {"department_section", "department_batch"}:
        return "batches_sections"
    if "curriculum" in blob:
        return "curriculum_courses"
    if "grading" in blob or "credit" in blob or resource_type == "academic_regulation":
        return "grading_credits"
    if "programme" in blob:
        return "programmes"
    if "course" in blob:
        return "courses"
    if "year" in blob or "semester" in blob or "term" in blob:
        return "years_programmes"
    if "regulation" in blob:
        return "grading_credits"
    return "general"


def _is_academic_audit(row: AuditLog) -> bool:
    if row.action.startswith("institution."):
        return False
    needles = (
        "academic",
        "batch_section",
        "regulation",
        "programme",
        "semester",
        "course",
        "curriculum",
        "grading",
        "credit",
        "calendar",
    )
    hay = f"{row.action} {row.resource_type or ''}".lower()
    return any(n in hay for n in needles)


def _area_open_href(area_key: str) -> str:
    routes = {
        "calendar": "/college-admin/academics/academic-calendar-configuration",
        "curriculum_courses": "/college-admin/academics/curriculum-management",
        "batches_sections": "/college-admin/academics/batch-section-configuration",
        "grading_credits": "/college-admin/academics/grading-system-configuration",
        "years_programmes": "/college-admin/academics/academic-year-management",
        "programmes": "/college-admin/academics/programme-management",
        "courses": "/college-admin/academics/course-configuration",
    }
    return routes.get(area_key, "/college-admin/academics/academic-configuration-dashboard")


def _version_summary(scope: str, snapshot: dict) -> tuple[str, str | None, str | None, str, str | None, str | None]:
    status = str(snapshot.get("status", "published")).lower()
    status_code = "pending" if status in {"draft", "pending"} else "applied"
    if scope == "academic_calendar":
        title = snapshot.get("title") or "Academic calendar"
        events = snapshot.get("events") or []
        if events:
            event = events[-1]
            summary = f"{event.get('title', 'Calendar event')} added to calendar"
            if "exam" in str(event.get("title", "")).lower():
                summary = f"Mid-sem exam dates added to calendar"
            return (
                summary,
                event.get("description"),
                f"Academic year {snapshot.get('academic_year_id', '—')}",
                status_code,
                None,
                None,
            )
        return (f"{title} published", None, None, status_code, None, None)
    if scope == "academic_year":
        label = snapshot.get("label", "Academic year")
        return (
            f"Academic year {label} configuration published",
            None,
            f"Intake {label}",
            status_code,
            str(snapshot.get("start_date")),
            str(snapshot.get("end_date")),
        )
    if scope.startswith("regulation_"):
        key = scope.replace("regulation_", "").replace("_", " ")
        return (
            f"{key.title()} regulation updated",
            None,
            snapshot.get("scope_key") or key,
            status_code,
            None,
            None,
        )
    label = _human_key(scope)
    return (f"{label} configuration v{snapshot.get('version', snapshot.get('version_number', '—'))}", None, None, status_code, None, None)


async def _actor_label(
    actor_id: PydanticObjectId | None,
    cache: dict[str, str],
    *,
    role_hint: str | None = None,
) -> str:
    if role_hint:
        return role_hint
    if actor_id is None:
        return "System"
    key = str(actor_id)
    if key in cache:
        return cache[key]
    user = await User.get(actor_id)
    label = user.full_name if user and user.full_name else key
    cache[key] = label
    return label


def _audit_summary(action: str, metadata: dict) -> str:
    for field in ("summary", "title", "change", "description"):
        value = metadata.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if action == "batch_section.auto_allocated":
        count = metadata.get("students_allocated", 0)
        return f"Auto-allocated students across sections ({count} pending)"
    if action == "academic_calendar.event_added":
        return f"Calendar event · {metadata.get('title', 'New event')}"
    if action == "academic_calendar.published":
        return "Academic calendar published"
    if "course" in action and metadata.get("course_code"):
        prev = metadata.get("previous_credits")
        new = metadata.get("credit_units")
        if prev is not None and new is not None:
            return f"{metadata['course_code']} credits changed {prev} → {new}"
    cleaned = action.replace("academic.", "").replace("batch_section.", "").replace("_", " ").replace(".", " · ")
    return cleaned.title()


async def _collect_changes(tenant_id: PydanticObjectId) -> list[_UnifiedChange]:
    changes: list[_UnifiedChange] = []

    versions = (
        await AcademicConfigurationVersion.find(Eq(AcademicConfigurationVersion.tenant_id, tenant_id))
        .sort("-published_at")
        .to_list()
    )
    for row in versions:
        area = _area_key_from_scope(row.scope)
        summary, reason, applies, status_code, previous, new = _version_summary(row.scope, row.snapshot or {})
        status_label = "Pending" if status_code == "pending" else "Applied"
        changes.append(
            _UnifiedChange(
                change_id=f"ver-{row.id}",
                created_at=row.published_at,
                actor_id=row.published_by,
                area_key=area,
                change_summary=summary,
                status_code=status_code,
                status_label=status_label,
                status_tone=_status_tone(status_code),
                detail_change_line=summary,
                reason_line=reason,
                applies_to_line=applies,
                previous_value=previous,
                new_value=new,
                approved_by_label="Academic configuration snapshot" if status_code == "applied" else None,
                open_href=_area_open_href(area),
            )
        )

    audits = await AuditLog.find(Eq(AuditLog.tenant_id, tenant_id)).sort("-created_at").to_list()
    for row in audits:
        if not _is_academic_audit(row):
            continue
        meta = row.metadata or {}
        area = _area_for_audit(row.action, row.resource_type)
        status_code = str(meta.get("status", "applied" if row.outcome == "success" else "rejected")).lower()
        if status_code not in {"applied", "pending", "rejected"}:
            status_code = "applied" if row.outcome == "success" else "rejected"
        status_label = status_code.title()
        changes.append(
            _UnifiedChange(
                change_id=f"aud-{row.id}",
                created_at=row.created_at,
                actor_id=row.actor_id,
                area_key=area,
                change_summary=_audit_summary(row.action, meta),
                status_code=status_code,
                status_label=status_label,
                status_tone=_status_tone(status_code),
                detail_change_line=_audit_summary(row.action, meta),
                reason_line=meta.get("reason") or meta.get("reason_line"),
                applies_to_line=meta.get("applies_to") or meta.get("batch_label") or meta.get("regulation_code"),
                approved_by_label=meta.get("approved_by"),
                previous_value=meta.get("previous_value"),
                new_value=meta.get("new_value"),
                open_href=_area_open_href(area),
                actor_role=meta.get("actor_role") or meta.get("role_title"),
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
    days = next((d for key, _, d in _DATE_RANGE_OPTIONS if key == date_range), 180)
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
            hay = f"{row.change_summary} {_AREA_TABLE_LABELS.get(row.area_key, '')}".lower()
            if needle not in hay:
                continue
        filtered.append(row)
    return filtered


async def get_academic_configuration_history_page(
    scope: AccessScope,
    *,
    page: int = 1,
    date_range: str = "last_6_months",
    setting_area: str | None = None,
    actor_id: str | None = None,
    search: str | None = None,
    selected_change_id: str | None = None,
) -> ConfigurationHistoryPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
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
            ConfigurationHistoryFilterOption(
                value=aid,
                label=await _actor_label(PydanticObjectId(aid), actor_cache),
            )
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
                setting_label=_AREA_TABLE_LABELS.get(row.area_key, _human_key(row.area_key)),
                changed_by_label=await _actor_label(row.actor_id, actor_cache, role_hint=row.actor_role),
                when_label=_format_when_date(row.created_at),
                status_code=row.status_code,
                status_label=row.status_label,
                status_tone=row.status_tone,
            )
        )

    selected: ConfigurationChangeDetail | None = None
    selected_row = next((r for r in filtered if r.change_id == selected_change_id), None) if selected_change_id else None
    if selected_row is None and filtered:
        selected_row = filtered[0]
    if selected_row:
        change_line = selected_row.detail_change_line
        if selected_row.previous_value and selected_row.new_value:
            change_line = f"{change_line} ({selected_row.previous_value} → {selected_row.new_value})"
        selected = ConfigurationChangeDetail(
            change_id=selected_row.change_id,
            setting_line=change_line,
            previous_value=selected_row.previous_value,
            new_value=selected_row.new_value,
            approved_by_label=selected_row.approved_by_label,
            reason_line=selected_row.reason_line,
            applies_to_line=selected_row.applies_to_line,
            ip_line=None,
            open_href=selected_row.open_href or "/college-admin/academics/academic-configuration-history",
            open_label="Open",
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    setting_options = [ConfigurationHistoryFilterOption(value="", label="All areas")] + [
        ConfigurationHistoryFilterOption(value=key, label=_AREA_TABLE_LABELS.get(key, _human_key(key)))
        for key in sorted(_AREA_LABELS.keys(), key=lambda k: _AREA_LABELS[k])
    ]

    now = utcnow()
    return ConfigurationHistoryPageRead(
        page_title="Academic Configuration History",
        page_subtitle="Changes to years, programmes, curricula, grading and calendars",
        export_label="Export log",
        date_range_filter_label="Date range",
        setting_filter_label="Area",
        user_filter_label="User",
        scope_indicator_label="College scope",
        updated_at_label=_format_when_short(now),
        date_range_options=[
            ConfigurationHistoryFilterOption(value=key, label=label) for key, label, _ in _DATE_RANGE_OPTIONS
        ],
        setting_options=setting_options,
        user_options=user_options,
        change_log_title="Change log",
        table_headers=["Change", "Area", "Changed by", "When", "Status"],
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
        footer_disclaimer="Live academic configuration · Published versions and audit log entries · All times IST",
        footer_snapshot_label=f"Sample snapshot · {now.astimezone(_IST).strftime('%d %b %Y, %H:%M IST')}",
        generated_at=now,
    )