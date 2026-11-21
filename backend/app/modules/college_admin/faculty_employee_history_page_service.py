"""Faculty / employee history page (CA 07.13)."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentHistory
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import FacultyEmployeeHistoryPageRead, FacultyEmployeeHistoryTableRow, PoliciesPagination

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _fmt_date(when) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b %Y")


def _reference(history_id: PydanticObjectId, when) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    suffix = str(history_id)[-4:].upper()
    return f"STC-{local.strftime('%m%y')}-{suffix}"


def _change_label(event: FacultyEmploymentHistory) -> str:
    if event.event_type == "status_review":
        return "Status review submitted"
    if event.event_type == "employment_status_change":
        if event.to_status:
            label = event.to_status.replace("_", " ").title()
            return f"Status changed to {label}"
        return event.note or "Employment status updated"
    if event.event_type == "profile_update":
        note = (event.note or "").strip()
        if note:
            return note if len(note) < 80 else f"{note[:77]}..."
        return "Profile updated"
    if event.event_type == "designation_assignment":
        note = (event.note or "").strip()
        if "professor" in note.lower() or "promoted" in note.lower():
            return note
        return note or "Designation updated"
    if event.event_type == "hired":
        return "Employee hired"
    if event.event_type == "transfer":
        return event.note or "Employee transferred"
    if event.event_type == "hr_registered":
        return "Employee registered"
    if event.event_type == "department_allocation":
        return event.note or "Department allocation updated"
    if event.event_type == "status_change":
        return event.note or "Status updated"
    if event.note:
        return event.note
    if event.to_status:
        return event.to_status.replace("_", " ").title()
    return event.event_type.replace("_", " ").title()


async def _actor_label(
    actor_id: PydanticObjectId | None,
    cache: dict[str, str],
    employees: dict[PydanticObjectId, EmployeeRecord],
) -> str:
    if actor_id is None:
        return "System"
    key = str(actor_id)
    if key in cache:
        return cache[key]
    user = await User.get(actor_id)
    if user is None:
        cache[key] = "System"
        return cache[key]
    emp = employees.get(actor_id)
    if emp and emp.designation:
        cache[key] = emp.designation
    else:
        cache[key] = user.full_name.strip() or "College admin"
    return cache[key]


async def get_faculty_employee_history_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> FacultyEmployeeHistoryPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    events = await FacultyEmploymentHistory.find(
        Eq(FacultyEmploymentHistory.tenant_id, tenant_id)
    ).sort("-created_at").to_list()

    total = len(events)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_events = events[start : start + _PAGE_SIZE]

    user_ids = list({e.user_id for e in events})
    actor_ids = list({e.actor_id for e in events if e.actor_id})
    lookup_ids = list({*user_ids, *actor_ids})
    users = await User.find(In(User.id, lookup_ids)).to_list() if lookup_ids else []
    user_by_id = {u.id: u for u in users if u.id}

    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    emp_by_user_id = {e.user_id: e for e in employees if e.user_id in actor_ids}

    actor_cache: dict[str, str] = {}
    rows: list[FacultyEmployeeHistoryTableRow] = []
    for evt in page_events:
        user = user_by_id.get(evt.user_id)
        name = user.full_name if user and user.full_name else "—"
        rows.append(
            FacultyEmployeeHistoryTableRow(
                row_id=str(evt.id),
                date_label=_fmt_date(evt.created_at),
                employee_name=name,
                change_label=_change_label(evt),
                actor_label=await _actor_label(evt.actor_id, actor_cache, emp_by_user_id),
                reference_label=_reference(evt.id, evt.created_at),
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return FacultyEmployeeHistoryPageRead(
        page_title="Faculty / Employee History",
        page_subtitle="Changes to staff records",
        export_label="Export",
        history_section_title="History",
        table_headers=["Date", "Employee", "Change", "By", "Reference"],
        history_rows=rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )