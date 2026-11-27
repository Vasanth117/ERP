"""Communication administration overview dashboard (CA 14.01)."""

from __future__ import annotations

import math
from calendar import month_name
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.communication_admin_models import (
    CommunicationDeliveryLog,
    CommunicationProviderSettings,
    CommunicationSchedule,
    DeliveryStatus,
    InstitutionAnnouncement,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CommunicationChannelSidebarItem,
    CommunicationDashboardDeliveryRow,
    CommunicationDashboardPageRead,
    PoliciesPagination,
    UserDashboardKpi,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_TABLE_HEADERS = ["Message", "Channel", "Recipients", "Delivered", "Failed", "Status"]

_CHANNEL_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("in_app", "In-app", "info"),
    ("email", "Email", "mail"),
    ("sms", "SMS", "phone"),
    ("whatsapp", "WhatsApp", "send"),
)

def _status_value(status: DeliveryStatus | str) -> str:
    return status.value if isinstance(status, DeliveryStatus) else str(status)


_SENT = frozenset({DeliveryStatus.SENT.value})
_FAILED = frozenset({DeliveryStatus.FAILED.value})


def _channel_label(channel: str) -> str:
    key = (channel or "").lower().replace("-", "_")
    for code, label, _icon in _CHANNEL_CATALOG:
        if code == key:
            return label
    return (channel or "—").replace("_", " ").title()


def _batch_status(delivered: int, failed: int) -> tuple[str, str]:
    if delivered <= 0 and failed > 0:
        return "Failed", "error"
    if failed > 0:
        return "Partial", "warning"
    if delivered > 0:
        return "Complete", "success"
    return "Queued", "muted"


def _provider_presentation(provider: CommunicationProviderSettings | None) -> tuple[str, str, str]:
    if provider is None:
        return "Not configured", "Not configured", "muted"
    mode = str((provider.config or {}).get("mode") or (provider.config or {}).get("environment") or "").lower()
    if mode in {"sandbox", "test", "staging"}:
        return "Sandbox", "Test", "warning"
    if provider.push_enabled:
        return "Live", "Live", "success"
    return "Configured", "Live", "success"


