"""Department status & history page (CA 04.11 — organization)."""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import DepartmentHistory, DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.institution_service import _ensure_settings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    DepartmentStatusHistoryEventRow,
    DepartmentStatusHistoryPageRead,
    DepartmentStatusHistoryStatusSummaryItem,
    DepartmentStatusHistoryTimelineItem,
    InstitutionFieldOption,
    PoliciesPagination,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 6
_DEFAULT_SINCE_YEAR = 2020

_CHANGE_FILTER_OPTIONS: tuple[tuple[str, str], ...] = (
    ("", "All changes"),
    ("created", "Created / proposed"),
    ("updated", "Profile & intake"),
    ("head_assigned", "Head of department"),
    ("transferred", "Reorganization"),
)


def _format_date_label(when: datetime) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b %Y")


def _format_timeline_date(when: datetime) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b %Y")


async def _actor_label(
    actor_id: PydanticObjectId | None,
    cache: dict[str, str],
    *,
    change_type: str,
    snapshot: dict,
    governing_council_label: str,
) -> str:
    if change_type == "transferred":
        return governing_council_label
    ref = (snapshot.get("order_reference") or snapshot.get("aicte_approval_reference") or "")
    if "aicte" in str(ref).lower():
        return "AICTE / Principal"
    approval = (snapshot.get("approval_status") or "").lower()
    if change_type == "head_assigned" and approval == "pending":
        return "Dean, Academics"
    if actor_id is None:
        return "System"
    key = str(actor_id)
    if key in cache:
        return cache[key]
    user = await User.get(actor_id)
    label = (user.full_name.strip() if user and user.full_name else None) or "College admin"
    cache[key] = label
    return label


def _derive_event_label(change_type: str, snapshot: dict, dept: InstitutionDepartment | None) -> str:
    if change_type == "head_assigned":
        appointment = (snapshot.get("appointment_type") or "regular").lower()
        if appointment == "acting":
            return "Acting HoD appointed"
        if appointment == "extension":
            return "HoD term extended"
        return "Head of department assigned"
    if change_type == "created":
        status = snapshot.get("status")
        status_val = status.value if hasattr(status, "value") else str(status or "").lower()
        if status_val == DepartmentStatus.DRAFT.value or status_val == "draft":
            return "Department proposed"
        intake = snapshot.get("approved_intake_ug") or (dept.approved_intake_ug if dept else None)
        if intake:
            return f"Created with {intake} intake"
        return "Department created"
    if change_type == "updated":
        before = snapshot.get("before") if isinstance(snapshot.get("before"), dict) else {}
        after = snapshot.get("after") if isinstance(snapshot.get("after"), dict) else {}
        old_intake = before.get("approved_intake_ug")
        new_intake = after.get("approved_intake_ug")
        if old_intake is not None and new_intake is not None and old_intake != new_intake:
            return f"Intake increased {old_intake} → {new_intake}"
        old_head = before.get("head_user_id")
        new_head = after.get("head_user_id")
        if old_head and not new_head:
            return "HoD resigned"
        new_status = after.get("status")
        new_status_val = new_status.value if hasattr(new_status, "value") else str(new_status or "")
        if new_status_val in {DepartmentStatus.ARCHIVED.value, DepartmentStatus.INACTIVE.value}:
            return "Merged / department closed"
        parent_name = after.get("parent_department_name") or snapshot.get("parent_department_name")
        if parent_name:
            return f"Merged into {parent_name}"
        return "Department profile updated"
    if change_type == "transferred":
        reason = (snapshot.get("reason") or "").strip()
        dept_blob = snapshot.get("department")
        parent_label = None
        if isinstance(dept_blob, dict):
            parent_label = dept_blob.get("parent_department_name")
        if reason:
            if "merg" in reason.lower():
                return f"Merged into {reason}"
            return reason
        if parent_label:
            return f"Merged into {parent_label}"
        return "Department reorganized"
    return change_type.replace("_", " ").title()


def _event_status(change_type: str, snapshot: dict) -> tuple[str, str, str]:
    if change_type == "head_assigned":
        approval = (snapshot.get("approval_status") or "approved").lower()
        if approval == "pending":
            return "pending", "Pending", "warning"
        return "approved", "Approved", "success"
    if change_type == "created":
        status = snapshot.get("status")
        status_val = status.value if hasattr(status, "value") else str(status or "").lower()
        if status_val == DepartmentStatus.DRAFT.value or status_val == "draft":
            return "draft", "Draft", "info"
        return "approved", "Approved", "success"
    if change_type == "transferred":
        return "merged", "Merged", "purple"
    if change_type == "updated":
        after = snapshot.get("after") if isinstance(snapshot.get("after"), dict) else {}
        before = snapshot.get("before") if isinstance(snapshot.get("before"), dict) else {}
        new_status = after.get("status")
        new_status_val = new_status.value if hasattr(new_status, "value") else str(new_status or "")
        if new_status_val in {DepartmentStatus.ARCHIVED.value, DepartmentStatus.INACTIVE.value}:
            return "merged", "Merged", "purple"
        if before.get("head_user_id") and not after.get("head_user_id"):
            return "approved", "Approved", "success"
        if (
            before.get("approved_intake_ug") is not None
            and after.get("approved_intake_ug") is not None
            and before.get("approved_intake_ug") != after.get("approved_intake_ug")
        ):
            return "approved", "Approved", "success"
        return "approved", "Approved", "success"
    return "approved", "Approved", "success"


