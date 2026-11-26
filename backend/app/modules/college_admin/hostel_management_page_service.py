"""Hostel management screens (CA 13.02–15) — backend-driven table shells."""

from __future__ import annotations

import math
from typing import Any, Awaitable, Callable

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import (
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBuilding,
    HostelResidentHistory,
    HostelRoom,
    HostelVisitorLog,
    HostelWaitingListEntry,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import HostelManagementPageRead, HostelManagementTableRow, PoliciesPagination
from app.modules.hostel.hostel_models import HostelApplication
from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassRequest
from app.modules.hostel.maintenance_models import HostelMaintenanceRequest
from app.modules.hostel.mess_models import HostelMessPlan
from app.modules.hostel.rules_incident_models import HostelIncident

_PAGE_SIZE = 8

_SCREEN_META: dict[str, dict[str, Any]] = {
    "hostel-building-management": {
        "figma_frame": "161:2589",
        "page_title": "Hostel Building Management",
        "page_subtitle": "Buildings, blocks, and bed capacity",
        "primary_action_label": "Add building",
        "primary_action_href": "?action=create",
        "section_title": "Buildings",
        "table_headers": ["Building", "Hostel", "Type", "Status", "Updated"],
        "empty_table_message": "No hostel buildings configured yet.",
        "loader": "buildings",
    },
    "room-management": {
        "figma_frame": "161:2906",
        "page_title": "Room Management",
        "page_subtitle": "Rooms, types, and capacity",
        "primary_action_label": "Add room",
        "primary_action_href": "?action=create",
        "section_title": "Rooms",
        "table_headers": ["Room", "Block", "Type", "Beds", "Status"],
        "empty_table_message": "No rooms configured yet.",
        "loader": "rooms",
    },
    "bed-allocation": {
        "figma_frame": "161:3257",
        "page_title": "Bed Allocation",
        "page_subtitle": "Assign beds and track occupancy",
        "primary_action_label": "Allocate bed",
        "primary_action_href": "?action=allocate",
        "section_title": "Beds",
        "table_headers": ["Bed", "Room", "Building", "Status", "Student"],
        "empty_table_message": "No beds registered yet.",
        "loader": "beds",
    },
    "hostel-admission-applications": {
        "figma_frame": "161:3565",
        "page_title": "Hostel Admission Applications",
        "page_subtitle": "Applications and waiting list",
        "primary_action_label": "Review applications",
        "primary_action_href": "?action=review",
        "section_title": "Applications",
        "table_headers": ["Application", "Student", "Room type", "Status", "Submitted"],
        "empty_table_message": "No admission applications yet.",
        "loader": "applications",
    },
    "resident-management": {
        "figma_frame": "161:3875",
        "page_title": "Resident Management",
        "page_subtitle": "Active residents and room details",
        "primary_action_label": "Add resident",
        "primary_action_href": "?action=create",
        "section_title": "Residents",
        "table_headers": ["Student", "Building", "Room", "Bed", "Status"],
        "empty_table_message": "No active residents yet.",
        "loader": "residents",
    },
    "hostel-check-in-checkout": {
        "figma_frame": "161:4221",
        "page_title": "Hostel Check-in / Checkout",
        "page_subtitle": "Check-in queue and recent movements",
        "primary_action_label": "Check in",
        "primary_action_href": "?action=check-in",
        "section_title": "Check-in queue",
        "table_headers": ["Student", "Building", "Room", "Action", "Date"],
        "empty_table_message": "No pending check-ins.",
        "loader": "check_ins",
    },
    "hostel-fee-management": {
        "figma_frame": "161:4530",
        "page_title": "Hostel Fee Management",
        "page_subtitle": "Fee plans and billing status",
        "primary_action_label": "Create demand",
        "primary_action_href": "?action=create",
        "section_title": "Fee records",
        "table_headers": ["Student", "Period", "Amount", "Due", "Status"],
        "empty_table_message": "No hostel fee records for this period.",
        "loader": "empty",
    },
    "mess-management": {
        "figma_frame": "161:4839",
        "page_title": "Mess Management",
        "page_subtitle": "Mess plans and enrolment",
        "primary_action_label": "Update plan",
        "primary_action_href": "?action=edit",
        "section_title": "Mess plans",
        "table_headers": ["Plan", "Meals", "Rate", "Residents", "Status"],
        "empty_table_message": "No mess plans configured yet.",
        "loader": "mess",
    },
    "visitor-management": {
        "figma_frame": "161:5143",
        "page_title": "Visitor Management",
        "page_subtitle": "Visitor log and approvals",
        "primary_action_label": "Log visitor",
        "primary_action_href": "?action=create",
        "section_title": "Visitors",
        "table_headers": ["Visitor", "Resident", "Checked in", "Purpose", "Status"],
        "empty_table_message": "No visitor entries yet.",
        "loader": "visitors",
    },
    "leave-outpass-approval": {
        "figma_frame": "161:5435",
        "page_title": "Leave & Outpass Approval",
        "page_subtitle": "Pending leave and outpass requests",
        "primary_action_label": "Review queue",
        "primary_action_href": "?action=review",
        "section_title": "Pending approvals",
        "table_headers": ["Student", "Type", "From", "To", "Status"],
        "empty_table_message": "No pending leave or outpass requests.",
        "loader": "outpass",
    },
    "maintenance-complaints": {
        "figma_frame": "161:5766",
        "page_title": "Maintenance & Complaints",
        "page_subtitle": "Open requests and resolution",
        "primary_action_label": "Raise complaint",
        "primary_action_href": "?action=create",
        "section_title": "Complaints",
        "table_headers": ["Request", "Location", "Priority", "Reported", "Status"],
        "empty_table_message": "No maintenance requests yet.",
        "loader": "maintenance",
    },
    "hostel-incident-management": {
        "figma_frame": "161:6075",
        "page_title": "Hostel Incident Management",
        "page_subtitle": "Incidents and disciplinary review",
        "primary_action_label": "Report incident",
        "primary_action_href": "?action=create",
        "section_title": "Incidents",
        "table_headers": ["Incident", "Severity", "Location", "Reported", "Status"],
        "empty_table_message": "No incidents recorded yet.",
        "loader": "incidents",
    },
    "hostel-reports": {
        "figma_frame": "161:6367",
        "page_title": "Hostel Reports",
        "page_subtitle": "Occupancy, fee and incident reports",
        "primary_action_label": "Create report",
        "primary_action_href": "?action=create",
        "section_title": "Reports",
        "table_headers": ["Report", "Period", "Format", "Last run", "Schedule"],
        "empty_table_message": "No report runs yet.",
        "loader": "empty",
    },
    "hostel-settings": {
        "figma_frame": "161:6645",
        "page_title": "Hostel Settings",
        "page_subtitle": "Rules and timings",
        "primary_action_label": "Save",
        "primary_action_href": "?action=save",
        "section_title": "Hostel rules",
        "table_headers": [],
        "empty_table_message": "",
        "loader": "empty",
    },
}


def _status_tone(status: str) -> tuple[str, str]:
    key = (status or "").lower()
    if key in {"active", "open", "approved", "available", "checked_in", "completed"}:
        return status.replace("_", " ").title(), "success"
    if key in {"pending", "requested", "awaiting", "in_progress"}:
        return status.replace("_", " ").title(), "warning"
    if key in {"rejected", "cancelled", "closed", "maintenance"}:
        return status.replace("_", " ").title(), "error"
    return (status or "—").replace("_", " ").title(), "muted"


async def _load_buildings(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    buildings = await HostelBuilding.find(Eq(HostelBuilding.tenant_id, tenant_id)).sort("name").to_list()
    rows: list[HostelManagementTableRow] = []
    for b in buildings:
        label, tone = _status_tone("active" if b.is_active else "inactive")
        rows.append(
            HostelManagementTableRow(
                row_id=b.building_code,
                cells=[
                    b.name or b.building_code,
                    b.hostel_code or "—",
                    b.building_type or "—",
                    label,
                    b.updated_at.strftime("%d %b %Y"),
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/hostel-building-management?id={b.building_code}",
            )
        )
    return rows


async def _load_rooms(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    rooms = await HostelRoom.find(Eq(HostelRoom.tenant_id, tenant_id)).sort("room_code").to_list()
    rows: list[HostelManagementTableRow] = []
    for room in rooms:
        label, tone = _status_tone(room.operational_status or "active")
        rows.append(
            HostelManagementTableRow(
                row_id=room.room_code,
                cells=[
                    room.room_code,
                    room.block_code,
                    room.room_type or "—",
                    str(room.bed_capacity),
                    label,
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/room-management?id={room.room_code}",
            )
        )
    return rows


async def _load_beds(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    beds = await HostelBed.find(Eq(HostelBed.tenant_id, tenant_id)).sort("bed_id").to_list()
    rows: list[HostelManagementTableRow] = []
    for bed in beds:
        label, tone = _status_tone(bed.status.value if hasattr(bed.status, "value") else str(bed.status))
        rows.append(
            HostelManagementTableRow(
                row_id=bed.bed_id,
                cells=[
                    bed.bed_id,
                    bed.room_code or "—",
                    bed.building_code,
                    label,
                    "—",
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/bed-allocation?id={bed.bed_id}",
            )
        )
    return rows


async def _load_applications(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    apps = await HostelApplication.find(Eq(HostelApplication.tenant_id, tenant_id)).sort("-created_at").to_list()
    if not apps:
        waiting = await HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, tenant_id)).sort("position").to_list()
        rows = []
        for w in waiting:
            rows.append(
                HostelManagementTableRow(
                    row_id=w.application_id,
                    cells=[w.application_id, "—", w.room_type or "Any", "Waiting", w.created_at.strftime("%d %b %Y")],
                    status_label="Waiting",
                    status_tone="info",
                    detail_href=f"/college-admin/hostel/hostel-admission-applications?id={w.application_id}",
                )
            )
        return rows
    user_ids = {a.student_user_id for a in apps if a.student_user_id}
    users = await User.find({"_id": {"$in": list(user_ids)}}).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}
    rows: list[HostelManagementTableRow] = []
    for app in apps[:50]:
        student = user_by_id.get(app.student_user_id) if app.student_user_id else None
        status = app.status.value if hasattr(app.status, "value") else str(app.status)
        label, tone = _status_tone(status)
        rows.append(
            HostelManagementTableRow(
                row_id=app.application_id,
                cells=[
                    app.application_id,
                    student.full_name if student else "—",
                    app.preferred_room_type or "—",
                    label,
                    app.submitted_at.strftime("%d %b %Y") if app.submitted_at else "—",
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/hostel-admission-applications?id={app.application_id}",
            )
        )
    return rows


async def _load_residents(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    active_statuses = [HostelAllocationStatus.ACTIVE.value, HostelAllocationStatus.CONFIRMED.value]
    allocs = await HostelAllocation.find(
        Eq(HostelAllocation.tenant_id, tenant_id),
        In(HostelAllocation.status, active_statuses),
    ).to_list()
    user_ids = {a.student_user_id for a in allocs}
    users = await User.find({"_id": {"$in": list(user_ids)}}).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}
    rows: list[HostelManagementTableRow] = []
    for alloc in allocs:
        student = user_by_id.get(alloc.student_user_id)
        label, tone = _status_tone(alloc.status.value if hasattr(alloc.status, "value") else str(alloc.status))
        rows.append(
            HostelManagementTableRow(
                row_id=alloc.allocation_id,
                cells=[
                    student.full_name if student else "—",
                    alloc.building_code,
                    alloc.room_code or "—",
                    alloc.bed_id or "—",
                    label,
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/resident-management?id={alloc.allocation_id}",
            )
        )
    return rows


async def _load_check_ins(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    history = await HostelResidentHistory.find(Eq(HostelResidentHistory.tenant_id, tenant_id)).sort("-created_at").limit(30).to_list()
    alloc_ids = {h.allocation_id for h in history}
    allocs = (
        await HostelAllocation.find(
            Eq(HostelAllocation.tenant_id, tenant_id),
            In(HostelAllocation.allocation_id, list(alloc_ids)),
        ).to_list()
        if alloc_ids
        else []
    )
    alloc_by_id = {a.allocation_id: a for a in allocs}
    user_ids = {h.student_user_id for h in history}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}
    rows: list[HostelManagementTableRow] = []
    for item in history:
        student = user_by_id.get(item.student_user_id)
        alloc = alloc_by_id.get(item.allocation_id)
        rows.append(
            HostelManagementTableRow(
                row_id=f"{item.allocation_id}:{item.created_at.isoformat()}",
                cells=[
                    student.full_name if student else "—",
                    alloc.building_code if alloc else "—",
                    alloc.room_code if alloc else "—",
                    item.event_type.replace("_", " ").title(),
                    item.created_at.strftime("%d %b %Y"),
                ],
                status_label=item.event_type.replace("_", " ").title(),
                status_tone="info",
                detail_href=f"/college-admin/hostel/hostel-check-in-checkout?id={item.allocation_id}",
            )
        )
    return rows


async def _load_mess(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    plans = await HostelMessPlan.find(Eq(HostelMessPlan.tenant_id, tenant_id)).to_list()
    rows: list[HostelManagementTableRow] = []
    for plan in plans:
        label, tone = _status_tone(plan.status.value if hasattr(plan.status, "value") else str(plan.status))
        rows.append(
            HostelManagementTableRow(
                row_id=plan.plan_code,
                cells=[
                    plan.title or plan.plan_code,
                    ", ".join(plan.included_meals) if plan.included_meals else "—",
                    f"₹{plan.monthly_amount:,.0f}" if plan.monthly_amount else "—",
                    "—",
                    label,
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/mess-management?id={plan.plan_code}",
            )
        )
    return rows


async def _load_visitors(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    logs = await HostelVisitorLog.find(Eq(HostelVisitorLog.tenant_id, tenant_id)).sort("-check_in_at").limit(40).to_list()
    resident_ids = {log.resident_user_id for log in logs}
    residents = await User.find(In(User.id, list(resident_ids))).to_list() if resident_ids else []
    resident_by_id = {u.id: u for u in residents}
    rows: list[HostelManagementTableRow] = []
    for log in logs:
        resident = resident_by_id.get(log.resident_user_id)
        visit_status = "checked_out" if log.check_out_at else "checked_in"
        label, tone = _status_tone(visit_status)
        rows.append(
            HostelManagementTableRow(
                row_id=log.visit_id,
                cells=[
                    log.visitor_name,
                    resident.full_name if resident else "—",
                    log.check_in_at.strftime("%d %b %H:%M") if log.check_in_at else "—",
                    log.purpose or "—",
                    label,
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/visitor-management?id={log.visit_id}",
            )
        )
    return rows


async def _load_outpass(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    pending_statuses = [
        HostelLeaveOutpassStatus.PENDING_APPROVAL.value,
        HostelLeaveOutpassStatus.SUBMITTED.value,
    ]
    pending = await HostelOutpassRequest.find(
        Eq(HostelOutpassRequest.tenant_id, tenant_id),
        In(HostelOutpassRequest.status, pending_statuses),
    ).sort("-created_at").to_list()
    student_ids = {r.student_user_id for r in pending}
    students = await User.find(In(User.id, list(student_ids))).to_list() if student_ids else []
    student_by_id = {u.id: u for u in students}
    rows: list[HostelManagementTableRow] = []
    for req in pending:
        student = student_by_id.get(req.student_user_id)
        label, tone = _status_tone(req.status.value if hasattr(req.status, "value") else str(req.status))
        rows.append(
            HostelManagementTableRow(
                row_id=req.request_id,
                cells=[
                    student.full_name if student else "—",
                    req.outpass_type.value if hasattr(req.outpass_type, "value") else "Outpass",
                    req.from_at.strftime("%d %b") if req.from_at else "—",
                    req.to_at.strftime("%d %b") if req.to_at else "—",
                    label,
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/leave-outpass-approval?id={req.request_id}",
            )
        )
    return rows


async def _load_maintenance(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    reqs = await HostelMaintenanceRequest.find(Eq(HostelMaintenanceRequest.tenant_id, tenant_id)).sort("-created_at").limit(40).to_list()
    rows: list[HostelManagementTableRow] = []
    for req in reqs:
        label, tone = _status_tone(req.status if isinstance(req.status, str) else str(req.status))
        location = f"{req.building_code} / {req.room_code}"
        rows.append(
            HostelManagementTableRow(
                row_id=req.request_id,
                cells=[
                    req.description[:48] + ("…" if len(req.description) > 48 else ""),
                    location,
                    "—",
                    req.created_at.strftime("%d %b %Y") if req.created_at else "—",
                    label,
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/maintenance-complaints?id={req.request_id}",
            )
        )
    return rows


async def _load_incidents(tenant_id: PydanticObjectId) -> list[HostelManagementTableRow]:
    incidents = await HostelIncident.find(Eq(HostelIncident.tenant_id, tenant_id)).sort("-created_at").limit(40).to_list()
    rows: list[HostelManagementTableRow] = []
    for inc in incidents:
        label, tone = _status_tone(inc.status.value if hasattr(inc.status, "value") else str(inc.status))
        sev = inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity)
        location = inc.room_code or inc.building_code or "—"
        summary = inc.description[:48] + ("…" if len(inc.description) > 48 else "")
        rows.append(
            HostelManagementTableRow(
                row_id=inc.incident_id,
                cells=[
                    summary or inc.incident_id,
                    sev.replace("_", " ").title(),
                    location,
                    inc.created_at.strftime("%d %b %Y") if inc.created_at else "—",
                    label,
                ],
                status_label=label,
                status_tone=tone,
                detail_href=f"/college-admin/hostel/hostel-incident-management?id={inc.incident_id}",
            )
        )
    return rows


_LOADERS: dict[str, Callable[[PydanticObjectId], Awaitable[list[HostelManagementTableRow]]]] = {
    "buildings": _load_buildings,
    "rooms": _load_rooms,
    "beds": _load_beds,
    "applications": _load_applications,
    "residents": _load_residents,
    "check_ins": _load_check_ins,
    "mess": _load_mess,
    "visitors": _load_visitors,
    "outpass": _load_outpass,
    "maintenance": _load_maintenance,
    "incidents": _load_incidents,
    "empty": lambda _tid: _empty_rows(),
}


async def _empty_rows() -> list[HostelManagementTableRow]:
    return []


async def get_hostel_management_page(
    scope: AccessScope,
    screen_slug: str,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HostelManagementPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    meta = _SCREEN_META.get(screen_slug)
    if not meta:
        raise AppError(status_code=404, message="Unknown hostel screen", code="hostel_screen_not_found")

    loader_key = meta["loader"]
    loader = _LOADERS.get(loader_key, _LOADERS["empty"])
    all_rows = await loader(tenant_id)

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_rows = len(all_rows)
    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    start = (page - 1) * page_size
    paged_rows = all_rows[start : start + page_size]
    showing_end = min(total_rows, start + len(paged_rows))
    showing_label = f"Showing {showing_end if total_rows else 0} of {total_rows:,}"
    count_label = f"{total_rows} of {total_rows}" if total_rows else "0 of 0"

    now = utcnow()
    return HostelManagementPageRead(
        screen_slug=screen_slug,
        figma_frame=meta["figma_frame"],
        page_title=meta["page_title"],
        page_subtitle=meta["page_subtitle"],
        primary_action_label=meta.get("primary_action_label"),
        primary_action_href=meta.get("primary_action_href"),
        section_title=meta["section_title"],
        count_label=count_label,
        table_headers=meta["table_headers"],
        rows=paged_rows,
        empty_table_message=meta["empty_table_message"],
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
        generated_at=now,
    )