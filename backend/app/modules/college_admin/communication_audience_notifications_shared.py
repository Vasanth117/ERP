"""Shared helpers for communication audience notification pages (CA 14.04–06)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, GTE, In, LTE

from app.modules.auth.models import User
from app.modules.college_admin.communication_admin_models import (
    AnnouncementAudience,
    CommunicationDeliveryLog,
    DeliveryStatus,
    InstitutionAnnouncement,
)
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.parents.models import ParentNotificationPreferences, ParentStudentRelationship
from app.common.time import utcnow
from app.modules.students.student_portal_models import StudentNotificationReadStatus

_IST = ZoneInfo("Asia/Kolkata")

_CHANNEL_LABELS = {
    "in_app": "App",
    "email": "Email",
    "sms": "SMS",
    "whatsapp": "WhatsApp",
}

_AUDIENCE_BY_SEGMENT = {
    "students": frozenset({AnnouncementAudience.STUDENTS.value}),
    "faculty": frozenset({AnnouncementAudience.FACULTY.value}),
    "parents": frozenset({AnnouncementAudience.PARENTS.value, AnnouncementAudience.CUSTOM.value}),
}

_SEGMENT_LABELS = {
    "students": "All students",
    "faculty": "All faculty",
    "parents": "All parents",
}


def status_value(status: DeliveryStatus | str) -> str:
    return status.value if isinstance(status, DeliveryStatus) else str(status)


def channel_label(channel: str) -> str:
    key = (channel or "").lower().replace("-", "_")
    return _CHANNEL_LABELS.get(key, (channel or "—").replace("_", " ").title())


def channels_label(channels: list[str]) -> str:
    if not channels:
        return "—"
    labels: list[str] = []
    for ch in channels:
        label = channel_label(ch)
        if label not in labels:
            labels.append(label)
    return ", ".join(labels)


def short_day(when: datetime | None) -> str:
    if when is None:
        return "—"
    local = when.astimezone(_IST) if when.tzinfo else when.replace(tzinfo=_IST)
    return local.strftime("%d %b")


def month_window(today) -> tuple[datetime, datetime]:
    month_start = today.replace(day=1)
    month_start_dt = datetime.combine(month_start, datetime.min.time(), tzinfo=_IST)
    if today.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    month_end_dt = datetime.combine(next_month, datetime.min.time(), tzinfo=_IST) - timedelta(seconds=1)
    return month_start_dt, month_end_dt


def announcement_in_segment(doc: InstitutionAnnouncement, segment: str) -> bool:
    aud = doc.audience.value if hasattr(doc.audience, "value") else str(doc.audience)
    allowed = _AUDIENCE_BY_SEGMENT.get(segment, frozenset())
    if aud not in allowed:
        return False
    if segment == "parents" and aud == AnnouncementAudience.CUSTOM.value:
        group = (doc.audience_group_id or "").lower()
        return "parent" in group or group in {"", "parents", "guardians"}
    return True


async def announcements_for_segment(tenant_id, segment: str) -> list[InstitutionAnnouncement]:
    docs = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id)).sort("-updated_at").to_list()
    return [d for d in docs if announcement_in_segment(d, segment)]


def audience_row_label(doc: InstitutionAnnouncement, segment: str) -> str:
    if doc.department_scope and doc.department_scope != "all":
        return doc.department_scope.replace("_", " ").upper()
    if doc.audience_group_id:
        return doc.audience_group_id.replace("_", " ").title()
    return _SEGMENT_LABELS.get(segment, "—")


async def delivery_batches(
    tenant_id,
    announcement_ids: set[str],
) -> dict[tuple[str, str], dict[str, int]]:
    if not announcement_ids:
        return {}
    logs = await CommunicationDeliveryLog.find(Eq(CommunicationDeliveryLog.tenant_id, tenant_id)).to_list()
    grouped: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"recipients": 0, "delivered": 0, "failed": 0})
    for log in logs:
        if log.announcement_id not in announcement_ids:
            continue
        key = (log.announcement_id, log.channel)
        grouped[key]["recipients"] += 1
        st = status_value(log.status)
        if st == DeliveryStatus.SENT.value:
            grouped[key]["delivered"] += 1
        elif st == DeliveryStatus.FAILED.value:
            grouped[key]["failed"] += 1
    return grouped


def batch_status(delivered: int, failed: int) -> tuple[str, str]:
    if delivered <= 0 and failed > 0:
        return "Failed", "error"
    if failed > 0:
        return "Partial", "warning"
    if delivered > 0:
        return "Complete", "success"
    return "Queued", "muted"


async def student_read_stats(tenant_id, month_start: datetime, month_end: datetime) -> tuple[int, int, int]:
    reads = await StudentNotificationReadStatus.find(
        Eq(StudentNotificationReadStatus.tenant_id, tenant_id),
        GTE(StudentNotificationReadStatus.updated_at, month_start),
        LTE(StudentNotificationReadStatus.updated_at, month_end),
    ).to_list()
    read_count = sum(1 for r in reads if r.read_at is not None)
    stale = 0
    cutoff = utcnow() - timedelta(days=3)
    for row in reads:
        if row.read_at is None and row.updated_at < cutoff:
            stale += 1
    return len(reads), read_count, stale


async def parent_reach_stats(tenant_id) -> tuple[int, int, int, int, str]:
    rels = await ParentStudentRelationship.find(Eq(ParentStudentRelationship.tenant_id, tenant_id)).to_list()
    parent_ids = {r.parent_user_id for r in rels}
    students = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).count()
    reachable = len(parent_ids)
    prefs = await ParentNotificationPreferences.find(Eq(ParentNotificationPreferences.tenant_id, tenant_id)).to_list()
    opted_out = sum(
        1
        for p in prefs
        if not p.email_enabled and not p.sms_enabled and not p.push_enabled and not p.in_app_enabled
    )
    invalid = 0
    if parent_ids:
        users = await User.find(In(User.id, list(parent_ids))).to_list()
        for user in users:
            if not (user.phone or user.email):
                invalid += 1
    pct = f"{(reachable / students * 100):.0f}% of students" if students else ""
    return reachable, students, opted_out, invalid, pct

