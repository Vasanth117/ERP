"""Announcements, notifications, documents and correction requests."""

from datetime import datetime, timezone
from uuid import uuid4

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.academics.models import AcademicCalendarEvent
from app.modules.examinations.semester_examination_models import ExaminationAnnouncement
from app.modules.students.assessment_models import StudentAssessmentNotification
from app.modules.students.examination_portal_models import StudentExaminationNotification
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.policy import require_student_scope
from app.modules.students.student_finance_models import StudentPaymentNotificationLog
from app.modules.students.student_lms_models import StudentLmsNotificationLog
from app.modules.students.student_portal_enums import StudentDocumentPortalType, StudentDocumentRequestStatus
from app.modules.students.student_portal_models import (
    StudentCommunicationPreferences,
    StudentDocumentReference,
    StudentDocumentRequest,
    StudentNotificationReadStatus,
    StudentProfileCorrectionRequest,
)
from app.modules.students.student_portal_schemas import (
    AnnouncementFeedRead,
    CommunicationPreferencesRead,
    CommunicationPreferencesUpdate,
    DocumentRequestInput,
    NotificationFeedRead,
    ProfileCorrectionInput,
    StudentDocumentPortalRead,
)

_reader = StudentDataReader()
_DOC_TYPES = frozenset(t.value for t in StudentDocumentPortalType)
_ALLOWED_CORRECTION_FIELDS = frozenset({"roll_number", "admission_number", "programme_name", "section_code", "display_name"})


async def _read_map(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> dict[str, StudentNotificationReadStatus]:
    rows = await StudentNotificationReadStatus.find({"tenant_id": tenant_id, "user_id": user_id}).to_list()
    return {r.notification_key: r for r in rows}


async def announcements(
    scope: AccessScope,
    user: User,
    *,
    scope_filter: str | None = None,
    pagination: Pagination,
) -> Page[AnnouncementFeedRead]:
    authorize(scope, Permission.STUDENT_COMMUNICATION_READ)
    tenant_id = require_student_scope(scope)
    read_map = await _read_map(tenant_id, user.id)
    items: list[AnnouncementFeedRead] = []
    if scope_filter in (None, "course"):
        for r in await _reader.academic_notifications(tenant_id, user.id, limit=50):
            key = f"course:{r['id']}"
            items.append(
                AnnouncementFeedRead(
                    id=r["id"],
                    scope="course",
                    title=r["title"],
                    body=r["body"],
                    course_code=r.get("course_code"),
                    created_at=r["created_at"],
                    read=read_map.get(key) is not None and read_map[key].read_at is not None,
                )
            )
    if scope_filter in (None, "department") and user.department_id is not None:
        events = await AcademicCalendarEvent.find(
            {
                "tenant_id": tenant_id,
                "department_id": user.department_id,
                "audience": {"$in": ["students", "all", "student", "department"]},
            }
        ).sort("-event_at").limit(30).to_list()
        for e in events:
            key = f"dept:{e.id}"
            items.append(
                AnnouncementFeedRead(
                    id=str(e.id),
                    scope="department",
                    title=e.title,
                    body=e.description or "",
                    course_code=None,
                    created_at=e.event_at,
                    read=read_map.get(key) is not None and read_map[key].read_at is not None,
                )
            )
    if scope_filter in (None, "college"):
        events = await AcademicCalendarEvent.find(
            {"tenant_id": tenant_id, "audience": {"$in": ["students", "all", "student"]}}
        ).sort("-event_at").limit(30).to_list()
        for e in events:
            key = f"college:{e.id}"
            items.append(
                AnnouncementFeedRead(
                    id=str(e.id),
                    scope="college",
                    title=e.title,
                    body=e.description or "",
                    course_code=None,
                    created_at=e.event_at,
                    read=read_map.get(key) is not None and read_map[key].read_at is not None,
                )
            )
    if scope_filter in (None, "examination"):
        exams = (
            await ExaminationAnnouncement.find({"tenant_id": tenant_id, "published": True})
            .sort("-created_at")
            .limit(30)
            .to_list()
        )
        for e in exams:
            key = f"exam:{e.announcement_id}"
            items.append(
                AnnouncementFeedRead(
                    id=e.announcement_id,
                    scope="examination",
                    title=e.title,
                    body=e.body[:500],
                    course_code=None,
                    created_at=e.created_at,
                    read=read_map.get(key) is not None and read_map[key].read_at is not None,
                )
            )
    items.sort(key=lambda x: x.created_at, reverse=True)
    slice_items = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_items, total=len(items), limit=pagination.limit, offset=pagination.offset)


