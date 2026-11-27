"""Delivery status monitoring and communication history (CA 14.12–13)."""

from __future__ import annotations

import csv
import io
import math
from calendar import month_name
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.communication_admin_models import (
    AnnouncementAudience,
    CommunicationDeliveryLog,
    DeliveryStatus,
    InstitutionAnnouncement,
)
from app.modules.college_admin.communication_audience_notifications_shared import batch_status, channel_label, channels_label
from app.modules.college_admin.communication_announcements_management_page_service import (
    _channels_label,
    _published_label,
    _reach_counts,
    _status_presentation,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CommunicationAnnouncementsTableRow,
    CommunicationDashboardDeliveryRow,
    CommunicationDeliveryStatusPageRead,
    CommunicationHistoryPageRead,
    InstitutionPolicyFilterOption,
    PoliciesPagination,
    UserDashboardKpi,
)

_IST = ZoneInfo("Asia/Kolkata")
_MONITORING_PAGE_SIZE = 3
_HISTORY_PAGE_SIZE = 4
_HISTORY_TABLE_HEADERS = ["Announcement", "Audience", "Channels", "Published", "Reach", "Status"]

_AUDIENCE_LABELS: dict[AnnouncementAudience, str] = {
    AnnouncementAudience.ALL: "Everyone",
    AnnouncementAudience.STUDENTS: "All students",
    AnnouncementAudience.FACULTY: "All faculty",
    AnnouncementAudience.PARENTS: "Parents",
    AnnouncementAudience.DEPARTMENT: "Department",
    AnnouncementAudience.CUSTOM: "Custom group",
}

_CHANNEL_FILTERS = [
    ("", "All channels"),
    ("in_app", "App"),
    ("email", "Email"),
    ("sms", "SMS"),
    ("whatsapp", "WhatsApp"),
]

_SENT = frozenset({DeliveryStatus.SENT.value, "sent"})
_FAILED = frozenset({DeliveryStatus.FAILED.value, "failed"})
_QUEUED = frozenset({DeliveryStatus.QUEUED.value, DeliveryStatus.RETRYING.value, "queued", "retrying"})


def _status_value(status: DeliveryStatus | str) -> str:
    return status.value if isinstance(status, DeliveryStatus) else str(status)


def _audience_label(doc: InstitutionAnnouncement) -> str:
    base = _AUDIENCE_LABELS.get(doc.audience, doc.audience.value.replace("_", " ").title())
    if doc.audience == AnnouncementAudience.CUSTOM and doc.audience_group_id:
        return doc.audience_group_id.replace("_", " ").title()
    if doc.audience == AnnouncementAudience.PARENTS and doc.audience_group_id:
        return doc.audience_group_id.replace("_", " ").title()
    if doc.audience == AnnouncementAudience.STUDENTS and doc.department_scope and doc.department_scope != "all":
        return "Students (scoped)"
    if doc.audience == AnnouncementAudience.ALL:
        ch_count = len({(c or "").lower() for c in (doc.channels or [])})
        if ch_count >= 3:
            return "Everyone"
    return base


def _today_bounds(now: datetime) -> tuple[datetime, datetime]:
    local = now.astimezone(_IST)
    start = datetime.combine(local.date(), datetime.min.time(), tzinfo=_IST)
    end = start + timedelta(days=1) - timedelta(microseconds=1)
    return start, end


def _month_bounds(month_key: str | None, now: datetime) -> tuple[datetime, datetime, str]:
    local = now.astimezone(_IST)
    if month_key and len(month_key) >= 7:
        try:
            year_s, month_s = month_key.split("-", 1)
            year, month = int(year_s), int(month_s)
            if 1 <= month <= 12:
                start = datetime(year, month, 1, tzinfo=_IST)
                if month == 12:
                    next_start = datetime(year + 1, 1, 1, tzinfo=_IST)
                else:
                    next_start = datetime(year, month + 1, 1, tzinfo=_IST)
                end = next_start - timedelta(microseconds=1)
                label = f"{month_name[month][:3]} {year}"
                return start, end, label
        except ValueError:
            pass
    start = datetime(local.year, local.month, 1, tzinfo=_IST)
    if local.month == 12:
        next_start = datetime(local.year + 1, 1, 1, tzinfo=_IST)
    else:
        next_start = datetime(local.year, local.month + 1, 1, tzinfo=_IST)
    end = next_start - timedelta(microseconds=1)
    label = f"{month_name[local.month][:3]} {local.year}"
    return start, end, label


def _month_options(now: datetime, count: int = 12) -> list[InstitutionPolicyFilterOption]:
    local = now.astimezone(_IST)
    options: list[InstitutionPolicyFilterOption] = []
    year, month = local.year, local.month
    for _ in range(count):
        value = f"{year:04d}-{month:02d}"
        label = f"{month_name[month][:3]} {year}"
        options.append(InstitutionPolicyFilterOption(value=value, label=label))
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    return options