async def get_communication_dashboard_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> CommunicationDashboardPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    month_start = today.replace(day=1)
    month_start_dt = datetime.combine(month_start, datetime.min.time(), tzinfo=_IST)
    if today.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    month_end_dt = datetime.combine(next_month, datetime.min.time(), tzinfo=_IST) - timedelta(seconds=1)
    week_end = now + timedelta(days=7)

    month_logs = await CommunicationDeliveryLog.find(
        Eq(CommunicationDeliveryLog.tenant_id, tenant_id),
        GTE(CommunicationDeliveryLog.created_at, month_start_dt),
        LTE(CommunicationDeliveryLog.created_at, month_end_dt),
    ).to_list()

    sent_count = sum(1 for row in month_logs if _status_value(row.status) in _SENT)
    total_attempts = len(month_logs)
    delivery_rate = (sent_count / total_attempts * 100) if total_attempts else 0.0

    scheduled = await CommunicationSchedule.find(
        Eq(CommunicationSchedule.tenant_id, tenant_id),
        Eq(CommunicationSchedule.executed, False),
        GTE(CommunicationSchedule.run_at, now),
        LTE(CommunicationSchedule.run_at, week_end),
    ).count()
    scheduled += await InstitutionAnnouncement.find(
        Eq(InstitutionAnnouncement.tenant_id, tenant_id),
        Eq(InstitutionAnnouncement.status, "scheduled"),
        GTE(InstitutionAnnouncement.scheduled_for, now),
        LTE(InstitutionAnnouncement.scheduled_for, week_end),
    ).count()

    retryable_failed = await CommunicationDeliveryLog.find(
        Eq(CommunicationDeliveryLog.tenant_id, tenant_id),
        Eq(CommunicationDeliveryLog.status, DeliveryStatus.FAILED),
    ).to_list()
    retryable_failed = [row for row in retryable_failed if row.retry_count < 3]
    failed_total = len(retryable_failed)

    kpis = [
        UserDashboardKpi(
            key="messages_sent",
            label="Messages sent",
            value=f"{total_attempts:,}",
            hint_line=f"{month_name[today.month][:3]} {today.year}",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="delivery_rate",
            label="Delivery rate",
            value=f"{delivery_rate:.1f}%",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="scheduled",
            label="Scheduled",
            value=f"{scheduled:,}",
            hint_line="Next 7 days",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="failed",
            label="Failed",
            value=f"{failed_total:,}",
            hint_line="Retry available" if failed_total else "",
            hint_tone="warning" if failed_total else "muted",
        ),
    ]

    all_logs = await CommunicationDeliveryLog.find(Eq(CommunicationDeliveryLog.tenant_id, tenant_id)).to_list()
    announcements = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).to_list()
    title_by_id = {a.announcement_id: a.title for a in announcements}

    grouped: dict[tuple[str, str], list[CommunicationDeliveryLog]] = defaultdict(list)
    for row in all_logs:
        grouped[(row.announcement_id, row.channel)].append(row)

    batch_rows: list[tuple[datetime, CommunicationDashboardDeliveryRow]] = []
    for (announcement_id, channel), logs in grouped.items():
        recipients = len(logs)
        delivered = 0
        failed = 0
        latest = logs[0].created_at
        for log in logs:
            if log.created_at and log.created_at > latest:
                latest = log.created_at
            status = _status_value(log.status)
            if status in _SENT:
                delivered += 1
            elif status in _FAILED:
                failed += 1
        status_label, status_tone = _batch_status(delivered, failed)
        title = title_by_id.get(announcement_id) or announcement_id
        batch_rows.append(
            (
                latest,
                CommunicationDashboardDeliveryRow(
                    batch_key=f"{announcement_id}:{channel}",
                    message_label=title,
                    channel_label=_channel_label(channel),
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

    providers = await CommunicationProviderSettings.find(Eq(CommunicationProviderSettings.tenant_id, tenant_id)).to_list()
    provider_by_channel = {p.channel: p for p in providers}
    channel_items: list[CommunicationChannelSidebarItem] = []
    channel_hrefs = {
        "in_app": "/college-admin/communication/communication-dashboard",
        "email": "/college-admin/communication/email-communication",
        "sms": "/college-admin/communication/sms-communication",
        "whatsapp": "/college-admin/communication/whatsapp-communication",
    }
    for channel_key, title, icon_key in _CHANNEL_CATALOG:
        provider = provider_by_channel.get(channel_key)
        subtitle, badge, tone = _provider_presentation(provider)
        channel_items.append(
            CommunicationChannelSidebarItem(
                channel_key=channel_key,
                title=title,
                subtitle_line=subtitle,
                status_label=badge,
                status_tone=tone,
                icon_key=icon_key,
                href=channel_hrefs.get(channel_key, "/college-admin/communication/communication-dashboard"),
            )
        )

    total_pages = math.ceil(total_batches / page_size) if total_batches else 0
    showing_end = min(total_batches, offset + len(page_batches))
    showing_label = f"Showing {showing_end:,} of {total_batches:,}"

    return CommunicationDashboardPageRead(
        page_title="Communication Dashboard",
        page_subtitle=f"Messages sent in {month_name[today.month]} {today.year}",
        create_announcement_label="Create announcement",
        create_announcement_href="/college-admin/communication/create-announcement",
        kpis=kpis,
        deliveries_section_title="Deliveries",
        table_headers=_TABLE_HEADERS,
        delivery_rows=page_batches,
        empty_table_message="No delivery batches recorded yet.",
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_batches,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        channels_section_title="Channels",
        channel_items=channel_items,
        generated_at=now,
    )