async def notifications_feed(scope: AccessScope, user: User, pagination: Pagination) -> Page[NotificationFeedRead]:
    authorize(scope, Permission.STUDENT_COMMUNICATION_READ)
    tenant_id = require_student_scope(scope)
    prefs = await get_preferences(scope, user)
    read_map = await _read_map(tenant_id, user.id)
    entries: list[NotificationFeedRead] = []
    if prefs.academic_enabled:
        for r in await StudentAssessmentNotification.find({"tenant_id": tenant_id, "user_id": user.id}).limit(30).to_list():
            key = f"assessment:{r.id}"
            entries.append(
                NotificationFeedRead(
                    notification_key=key,
                    source="assessment",
                    title=r.title,
                    body=r.body,
                    created_at=r.created_at,
                    read=read_map.get(key) is not None and read_map[key].read_at is not None,
                )
            )
        for r in await StudentLmsNotificationLog.find({"tenant_id": tenant_id, "user_id": user.id}).limit(30).to_list():
            key = f"lms:{r.id}"
            entries.append(
                NotificationFeedRead(
                    notification_key=key,
                    source="lms",
                    title=r.title,
                    body=r.body,
                    created_at=r.created_at,
                    read=read_map.get(key) is not None and read_map[key].read_at is not None,
                )
            )
    if prefs.examination_enabled:
        for r in await StudentExaminationNotification.find({"tenant_id": tenant_id, "user_id": user.id}).limit(30).to_list():
            key = f"exam:{r.id}"
            entries.append(
                NotificationFeedRead(
                    notification_key=key,
                    source="examination",
                    title=r.title,
                    body=r.body,
                    created_at=r.created_at,
                    read=read_map.get(key) is not None and read_map[key].read_at is not None,
                )
            )
    if prefs.finance_enabled:
        for r in await StudentPaymentNotificationLog.find({"tenant_id": tenant_id, "user_id": user.id}).limit(30).to_list():
            key = f"finance:{r.id}"
            entries.append(
                NotificationFeedRead(
                    notification_key=key,
                    source="finance",
                    title=r.title,
                    body=r.body,
                    created_at=r.created_at,
                    read=read_map.get(key) is not None and read_map[key].read_at is not None,
                )
            )
    entries.sort(key=lambda x: x.created_at, reverse=True)
    slice_items = entries[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_items, total=len(entries), limit=pagination.limit, offset=pagination.offset)


async def mark_notification_read(scope: AccessScope, user: User, notification_key: str) -> dict:
    authorize(scope, Permission.STUDENT_COMMUNICATION_MANAGE)
    tenant_id = require_student_scope(scope)
    row = await StudentNotificationReadStatus.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "notification_key": notification_key}
    )
    now = utcnow()
    if row is None:
        await StudentNotificationReadStatus(
            tenant_id=tenant_id,
            user_id=user.id,
            notification_key=notification_key,
            source=notification_key.split(":", 1)[0],
            read_at=now,
        ).insert()
    else:
        row.read_at = now
        row.updated_at = now
        await row.save()
    return {"notification_key": notification_key, "read_at": now}


async def get_preferences(scope: AccessScope, user: User) -> CommunicationPreferencesRead:
    authorize(scope, Permission.STUDENT_COMMUNICATION_READ)
    tenant_id = require_student_scope(scope)
    row = await StudentCommunicationPreferences.find_one({"tenant_id": tenant_id, "user_id": user.id})
    if row is None:
        return CommunicationPreferencesRead(
            email_enabled=True,
            push_enabled=False,
            academic_enabled=True,
            finance_enabled=True,
            examination_enabled=True,
        )
    return CommunicationPreferencesRead(
        email_enabled=row.email_enabled,
        push_enabled=row.push_enabled,
        academic_enabled=row.academic_enabled,
        finance_enabled=row.finance_enabled,
        examination_enabled=row.examination_enabled,
    )


