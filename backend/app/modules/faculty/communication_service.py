"""Faculty academic communication."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.faculty.communication_models import (
    AcademicMessage,
    AnnouncementPublishEvent,
    CommunicationRecipient,
    FacultyAnnouncement,
    FacultyNotificationDeliveryLog,
    FacultyNotificationPreferences,
)
from app.modules.faculty.communication_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementUpdate,
    AssignmentUpdateShare,
    MessageRead,
    NotificationItemRead,
    NotificationPreferencesRead,
    NotificationPreferencesUpdate,
    RecipientRead,
)
from app.modules.lms.models import CourseAssignment
from app.modules.faculty.course_access import require_course_access, resolve_course_id
from app.modules.faculty.enums import FacultyActivityType, FacultyNotificationCategory
from app.modules.faculty.integrations.notification_dispatch import queue_faculty_notification
from app.modules.faculty.models import FacultyNotification, FacultyTimetableNotification
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.repositories import FacultyActivityRepository

_activity_repo = FacultyActivityRepository()


def _announcement_read(doc: FacultyAnnouncement) -> AnnouncementRead:
    return AnnouncementRead(
        id=str(doc.id),
        course_code=doc.course_code,
        section=doc.section,
        title=doc.title,
        body=doc.body,
        status=doc.status,
        created_at=doc.created_at,
        publish_history=[e.model_dump(mode="json") for e in doc.publish_history],
    )


async def create_announcement(scope: AccessScope, user: User, payload: AnnouncementCreate) -> AnnouncementRead:
    authorize(scope, Permission.FACULTY_COMMUNICATION_MANAGE)
    tenant_id = require_faculty_scope(scope)
    if payload.section:
        await require_course_access(tenant_id, user.id, course_code=payload.course_code, section=payload.section)
    else:
        await require_course_access(tenant_id, user.id, course_code=payload.course_code)
    doc = FacultyAnnouncement(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        course_code=payload.course_code,
        section=payload.section,
        title=payload.title.strip(),
        body=payload.body.strip(),
        assignment_id=payload.assignment_id,
    )
    await doc.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.announcement.created",
        resource_type="faculty_announcement",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    return _announcement_read(doc)


async def update_announcement(
    scope: AccessScope,
    user: User,
    announcement_id: PydanticObjectId,
    payload: AnnouncementUpdate,
) -> AnnouncementRead:
    authorize(scope, Permission.FACULTY_COMMUNICATION_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await FacultyAnnouncement.get(announcement_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status != "draft":
        raise AppError(code="FORBIDDEN", message="Only draft announcements can be edited", status_code=403)
    if payload.title is not None:
        doc.title = payload.title
    if payload.body is not None:
        doc.body = payload.body
    doc.updated_at = utcnow()
    await doc.save()
    return _announcement_read(doc)


async def _roster_recipients(
    tenant_id: PydanticObjectId, course_code: str, section: str | None
) -> list[EnrollmentRosterEntry]:
    course_id = await resolve_course_id(tenant_id, course_code)
    filters: dict = {"tenant_id": tenant_id, "course_id": course_id}
    if section:
        filters["section_code"] = section
    return await EnrollmentRosterEntry.find(filters).to_list()


async def publish_announcement(
    scope: AccessScope, user: User, announcement_id: PydanticObjectId
) -> AnnouncementRead:
    authorize(scope, Permission.FACULTY_COMMUNICATION_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await FacultyAnnouncement.get(announcement_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status == "published":
        raise AppError(code="CONFLICT", message="Announcement already published", status_code=409)
    section = doc.section or "A"
    await require_course_access(tenant_id, user.id, course_code=doc.course_code, section=section)
    roster = await _roster_recipients(tenant_id, doc.course_code, doc.section)
    if not roster:
        raise AppError(code="VALIDATION_ERROR", message="No authorized recipients for this scope", status_code=422)
    prefs = await _prefs(tenant_id, user.id)
    for entry in roster:
        await CommunicationRecipient(
            tenant_id=tenant_id,
            announcement_id=doc.id,
            student_user_id=entry.student_user_id,
            course_code=doc.course_code,
            section=entry.section_code,
        ).insert()
    doc.status = "published"
    doc.publish_history.append(AnnouncementPublishEvent(published_at=utcnow(), action="published"))
    doc.updated_at = utcnow()
    await doc.save()
    await queue_faculty_notification(
        tenant_id=tenant_id,
        user_id=user.id,
        channel="email",
        template="announcement_published",
        payload_ref=str(doc.id),
        email_enabled=prefs.email_enabled,
        push_enabled=prefs.push_enabled,
    )
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.NOTIFICATION,
        title=f"Announcement published: {doc.title}",
    )
    return _announcement_read(doc)


async def withdraw_announcement(
    scope: AccessScope, user: User, announcement_id: PydanticObjectId
) -> AnnouncementRead:
    authorize(scope, Permission.FACULTY_COMMUNICATION_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await FacultyAnnouncement.get(announcement_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    doc.status = "withdrawn"
    doc.withdrawn_at = utcnow()
    doc.publish_history.append(AnnouncementPublishEvent(published_at=utcnow(), action="withdrawn"))
    await doc.save()
    return _announcement_read(doc)


async def list_announcements(scope: AccessScope, user: User) -> list[AnnouncementRead]:
    authorize(scope, Permission.FACULTY_COMMUNICATION_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await FacultyAnnouncement.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-created_at").to_list()
    return [_announcement_read(r) for r in rows]


async def list_recipients(
    scope: AccessScope, user: User, announcement_id: PydanticObjectId
) -> list[RecipientRead]:
    authorize(scope, Permission.FACULTY_COMMUNICATION_READ)
    tenant_id = require_faculty_scope(scope)
    doc = await FacultyAnnouncement.get(announcement_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    rows = await CommunicationRecipient.find(
        {"tenant_id": tenant_id, "announcement_id": announcement_id}
    ).to_list()
    return [
        RecipientRead(
            student_user_id=str(r.student_user_id),
            course_code=r.course_code,
            section=r.section,
            delivery_status=r.delivery_status,
        )
        for r in rows
    ]


async def send_academic_reminder(
    scope: AccessScope,
    user: User,
    *,
    course_code: str,
    section: str | None,
    subject: str,
    body: str,
) -> MessageRead:
    authorize(scope, Permission.FACULTY_COMMUNICATION_MANAGE)
    tenant_id = require_faculty_scope(scope)
    await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    msg = AcademicMessage(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        course_code=course_code,
        section=section,
        subject=subject.strip(),
        body=body.strip(),
    )
    await msg.insert()
    prefs = await _prefs(tenant_id, user.id)
    await queue_faculty_notification(
        tenant_id=tenant_id,
        user_id=user.id,
        channel="email",
        template="academic_reminder",
        payload_ref=str(msg.id),
        email_enabled=prefs.email_enabled,
        push_enabled=prefs.push_enabled,
    )
    return MessageRead(
        id=str(msg.id),
        subject=msg.subject,
        body=msg.body,
        course_code=msg.course_code,
        section=msg.section,
        created_at=msg.created_at,
    )


async def communication_history(scope: AccessScope, user: User) -> list[MessageRead]:
    authorize(scope, Permission.FACULTY_COMMUNICATION_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await AcademicMessage.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-created_at").limit(100).to_list()
    return [
        MessageRead(
            id=str(r.id),
            subject=r.subject,
            body=r.body,
            course_code=r.course_code,
            section=r.section,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def _prefs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> FacultyNotificationPreferences:
    doc = await FacultyNotificationPreferences.find_one({"tenant_id": tenant_id, "user_id": user_id})
    if doc is None:
        doc = FacultyNotificationPreferences(tenant_id=tenant_id, user_id=user_id)
        await doc.insert()
    return doc


async def get_notification_preferences(scope: AccessScope, user: User) -> NotificationPreferencesRead:
    authorize(scope, Permission.FACULTY_COMMUNICATION_READ)
    tenant_id = require_faculty_scope(scope)
    prefs = await _prefs(tenant_id, user.id)
    return NotificationPreferencesRead(
        email_enabled=prefs.email_enabled,
        push_enabled=prefs.push_enabled,
        digest_only=prefs.digest_only,
    )


async def update_notification_preferences(
    scope: AccessScope, user: User, payload: NotificationPreferencesUpdate
) -> NotificationPreferencesRead:
    authorize(scope, Permission.FACULTY_COMMUNICATION_MANAGE)
    tenant_id = require_faculty_scope(scope)
    prefs = await _prefs(tenant_id, user.id)
    if payload.email_enabled is not None:
        prefs.email_enabled = payload.email_enabled
    if payload.push_enabled is not None:
        prefs.push_enabled = payload.push_enabled
    if payload.digest_only is not None:
        prefs.digest_only = payload.digest_only
    prefs.updated_at = utcnow()
    await prefs.save()
    return await get_notification_preferences(scope, user)


async def list_academic_notifications(scope: AccessScope, user: User) -> list[NotificationItemRead]:
    authorize(scope, Permission.FACULTY_COMMUNICATION_READ)
    tenant_id = require_faculty_scope(scope)
    items: list[NotificationItemRead] = []
    for doc in await FacultyNotification.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-created_at").limit(50).to_list():
        items.append(
            NotificationItemRead(
                id=str(doc.id),
                source="academic",
                title=doc.title,
                body=doc.body,
                created_at=doc.created_at,
                read_at=doc.read_at,
            )
        )
    for doc in await FacultyTimetableNotification.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-created_at").limit(50).to_list():
        items.append(
            NotificationItemRead(
                id=str(doc.id),
                source="timetable",
                title=doc.title,
                body=doc.body,
                created_at=doc.created_at,
                read_at=doc.read_at,
            )
        )
    for category, source in (
        (FacultyNotificationCategory.DEPARTMENT, "department"),
        (FacultyNotificationCategory.EXAMINATION, "examination"),
    ):
        extra = await FacultyNotification.find(
            {"tenant_id": tenant_id, "user_id": user.id, "category": category}
        ).to_list()
        for doc in extra:
            if any(i.id == str(doc.id) for i in items):
                continue
            items.append(
                NotificationItemRead(
                    id=str(doc.id),
                    source=source,
                    title=doc.title,
                    body=doc.body,
                    created_at=doc.created_at,
                    read_at=doc.read_at,
                )
            )
    items.sort(key=lambda i: i.created_at, reverse=True)
    return items[:50]


async def share_assignment_update(
    scope: AccessScope, user: User, payload: AssignmentUpdateShare
) -> MessageRead:
    """Notify assigned course scope about an LMS assignment change."""
    authorize(scope, Permission.FACULTY_COMMUNICATION_MANAGE)
    tenant_id = require_faculty_scope(scope)
    assignment_oid = to_object_id(payload.assignment_id, "assignment id")
    doc = await CourseAssignment.get(assignment_oid)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    await require_course_access(
        tenant_id,
        user.id,
        course_code=doc.course_code,
        section=doc.section,
    )
    body = (payload.body or f"Assignment '{doc.title}' has been updated.").strip()
    subject = f"Assignment update: {doc.title}"
    msg = AcademicMessage(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        course_code=doc.course_code,
        section=doc.section,
        subject=subject[:200],
        body=body[:4000],
    )
    await msg.insert()
    prefs = await _prefs(tenant_id, user.id)
    await queue_faculty_notification(
        tenant_id=tenant_id,
        user_id=user.id,
        channel="email",
        template="assignment_update",
        payload_ref=str(msg.id),
        email_enabled=prefs.email_enabled,
        push_enabled=prefs.push_enabled,
    )
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.assignment_update.shared",
        resource_type="academic_message",
        resource_id=str(msg.id),
        tenant_id=tenant_id,
    )
    return MessageRead(
        id=str(msg.id),
        subject=msg.subject,
        body=msg.body,
        course_code=msg.course_code,
        section=msg.section,
        created_at=msg.created_at,
    )


async def mark_notification_read(
    scope: AccessScope,
    user: User,
    notification_id: str,
    *,
    source: str = "academic",
) -> NotificationItemRead:
    authorize(scope, Permission.FACULTY_COMMUNICATION_READ)
    tenant_id = require_faculty_scope(scope)
    oid = to_object_id(notification_id, "notification id")
    if source == "timetable":
        doc = await FacultyTimetableNotification.get(oid)
    elif source in {"academic", "department", "examination"}:
        doc = await FacultyNotification.get(oid)
    else:
        doc = await FacultyNotification.get(oid)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Notification not found", status_code=404)
    doc.read_at = utcnow()
    await doc.save()
    return NotificationItemRead(
        id=str(doc.id),
        source=source,
        title=doc.title,
        body=doc.body,
        created_at=doc.created_at,
        read_at=doc.read_at,
    )
