"""Communication channel pages — email, SMS, WhatsApp (CA 14.07–09)."""

from __future__ import annotations

import math
from collections import defaultdict

from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.communication_admin_models import (
    CommunicationDeliveryLog,
    CommunicationProviderSettings,
    CommunicationTemplate,
    DeliveryStatus,
    InstitutionAnnouncement,
)
from app.modules.college_admin.communication_audience_notifications_shared import (
    audience_row_label,
    batch_status,
    month_window,
    short_day,
    status_value,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CommunicationChannelAlertBanner,
    CommunicationEmailCampaignRow,
    CommunicationEmailChannelPageRead,
    CommunicationSmsBatchRow,
    CommunicationSmsChannelPageRead,
    CommunicationWhatsappChannelPageRead,
    CommunicationWhatsappTemplateRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.students.student_portal_models import StudentNotificationReadStatus

_IST = __import__("zoneinfo").ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3


def _audience_label_for_doc(doc: InstitutionAnnouncement) -> str:
    from app.modules.college_admin.communication_admin_models import AnnouncementAudience

    aud = doc.audience.value if hasattr(doc.audience, "value") else str(doc.audience)
    if aud == AnnouncementAudience.STUDENTS.value:
        return audience_row_label(doc, "students")
    if aud == AnnouncementAudience.FACULTY.value:
        return audience_row_label(doc, "faculty")
    if aud in {AnnouncementAudience.PARENTS.value, AnnouncementAudience.CUSTOM.value}:
        return audience_row_label(doc, "parents")
    if aud == AnnouncementAudience.ALL.value:
        return "Everyone"
    return audience_row_label(doc, "students")


def _channel_key(name: str) -> str:
    return (name or "").lower().replace("-", "_")


async def _provider(tenant_id, channel: str) -> CommunicationProviderSettings | None:
    return await CommunicationProviderSettings.find_one(
        Eq(CommunicationProviderSettings.tenant_id, tenant_id),
        Eq(CommunicationProviderSettings.channel, channel),
    )


async def _logs_for_channel(tenant_id, channel: str, *, month_start=None, month_end=None) -> list[CommunicationDeliveryLog]:
    query = CommunicationDeliveryLog.find(Eq(CommunicationDeliveryLog.tenant_id, tenant_id))
    logs = await query.to_list()
    key = _channel_key(channel)
    filtered = [log for log in logs if _channel_key(log.channel) == key]
    if month_start and month_end:
        filtered = [log for log in filtered if month_start <= log.created_at <= month_end]
    return filtered


def _announcements_using_channel(docs: list[InstitutionAnnouncement], channel: str) -> list[InstitutionAnnouncement]:
    key = _channel_key(channel)
    return [d for d in docs if key in {_channel_key(c) for c in (d.channels or [])}]


async def _read_count_for_announcement(tenant_id, announcement_id: str) -> int:
    rows = await StudentNotificationReadStatus.find(
        Eq(StudentNotificationReadStatus.tenant_id, tenant_id),
    ).to_list()
    prefix = announcement_id
    return sum(1 for row in rows if row.read_at and row.notification_key.startswith(prefix))


def _paginate(rows: list, page: int, page_size: int):
    total = len(rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    paged = rows[offset : offset + page_size]
    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(paged))
    return paged, total, total_pages, showing_end, f"{showing_end} of {total}"


async def get_communication_email_channel_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> CommunicationEmailChannelPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    month_start, month_end = month_window(today)
    channel = "email"

    provider = await _provider(tenant_id, channel)
    config = provider.config if provider else {}
    sender_domain = str(config.get("sender_domain") or config.get("from_domain") or "—")
    domain_verified = bool(config.get("domain_verified", provider.push_enabled if provider else False))
    domain_hint = "Verified" if domain_verified else "Unverified"
    domain_tone = "success" if domain_verified else "warning"

    month_logs = await _logs_for_channel(tenant_id, channel, month_start=month_start, month_end=month_end)
    sent = len(month_logs)
    delivered = sum(1 for log in month_logs if status_value(log.status) == DeliveryStatus.SENT.value)
    bounced = sum(1 for log in month_logs if status_value(log.status) == DeliveryStatus.FAILED.value)
    delivery_rate = (delivered / sent * 100) if sent else 0.0

    announcements = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).to_list()
    email_ann = _announcements_using_channel(announcements, channel)
    logs_all = await _logs_for_channel(tenant_id, channel)
    stats_by_aid: dict[str, dict[str, int]] = defaultdict(lambda: {"recipients": 0, "delivered": 0, "failed": 0})
    for log in logs_all:
        bucket = stats_by_aid[log.announcement_id]
        bucket["recipients"] += 1
        if status_value(log.status) == DeliveryStatus.SENT.value:
            bucket["delivered"] += 1
        elif status_value(log.status) == DeliveryStatus.FAILED.value:
            bucket["failed"] += 1

    campaign_rows: list[CommunicationEmailCampaignRow] = []
    for doc in email_ann:
        if doc.status not in {"published", "scheduled"}:
            continue
        stats = stats_by_aid.get(doc.announcement_id, {"recipients": 0, "delivered": 0, "failed": 0})
        opened_reads = await _read_count_for_announcement(tenant_id, doc.announcement_id)
        opened_pct = int(opened_reads / stats["delivered"] * 100) if stats["delivered"] else 0
        opened_pct = min(opened_pct, 100)
        status_label, status_tone = batch_status(stats["delivered"], stats["failed"])
        campaign_rows.append(
            CommunicationEmailCampaignRow(
                row_key=doc.announcement_id,
                campaign_label=doc.title,
                audience_label=_audience_label_for_doc(doc),
                sent_label=short_day(doc.published_at or doc.scheduled_for or doc.updated_at),
                opened_label=f"{opened_pct}%",
                bounced_count=stats["failed"],
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/communication/create-announcement?announcement_id={doc.announcement_id}",
            )
        )
    campaign_rows.sort(key=lambda r: r.sent_label, reverse=True)

    paged, total, total_pages, _, footer = _paginate(campaign_rows, page, page_size)

    return CommunicationEmailChannelPageRead(
        page_title="Email Communication",
        page_subtitle="Email delivery and sender setup",
        primary_action_label="New email campaign",
        primary_action_href="/college-admin/communication/create-announcement?audience=students&preset_channels=email",
        kpis=[
            UserDashboardKpi(key="sent_month", label="Sent this month", value=f"{sent:,}", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="delivered", label="Delivered", value=f"{delivery_rate:.1f}%", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="bounced", label="Bounced", value=f"{bounced:,}", hint_line="", hint_tone="warning" if bounced else "muted"),
            UserDashboardKpi(
                key="sender_domain",
                label="Sender domain",
                value=sender_domain,
                hint_line=domain_hint,
                hint_tone=domain_tone,
            ),
        ],
        campaigns_section_title="Campaigns",
        table_headers=["Campaign", "Audience", "Sent", "Opened", "Bounced", "Status"],
        campaign_rows=paged,
        empty_table_message="No email campaigns yet.",
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


async def get_communication_sms_channel_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> CommunicationSmsChannelPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    month_start, month_end = month_window(today)
    channel = "sms"

    provider = await _provider(tenant_id, channel)
    config = provider.config if provider else {}
    credits_left = int(config.get("credits_remaining") or config.get("credits_left") or 0)

    month_logs = await _logs_for_channel(tenant_id, channel, month_start=month_start, month_end=month_end)
    sent = len(month_logs)
    delivered = sum(1 for log in month_logs if status_value(log.status) == DeliveryStatus.SENT.value)
    failed = sum(1 for log in month_logs if status_value(log.status) == DeliveryStatus.FAILED.value)
    delivery_rate = (delivered / sent * 100) if sent else 0.0

    logs_all = await _logs_for_channel(tenant_id, channel)
    announcements = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).to_list()
    title_by_id = {a.announcement_id: a.title for a in announcements}

    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"recipients": 0, "delivered": 0, "failed": 0})
    batch_labels: dict[str, str] = {}
    for log in logs_all:
        batch_key = log.log_id.rsplit("_", 1)[0] if "_" in log.log_id else log.log_id
        bucket = grouped[batch_key]
        bucket["recipients"] += 1
        batch_labels[batch_key] = title_by_id.get(log.announcement_id, log.announcement_id)
        if status_value(log.status) == DeliveryStatus.SENT.value:
            bucket["delivered"] += 1
        elif status_value(log.status) == DeliveryStatus.FAILED.value:
            bucket["failed"] += 1

    batch_rows: list[CommunicationSmsBatchRow] = []
    for batch_key, stats in grouped.items():
        status_label, status_tone = batch_status(stats["delivered"], stats["failed"])
        batch_rows.append(
            CommunicationSmsBatchRow(
                row_key=batch_key,
                batch_label=batch_key.upper() if batch_key.startswith("dl_") else batch_key,
                template_label=batch_labels.get(batch_key, "—"),
                recipients_count=stats["recipients"],
                delivered_count=stats["delivered"],
                failed_count=stats["failed"],
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/communication/delivery-status-monitoring?batch={batch_key}",
            )
        )
    batch_rows.sort(key=lambda r: r.batch_label, reverse=True)

    paged, total, total_pages, _, footer = _paginate(batch_rows, page, page_size)

    return CommunicationSmsChannelPageRead(
        page_title="SMS Communication",
        page_subtitle="SMS credits and delivery",
        primary_action_label="New SMS",
        primary_action_href="/college-admin/communication/create-announcement?audience=students&preset_channels=sms",
        kpis=[
            UserDashboardKpi(key="sent_month", label="Sent this month", value=f"{sent:,}", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="delivered", label="Delivered", value=f"{delivery_rate:.1f}%", hint_line="", hint_tone="muted"),
            UserDashboardKpi(
                key="credits",
                label="Credits left",
                value=f"{credits_left:,}" if credits_left else "—",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(key="failed", label="Failed", value=f"{failed:,}", hint_line="", hint_tone="warning" if failed else "muted"),
        ],
        batches_section_title="SMS batches",
        table_headers=["Batch", "Template", "Recipients", "Delivered", "Failed", "Status"],
        batch_rows=paged,
        empty_table_message="No SMS batches yet.",
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


def _language_label(code: str) -> str:
    mapping = {"en": "English", "hi": "Hindi", "ta": "Tamil"}
    return mapping.get((code or "").lower(), (code or "—").title())


def _approval_presentation(status: str) -> tuple[str, str]:
    key = (status or "pending").lower()
    if key == "approved":
        return "Approved", "success"
    if key == "rejected":
        return "Rejected", "error"
    return "Pending", "warning"


async def get_communication_whatsapp_channel_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> CommunicationWhatsappChannelPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    channel = "whatsapp"

    provider = await _provider(tenant_id, channel)
    config = provider.config if provider else {}
    mode = str(config.get("mode") or config.get("environment") or "sandbox").lower()
    sandbox = mode in {"sandbox", "test", "staging"} or not (provider and provider.push_enabled)

    templates = await CommunicationTemplate.find(
        Eq(CommunicationTemplate.tenant_id, tenant_id),
        Eq(CommunicationTemplate.channel, channel),
    ).sort("-updated_at").to_list()

    approved = sum(1 for t in templates if (t.approval_status or "").lower() == "approved")
    pending = sum(1 for t in templates if (t.approval_status or "").lower() != "approved")
    test_messages = int(config.get("test_messages_sent") or config.get("test_messages") or 0)
    opt_ins = int(config.get("opt_ins") or config.get("opt_in_count") or 0)

    template_rows: list[CommunicationWhatsappTemplateRow] = []
    for tmpl in templates:
        status_label, status_tone = _approval_presentation(tmpl.approval_status)
        template_rows.append(
            CommunicationWhatsappTemplateRow(
                row_key=f"{tmpl.template_code}:{tmpl.channel}",
                template_label=tmpl.subject or tmpl.template_code.replace("_", " ").title(),
                category_label=(tmpl.category or "utility").title(),
                language_label=_language_label(tmpl.language),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/communication/communication-templates?template={tmpl.template_code}",
            )
        )

    paged, total, total_pages, _, footer = _paginate(template_rows, page, page_size)

    alert: CommunicationChannelAlertBanner | None = None
    if sandbox:
        alert = CommunicationChannelAlertBanner(
            tone="warning",
            message=(
                "WhatsApp is in sandbox mode. Messages go only to test numbers until the business account "
                "is verified. Configure under Integrations."
            ),
            link_label="Open Integrations",
            link_href="/college-admin/integrations/whatsapp-integration",
        )

    return CommunicationWhatsappChannelPageRead(
        page_title="WhatsApp Communication",
        page_subtitle="Available when the integration is connected",
        primary_action_label="Open integration",
        primary_action_href="/college-admin/integrations/whatsapp-integration",
        primary_action_style="link",
        alert_banner=alert,
        kpis=[
            UserDashboardKpi(key="approved", label="Templates approved", value=f"{approved:,}", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="pending", label="Templates pending", value=f"{pending:,}", hint_line="", hint_tone="warning" if pending else "muted"),
            UserDashboardKpi(key="test_msgs", label="Test messages", value=f"{test_messages:,}", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="opt_ins", label="Opt-ins", value=f"{opt_ins:,}", hint_line="", hint_tone="muted"),
        ],
        templates_section_title="Templates",
        table_headers=["Template", "Category", "Language", "Status"],
        template_rows=paged,
        empty_table_message="No WhatsApp templates configured yet.",
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