"""Hostel administration overview dashboard (CA 13.01)."""

from __future__ import annotations

import math
from datetime import date, datetime
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelDashboardOutpassRow,
    HostelDashboardPageRead,
    PoliciesPagination,
    StudentAdminWorkQueueItem,
    UserDashboardKpi,
)
from app.modules.hostel.dashboard_service import get_hostel_dashboard_overview
from app.modules.hostel.hostel_portal_enums import HostelDashboardDateRange
from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassRequest, HostelOutpassType

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Resident", "Type", "From", "To", "Guardian", "Status"]

_INFORMED_STATUSES = frozenset(
    {
        HostelLeaveOutpassStatus.APPROVED.value,
        HostelLeaveOutpassStatus.DEPARTURE_RECORDED.value,
        HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value,
        HostelLeaveOutpassStatus.RETURNED.value,
        HostelLeaveOutpassStatus.CLOSED.value,
    }
)
_AWAITING_STATUSES = frozenset(
    {
        HostelLeaveOutpassStatus.PENDING_APPROVAL.value,
        HostelLeaveOutpassStatus.SUBMITTED.value,
        HostelLeaveOutpassStatus.RETURNED_FOR_CORRECTION.value,
    }
)

_OUTPASS_TYPE_LABELS: dict[HostelOutpassType, str] = {
    HostelOutpassType.WEEKEND: "Weekend",
    HostelOutpassType.DAY: "Day pass",
    HostelOutpassType.SHORT: "Short outpass",
    HostelOutpassType.OVERNIGHT: "Overnight",
    HostelOutpassType.EMERGENCY: "Emergency",
    HostelOutpassType.SPECIAL: "Special",
}


def _short_day(d: date) -> str:
    return d.strftime("%d %b")


def _outpass_type_label(req: HostelOutpassRequest) -> str:
    reason_lower = (req.reason or "").lower()
    dest_lower = (req.destination or "").lower()
    if "late" in reason_lower or "late return" in reason_lower:
        return "Late return"
    if "home" in dest_lower or "home visit" in reason_lower:
        return "Home visit"
    return _OUTPASS_TYPE_LABELS.get(req.outpass_type, req.outpass_type.value.replace("_", " ").title())


def _guardian_for_status(status: HostelLeaveOutpassStatus | str) -> tuple[str, str]:
    key = status.value if isinstance(status, HostelLeaveOutpassStatus) else str(status)
    if key in _INFORMED_STATUSES:
        return "Informed", "success"
    if key in _AWAITING_STATUSES:
        return "Awaiting", "warning"
    if key == HostelLeaveOutpassStatus.REJECTED.value:
        return "Not informed", "error"
    return "—", "muted"


def _status_presentation(status: HostelLeaveOutpassStatus | str) -> tuple[str, str]:
    key = status.value if isinstance(status, HostelLeaveOutpassStatus) else str(status)
    if key in _AWAITING_STATUSES:
        return "Pending", "warning"
    if key == HostelLeaveOutpassStatus.APPROVED.value:
        return "Approved", "success"
    if key == HostelLeaveOutpassStatus.REJECTED.value:
        return "Rejected", "error"
    if key in {HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value, HostelLeaveOutpassStatus.DEPARTURE_RECORDED.value}:
        return "Active", "info"
    if key == HostelLeaveOutpassStatus.RETURNED.value:
        return "Returned", "success"
    return key.replace("_", " ").title(), "muted"


def _outpass_sort_key(req: HostelOutpassRequest) -> tuple[int, datetime]:
    status = req.status.value if hasattr(req.status, "value") else str(req.status)
    priority = 0 if status in _AWAITING_STATUSES else 1
    return priority, req.from_at


