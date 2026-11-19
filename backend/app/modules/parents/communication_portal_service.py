"""Parent communication dashboard, notifications, preferences."""

from datetime import datetime, timedelta, timezone

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.parents.enums import (
    MANDATORY_PARENT_NOTIFICATION_CATEGORIES,
    ParentCommunicationInboxCategory,
    ParentDataPermission,
    ParentNotificationPriority,
)
from app.modules.parents.integrations.communication_aggregator import (
    collect_institutional_announcements,
    collect_meeting_notifications,
    collect_parent_activity_notifications,
    collect_service_request_updates,
    collect_student_notifications,
)
from app.modules.parents.models import (
    ParentNotificationAcknowledgement,
    ParentNotificationPreferences,
    ParentNotificationReadHistory,
)
from app.modules.parents.phase4_schemas import (
    ParentCommunicationDashboardRead,
    ParentNotificationDetailRead,
    ParentNotificationPreferencesRead,
    ParentNotificationPreferencesUpdate,
    ParentNotificationRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.repositories import ParentRelationshipRepository, ParentProfileRepository
from app.modules.parents.relationship_access import require_student_access

_relationship_repo = ParentRelationshipRepository()
_profile_repo = ParentProfileRepository()


def _parse_dt(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def _read_map(tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId) -> dict[str, ParentNotificationReadHistory]:
    rows = await ParentNotificationReadHistory.find({"tenant_id": tenant_id, "parent_user_id": parent_user_id}).to_list()
    return {r.notification_key: r for r in rows}


async def _ack_map(tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId) -> dict[str, ParentNotificationAcknowledgement]:
    rows = await ParentNotificationAcknowledgement.find(
        {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
    ).to_list()
    return {r.notification_key: r for r in rows}


async def _notification_preferences(tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId) -> ParentNotificationPreferences:
    row = await ParentNotificationPreferences.find_one({"tenant_id": tenant_id, "parent_user_id": parent_user_id})
    if row is None:
        profile = await _profile_repo.get_by_user(tenant_id, parent_user_id)
        prefs = profile.communication_preferences if profile else None
        row = ParentNotificationPreferences(
            tenant_id=tenant_id,
            parent_user_id=parent_user_id,
            email_enabled=prefs.email_enabled if prefs else True,
            sms_enabled=prefs.sms_enabled if prefs else False,
            push_enabled=prefs.push_enabled if prefs else True,
            in_app_enabled=True,
            preferred_language=prefs.preferred_language if prefs else None,
        )
        await row.insert()
    return row


def _category_allowed(prefs: ParentNotificationPreferences, category: str) -> bool:
    if category in MANDATORY_PARENT_NOTIFICATION_CATEGORIES:
        return True
    if not prefs.in_app_enabled:
        return False
    if category in prefs.category_enabled and not prefs.category_enabled[category]:
        return False
    return True


async def _aggregate_inbox(
    tenant_id: PydanticObjectId,
    parent_user_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId | None = None,
) -> list[dict]:
    items: list[dict] = []
    relationships = await _relationship_repo.list_active_for_parent(tenant_id, parent_user_id)
    items.extend(await collect_institutional_announcements(tenant_id, parent_user_id))
    items.extend(await collect_parent_activity_notifications(tenant_id, parent_user_id, student_user_id))
    items.extend(await collect_meeting_notifications(tenant_id, parent_user_id, student_user_id))
    items.extend(await collect_service_request_updates(tenant_id, parent_user_id, student_user_id))

    for rel in relationships:
        if student_user_id is not None and rel.student_user_id != student_user_id:
            continue
        perms = await _relationship_repo.permissions_for_relationship(tenant_id, rel.id)
        grants = perms.grants if perms else {}
        if not grants.get(ParentDataPermission.RECEIVE_ANNOUNCEMENTS.value, True):
            continue
        items.extend(
            await collect_student_notifications(tenant_id, parent_user_id, rel.student_user_id, grants)
        )

    if student_user_id is not None:
        filtered: list[dict] = []
        for item in items:
            sid = item.get("student_user_id")
            if sid is None or sid == student_user_id:
                filtered.append(item)
        items = filtered

    dedup: dict[str, dict] = {}
    for item in items:
        key = item["notification_key"]
        if key not in dedup or item.get("published_at", utcnow()) > dedup[key].get("published_at", utcnow()):
            dedup[key] = item
    return list(dedup.values())


def _map_notification(
    raw: dict,
    read_map: dict[str, ParentNotificationReadHistory],
    ack_map: dict[str, ParentNotificationAcknowledgement],
) -> ParentNotificationRead:
    key = raw["notification_key"]
    pub = raw.get("published_at")
    if not isinstance(pub, datetime):
        pub = _parse_dt(pub) or utcnow()
    student_id = raw.get("student_user_id")
    return ParentNotificationRead(
        notification_key=key,
        category=ParentCommunicationInboxCategory(raw.get("category", ParentCommunicationInboxCategory.OTHER.value)),
        priority=ParentNotificationPriority(raw.get("priority", ParentNotificationPriority.NORMAL.value)),
        title=raw["title"],
        body=raw["body"],
        student_user_id=str(student_id) if student_id else None,
        student_display_name=raw.get("student_display_name"),
        source=raw.get("source"),
        related_request_id=raw.get("related_request_id"),
        attachment_refs=list(raw.get("attachment_refs") or []),
        requires_acknowledgement=bool(raw.get("requires_acknowledgement")),
        published_at=pub,
        expires_at=_parse_dt(raw.get("expires_at")),
        read=key in read_map,
        acknowledged=key in ack_map,
        delivery_status=raw.get("delivery_status"),
    )


async def get_communication_dashboard(scope: AccessScope, parent: User) -> ParentCommunicationDashboardRead:
    authorize(scope, Permission.PARENT_COMMUNICATION_READ)
    tenant_id = require_parent_scope(scope)
    inbox = await _aggregate_inbox(tenant_id, parent.id)
    read_map = await _read_map(tenant_id, parent.id)
    unread = sum(1 for i in inbox if i["notification_key"] not in read_map)
    def count_cat(cat: str) -> int:
        return sum(1 for i in inbox if i.get("category") == cat)
    important = sum(
        1
        for i in inbox
        if i.get("priority") in {ParentNotificationPriority.HIGH.value, ParentNotificationPriority.URGENT.value}
        or i.get("requires_acknowledgement")
    )
    return ParentCommunicationDashboardRead(
        total_notifications=len(inbox),
        unread_notifications=unread,
        important_count=important,
        examination_notices=count_cat(ParentCommunicationInboxCategory.EXAMINATION.value),
        attendance_alerts=count_cat(ParentCommunicationInboxCategory.ATTENDANCE.value),
        fee_reminders=count_cat(ParentCommunicationInboxCategory.FINANCE.value),
        service_request_updates=count_cat(ParentCommunicationInboxCategory.SERVICE_REQUEST.value),
        parent_activity_count=count_cat(ParentCommunicationInboxCategory.PARENT_ACTIVITY.value),
    )


async def list_notifications(
    scope: AccessScope,
    parent: User,
    pagination: Pagination,
    *,
    student_user_id: str | None = None,
    category: ParentCommunicationInboxCategory | None = None,
    unread_only: bool = False,
    priority: ParentNotificationPriority | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> Page[ParentNotificationRead]:
    authorize(scope, Permission.PARENT_COMMUNICATION_READ)
    tenant_id = require_parent_scope(scope)
    prefs = await _notification_preferences(tenant_id, parent.id)
    sid = PydanticObjectId(student_user_id) if student_user_id else None
    if sid is not None:
        await require_student_access(
            tenant_id, parent.id, sid, ParentDataPermission.RECEIVE_ANNOUNCEMENTS
        )
    inbox = await _aggregate_inbox(tenant_id, parent.id, student_user_id=sid)
    read_map = await _read_map(tenant_id, parent.id)
    ack_map = await _ack_map(tenant_id, parent.id)

    filtered: list[dict] = []
    for raw in inbox:
        if category is not None and raw.get("category") != category.value:
            continue
        if unread_only and raw["notification_key"] in read_map:
            continue
        if priority is not None and raw.get("priority") != priority.value:
            continue
        pub = raw.get("published_at")
        if not isinstance(pub, datetime):
            pub = _parse_dt(pub)
        if from_date and pub and pub < from_date:
            continue
        if to_date and pub and pub > to_date:
            continue
        if not _category_allowed(prefs, raw.get("category", "")):
            continue
        filtered.append(raw)

    filtered.sort(key=lambda x: _parse_dt(x.get("published_at")) or utcnow(), reverse=True)
    slice_rows = filtered[pagination.offset : pagination.offset + pagination.limit]
    items = [_map_notification(r, read_map, ack_map) for r in slice_rows]
    return Page(items=items, total=len(filtered), limit=pagination.limit, offset=pagination.offset)


async def get_notification_detail(
    scope: AccessScope, parent: User, notification_key: str
) -> ParentNotificationDetailRead:
    authorize(scope, Permission.PARENT_COMMUNICATION_READ)
    tenant_id = require_parent_scope(scope)
    inbox = await _aggregate_inbox(tenant_id, parent.id)
    match = next((i for i in inbox if i["notification_key"] == notification_key), None)
    if match is None:
        raise AppError(code="NOT_FOUND", message="Notification not found", status_code=404)
    read_map = await _read_map(tenant_id, parent.id)
    ack_map = await _ack_map(tenant_id, parent.id)
    base = _map_notification(match, read_map, ack_map)
    return ParentNotificationDetailRead(**base.model_dump(), workflow_ref=match.get("related_request_id"))


async def mark_notification_read(scope: AccessScope, parent: User, notification_key: str) -> dict:
    authorize(scope, Permission.PARENT_COMMUNICATION_MANAGE)
    tenant_id = require_parent_scope(scope)
    inbox = await _aggregate_inbox(tenant_id, parent.id)
    if not any(i["notification_key"] == notification_key for i in inbox):
        raise AppError(code="NOT_FOUND", message="Notification not found", status_code=404)
    row = await ParentNotificationReadHistory.find_one(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "notification_key": notification_key}
    )
    now = utcnow()
    if row is None:
        raw = next(i for i in inbox if i["notification_key"] == notification_key)
        await ParentNotificationReadHistory(
            tenant_id=tenant_id,
            parent_user_id=parent.id,
            notification_key=notification_key,
            category=raw.get("category", "other"),
            student_user_id=raw.get("student_user_id"),
            source=raw.get("source"),
            read_at=now,
        ).insert()
    else:
        row.read_at = now
        await row.save()
    return {"notification_key": notification_key, "read_at": now}


async def acknowledge_notification(scope: AccessScope, parent: User, notification_key: str) -> dict:
    authorize(scope, Permission.PARENT_COMMUNICATION_MANAGE)
    tenant_id = require_parent_scope(scope)
    inbox = await _aggregate_inbox(tenant_id, parent.id)
    raw = next((i for i in inbox if i["notification_key"] == notification_key), None)
    if raw is None:
        raise AppError(code="NOT_FOUND", message="Notification not found", status_code=404)
    await mark_notification_read(scope, parent, notification_key)
    ack = await ParentNotificationAcknowledgement.find_one(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "notification_key": notification_key}
    )
    now = utcnow()
    if ack is None:
        await ParentNotificationAcknowledgement(
            tenant_id=tenant_id,
            parent_user_id=parent.id,
            notification_key=notification_key,
            student_user_id=raw.get("student_user_id"),
            requires_acknowledgement=bool(raw.get("requires_acknowledgement")),
            acknowledged_at=now,
        ).insert()
    return {"notification_key": notification_key, "acknowledged_at": now}


async def get_notification_preferences(scope: AccessScope, parent: User) -> ParentNotificationPreferencesRead:
    authorize(scope, Permission.PARENT_COMMUNICATION_READ)
    tenant_id = require_parent_scope(scope)
    row = await _notification_preferences(tenant_id, parent.id)
    return ParentNotificationPreferencesRead(
        email_enabled=row.email_enabled,
        sms_enabled=row.sms_enabled,
        push_enabled=row.push_enabled,
        in_app_enabled=row.in_app_enabled,
        preferred_language=row.preferred_language,
        category_enabled=dict(row.category_enabled),
    )


async def update_notification_preferences(
    scope: AccessScope, parent: User, payload: ParentNotificationPreferencesUpdate
) -> ParentNotificationPreferencesRead:
    authorize(scope, Permission.PARENT_COMMUNICATION_MANAGE)
    tenant_id = require_parent_scope(scope)
    row = await _notification_preferences(tenant_id, parent.id)
    data = payload.model_dump(exclude_unset=True)
    if "category_enabled" in data and data["category_enabled"]:
        for cat in MANDATORY_PARENT_NOTIFICATION_CATEGORIES:
            data["category_enabled"].pop(cat, None)
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = utcnow()
    await row.save()
    return await get_notification_preferences(scope, parent)