def _timeline_tone(change_type: str, snapshot: dict, status_tone: str) -> str:
    if status_tone == "warning":
        return "warning"
    if status_tone == "purple":
        return "muted"
    if change_type == "updated":
        before = snapshot.get("before") if isinstance(snapshot.get("before"), dict) else {}
        after = snapshot.get("after") if isinstance(snapshot.get("after"), dict) else {}
        if before.get("head_user_id") and not after.get("head_user_id"):
            return "error"
    if change_type in {"created", "updated"}:
        return "success"
    if change_type == "head_assigned":
        appointment = (snapshot.get("appointment_type") or "").lower()
        if appointment == "acting":
            return "warning"
    return "info"


async def get_department_status_history_page(
    scope: AccessScope,
    *,
    page: int = 1,
    since_year: str | None = None,
    department_id: str | None = None,
    change_type_filter: str | None = None,
    selected_department_id: str | None = None,
) -> DepartmentStatusHistoryPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    settings_doc = await _ensure_settings(tenant_id)
    org_settings = settings_doc.settings.get("organization")
    org_settings = org_settings if isinstance(org_settings, dict) else {}
    governing_label = str(org_settings.get("governing_body_title") or "Governing Council")

    departments = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).sort("+name").to_list()
    dept_by_id: dict[str, InstitutionDepartment] = {str(d.id): d for d in departments}

    history_rows = await (
        DepartmentHistory.find(Eq(DepartmentHistory.tenant_id, tenant_id)).sort("-created_at").to_list()
    )

    year_floor = _DEFAULT_SINCE_YEAR
    if since_year in (None, ""):
        year_floor = _DEFAULT_SINCE_YEAR
    elif since_year == "all":
        year_floor = 1800
    elif since_year.isdigit():
        year_floor = int(since_year)
    else:
        raise AppError(code="VALIDATION_ERROR", message="Invalid since_year", status_code=422)

    change_filter = (change_type_filter or "").strip().lower()
    dept_filter_oid: PydanticObjectId | None = None
    if department_id:
        dept_filter_oid = to_object_id(department_id, "department_id")

    unified: list[tuple[DepartmentHistory, InstitutionDepartment | None]] = []
    for row in history_rows:
        if as_utc_aware(row.created_at).astimezone(_IST).year < year_floor:
            continue
        if dept_filter_oid and row.department_id != dept_filter_oid:
            continue
        if change_filter and row.change_type.lower() != change_filter:
            continue
        dept = dept_by_id.get(str(row.department_id))
        unified.append((row, dept))

    actor_cache: dict[str, str] = {}
    event_rows: list[DepartmentStatusHistoryEventRow] = []
    for row, dept in unified:
        snapshot = row.snapshot if isinstance(row.snapshot, dict) else {}
        status_code, status_label, status_tone = _event_status(row.change_type, snapshot)
        event_rows.append(
            DepartmentStatusHistoryEventRow(
                event_id=str(row.id),
                department_id=str(row.department_id),
                event_label=_derive_event_label(row.change_type, snapshot, dept),
                department_label=dept.name if dept else "Unknown department",
                by_label=await _actor_label(
                    row.actor_id,
                    actor_cache,
                    change_type=row.change_type,
                    snapshot=snapshot,
                    governing_council_label=governing_label,
                ),
                date_label=_format_date_label(row.created_at),
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    total = len(event_rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = event_rows[start : start + _PAGE_SIZE]
    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    selected_id = (selected_department_id or "").strip()
    if not selected_id and page_slice:
        selected_id = page_slice[0].department_id
    if not selected_id and event_rows:
        selected_id = event_rows[0].department_id
    if selected_id and selected_id not in dept_by_id:
        selected_id = ""

    selected_dept = dept_by_id.get(selected_id) if selected_id else None
    timeline: list[DepartmentStatusHistoryTimelineItem] = []
    if selected_id:
        dept_history = await (
            DepartmentHistory.find(
                Eq(DepartmentHistory.tenant_id, tenant_id),
                Eq(DepartmentHistory.department_id, to_object_id(selected_id, "department_id")),
            )
            .sort("+created_at")
            .to_list()
        )
        if not dept_history and selected_dept:
            intake = selected_dept.approved_intake_ug
            label = f"Created with {intake} intake" if intake else "Department established"
            timeline.append(
                DepartmentStatusHistoryTimelineItem(
                    event_id="dept-establish",
                    title=label,
                    date_label=str(selected_dept.establishment_year or _format_timeline_date(selected_dept.created_at)),
                    tone="success",
                    nested_status_label=None,
                )
            )
        for row in dept_history:
            snapshot = row.snapshot if isinstance(row.snapshot, dict) else {}
            status_code, status_label, status_tone = _event_status(row.change_type, snapshot)
            timeline.append(
                DepartmentStatusHistoryTimelineItem(
                    event_id=str(row.id),
                    title=_derive_event_label(row.change_type, snapshot, selected_dept),
                    date_label=_format_timeline_date(row.created_at),
                    tone=_timeline_tone(row.change_type, snapshot, status_tone),
                    nested_status_label=status_label if status_code == "pending" else None,
                )
            )

    active_count = sum(1 for d in departments if d.status == DepartmentStatus.ACTIVE)
    draft_count = sum(1 for d in departments if d.status == DepartmentStatus.DRAFT)
    historical_count = sum(
        1 for d in departments if d.status in {DepartmentStatus.ARCHIVED, DepartmentStatus.INACTIVE}
    )
    programme_active = sum(len(d.programme_codes) for d in departments if d.status == DepartmentStatus.ACTIVE)

    since_options: list[InstitutionFieldOption] = [InstitutionFieldOption(value="all", label="All years")]
    current_year = utcnow().astimezone(_IST).year
    earliest = year_floor
    for row in history_rows:
        earliest = min(earliest, as_utc_aware(row.created_at).astimezone(_IST).year)
    earliest = min(earliest, _DEFAULT_SINCE_YEAR)
    for year in range(_DEFAULT_SINCE_YEAR, current_year + 1):
        if year >= earliest:
            since_options.append(InstitutionFieldOption(value=str(year), label=f"Since {year}"))

    dept_options = [InstitutionFieldOption(value="", label="All departments")]
    for dept in departments:
        dept_options.append(InstitutionFieldOption(value=str(dept.id), label=dept.name))

    change_options = [InstitutionFieldOption(value=key, label=label) for key, label in _CHANGE_FILTER_OPTIONS]

    generated = utcnow()
    updated_label = generated.astimezone(_IST).strftime("Updated %H:%M IST")
    selected_since = since_year if since_year not in (None, "") else str(_DEFAULT_SINCE_YEAR)
    if selected_since == "all":
        selected_since = "all"

    showing_label = f"Showing {len(page_slice)} of {total} events" if total else "Showing 0 events"

    footer_disclaimer = org_settings.get("history_footer_disclaimer")
    if not footer_disclaimer:
        footer_disclaimer = (
            "Illustrative data only · No live student, faculty or finance records · All times IST"
        )

    timeline_title = "Selected department"
    if selected_dept:
        timeline_title = f"Selected: {selected_dept.name}"

    return DepartmentStatusHistoryPageRead(
        page_title="Department Status & History",
        page_subtitle="Lifecycle status and change history for every department",
        export_label="Export log",
        since_year_filter_label="Date range",
        department_filter_label="Departments",
        change_type_filter_label="Change type",
        scope_indicator_label="College scope",
        updated_at_label=updated_label,
        since_year_options=since_options,
        department_options=dept_options,
        change_type_options=change_options,
        selected_since_year=selected_since,
        selected_department_id=department_id or "",
        selected_change_type=change_filter,
        table_headers=["Event", "Department", "By", "Date", "Status"],
        events=page_slice,
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        showing_label=showing_label,
        status_summary_title="Status summary",
        status_summary_items=[
            DepartmentStatusHistoryStatusSummaryItem(
                key="active",
                title="Active",
                subtitle="Running programmes",
                count=active_count,
                badge_tone="success",
                detail_count=programme_active,
            ),
            DepartmentStatusHistoryStatusSummaryItem(
                key="draft",
                title="Draft",
                subtitle="Awaiting approval",
                count=draft_count,
                badge_tone="info",
                detail_count=None,
            ),
            DepartmentStatusHistoryStatusSummaryItem(
                key="historical",
                title="Merged / closed",
                subtitle="Historical",
                count=historical_count,
                badge_tone="muted",
                detail_count=None,
            ),
        ],
        timeline_section_title=timeline_title,
        selected_timeline_department_id=selected_id,
        timeline_items=timeline,
        footer_disclaimer=footer_disclaimer,
        footer_snapshot_label="Sample snapshot",
        generated_at=generated,
    )