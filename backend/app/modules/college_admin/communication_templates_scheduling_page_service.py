"""Communication templates and scheduled messages (CA 14.10–11)."""

from __future__ import annotations

import math
import re
from collections import defaultdict

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.communication_admin_models import (
    AnnouncementAudience,
    CommunicationTemplate,
    InstitutionAnnouncement,
)
from app.modules.college_admin.communication_audience_notifications_shared import channels_label, short_day
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CommunicationScheduledMessageRow,
    CommunicationScheduledMessagesPageRead,
    CommunicationTemplateManagementRow,
    CommunicationTemplatesManagementPageRead,
    PoliciesPagination,
)

_IST = __import__("zoneinfo").ZoneInfo("Asia/Kolkata")
_TEMPLATE_PAGE_SIZE = 4
_SCHEDULED_PAGE_SIZE = 3

_VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}|\{\s*(\w+)\s*\}")

_AUDIENCE_LABELS: dict[AnnouncementAudience, str] = {
    AnnouncementAudience.ALL: "Everyone",
    AnnouncementAudience.STUDENTS: "All students",
    AnnouncementAudience.FACULTY: "All faculty",
    AnnouncementAudience.PARENTS: "Parents",
    AnnouncementAudience.DEPARTMENT: "Department",
    AnnouncementAudience.CUSTOM: "Custom group",
}

_ROLE_LABELS: dict[Role, str] = {
    Role.COLLEGE_ADMIN: "College Admin",
    Role.FINANCE_STAFF: "Finance Officer",
    Role.ACCOUNTS_STAFF: "Finance Officer",
    Role.HR_STAFF: "HR Officer",
    Role.DEPARTMENT_ADMIN: "Department Admin",
    Role.FACULTY: "Faculty",
}


def _language_label(code: str) -> str:
    mapping = {"en": "English", "hi": "Hindi", "ta": "Tamil"}
    return mapping.get((code or "").lower(), (code or "—").title())


def _variable_count(body: str) -> int:
    if not body:
        return 0
    keys: set[str] = set()
    for match in _VAR_PATTERN.finditer(body):
        key = match.group(1) or match.group(2)
        if key:
            keys.add(key)
    return len(keys)


def _template_status(approval_statuses: list[str]) -> tuple[str, str]:
    lowered = {(s or "pending").lower() for s in approval_statuses}
    if "rejected" in lowered:
        return "Rejected", "error"
    if lowered <= {"approved"}:
        return "Approved", "success"
    if "pending" in lowered:
        return "In review", "warning"
    return "In review", "warning"


def _channels_group_label(channels: list[str]) -> str:
    label = channels_label(channels)
    if not channels:
        return "—"
    if len(channels) >= 4:
        return "All"
    return label


def _paginate(rows: list, page: int, page_size: int):
    total = len(rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    paged = rows[offset : offset + page_size]
    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(paged))
    return paged, total, total_pages, f"{showing_end} of {total}"


def _audience_label(doc: InstitutionAnnouncement) -> str:
    aud = doc.audience
    base = _AUDIENCE_LABELS.get(aud, aud.value.replace("_", " ").title())
    if aud == AnnouncementAudience.CUSTOM and doc.audience_group_id:
        return doc.audience_group_id.replace("_", " ").title()
    if aud == AnnouncementAudience.PARENTS and doc.audience_group_id:
        return doc.audience_group_id.replace("_", " ").title()
    if aud == AnnouncementAudience.STUDENTS and doc.department_scope and doc.department_scope != "all":
        return "Students (scoped)"
    return base


def _send_at_label(when) -> str:
    if when is None:
        return "—"
    local = when.astimezone(_IST) if when.tzinfo else when.replace(tzinfo=_IST)
    return local.strftime("%d %b %H:%M")


def _schedule_status(doc: InstitutionAnnouncement) -> tuple[str, str]:
    if (doc.status or "").lower() == "scheduled":
        return "Scheduled", "info"
    return "Draft", "muted"


def _creator_label(user: User | None) -> str:
    if user is None:
        return "—"
    if user.full_name and user.full_name.strip():
        return user.full_name.strip()
    return _ROLE_LABELS.get(user.role, user.role.value.replace("_", " ").title())


