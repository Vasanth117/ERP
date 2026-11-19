"""Parent attendance monitoring, alerts, and enquiries."""

from datetime import date

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.parents.enums import (
    ParentAttendanceAlertSeverity,
    ParentAttendanceEnquiryStatus,
    ParentDataPermission,
)
from app.modules.parents.integrations.attendance_reader import (
    academic_term,
    attendance_history_marks,
    daily_marks,
    semester_attendance_summary,
    shortage_list,
)
from app.modules.parents.models import (
    ParentAttendanceAlert,
    ParentAttendanceAlertAcknowledgement,
    ParentAttendanceEnquiry,
    ParentAttendanceEnquiryHistory,
)
from app.modules.parents.phase2_schemas import (
    ParentAttendanceAlertRead,
    ParentAttendanceDashboardRead,
    ParentAttendanceEnquiryCreate,
    ParentAttendanceEnquiryRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent
from app.modules.students.student_schedule_schemas import AttendanceMarkRead, AttendanceShortageRead, SubjectAttendanceDetailRead


def _alert_key(
    tenant_id: PydanticObjectId,
    parent_user_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    course_code: str,
    section: str,
) -> str:
    return f"{tenant_id}:{parent_user_id}:{student_user_id}:{year}:{semester}:{course_code}:{section}:shortage"


async def sync_attendance_alerts(
    tenant_id: PydanticObjectId,
    parent_user_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> None:
    _, perms = await require_student_access(tenant_id, parent_user_id, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    if perms is None or not perms.grants.get(ParentDataPermission.VIEW_ATTENDANCE.value):
        return
    summary, _ = await semester_attendance_summary(tenant_id, student_user_id, year=year, semester=semester)
    for subject in summary.subjects:
        if not subject.below_threshold or subject.percentage is None:
            continue
        key = _alert_key(
            tenant_id,
            parent_user_id,
            student_user_id,
            year=year,
            semester=semester,
            course_code=subject.course_code,
            section=subject.section,
        )
        severity = (
            ParentAttendanceAlertSeverity.CRITICAL.value
            if subject.percentage < subject.min_required - 10
            else ParentAttendanceAlertSeverity.WARNING.value
        )
        title = f"Attendance shortage — {subject.course_code}"
        body = f"Attendance is {subject.percentage}% (required {subject.min_required}%)"
        existing = await ParentAttendanceAlert.find_one({"tenant_id": tenant_id, "alert_key": key})
        now = utcnow()
        if existing:
            existing.percentage = subject.percentage
            existing.min_required = subject.min_required
            existing.body = body
            existing.severity = severity
            existing.source_updated_at = now
            existing.updated_at = now
            await existing.save()
        else:
            await ParentAttendanceAlert(
                tenant_id=tenant_id,
                parent_user_id=parent_user_id,
                student_user_id=student_user_id,
                alert_key=key,
                academic_year_label=year,
                semester_label=semester,
                course_code=subject.course_code,
                section=subject.section,
                severity=severity,
                title=title,
                body=body,
                percentage=subject.percentage,
                min_required=subject.min_required,
                source_updated_at=now,
            ).insert()


async def get_attendance_dashboard(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ParentAttendanceDashboardRead:
    authorize(scope, Permission.PARENT_ATTENDANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    year, semester = await academic_term(tenant_id, year=academic_year_label, semester=semester_label)
    await sync_attendance_alerts(tenant_id, parent.id, sid, year=year, semester=semester)
    summary, counts = await semester_attendance_summary(tenant_id, sid, year=year, semester=semester)
    pending = await ParentAttendanceAlert.find(
        {
            "tenant_id": tenant_id,
            "parent_user_id": parent.id,
            "student_user_id": sid,
            "acknowledged_at": None,
        }
    ).count()
    return ParentAttendanceDashboardRead(
        summary=summary,
        present_marks=counts["present_marks"],
        absent_marks=counts["absent_marks"],
        excused_marks=counts["excused_marks"],
        working_sessions=counts["working_sessions"],
        alerts_pending=pending,
    )


async def get_subject_attendance(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> list[SubjectAttendanceDetailRead]:
    authorize(scope, Permission.PARENT_ATTENDANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    year, semester = await academic_term(tenant_id, year=academic_year_label, semester=semester_label)
    summary, _ = await semester_attendance_summary(tenant_id, sid, year=year, semester=semester)
    return summary.subjects


async def get_daily_attendance(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    session_date: date,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> list[AttendanceMarkRead]:
    authorize(scope, Permission.PARENT_ATTENDANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    year, semester = await academic_term(tenant_id, year=academic_year_label, semester=semester_label)
    return await daily_marks(tenant_id, sid, session_date=session_date, year=year, semester=semester)


async def get_attendance_history(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    pagination: Pagination,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> Page[AttendanceMarkRead]:
    authorize(scope, Permission.PARENT_ATTENDANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    year, semester = await academic_term(tenant_id, year=academic_year_label, semester=semester_label)
    items, total = await attendance_history_marks(
        tenant_id, sid, year=year, semester=semester, offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_attendance_shortages(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> list[AttendanceShortageRead]:
    authorize(scope, Permission.PARENT_ATTENDANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    year, semester = await academic_term(tenant_id, year=academic_year_label, semester=semester_label)
    summary, _ = await semester_attendance_summary(tenant_id, sid, year=year, semester=semester)
    return await shortage_list(summary)


async def list_attendance_alerts(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    *,
    unacknowledged_only: bool = False,
) -> list[ParentAttendanceAlertRead]:
    authorize(scope, Permission.PARENT_ATTENDANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    filters: dict = {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    if unacknowledged_only:
        filters["acknowledged_at"] = None
    rows = await ParentAttendanceAlert.find(filters).sort("-updated_at").to_list()
    return [
        ParentAttendanceAlertRead(
            alert_id=str(r.id),
            severity=r.severity,
            title=r.title,
            body=r.body,
            course_code=r.course_code,
            percentage=r.percentage,
            min_required=r.min_required,
            acknowledged=r.acknowledged_at is not None,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


async def acknowledge_alert(scope: AccessScope, parent: User, student_user_id: str, alert_id: str) -> dict:
    authorize(scope, Permission.PARENT_ATTENDANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    aid = PydanticObjectId(alert_id)
    alert = await ParentAttendanceAlert.get(aid)
    if alert is None or str(alert.tenant_id) != str(tenant_id) or str(alert.student_user_id) != str(sid):
        raise AppError(code="NOT_FOUND", message="Alert not found", status_code=404)
    if str(alert.parent_user_id) != str(parent.id):
        raise AppError(code="FORBIDDEN", message="Alert not assigned to this parent", status_code=403)
    now = utcnow()
    alert.acknowledged_at = now
    alert.updated_at = now
    await alert.save()
    existing_ack = await ParentAttendanceAlertAcknowledgement.find_one(
        {"tenant_id": tenant_id, "alert_id": aid, "parent_user_id": parent.id}
    )
    if existing_ack is None:
        await ParentAttendanceAlertAcknowledgement(
            tenant_id=tenant_id, alert_id=aid, parent_user_id=parent.id, acknowledged_at=now
        ).insert()
    return {"alert_id": str(alert.id), "acknowledged_at": now.isoformat()}


async def submit_attendance_enquiry(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    payload: ParentAttendanceEnquiryCreate,
) -> ParentAttendanceEnquiryRead:
    authorize(scope, Permission.PARENT_ATTENDANCE_ENQUIRY)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    rel, _ = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.VIEW_ATTENDANCE)
    doc = ParentAttendanceEnquiry(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        relationship_id=rel.id,
        category=payload.category,
        course_code=payload.course_code,
        section=payload.section,
        attendance_date=payload.attendance_date,
        period_label=payload.period_label,
        description=payload.description.strip(),
        supporting_info=payload.supporting_info,
        status=ParentAttendanceEnquiryStatus.SUBMITTED.value,
    )
    await doc.insert()
    await ParentAttendanceEnquiryHistory(
        tenant_id=tenant_id,
        enquiry_id=doc.id,
        from_status=None,
        to_status=doc.status,
        note="Submitted by parent",
        changed_by=parent.id,
    ).insert()
    return ParentAttendanceEnquiryRead(
        enquiry_id=str(doc.id),
        category=doc.category,
        course_code=doc.course_code,
        section=doc.section,
        attendance_date=doc.attendance_date,
        status=doc.status,
        response_notes=doc.response_notes,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def list_attendance_enquiries(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentAttendanceEnquiryRead]:
    authorize(scope, Permission.PARENT_ATTENDANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_ATTENDANCE)
    rows = await ParentAttendanceEnquiry.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-created_at").to_list()
    return [
        ParentAttendanceEnquiryRead(
            enquiry_id=str(r.id),
            category=r.category,
            course_code=r.course_code,
            section=r.section,
            attendance_date=r.attendance_date,
            status=r.status,
            response_notes=r.response_notes,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]