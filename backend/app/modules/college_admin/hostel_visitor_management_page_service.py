"""Hostel visitor management (CA 13.10)."""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelVisitorLog
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelVisitorManagementPageRead,
    HostelVisitorManagementTableRow,
    PoliciesPagination,
)
from app.modules.hostel.visitor_models import HostelVisitorEntry, HostelVisitorStatus

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Visitor", "Visiting", "Relation", "In", "Out", "Status"]
_IST = ZoneInfo("Asia/Kolkata")
_INSIDE = frozenset(
    {
        HostelVisitorStatus.INSIDE.value,
        HostelVisitorStatus.ENTRY_RECORDED.value,
        HostelVisitorStatus.APPROVED.value,
    }
)


def _time_label(when: datetime | None) -> str:
    if when is None:
        return "—"
    local = when.astimezone(_IST) if when.tzinfo else when.replace(tzinfo=_IST)
    return local.strftime("%H:%M")


def _visitor_status(*, inside: bool, exited: bool) -> tuple[str, str]:
    if inside:
        return "Inside", "info"
    if exited:
        return "Left", "success"
    return "Expected", "muted"


async def get_hostel_visitor_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HostelVisitorManagementPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    entries = await HostelVisitorEntry.find(Eq(HostelVisitorEntry.tenant_id, tenant_id)).sort("-updated_at").to_list()
    logs = await HostelVisitorLog.find(Eq(HostelVisitorLog.tenant_id, tenant_id)).sort("-check_in_at").to_list()

    resident_ids: set[PydanticObjectId] = set()
    for entry in entries:
        resident_ids.add(entry.resident_user_id)
    for log in logs:
        resident_ids.add(log.resident_user_id)

    users = await User.find(In(User.id, list(resident_ids))).to_list() if resident_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[HostelVisitorManagementTableRow] = []
    seen_ids: set[str] = set()

    for entry in entries:
        seen_ids.add(entry.visit_id)
        resident = user_by_id.get(entry.resident_user_id)
        entry_at = entry.actual_entry_at or entry.expected_arrival or entry.created_at
        exit_at = entry.actual_exit_at or entry.expected_departure
        inside = (entry.status.value if hasattr(entry.status, "value") else str(entry.status)) in _INSIDE
        exited = entry.status == HostelVisitorStatus.EXITED or exit_at is not None
        if not inside and entry_at and exit_at is None and entry.status not in (HostelVisitorStatus.EXITED,):
            if entry.status in (HostelVisitorStatus.INSIDE, HostelVisitorStatus.ENTRY_RECORDED):
                inside = True
        status_label, status_tone = _visitor_status(inside=inside and exit_at is None, exited=exited and exit_at is not None)
        if inside and exit_at is None:
            status_label, status_tone = "Inside", "info"
        elif exit_at is not None or entry.status == HostelVisitorStatus.EXITED:
            status_label, status_tone = "Left", "success"
        relation = entry.relationship_to_resident or "—"
        table_rows.append(
            HostelVisitorManagementTableRow(
                visit_key=entry.visit_id,
                visitor_label=entry.visitor_name,
                visiting_label=resident.full_name if resident else "—",
                relation_label=relation.replace("_", " ").title() if relation != "—" else relation,
                in_label=_time_label(entry_at),
                out_label=_time_label(exit_at) if exit_at else "—",
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hostel/visitor-management?id={entry.visit_id}",
            )
        )

    for log in logs:
        if log.visit_id in seen_ids:
            continue
        resident = user_by_id.get(log.resident_user_id)
        inside = log.check_out_at is None
        status_label, status_tone = ("Inside", "info") if inside else ("Left", "success")
        table_rows.append(
            HostelVisitorManagementTableRow(
                visit_key=log.visit_id,
                visitor_label=log.visitor_name,
                visiting_label=resident.full_name if resident else "—",
                relation_label=log.purpose or "—",
                in_label=_time_label(log.check_in_at),
                out_label=_time_label(log.check_out_at) if log.check_out_at else "—",
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hostel/visitor-management?id={log.visit_id}",
            )
        )

    def _row_day(row: HostelVisitorManagementTableRow, source_entries: dict[str, HostelVisitorEntry], source_logs: dict[str, HostelVisitorLog]) -> date | None:
        entry = source_entries.get(row.visit_key)
        if entry:
            when = entry.actual_entry_at or entry.expected_arrival or entry.created_at
            return when.astimezone(_IST).date() if when else None
        log = source_logs.get(row.visit_key)
        if log and log.check_in_at:
            return log.check_in_at.astimezone(_IST).date()
        return None

    entry_by_id = {e.visit_id: e for e in entries}
    log_by_id = {l.visit_id: l for l in logs}
    today_rows = [r for r in table_rows if _row_day(r, entry_by_id, log_by_id) == today]
    display_rows = today_rows
    today_total = len(today_rows)

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total = len(display_rows)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged_rows = display_rows[start : start + page_size]
    showing_end = min(total, start + len(paged_rows))
    count_label = f"{len(paged_rows)} of {today_total} today"

    return HostelVisitorManagementPageRead(
        page_title="Visitor Management",
        page_subtitle="Visitor passes and logs",
        register_visitor_label="Register visitor",
        register_visitor_href="/college-admin/hostel/visitor-management?action=register",
        visitors_section_title="Visitors",
        table_headers=_TABLE_HEADERS,
        visitor_rows=paged_rows,
        empty_table_message="No visitor entries yet.",
        count_label=count_label,
        showing_label=f"Showing {showing_end if total else 0} of {total:,}",
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