async def get_communication_templates_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _TEMPLATE_PAGE_SIZE,
) -> CommunicationTemplatesManagementPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    templates = await CommunicationTemplate.find(Eq(CommunicationTemplate.tenant_id, tenant_id)).sort("-updated_at").to_list()

    grouped: dict[str, list[CommunicationTemplate]] = defaultdict(list)
    for tmpl in templates:
        grouped[tmpl.template_code].append(tmpl)

    rows: list[CommunicationTemplateManagementRow] = []
    for code, docs in sorted(
        grouped.items(),
        key=lambda item: max(d.updated_at for d in item[1]),
        reverse=True,
    ):
        docs.sort(key=lambda d: d.updated_at, reverse=True)
        primary = docs[0]
        channels = [d.channel for d in docs]
        languages = sorted({_language_label(d.language) for d in docs})
        variables = max(_variable_count(d.body) for d in docs)
        updated = max(d.updated_at for d in docs)
        status_label, status_tone = _template_status([d.approval_status for d in docs])
        template_label = primary.subject or code.replace("_", " ").title()
        rows.append(
            CommunicationTemplateManagementRow(
                row_key=code,
                template_label=template_label,
                channel_label=_channels_group_label(channels),
                language_label=", ".join(languages),
                variables_count=variables,
                updated_label=short_day(updated),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/communication/communication-templates?template={code}",
            )
        )
    paged, total, total_pages, footer = _paginate(rows, page, page_size)

    return CommunicationTemplatesManagementPageRead(
        page_title="Communication Templates",
        page_subtitle="Reusable message templates",
        primary_action_label="New template",
        primary_action_href="/college-admin/communication/communication-templates?create=1",
        templates_section_title="Templates",
        table_headers=["Template", "Channel", "Language", "Variables", "Updated", "Status"],
        template_rows=paged,
        empty_table_message="No communication templates yet.",
        count_footer_label=footer,
        showing_label=f"Showing {min(page_size, total):,} of {total:,}",
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


async def get_communication_scheduled_messages_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _SCHEDULED_PAGE_SIZE,
) -> CommunicationScheduledMessagesPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    docs = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).sort("-updated_at").to_list()
    queued: list[InstitutionAnnouncement] = []
    for doc in docs:
        status = (doc.status or "").lower()
        if status == "published":
            continue
        if status == "scheduled" and doc.scheduled_for:
            queued.append(doc)
        elif status == "draft" and doc.scheduled_for:
            queued.append(doc)

    queued.sort(key=lambda d: d.scheduled_for or d.updated_at, reverse=True)

    actor_ids = {doc.actor_id for doc in queued if doc.actor_id}
    users_by_id: dict = {}
    if actor_ids:
        users = await User.find(In(User.id, list(actor_ids))).to_list()
        users_by_id = {u.id: u for u in users}

    rows: list[CommunicationScheduledMessageRow] = []
    for doc in queued:
        status_label, status_tone = _schedule_status(doc)
        user = users_by_id.get(doc.actor_id) if doc.actor_id else None
        rows.append(
            CommunicationScheduledMessageRow(
                row_key=doc.announcement_id,
                message_label=doc.title,
                audience_label=_audience_label(doc),
                channels_label=channels_label(doc.channels),
                send_at_label=_send_at_label(doc.scheduled_for),
                created_by_label=_creator_label(user),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/communication/create-announcement?announcement_id={doc.announcement_id}",
            )
        )

    paged, total, total_pages, footer = _paginate(rows, page, page_size)

    return CommunicationScheduledMessagesPageRead(
        page_title="Scheduled Messages",
        page_subtitle="Messages queued for later",
        primary_action_label="Schedule message",
        primary_action_href="/college-admin/communication/create-announcement?publish_timing=schedule",
        scheduled_section_title="Scheduled",
        table_headers=["Message", "Audience", "Channels", "Send at", "Created by", "Status"],
        message_rows=paged,
        empty_table_message="No scheduled messages yet.",
        count_footer_label=footer,
        showing_label=f"Showing {min(page_size, total):,} of {total:,}",
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