def _doc_in_month(doc: InstitutionAnnouncement, start: datetime, end: datetime) -> bool:
    for when in (doc.published_at, doc.scheduled_for, doc.updated_at, doc.created_at):
        if when is None:
            continue
        local = when.astimezone(_IST) if when.tzinfo else when.replace(tzinfo=_IST)
        if start <= local <= end:
            return True
    return False


def _avg_delay_seconds(logs: list[CommunicationDeliveryLog]) -> float:
    delays: list[float] = []
    for log in logs:
        if _status_value(log.status) not in _SENT:
            continue
        delta = (log.updated_at - log.created_at).total_seconds()
        if delta >= 0:
            delays.append(delta)
    if not delays:
        return 0.0
    return sum(delays) / len(delays)


async def get_communication_delivery_status_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _MONITORING_PAGE_SIZE,
) -> CommunicationDeliveryStatusPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    day_start, day_end = _today_bounds(now)

    all_logs = await CommunicationDeliveryLog.find(Eq(CommunicationDeliveryLog.tenant_id, tenant_id)).to_list()
    in_queue = sum(1 for log in all_logs if _status_value(log.status) in _QUEUED)
    delivered_today = sum(
        1
        for log in all_logs
        if _status_value(log.status) in _SENT and day_start <= log.updated_at.astimezone(_IST) <= day_end
    )
    failed_today = sum(
        1
        for log in all_logs
        if _status_value(log.status) in _FAILED and day_start <= log.updated_at.astimezone(_IST) <= day_end
    )
    today_logs = [
        log
        for log in all_logs
        if day_start <= log.updated_at.astimezone(_IST) <= day_end and _status_value(log.status) in _SENT
    ]
    avg_delay = _avg_delay_seconds(today_logs)
    delay_label = f"{int(round(avg_delay))} sec" if avg_delay else "—"

    announcements = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).to_list()
    title_by_id = {a.announcement_id: a.title for a in announcements}

    grouped: dict[tuple[str, str], list[CommunicationDeliveryLog]] = defaultdict(list)
    for row in all_logs:
        grouped[(row.announcement_id, row.channel)].append(row)

    batch_rows: list[tuple[datetime, CommunicationDashboardDeliveryRow]] = []
    for (announcement_id, channel), logs in grouped.items():
        recipients = len(logs)
        delivered = sum(1 for log in logs if _status_value(log.status) in _SENT)
        failed = sum(1 for log in logs if _status_value(log.status) in _FAILED)
        latest = max(log.updated_at for log in logs)
        status_label, status_tone = batch_status(delivered, failed)
        title = title_by_id.get(announcement_id) or announcement_id
        batch_rows.append(
            (
                latest,
                CommunicationDashboardDeliveryRow(
                    batch_key=f"{announcement_id}:{channel}",
                    message_label=title,
                    channel_label=channel_label(channel),
                    recipients_count=recipients,
                    delivered_count=delivered,
                    failed_count=failed,
                    status_label=status_label,
                    status_tone=status_tone,
                    detail_href=f"/college-admin/communication/delivery-status-monitoring?announcement_id={announcement_id}&channel={channel}",
                ),
            )
        )

    batch_rows.sort(key=lambda item: item[0], reverse=True)
    total_batches = len(batch_rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    page_batches = [row for _when, row in batch_rows[offset : offset + page_size]]
    total_pages = math.ceil(total_batches / page_size) if total_batches else 0
    showing_end = min(total_batches, offset + len(page_batches))
    showing_label = f"Showing {showing_end:,} of {total_batches:,}"

    failed_count = sum(1 for log in all_logs if _status_value(log.status) in _FAILED)

    return CommunicationDeliveryStatusPageRead(
        page_title="Delivery Status Monitoring",
        page_subtitle="Track sends and retry failures",
        retry_action_label="Retry failed",
        retry_enabled=failed_count > 0,
        kpis=[
            UserDashboardKpi(key="in_queue", label="In queue", value=f"{in_queue:,}", hint_line="", hint_tone="muted"),
            UserDashboardKpi(
                key="delivered_today",
                label="Delivered today",
                value=f"{delivered_today:,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="failed_today",
                label="Failed today",
                value=f"{failed_today:,}",
                hint_line="",
                hint_tone="warning" if failed_today else "muted",
            ),
            UserDashboardKpi(key="avg_delay", label="Average delay", value=delay_label, hint_line="", hint_tone="muted"),
        ],
        deliveries_section_title="Deliveries",
        table_headers=["Message", "Channel", "Recipients", "Delivered", "Failed", "Status"],
        delivery_rows=page_batches,
        empty_table_message="No delivery batches recorded yet.",
        showing_label=showing_label,
        count_footer_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_batches,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )


async def _filter_history_docs(
    tenant_id,
    *,
    search: str | None,
    month: str | None,
    channel: str | None,
    sender: str | None,
    now: datetime,
) -> tuple[list[InstitutionAnnouncement], dict]:
    docs = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).sort("-updated_at").to_list()
    month_start, month_end, _ = _month_bounds(month, now)
    needle = (search or "").strip().lower()
    channel_key = (channel or "").strip().lower()
    sender_key = (sender or "").strip()

    actor_ids = {doc.actor_id for doc in docs if doc.actor_id}
    users_by_id: dict = {}
    if actor_ids:
        users = await User.find(In(User.id, list(actor_ids))).to_list()
        users_by_id = {u.id: u for u in users}

    filtered: list[InstitutionAnnouncement] = []
    for doc in docs:
        if not _doc_in_month(doc, month_start, month_end):
            continue
        if channel_key and channel_key not in {(c or "").lower().replace("-", "_") for c in (doc.channels or [])}:
            continue
        if sender_key and doc.actor_id and str(doc.actor_id) != sender_key:
            continue
        if needle:
            title_hit = needle in (doc.title or "").lower()
            id_hit = needle in (doc.announcement_id or "").lower()
            actor = users_by_id.get(doc.actor_id) if doc.actor_id else None
            sender_hit = actor and needle in (actor.full_name or "").lower()
            if not title_hit and not id_hit and not sender_hit:
                continue
        filtered.append(doc)
    return filtered, users_by_id


