"""Aggregate parent-visible notifications from authoritative modules."""

from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.modules.academics.models import AcademicCalendarEvent
from app.modules.examinations.semester_examination_models import ExaminationAnnouncement
from app.modules.parents.enums import (
    ParentCommunicationInboxCategory,
    ParentDataPermission,
    ParentNotificationPriority,
    ParentProfileChangeStatus,
)
from app.modules.parents.models import (
    ParentAcademicEnquiry,
    ParentAttendanceAlert,
    ParentAttendanceEnquiry,
    ParentExamNotification,
    ParentFinanceEnquiry,
    ParentMeetingRequest,
    ParentProfileChangeRequest,
    ParentStudentLinkRequest,
    ParentStudentServiceRequest,
)
from app.modules.students.assessment_models import StudentAssessmentNotification
from app.modules.students.examination_portal_models import StudentExaminationNotification
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.student_finance_models import StudentPaymentNotificationLog
from app.modules.students.models import StudentProfile

_reader = StudentDataReader()


async def _student_name(tenant_id: PydanticObjectId, student_user_id: PydanticObjectId) -> str | None:
    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": student_user_id})
    if profile is None:
        return None
    return getattr(profile, "display_name", None) or profile.roll_number


async def collect_institutional_announcements(tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId) -> list[dict]:
    items: list[dict] = []
    events = await AcademicCalendarEvent.find(
        {"tenant_id": tenant_id, "audience": {"$in": ["parents", "all", "students"]}}
    ).sort("-event_at").limit(40).to_list()
    for e in events:
        key = f"institution:calendar:{e.id}"
        items.append(
            {
                "notification_key": key,
                "category": ParentCommunicationInboxCategory.INSTITUTIONAL.value,
                "priority": ParentNotificationPriority.NORMAL.value,
                "title": e.title,
                "body": (e.description or "")[:2000],
                "student_user_id": None,
                "source": "academic_calendar",
                "published_at": e.event_at,
                "expires_at": None,
                "requires_acknowledgement": False,
            }
        )
    exams = (
        await ExaminationAnnouncement.find({"tenant_id": tenant_id, "published": True})
        .sort("-created_at")
        .limit(20)
        .to_list()
    )
    for ann in exams:
        key = f"institution:exam:{ann.announcement_id}"
        items.append(
            {
                "notification_key": key,
                "category": ParentCommunicationInboxCategory.EXAMINATION.value,
                "priority": ParentNotificationPriority.HIGH.value,
                "title": ann.title,
                "body": ann.body[:2000],
                "student_user_id": None,
                "source": "examination_cell",
                "published_at": ann.created_at,
                "expires_at": None,
                "requires_acknowledgement": False,
            }
        )
    return items


