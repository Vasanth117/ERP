"""Digital library management (CA 12.11)."""

from __future__ import annotations

import math
from datetime import timedelta
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryDigitalLibraryPageRead,
    LibraryDigitalResourceTableRow,
    PoliciesPagination,
)
from app.modules.library.digital_enums import DigitalAvailabilityStatus
from app.modules.library.digital_models import LibraryDigitalAccessLog
from app.modules.library.library_models import LibraryDigitalResource

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_TABLE_HEADERS = ["Resource", "Type", "Licence", "Users", "Expires", "Status"]
_RENEWAL_WINDOW_DAYS = 120

_TYPE_LABELS: dict[str, str] = {
    "ebook": "E-books",
    "journal": "Journal",
    "research_paper": "Research paper",
    "reference": "Reference",
    "database": "Database",
    "open_access": "Open access",
}


def _type_label(doc: LibraryDigitalResource) -> str:
    meta = doc.metadata or {}
    for key in ("display_type", "resource_kind", "type"):
        raw = meta.get(key)
        if raw:
            return str(raw).replace("_", " ").strip().title()
    cat = (doc.category or "").lower()
    if cat in {"database", "ebooks", "e-books", "open_access", "open access"}:
        return _TYPE_LABELS.get(cat.replace(" ", "_").replace("-", "_"), cat.title())
    key = (doc.resource_type or "ebook").lower()
    return _TYPE_LABELS.get(key, key.replace("_", " ").title())


def _licence_label(doc: LibraryDigitalResource) -> str:
    meta = doc.metadata or {}
    for key in ("licence", "license", "licence_type", "license_label"):
        raw = meta.get(key)
        if raw:
            return str(raw).replace("_", " ").strip().title()
    if doc.license_type:
        return doc.license_type.replace("_", " ").title()
    if not doc.license_expires_at and not doc.requires_membership:
        return "Free"
    if meta.get("open_access") or (doc.category or "").lower() in {"open_access", "open access"}:
        return "Free"
    return "Institutional"


def _expires_label(doc: LibraryDigitalResource) -> str:
    if not doc.license_expires_at:
        return "—"
    day = doc.license_expires_at.astimezone(_IST).date()
    return day.strftime("%d %b %Y")


def _resource_status(doc: LibraryDigitalResource, *, now) -> tuple[str, str]:
    expires = doc.license_expires_at
    if doc.availability_status == DigitalAvailabilityStatus.EXPIRED.value:
        return "Expired", "error"
    if doc.availability_status == DigitalAvailabilityStatus.WITHDRAWN.value:
        return "Withdrawn", "muted"
    if expires and expires < now:
        return "Expired", "error"
    if expires and expires <= now + timedelta(days=_RENEWAL_WINDOW_DAYS):
        return "Renewal due", "warning"
    return "Active", "success"


async def _users_by_resource(tenant_id, resource_ids: list[str]) -> dict[str, int]:
    if not resource_ids:
        return {}
    collection = LibraryDigitalAccessLog.get_motor_collection()
    pipeline = [
        {"$match": {"tenant_id": tenant_id, "resource_id": {"$in": resource_ids}}},
        {"$group": {"_id": {"resource_id": "$resource_id", "user_id": "$user_id"}}},
        {"$group": {"_id": "$_id.resource_id", "users": {"$sum": 1}}},
    ]
    counts: dict[str, int] = {}
    async for row in collection.aggregate(pipeline):
        counts[row["_id"]] = int(row["users"])
    return counts


async def get_library_digital_library_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryDigitalLibraryPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    query = LibraryDigitalResource.find(Eq(LibraryDigitalResource.tenant_id, tenant_id)).sort("-updated_at")
    total = await query.count()
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    resources = await query.skip(offset).limit(page_size).to_list()

    resource_ids = [r.resource_id for r in resources]
    users_by_id = await _users_by_resource(tenant_id, resource_ids)

    table_rows: list[LibraryDigitalResourceTableRow] = []
    for doc in resources:
        status_label, status_tone = _resource_status(doc, now=now)
        users = users_by_id.get(doc.resource_id, 0)
        table_rows.append(
            LibraryDigitalResourceTableRow(
                resource_id=doc.resource_id,
                title=doc.title,
                type_label=_type_label(doc),
                licence_label=_licence_label(doc),
                users_label=f"{users:,}",
                expires_label=_expires_label(doc),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/digital-library-management?id={doc.resource_id}",
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(table_rows))
    showing_label = f"{showing_end:,} of {total:,}"

    return LibraryDigitalLibraryPageRead(
        page_title="Digital Library Management",
        page_subtitle="E-books, journals and databases",
        add_resource_label="Add resource",
        add_resource_href="/college-admin/library/digital-library-management?action=create",
        digital_resources_section_title="Digital resources",
        table_headers=_TABLE_HEADERS,
        resource_rows=table_rows,
        empty_table_message="No digital resources yet.",
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