async def update_preferences(
    scope: AccessScope, user: User, payload: CommunicationPreferencesUpdate
) -> CommunicationPreferencesRead:
    authorize(scope, Permission.STUDENT_COMMUNICATION_MANAGE)
    tenant_id = require_student_scope(scope)
    row = await StudentCommunicationPreferences.find_one({"tenant_id": tenant_id, "user_id": user.id})
    data = payload.model_dump(exclude_unset=True)
    if row is None:
        row = StudentCommunicationPreferences(tenant_id=tenant_id, user_id=user.id, **data)
        row.updated_at = utcnow()
        await row.insert()
    else:
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = utcnow()
        await row.save()
    return await get_preferences(scope, user)


async def authorized_documents(scope: AccessScope, user: User) -> list[StudentDocumentPortalRead]:
    authorize(scope, Permission.STUDENT_COMMUNICATION_READ)
    tenant_id = require_student_scope(scope)
    from app.modules.students.integrations.academic_document_reader import published_documents

    portal_refs = await StudentDocumentReference.find(
        {"tenant_id": tenant_id, "user_id": user.id, "authorized": True}
    ).to_list()
    academic = await published_documents(tenant_id, user.id)
    seen = {r.document_id for r in portal_refs}
    items = [
        StudentDocumentPortalRead(document_id=r.document_id, document_type=r.document_type, title=r.title)
        for r in portal_refs
    ]
    for doc in academic:
        if doc.document_id in seen:
            continue
        items.append(
            StudentDocumentPortalRead(
                document_id=doc.document_id,
                document_type=doc.document_type.value,
                title=doc.title,
            )
        )
    return items


async def submit_document_request(scope: AccessScope, user: User, payload: DocumentRequestInput) -> dict:
    authorize(scope, Permission.STUDENT_COMMUNICATION_MANAGE)
    tenant_id = require_student_scope(scope)
    if payload.request_type not in _DOC_TYPES:
        raise AppError(code="VALIDATION_ERROR", message="Invalid document type", status_code=422)
    request_id = f"doc_{uuid4().hex}"
    await StudentDocumentRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=request_id,
        request_type=StudentDocumentPortalType(payload.request_type),
        reason=payload.reason,
        status=StudentDocumentRequestStatus.SUBMITTED,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.document.request_submitted",
        resource_type="student_document_request",
        resource_id=request_id,
        tenant_id=tenant_id,
    )
    return {"request_id": request_id, "status": "submitted"}


async def document_request_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.STUDENT_COMMUNICATION_READ)
    tenant_id = require_student_scope(scope)
    total = await StudentDocumentRequest.find({"tenant_id": tenant_id, "user_id": user.id}).count()
    rows = (
        await StudentDocumentRequest.find({"tenant_id": tenant_id, "user_id": user.id})
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [
        {
            "request_id": r.request_id,
            "request_type": r.request_type.value,
            "status": r.status.value,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def submit_profile_correction(scope: AccessScope, user: User, payload: ProfileCorrectionInput) -> dict:
    authorize(scope, Permission.STUDENT_COMMUNICATION_MANAGE)
    tenant_id = require_student_scope(scope)
    if payload.field_name not in _ALLOWED_CORRECTION_FIELDS:
        raise AppError(code="FORBIDDEN", message="Field cannot be corrected via student portal", status_code=403)
    request_id = f"pfc_{uuid4().hex}"
    await StudentProfileCorrectionRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=request_id,
        field_name=payload.field_name,
        proposed_value=payload.proposed_value.strip(),
        reason=payload.reason.strip(),
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.profile_correction_submitted",
        resource_type="student_profile_correction_request",
        resource_id=request_id,
        tenant_id=tenant_id,
    )
    return {"request_id": request_id, "status": "submitted"}


async def correction_history(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.STUDENT_COMMUNICATION_READ)
    tenant_id = require_student_scope(scope)
    rows = await StudentProfileCorrectionRequest.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-created_at").to_list()
    return [
        {
            "request_id": r.request_id,
            "field_name": r.field_name,
            "status": r.status.value,
            "created_at": r.created_at,
        }
        for r in rows
    ]
