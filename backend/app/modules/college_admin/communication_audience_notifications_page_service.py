"""Audience notification pages — students, faculty, parents (CA 14.04–06)."""

from __future__ import annotations

import math

from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.communication_admin_models import (
    CommunicationDeliveryLog,
    DeliveryStatus,
    InstitutionAnnouncement,
)
from app.modules.college_admin.communication_audience_notifications_shared import (
    announcement_in_segment,
    announcements_for_segment,
    audience_row_label,
    batch_status,
    channel_label,
    channels_label,
    delivery_batches,
    month_window,
    parent_reach_stats,
    short_day,
    status_value,
    student_read_stats,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CommunicationAudienceDeliveryRow,
    CommunicationFacultyNotificationRow,
    CommunicationParentMessageRow,
    CommunicationStudentNotificationsPageRead,
    CommunicationFacultyNotificationsPageRead,
    CommunicationParentCommunicationPageRead,
    PoliciesPagination,
    UserDashboardKpi,
)

_IST = __import__("zoneinfo").ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3


def _segment_new_href(segment: str) -> str:
    audience = {"students": "students", "faculty": "faculty", "parents": "parents"}.get(segment, "students")
    return f"/college-admin/communication/create-announcement?audience={audience}"


async def _scheduled_count(tenant_id, docs: list[InstitutionAnnouncement], now) -> int:
    week_end = now + __import__("datetime").timedelta(days=7)
    count = sum(1 for d in docs if d.status == "scheduled" and d.scheduled_for and now <= d.scheduled_for <= week_end)
    return count


async def _month_sent_logs(tenant_id, announcement_ids: set[str], month_start, month_end) -> int:
    if not announcement_ids:
        return 0
    logs = await CommunicationDeliveryLog.find(
        Eq(CommunicationDeliveryLog.tenant_id, tenant_id),
        GTE(CommunicationDeliveryLog.created_at, month_start),
        LTE(CommunicationDeliveryLog.created_at, month_end),
    ).to_list()
    return sum(1 for log in logs if log.announcement_id in announcement_ids and status_value(log.status) == DeliveryStatus.SENT.value)


async def get_communication_student_notifications_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> CommunicationStudentNotificationsPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    month_start, month_end = month_window(today)

    docs = await announcements_for_segment(tenant_id, "students")
    ids = {d.announcement_id for d in docs}
    sent_month = await _month_sent_logs(tenant_id, ids, month_start, month_end)
    total_reads, read_count, unread_stale = await student_read_stats(tenant_id, month_start, month_end)
    read_rate = (read_count / total_reads * 100) if total_reads else 0.0
    scheduled = await _scheduled_count(tenant_id, docs, now)

    batches = await delivery_batches(tenant_id, ids)
    title_by_id = {d.announcement_id: d.title for d in docs}
    rows: list[tuple[str, CommunicationAudienceDeliveryRow]] = []
    for (aid, channel), stats in batches.items():
        status_label, status_tone = batch_status(stats["delivered"], stats["failed"])
        rows.append(
            (
                aid,
                CommunicationAudienceDeliveryRow(
                    row_key=f"{aid}:{channel}",
                    message_label=title_by_id.get(aid, aid),
                    channel_label=channel_label(channel),
                    recipients_count=stats["recipients"],
                    delivered_count=stats["delivered"],
                    failed_count=stats["failed"],
                    status_label=status_label,
                    status_tone=status_tone,
                    detail_href=f"/college-admin/communication/delivery-status-monitoring?announcement_id={aid}&channel={channel}",
                ),
            )
        )
    rows.sort(key=lambda item: item[0], reverse=True)
    table_rows = [r for _k, r in rows]

    return _student_page_response(
        page=page,
        page_size=page_size,
        now=now,
        kpis=[
            UserDashboardKpi(key="sent_month", label="Sent this month", value=f"{sent_month:,}", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="read_rate", label="Read rate", value=f"{read_rate:.0f}%", hint_line="", hint_tone="muted"),
            UserDashboardKpi(
                key="unread_stale",
                label="Unread over 3 days",
                value=f"{unread_stale:,}",
                hint_line="",
                hint_tone="warning" if unread_stale else "muted",
            ),
            UserDashboardKpi(
                key="scheduled",
                label="Scheduled",
                value=f"{scheduled:,}",
                hint_line="",
                hint_tone="info" if scheduled else "muted",
            ),
        ],
        table_rows=table_rows,
    )