async def collect_student_notifications(
    tenant_id: PydanticObjectId,
    parent_user_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    grants: dict[str, bool],
) -> list[dict]:
    items: list[dict] = []
    name = await _student_name(tenant_id, student_user_id)

    if grants.get(ParentDataPermission.VIEW_ATTENDANCE.value, False):
        alerts = await ParentAttendanceAlert.find(
            {"tenant_id": tenant_id, "parent_user_id": parent_user_id, "student_user_id": student_user_id}
        ).sort("-created_at").limit(20).to_list()
        for a in alerts:
            key = f"attendance:alert:{a.id}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.ATTENDANCE.value,
                    "priority": a.severity or ParentNotificationPriority.NORMAL.value,
                    "title": a.title,
                    "body": a.body,
                    "student_user_id": student_user_id,
                    "student_display_name": name,
                    "source": "attendance",
                    "published_at": a.created_at,
                    "requires_acknowledgement": a.severity == "critical",
                }
            )

    if grants.get(ParentDataPermission.VIEW_EXAM_TIMETABLE.value, False):
        for row in await ParentExamNotification.find(
            {"tenant_id": tenant_id, "parent_user_id": parent_user_id, "student_user_id": student_user_id}
        ).sort("-created_at").limit(30).to_list():
            key = f"parent_exam:{row.notification_key}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.EXAMINATION.value,
                    "priority": ParentNotificationPriority.NORMAL.value,
                    "title": row.title,
                    "body": row.body,
                    "student_user_id": student_user_id,
                    "student_display_name": name,
                    "source": row.category,
                    "published_at": row.created_at,
                    "requires_acknowledgement": False,
                }
            )
        for r in await StudentExaminationNotification.find({"tenant_id": tenant_id, "user_id": student_user_id}).limit(
            20
        ).to_list():
            key = f"student_exam:{r.id}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.EXAMINATION.value,
                    "priority": ParentNotificationPriority.NORMAL.value,
                    "title": r.title,
                    "body": r.body,
                    "student_user_id": student_user_id,
                    "student_display_name": name,
                    "source": "examination",
                    "published_at": r.created_at,
                    "requires_acknowledgement": False,
                }
            )

    if grants.get(ParentDataPermission.VIEW_RESULTS.value, False):
        for r in await StudentAssessmentNotification.find({"tenant_id": tenant_id, "user_id": student_user_id}).limit(
            15
        ).to_list():
            key = f"assessment:{r.id}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.ACADEMIC.value,
                    "priority": ParentNotificationPriority.NORMAL.value,
                    "title": r.title,
                    "body": r.body,
                    "student_user_id": student_user_id,
                    "student_display_name": name,
                    "source": "assessment",
                    "published_at": r.created_at,
                    "requires_acknowledgement": False,
                }
            )
        for r in await _reader.academic_notifications(tenant_id, student_user_id, limit=15):
            key = f"course:{r['id']}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.ACADEMIC.value,
                    "priority": ParentNotificationPriority.NORMAL.value,
                    "title": r["title"],
                    "body": r["body"],
                    "student_user_id": student_user_id,
                    "student_display_name": name,
                    "source": "course",
                    "published_at": r["created_at"],
                    "requires_acknowledgement": False,
                }
            )

    if grants.get(ParentDataPermission.VIEW_FEES.value, False):
        for r in await StudentPaymentNotificationLog.find({"tenant_id": tenant_id, "user_id": student_user_id}).limit(
            20
        ).to_list():
            key = f"finance:{r.id}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.FINANCE.value,
                    "priority": ParentNotificationPriority.NORMAL.value,
                    "title": r.title,
                    "body": r.body,
                    "student_user_id": student_user_id,
                    "student_display_name": name,
                    "source": "finance",
                    "published_at": r.created_at,
                    "requires_acknowledgement": False,
                }
            )

    if grants.get(ParentDataPermission.RECEIVE_ANNOUNCEMENTS.value, False):
        pass  # course + institutional handled elsewhere

    return items


