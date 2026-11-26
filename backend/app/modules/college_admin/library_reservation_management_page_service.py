"""Reservation management queue (CA 12.07)."""

from __future__ import annotations

import math
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
    LibraryReservationManagementPageRead,
    LibraryReservationManagementTableRow,
    PoliciesPagination,
)
from app.modules.library.library_enums import LibraryReservationStatus
from app.modules.library.library_models import LibraryReservation

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_TABLE_HEADERS = ["Title", "Member", "Queue", "Reserved", "Expires", "Status"]
_ACTIVE = frozenset({LibraryReservationStatus.QUEUED, LibraryReservationStatus.READY})


def _short_day(d) -> str:
    return d.strftime("%d %b")


def _reservation_status(res: LibraryReservation) -> tuple[str, str]:
    if res.status == LibraryReservationStatus.READY:
        return "Ready", "success"
    if res.status == LibraryReservationStatus.QUEUED:
        return "Waiting", "info"
    return res.status.value.replace("_", " ").title(), "muted"


def _sort_key(res: LibraryReservation) -> tuple[int, str, int, object]:
    ready_first = 0 if res.status == LibraryReservationStatus.READY else 1
    return ready_first, res.title.lower(), res.queue_position, res.created_at


async def get_library_reservation_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryReservationManagementPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    reservations = await LibraryReservation.find(
        Eq(LibraryReservation.tenant_id, tenant_id),
        In(LibraryReservation.status, list(_ACTIVE)),
    ).to_list()
    reservations.sort(key=_sort_key)

    user_ids = {r.student_user_id for r in reservations}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[LibraryReservationManagementTableRow] = []
    for res in reservations:
        member = user_by_id.get(res.student_user_id)
        member_name = member.full_name if member else "—"
        status_label, status_tone = _reservation_status(res)
        reserved = res.created_at.astimezone(_IST).date()
        expires_label = "—"
        if res.expires_at:
            expires_label = _short_day(res.expires_at.astimezone(_IST).date())
        table_rows.append(
            LibraryReservationManagementTableRow(
                reservation_id=res.reservation_id,
                title=res.title,
                member_name=member_name,
                queue_label=str(res.queue_position),
                reserved_label=_short_day(reserved),
                expires_label=expires_label,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/reservation-management?id={res.reservation_id}",
            )
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_rows = len(table_rows)
    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total_rows, start + len(paged_rows))
    showing_label = f"{showing_end:,} of {total_rows:,}"

    return LibraryReservationManagementPageRead(
        page_title="Reservation Management",
        page_subtitle="Hold queue for in-demand titles",
        export_label="Export",
        reservations_section_title="Reservations",
        table_headers=_TABLE_HEADERS,
        reservation_rows=paged_rows,
        empty_table_message="No active reservations yet.",
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