async def get_hostel_dashboard_page(
    scope: AccessScope,
    user: User,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HostelDashboardPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    overview = await get_hostel_dashboard_overview(
        scope,
        user,
        anchor_date=today,
        date_range=HostelDashboardDateRange.WEEK,
    )
    hostel = overview.hostel_overview
    resident = overview.resident_overview
    maintenance = overview.maintenance_overview
    mess = overview.mess_overview
    incidents = overview.incident_overview

    occ_pct = hostel.occupancy_percentage
    block_count = hostel.total_blocks or hostel.total_buildings
    blocks_hint = f"{block_count} block{'s' if block_count != 1 else ''}" if block_count else "No blocks configured"

    kpis = [
        UserDashboardKpi(
            key="capacity",
            label="Capacity",
            value=f"{hostel.total_beds:,} beds",
            hint_line=blocks_hint,
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="occupied",
            label="Occupied",
            value=f"{hostel.occupied_beds:,}",
            hint_line=f"{occ_pct:.1f}%",
            hint_tone="success" if occ_pct else "muted",
        ),
        UserDashboardKpi(
            key="vacant",
            label="Vacant",
            value=f"{hostel.available_beds:,}",
            hint_line="Available beds",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="open_complaints",
            label="Open complaints",
            value=f"{maintenance.open_complaints:,}",
            hint_line=f"{maintenance.high_priority:,} urgent" if maintenance.high_priority else "No urgent items",
            hint_tone="warning" if maintenance.high_priority else "info",
        ),
    ]

    outpass_docs = await HostelOutpassRequest.find(Eq(HostelOutpassRequest.tenant_id, tenant_id)).to_list()
    outpass_docs.sort(key=_outpass_sort_key)

    user_ids = {r.student_user_id for r in outpass_docs}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[HostelDashboardOutpassRow] = []
    for req in outpass_docs:
        student = user_by_id.get(req.student_user_id)
        resident_label = student.full_name if student else "—"
        from_day = _short_day(req.from_at.astimezone(_IST).date())
        to_day = _short_day(req.to_at.astimezone(_IST).date())
        guardian_label, guardian_tone = _guardian_for_status(req.status)
        status_label, status_tone = _status_presentation(req.status)
        table_rows.append(
            HostelDashboardOutpassRow(
                request_id=req.request_id,
                resident_label=resident_label,
                type_label=_outpass_type_label(req),
                from_label=from_day,
                to_label=to_day,
                guardian_label=guardian_label,
                guardian_tone=guardian_tone,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hostel/leave-outpass-approval?id={req.request_id}",
            )
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_rows = len(table_rows)
    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total_rows, start + len(paged_rows))
    showing_label = f"Showing {showing_end if total_rows else 0} of {total_rows:,}"

    fee_defaulters = mess.pending_billing_records

    needs_attention = [
        StudentAdminWorkQueueItem(
            key="admission_applications",
            title="Admission applications",
            subtitle="pending",
            count=resident.pending_applications,
            href="/college-admin/hostel/hostel-admission-applications",
            action_label="Review →",
            icon_slug="file-text",
        ),
        StudentAdminWorkQueueItem(
            key="fee_defaulters",
            title="Fee defaulters",
            subtitle="residents",
            count=fee_defaulters,
            href="/college-admin/hostel/hostel-fee-management",
            action_label="View →",
            icon_slug="alert-circle",
        ),
        StudentAdminWorkQueueItem(
            key="incidents_open",
            title="Incidents open",
            subtitle="under review",
            count=incidents.open_incidents,
            href="/college-admin/hostel/hostel-incident-management",
            action_label="Open →",
            icon_slug="alert-triangle",
        ),
    ]

    page_subtitle = f"Occupancy and operations • {_short_day(today)}"

    return HostelDashboardPageRead(
        page_title="Hostel Dashboard",
        page_subtitle=page_subtitle,
        export_label="Export",
        open_portal_label="Open Hostel portal",
        open_portal_href="/college-admin/hostel/resident-management",
        kpis=kpis,
        outpass_section_title="Outpass requests",
        outpass_view_all_href="/college-admin/hostel/leave-outpass-approval",
        outpass_view_all_label="View all →",
        table_headers=_TABLE_HEADERS,
        outpass_rows=paged_rows,
        empty_table_message="No outpass requests yet.",
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_rows,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        needs_attention_title="Needs attention",
        needs_attention_items=needs_attention,
        generated_at=now,
    )