async def collect_meeting_notifications(
    tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId, student_user_id: PydanticObjectId | None
) -> list[dict]:
    filters: dict = {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
    if student_user_id is not None:
        filters["student_user_id"] = student_user_id
    items: list[dict] = []
    for row in await ParentMeetingRequest.find(filters).sort("-updated_at").limit(25).to_list():
        if row.status in {"submitted"}:
            continue
        key = f"parent:meeting:{row.request_id}"
        body = row.rejection_reason or row.purpose[:500]
        items.append(
            {
                "notification_key": key,
                "category": ParentCommunicationInboxCategory.MEETING.value,
                "priority": ParentNotificationPriority.HIGH.value,
                "title": f"Meeting request — {row.status}",
                "body": body,
                "student_user_id": row.student_user_id,
                "source": "meeting",
                "related_request_id": row.request_id,
                "published_at": row.updated_at,
                "requires_acknowledgement": row.status in {"confirmed", "rejected"},
            }
        )
    return items


async def collect_parent_activity_notifications(
    tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId, student_user_id: PydanticObjectId | None
) -> list[dict]:
    items: list[dict] = []
    filters_link = {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
    if student_user_id is not None:
        filters_link["student_user_id"] = student_user_id
    for req in await ParentStudentLinkRequest.find(filters_link).sort("-updated_at").limit(10).to_list():
        key = f"parent:link:{req.id}"
        items.append(
            {
                "notification_key": key,
                "category": ParentCommunicationInboxCategory.PARENT_ACTIVITY.value,
                "priority": ParentNotificationPriority.HIGH.value,
                "title": f"Student link request: {req.status.value}",
                "body": req.relationship_declaration[:500],
                "student_user_id": req.student_user_id,
                "source": "linking",
                "published_at": req.updated_at,
                "requires_acknowledgement": req.status.value in {"approved", "rejected"},
            }
        )
    for enq in await ParentAcademicEnquiry.find(
        {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
        | ({"student_user_id": student_user_id} if student_user_id else {})
    ).sort("-updated_at").limit(15).to_list():
        if enq.response_notes:
            key = f"parent:academic_enquiry:{enq.id}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.PARENT_ACTIVITY.value,
                    "priority": ParentNotificationPriority.NORMAL.value,
                    "title": "Academic enquiry response",
                    "body": enq.response_notes[:2000],
                    "student_user_id": enq.student_user_id,
                    "source": "academic_enquiry",
                    "related_request_id": str(enq.id),
                    "published_at": enq.responded_at or enq.updated_at,
                    "requires_acknowledgement": False,
                }
            )
    for enq in await ParentAttendanceEnquiry.find(
        {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
        | ({"student_user_id": student_user_id} if student_user_id else {})
    ).sort("-updated_at").limit(15).to_list():
        if enq.response_notes:
            key = f"parent:attendance_enquiry:{enq.id}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.PARENT_ACTIVITY.value,
                    "priority": ParentNotificationPriority.NORMAL.value,
                    "title": "Attendance enquiry response",
                    "body": enq.response_notes[:2000],
                    "student_user_id": enq.student_user_id,
                    "source": "attendance_enquiry",
                    "published_at": enq.responded_at or enq.updated_at,
                    "requires_acknowledgement": False,
                }
            )
    for enq in await ParentFinanceEnquiry.find(
        {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
        | ({"student_user_id": student_user_id} if student_user_id else {})
    ).sort("-updated_at").limit(15).to_list():
        if enq.response_notes:
            key = f"parent:finance_enquiry:{enq.id}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.FINANCE.value,
                    "priority": ParentNotificationPriority.NORMAL.value,
                    "title": "Finance enquiry response",
                    "body": enq.response_notes[:2000],
                    "student_user_id": enq.student_user_id,
                    "source": "finance_enquiry",
                    "published_at": enq.responded_at or enq.updated_at,
                    "requires_acknowledgement": False,
                }
            )
    for chg in await ParentProfileChangeRequest.find(
        {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
    ).sort("-updated_at").limit(10).to_list():
        if chg.status in {ParentProfileChangeStatus.APPROVED, ParentProfileChangeStatus.REJECTED}:
            key = f"parent:profile_change:{chg.id}"
            items.append(
                {
                    "notification_key": key,
                    "category": ParentCommunicationInboxCategory.PARENT_ACTIVITY.value,
                    "priority": ParentNotificationPriority.HIGH.value,
                    "title": f"Profile correction {chg.status.value}",
                    "body": chg.reason[:500],
                    "student_user_id": None,
                    "source": "profile",
                    "published_at": chg.updated_at,
                    "requires_acknowledgement": True,
                }
            )
    return items


async def collect_service_request_updates(
    tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId, student_user_id: PydanticObjectId | None
) -> list[dict]:
    filters: dict = {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
    if student_user_id is not None:
        filters["student_user_id"] = student_user_id
    items: list[dict] = []
    for row in await ParentStudentServiceRequest.find(filters).sort("-updated_at").limit(30).to_list():
        if row.status in {"submitted", "received"}:
            continue
        key = f"parent:service_request:{row.request_id}"
        body = row.resolution_remarks or row.status
        items.append(
            {
                "notification_key": key,
                "category": ParentCommunicationInboxCategory.SERVICE_REQUEST.value,
                "priority": ParentNotificationPriority.NORMAL.value,
                "title": f"Service request update — {row.subject}",
                "body": body[:2000],
                "student_user_id": row.student_user_id,
                "source": "service_request",
                "related_request_id": row.request_id,
                "published_at": row.updated_at,
                "requires_acknowledgement": False,
            }
        )
    return items