def _paginate_table_rows(table_rows: list, page: int, page_size: int):
    total = len(table_rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    paged = table_rows[offset : offset + page_size]
    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(paged))
    return paged, total, total_pages, showing_end, f"Showing {showing_end:,} of {total:,}"


def _student_page_response(*, page, page_size, now, kpis, table_rows):
    paged, total, total_pages, _, showing_label = _paginate_table_rows(table_rows, page, page_size)
    return CommunicationStudentNotificationsPageRead(
        page_title="Student Notifications",
        page_subtitle="Messages to students",
        new_notification_label="New notification",
        new_notification_href=_segment_new_href("students"),
        kpis=kpis,
        deliveries_section_title="Deliveries",
        table_headers=["Message", "Channel", "Recipients", "Delivered", "Failed", "Status"],
        delivery_rows=paged,
        empty_table_message="No student deliveries recorded yet.",
        showing_label=showing_label,
        count_footer_label=f"{min(page_size, total)} of {total}" if total else "0 of 0",
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


async def get_communication_faculty_notifications_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> CommunicationFacultyNotificationsPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    month_start, month_end = month_window(today)

    docs = await announcements_for_segment(tenant_id, "faculty")
    ids = {d.announcement_id for d in docs}
    sent_month = await _month_sent_logs(tenant_id, ids, month_start, month_end)
    scheduled = await _scheduled_count(tenant_id, docs, now)
    pending_ack = sum(1 for d in docs if d.status == "published" and d.pin_to_dashboard)

    batch_stats = await delivery_batches(tenant_id, ids)
    delivered_by_aid: dict[str, int] = {}
    recipients_by_aid: dict[str, int] = {}
    for (aid, _channel), stats in batch_stats.items():
        delivered_by_aid[aid] = delivered_by_aid.get(aid, 0) + stats["delivered"]
        recipients_by_aid[aid] = recipients_by_aid.get(aid, 0) + stats["recipients"]

    read_rate = 0.0
    if ids:
        read_rate = (sum(delivered_by_aid.values()) / max(sent_month, 1) * 100) if sent_month else 0.0
        read_rate = min(read_rate, 100.0)

    table_rows: list[CommunicationFacultyNotificationRow] = []
    for doc in docs:
        if doc.status not in {"published", "scheduled"}:
            continue
        sent = short_day(doc.published_at or doc.scheduled_for or doc.updated_at)
        delivered = delivered_by_aid.get(doc.announcement_id, 0)
        recipients = recipients_by_aid.get(doc.announcement_id, 0)
        audience = audience_row_label(doc, "faculty")
        read_label = f"{delivered:,} of {recipients:,}" if recipients else "—"
        ack = "Required" if doc.pin_to_dashboard else "Not required"
        table_rows.append(
            CommunicationFacultyNotificationRow(
                row_key=doc.announcement_id,
                notification_label=doc.title,
                audience_label=audience,
                sent_label=sent,
                read_label=read_label,
                acknowledged_label=ack,
                detail_href=f"/college-admin/communication/create-announcement?announcement_id={doc.announcement_id}",
            )
        )

    paged, total, total_pages, showing_end, showing_label = _paginate_table_rows(table_rows, page, page_size)
    count_footer = f"{showing_end} of {total}"

    return CommunicationFacultyNotificationsPageRead(
        page_title="Faculty Notifications",
        page_subtitle="Messages to faculty and staff",
        new_notification_label="New notification",
        new_notification_href=_segment_new_href("faculty"),
        kpis=[
            UserDashboardKpi(key="sent_month", label="Sent this month", value=f"{sent_month:,}", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="read_rate", label="Read rate", value=f"{read_rate:.0f}%", hint_line="", hint_tone="muted"),
            UserDashboardKpi(
                key="pending_ack",
                label="Pending acknowledgement",
                value=f"{pending_ack:,}",
                hint_line="",
                hint_tone="warning" if pending_ack else "muted",
            ),
            UserDashboardKpi(key="scheduled", label="Scheduled", value=f"{scheduled:,}", hint_line="", hint_tone="info" if scheduled else "muted"),
        ],
        recent_section_title="Recent",
        table_headers=["Notification", "Audience", "Sent", "Read", "Acknowledged"],
        notification_rows=paged,
        empty_table_message="No faculty notifications yet.",
        showing_label=showing_label,
        count_footer_label=count_footer,
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


async def get_communication_parent_communication_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> CommunicationParentCommunicationPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    month_start, month_end = month_window(today)

    docs = await announcements_for_segment(tenant_id, "parents")
    ids = {d.announcement_id for d in docs}
    sent_month = await _month_sent_logs(tenant_id, ids, month_start, month_end)
    reachable, student_count, opted_out, invalid, reach_hint = await parent_reach_stats(tenant_id)

    batches = await delivery_batches(tenant_id, ids)
    title_by_id = {d.announcement_id: d.title for d in docs}
    channels_by_id = {d.announcement_id: d.channels for d in docs}

    grouped_by_aid: dict[str, dict[str, int]] = {}
    for (aid, _channel), stats in batches.items():
        bucket = grouped_by_aid.setdefault(aid, {"delivered": 0, "recipients": 0})
        bucket["delivered"] += stats["delivered"]
        bucket["recipients"] += stats["recipients"]

    table_rows: list[CommunicationParentMessageRow] = []
    for doc in docs:
        if doc.status not in {"published", "scheduled"}:
            continue
        stats = grouped_by_aid.get(doc.announcement_id, {"delivered": 0, "recipients": 0})
        delivered_label = (
            f"{stats['delivered']:,} of {stats['recipients']:,}"
            if stats["recipients"]
            else "—"
        )
        table_rows.append(
            CommunicationParentMessageRow(
                row_key=doc.announcement_id,
                message_label=doc.title,
                audience_label=audience_row_label(doc, "parents"),
                channel_label=channels_label(doc.channels),
                sent_label=short_day(doc.published_at or doc.scheduled_for or doc.updated_at),
                delivered_label=delivered_label,
                detail_href=f"/college-admin/communication/create-announcement?announcement_id={doc.announcement_id}",
            )
        )

    paged, total, total_pages, showing_end, showing_label = _paginate_table_rows(table_rows, page, page_size)

    return CommunicationParentCommunicationPageRead(
        page_title="Parent Communication",
        page_subtitle="Messages to parents and guardians",
        new_message_label="New message",
        new_message_href=_segment_new_href("parents"),
        kpis=[
            UserDashboardKpi(
                key="parents_reachable",
                label="Parents reachable",
                value=f"{reachable:,}",
                hint_line=reach_hint,
                hint_tone="info" if reach_hint else "muted",
            ),
            UserDashboardKpi(key="opted_out", label="Opted out", value=f"{opted_out:,}", hint_line="", hint_tone="muted"),
            UserDashboardKpi(
                key="invalid_contacts",
                label="Invalid contacts",
                value=f"{invalid:,}",
                hint_line="Need update" if invalid else "",
                hint_tone="warning" if invalid else "muted",
            ),
            UserDashboardKpi(key="sent_month", label="Sent this month", value=f"{sent_month:,}", hint_line="", hint_tone="muted"),
        ],
        recent_section_title="Recent",
        table_headers=["Message", "Audience", "Channel", "Sent", "Delivered"],
        message_rows=paged,
        empty_table_message="No parent messages yet.",
        showing_label=showing_label,
        count_footer_label=f"{showing_end} of {total}",
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