"""Leave & outpass approval (CA 13.11)."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hostel_outpass_page_shared import (
    guardian_for_status,
    outpass_sort_key,
    outpass_status_presentation,
    outpass_type_label,
    short_day,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelLeaveOutpassApprovalPageRead,
    HostelLeaveOutpassApprovalTableRow,
    PoliciesPagination,
)
from app.modules.hostel.leave_outpass_models import HostelOutpassRequest

_PAGE_SIZE = 4
_TABLE_HEADERS = ["Resident", "Type", "From", "To", "Guardian", "Status"]
_IST = ZoneInfo("Asia/Kolkata")


async def get_hostel_leave_outpass_approval_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HostelLeaveOutpassApprovalPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    outpass_docs = await HostelOutpassRequest.find(Eq(HostelOutpassRequest.tenant_id, tenant_id)).to_list()
    outpass_docs.sort(key=outpass_sort_key)

    user_ids = {r.student_user_id for r in outpass_docs}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[HostelLeaveOutpassApprovalTableRow] = []
    for req in outpass_docs:
        student = user_by_id.get(req.student_user_id)
        from_day = short_day(req.from_at.astimezone(_IST).date())
        to_day = short_day(req.to_at.astimezone(_IST).date())
        guardian_label, guardian_tone = guardian_for_status(req.status)
        status_label, status_tone = outpass_status_presentation(req.status)
        table_rows.append(
            HostelLeaveOutpassApprovalTableRow(
                request_id=req.request_id,
                resident_label=student.full_name if student else "—",
                type_label=outpass_type_label(req),
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
    total = len(table_rows)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total, start + len(paged_rows))
    count_label = f"{showing_end} of {total}"
    showing_label = f"Showing {showing_end if total else 0} of {total:,}"

    return HostelLeaveOutpassApprovalPageRead(
        page_title="Leave & Outpass Approval",
        page_subtitle="Requests awaiting warden or admin decision",
        export_label="Export",
        export_href="/college-admin/hostel/leave-outpass-approval?export=1",
        outpass_section_title="Outpass requests",
        table_headers=_TABLE_HEADERS,
        outpass_rows=paged_rows,
        empty_table_message="No outpass requests yet.",
        count_label=count_label,
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