async def get_communication_history_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _HISTORY_PAGE_SIZE,
    search: str | None = None,
    month: str | None = None,
    channel: str | None = None,
    sender: str | None = None,
) -> CommunicationHistoryPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    filtered, users_by_id = await _filter_history_docs(
        tenant_id,
        search=search,
        month=month,
        channel=channel,
        sender=sender,
        now=now,
    )
    total = len(filtered)
    reach = await _reach_counts(tenant_id, [d.announcement_id for d in filtered])

    table_rows: list[CommunicationAnnouncementsTableRow] = []
    for doc in filtered:
        status_label, status_tone = _status_presentation(doc.status)
        count = reach.get(doc.announcement_id, 0)
        channels = _channels_label(doc.channels)
        table_rows.append(
            CommunicationAnnouncementsTableRow(
                announcement_id=doc.announcement_id,
                title=doc.title,
                audience_label=_audience_label(doc),
                channels_label=channels,
                published_label=_published_label(doc),
                reach_label=f"{count:,}" if count and doc.status == "published" else "—",
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

    all_docs = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).to_list()
    actor_ids_all = {doc.actor_id for doc in all_docs if doc.actor_id}
    if actor_ids_all:
        for user in await User.find(In(User.id, list(actor_ids_all))).to_list():
            users_by_id[user.id] = user

    sender_options = [InstitutionPolicyFilterOption(value="", label="All senders")]
    for doc in all_docs:
        if not doc.actor_id:
            continue
        uid = str(doc.actor_id)
        if any(opt.value == uid for opt in sender_options):
            continue
        user = users_by_id.get(doc.actor_id)
        label = user.full_name if user and user.full_name else uid
        if user and not user.full_name:
            label = user.role.value.replace("_", " ").title()
        sender_options.append(InstitutionPolicyFilterOption(value=uid, label=label))
    sender_options[1:] = sorted(sender_options[1:], key=lambda o: o.label.lower())

    _, _, month_label = _month_bounds(month, now)

    return CommunicationHistoryPageRead(
        page_title="Communication History",
        page_subtitle="Audit trail of messages",
        export_label="Export",
        export_api_path="/college-admin/communication-administration/history/export",
        search_placeholder="Search message, sender or recipient",
        month_filter_label=month_label,
        channel_filter_label="All channels",
        sender_filter_label="All senders",
        month_options=_month_options(now),
        channel_options=[InstitutionPolicyFilterOption(value=v, label=l) for v, l in _CHANNEL_FILTERS],
        sender_options=sender_options,
        announcements_section_title="Announcements",
        table_headers=_HISTORY_TABLE_HEADERS,
        announcement_rows=paged,
        empty_table_message="No messages match your filters.",
        showing_label=showing_label,
        count_footer_label=showing_label,
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


async def export_communication_history_csv(
    scope: AccessScope,
    *,
    search: str | None = None,
    month: str | None = None,
    channel: str | None = None,
    sender: str | None = None,
) -> str:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    filtered, _ = await _filter_history_docs(
        tenant_id,
        search=search,
        month=month,
        channel=channel,
        sender=sender,
        now=now,
    )
    reach = await _reach_counts(tenant_id, [d.announcement_id for d in filtered])
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Announcement", "Audience", "Channels", "Published", "Reach", "Status"])
    for doc in filtered:
        status_label, _ = _status_presentation(doc.status)
        count = reach.get(doc.announcement_id, 0)
        writer.writerow(
            [
                doc.title,
                _audience_label(doc),
                _channels_label(doc.channels),
                _published_label(doc),
                f"{count:,}" if count and doc.status == "published" else "—",
                status_label,
            ]
        )
    return buffer.getvalue()