"""Communication announcements management (CA 14.02)."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.communication_admin_models import (
    AnnouncementAudience,
    CommunicationDeliveryLog,
    DeliveryStatus,
    InstitutionAnnouncement,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CommunicationAnnouncementsManagementPageRead,
    CommunicationAnnouncementsTableRow,
    InstitutionPolicyFilterOption,
    PoliciesPagination,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Announcement", "Audience", "Channels", "Published", "Reach", "Status"]

_AUDIENCE_LABELS: dict[AnnouncementAudience, str] = {
    AnnouncementAudience.ALL: "Everyone",
    AnnouncementAudience.STUDENTS: "All students",
    AnnouncementAudience.FACULTY: "All faculty",
    AnnouncementAudience.DEPARTMENT: "Department",
    AnnouncementAudience.CUSTOM: "Custom group",
}

_CHANNEL_LABELS = {
    "in_app": "App",
    "email": "Email",
    "sms": "SMS",
    "whatsapp": "WhatsApp",
}

_STATUS_FILTERS = [
    ("", "All statuses"),
    ("draft", "Draft"),
    ("scheduled", "Scheduled"),
    ("published", "Published"),
]

_AUDIENCE_FILTERS = [
    ("", "All audiences"),
    (AnnouncementAudience.ALL.value, "Everyone"),
    (AnnouncementAudience.STUDENTS.value, "All students"),
    (AnnouncementAudience.FACULTY.value, "All faculty"),
    (AnnouncementAudience.DEPARTMENT.value, "Department"),
    (AnnouncementAudience.PARENTS.value, "Parents and guardians"),
    (AnnouncementAudience.CUSTOM.value, "Custom group"),
]


def _audience_label(doc: InstitutionAnnouncement) -> str:
    base = _AUDIENCE_LABELS.get(doc.audience, doc.audience.value.replace("_", " ").title())
    if doc.audience == AnnouncementAudience.CUSTOM and doc.audience_group_id:
        return doc.audience_group_id.replace("_", " ").title()
    if doc.audience == AnnouncementAudience.STUDENTS and doc.department_scope and doc.department_scope != "all":
        return "Students (scoped)"
    audience_val = doc.audience.value if hasattr(doc.audience, "value") else str(doc.audience)
    if audience_val == AnnouncementAudience.STUDENTS.value:
        return base
    return base


def _channels_label(channels: list[str]) -> str:
    if not channels:
        return "—"
    labels = []
    for ch in channels:
        key = (ch or "").lower()
        label = _CHANNEL_LABELS.get(key, key.replace("_", " ").title())
        if label not in labels:
            labels.append(label)
    if len(labels) >= 4:
        return "All channels"
    return ", ".join(labels)


def _published_label(doc: InstitutionAnnouncement) -> str:
    if doc.status != "published" or not doc.published_at:
        return "—"
    local = doc.published_at.astimezone(_IST) if doc.published_at.tzinfo else doc.published_at.replace(tzinfo=_IST)
    return local.strftime("%d %b")


def _status_presentation(status: str) -> tuple[str, str]:
    key = (status or "draft").lower()
    if key == "published":
        return "Published", "success"
    if key == "scheduled":
        return "Scheduled", "info"
    return "Draft", "muted"


async def _reach_counts(tenant_id, announcement_ids: list[str]) -> dict[str, int]:
    if not announcement_ids:
        return {}
    logs = await CommunicationDeliveryLog.find(
        Eq(CommunicationDeliveryLog.tenant_id, tenant_id),
        Eq(CommunicationDeliveryLog.status, DeliveryStatus.SENT),
    ).to_list()
    counts: dict[str, int] = {aid: 0 for aid in announcement_ids}
    for log in logs:
        if log.announcement_id in counts:
            counts[log.announcement_id] += 1
    return counts


async def get_communication_announcements_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    search: str | None = None,
    audience: str | None = None,
    status: str | None = None,
) -> CommunicationAnnouncementsManagementPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    docs = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).sort("-updated_at").to_list()
    needle = (search or "").strip().lower()
    audience_key = (audience or "").strip().lower()
    status_key = (status or "").strip().lower()

    filtered: list[InstitutionAnnouncement] = []
    for doc in docs:
        if needle and needle not in (doc.title or "").lower() and needle not in (doc.announcement_id or "").lower():
            continue
        aud_val = doc.audience.value if hasattr(doc.audience, "value") else str(doc.audience)
        if audience_key and aud_val != audience_key:
            continue
        if status_key and (doc.status or "draft").lower() != status_key:
            continue
        filtered.append(doc)

    total = len(filtered)
    reach = await _reach_counts(tenant_id, [d.announcement_id for d in filtered])

    table_rows: list[CommunicationAnnouncementsTableRow] = []
    for doc in filtered:
        status_label, status_tone = _status_presentation(doc.status)
        count = reach.get(doc.announcement_id, 0)
        table_rows.append(
            CommunicationAnnouncementsTableRow(
                announcement_id=doc.announcement_id,
                title=doc.title,
                audience_label=_audience_label(doc),
                channels_label=_channels_label(doc.channels),
                published_label=_published_label(doc),
                reach_label=f"{count:,}" if count else "—",
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/communication/create-announcement?announcement_id={doc.announcement_id}",
            )
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    paged = table_rows[offset : offset + page_size]
    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(paged))
    showing_label = f"Showing {showing_end:,} of {total:,}"

    return CommunicationAnnouncementsManagementPageRead(
        page_title="Announcements Management",
        page_subtitle="Drafts, scheduled and published announcements",
        new_announcement_label="New announcement",
        new_announcement_href="/college-admin/communication/create-announcement",
        search_placeholder="Search announcements",
        audience_filter_label="All audiences",
        status_filter_label="All statuses",
        audience_options=[InstitutionPolicyFilterOption(value=v, label=l) for v, l in _AUDIENCE_FILTERS],
        status_options=[InstitutionPolicyFilterOption(value=v, label=l) for v, l in _STATUS_FILTERS],
        announcements_section_title="Announcements",
        table_headers=_TABLE_HEADERS,
        announcement_rows=paged,
        empty_table_message="No announcements match your filters.",
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