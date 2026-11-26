"""Book acquisition requests (CA 12.05)."""

from __future__ import annotations

import math

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.library_admin_models import LibraryAcquisition
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryBookAcquisitionPageRead,
    LibraryBookAcquisitionTableRow,
    PoliciesPagination,
)
from app.modules.library.acquisition_enums import LibraryAcquisitionStatus
from app.modules.library.acquisition_models import LibraryAcquisitionQuotation

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Request", "Title", "Requested by", "Copies", "Cost", "Status"]

_STATUS_LABELS: dict[str, tuple[str, str]] = {
    LibraryAcquisitionStatus.PENDING_APPROVAL.value: ("Pending approval", "warning"),
    LibraryAcquisitionStatus.SUBMITTED.value: ("Pending approval", "warning"),
    LibraryAcquisitionStatus.APPROVED.value: ("Approved", "success"),
    LibraryAcquisitionStatus.ORDERED.value: ("Ordered", "info"),
    LibraryAcquisitionStatus.QUOTED.value: ("Quoted", "info"),
    LibraryAcquisitionStatus.PARTIAL_RECEIVED.value: ("Partial received", "info"),
    LibraryAcquisitionStatus.RECEIVED.value: ("Received", "success"),
    LibraryAcquisitionStatus.REGISTERED.value: ("Registered", "success"),
    LibraryAcquisitionStatus.REJECTED.value: ("Rejected", "error"),
    LibraryAcquisitionStatus.CANCELLED.value: ("Cancelled", "muted"),
    LibraryAcquisitionStatus.DRAFT.value: ("Draft", "muted"),
}


def _status_label(doc: LibraryAcquisition) -> tuple[str, str]:
    key = (doc.approval_status or doc.status or "").lower()
    if key in _STATUS_LABELS:
        return _STATUS_LABELS[key]
    if doc.status:
        return doc.status.replace("_", " ").title(), "muted"
    return "—", "muted"


async def _cost_label(tenant_id, doc: LibraryAcquisition) -> str:
    meta = doc.metadata or {}
    for field in ("estimated_cost", "cost", "amount", "total_cost"):
        raw = meta.get(field)
        if raw is not None:
            try:
                return f"₹{float(raw):,.0f}"
            except (TypeError, ValueError):
                continue
    if doc.selected_quotation_id:
        quote = await LibraryAcquisitionQuotation.find_one(
            Eq(LibraryAcquisitionQuotation.tenant_id, tenant_id),
            Eq(LibraryAcquisitionQuotation.quotation_id, doc.selected_quotation_id),
        )
        if quote:
            return f"₹{quote.amount:,.0f}"
    if doc.vendor and meta.get("unit_price") and doc.quantity:
        try:
            return f"₹{float(meta['unit_price']) * doc.quantity:,.0f}"
        except (TypeError, ValueError):
            pass
    return "—"


async def _requested_by(
    tenant_id,
    doc: LibraryAcquisition,
    user_by_id: dict,
) -> str:
    meta = doc.metadata or {}
    if meta.get("requested_by"):
        return str(meta["requested_by"])
    if meta.get("department"):
        return str(meta["department"])
    if doc.suggested_by and doc.suggested_by in user_by_id:
        return user_by_id[doc.suggested_by].full_name or "—"
    if doc.actor_id and doc.actor_id in user_by_id:
        return user_by_id[doc.actor_id].full_name or "—"
    return "—"


async def get_library_book_acquisition_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryBookAcquisitionPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size

    query = LibraryAcquisition.find(Eq(LibraryAcquisition.tenant_id, tenant_id)).sort("-created_at")
    total = await query.count()
    rows = await query.skip(offset).limit(page_size).to_list()

    user_ids = {doc.suggested_by for doc in rows if doc.suggested_by} | {doc.actor_id for doc in rows if doc.actor_id}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[LibraryBookAcquisitionTableRow] = []
    for doc in rows:
        status_label, status_tone = _status_label(doc)
        table_rows.append(
            LibraryBookAcquisitionTableRow(
                acquisition_id=doc.acquisition_id,
                title=doc.title or doc.book_id or doc.acquisition_id,
                requested_by_label=await _requested_by(tenant_id, doc, user_by_id),
                copies_label=f"{doc.quantity:,}",
                cost_label=await _cost_label(tenant_id, doc),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/book-acquisition?id={doc.acquisition_id}",
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(table_rows))
    showing_label = f"{showing_end:,} of {total:,}"

    return LibraryBookAcquisitionPageRead(
        page_title="Book Acquisition",
        page_subtitle="Purchase requests and orders",
        new_request_label="New request",
        new_request_href="/college-admin/library/book-acquisition?action=create",
        acquisitions_section_title="Acquisitions",
        table_headers=_TABLE_HEADERS,
        acquisition_rows=table_rows,
        empty_table_message="No acquisition requests yet.",
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