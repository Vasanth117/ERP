"""Faculty attendance workflows."""

from datetime import date, datetime

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.models import PendingAttendanceSubmission
from app.modules.academics.repositories import AcademicQueryRepository
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import (
    AttendanceCorrectionRequest,
    AttendancePolicyReference,
    AttendanceRecord,
    AttendanceSession,
)
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.faculty.attendance_schemas import (
    AssignedClassRead,
    AttendanceCorrectionCreate,
    AttendanceCorrectionRead,
    AttendanceRecordRead,
    AttendanceReportRead,
    AttendanceSessionCreate,
    AttendanceSessionRead,
    AttendanceShortageStudent,
    AttendanceSubmitPayload,
    StudentAttendanceSummary,
    SubjectAttendanceSummary,
)
from app.modules.faculty.course_access import require_course_access, resolve_course_id
from app.modules.faculty.enums import FacultyActivityType
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.repositories import FacultyActivityRepository, FacultyAssignmentRepository
from app.common.ids import to_object_id

_assignment_repo = FacultyAssignmentRepository()
_activity_repo = FacultyActivityRepository()
_academic = AcademicQueryRepository()


async def _policy(tenant_id: PydanticObjectId) -> AttendancePolicyReference:
    doc = await AttendancePolicyReference.find_one({"tenant_id": tenant_id, "is_active": True})
    if doc is None:
        doc = AttendancePolicyReference(tenant_id=tenant_id)
        await doc.insert()
    return doc


def _session_read(session: AttendanceSession) -> AttendanceSessionRead:
    return AttendanceSessionRead(
        id=str(session.id),
        course_code=session.course_code,
        section=session.section,
        session_date=session.session_date,
        status=session.status,
        subject_id=session.subject_id,
        submitted_at=session.submitted_at,
    )


async def list_assigned_classes(scope: AccessScope, user: User) -> list[AssignedClassRead]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await _assignment_repo.list_active_for_user(tenant_id, user.id)
    return [
        AssignedClassRead(
            course_code=r.course_code,
            course_name=r.course_name,
            section=r.section,
            course_id=r.course_id,
            subject_id=r.subject_id,
        )
        for r in rows
    ]


async def roster_for_class(
    scope: AccessScope,
    user: User,
    course_code: str,
    section: str,
) -> list[dict[str, str]]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    course_id = await resolve_course_id(tenant_id, course_code)
    roster = await _academic.roster(tenant_id, course_id, section)
    return [
        {"student_user_id": str(e.student_user_id), "roll_number": e.roll_number, "display_name": e.display_name}
        for e in roster
    ]


async def create_attendance_session(
    scope: AccessScope,
    user: User,
    payload: AttendanceSessionCreate,
) -> AttendanceSessionRead:
    authorize(scope, Permission.FACULTY_ATTENDANCE_MANAGE)
    tenant_id = require_faculty_scope(scope)
    assignment = await require_course_access(
        tenant_id, user.id, course_code=payload.course_code, section=payload.section
    )
    course_id = assignment.course_id or await resolve_course_id(tenant_id, payload.course_code)
    existing = await AttendanceSession.find_one(
        {
            "tenant_id": tenant_id,
            "course_code": payload.course_code,
            "section": payload.section,
            "session_date": payload.session_date,
            "faculty_user_id": user.id,
        }
    )
    if existing and existing.status != AttendanceSessionStatus.DRAFT:
        raise AppError(
            code="CONFLICT",
            message="Attendance for this class and date is already submitted",
            status_code=409,
        )
    if existing:
        return _session_read(existing)
    class_session_id = (
        to_object_id(payload.class_session_id, "class session id") if payload.class_session_id else None
    )
    session = AttendanceSession(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        course_id=course_id,
        course_code=payload.course_code,
        section=payload.section,
        subject_id=payload.subject_id or assignment.subject_id,
        class_session_id=class_session_id,
        session_date=payload.session_date,
        academic_year_label=assignment.academic_year_label,
        semester_label=assignment.semester_label,
    )
    await session.insert()
    return _session_read(session)


async def list_attendance_sessions(
    scope: AccessScope,
    user: User,
    *,
    course_code: str | None = None,
    section: str | None = None,
    session_date: date | None = None,
) -> list[AttendanceSessionRead]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    filters: dict = {"tenant_id": tenant_id, "faculty_user_id": user.id}
    if course_code:
        filters["course_code"] = course_code
    if section:
        filters["section"] = section
    if session_date:
        filters["session_date"] = session_date
    sessions = await AttendanceSession.find(filters).sort("-session_date").to_list()
    return [_session_read(s) for s in sessions]


async def submit_attendance(
    scope: AccessScope,
    user: User,
    session_id: PydanticObjectId,
    payload: AttendanceSubmitPayload,
) -> AttendanceSessionRead:
    authorize(scope, Permission.FACULTY_ATTENDANCE_MANAGE)
    tenant_id = require_faculty_scope(scope)
    session = await AttendanceSession.get(session_id)
    if session is None or str(session.tenant_id) != str(tenant_id) or str(session.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Attendance session not found", status_code=404)
    if session.status != AttendanceSessionStatus.DRAFT:
        raise AppError(code="CONFLICT", message="Attendance session is already submitted", status_code=409)
    await require_course_access(tenant_id, user.id, course_code=session.course_code, section=session.section)
    course_id = session.course_id
    roster = await _academic.roster(tenant_id, course_id, session.section)
    allowed_students = {str(e.student_user_id) for e in roster}
    for mark in payload.marks:
        if mark.student_user_id not in allowed_students:
            raise AppError(code="FORBIDDEN", message="Student is not in this class roster", status_code=403)
    for mark in payload.marks:
        student_id = to_object_id(mark.student_user_id, "student id")
        existing = await AttendanceRecord.find_one({"session_id": session_id, "student_user_id": student_id})
        if existing:
            existing.status = mark.status
            existing.remarks = mark.remarks
            existing.updated_at = utcnow()
            await existing.save()
        else:
            await AttendanceRecord(
                tenant_id=tenant_id,
                session_id=session_id,
                student_user_id=student_id,
                status=mark.status,
                remarks=mark.remarks,
            ).insert()
    session.status = AttendanceSessionStatus.SUBMITTED
    session.submitted_at = utcnow()
    session.updated_at = utcnow()
    await session.save()
    await PendingAttendanceSubmission.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": user.id,
            "course_code": session.course_code,
            "section": session.section,
            "session_date": session.session_date,
            "status": "pending",
        }
    ).delete()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.ATTENDANCE_SUBMITTED,
        title=f"Attendance submitted {session.course_code}/{session.section}",
        metadata={"session_id": str(session_id)},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.attendance.submitted",
        resource_type="attendance_session",
        resource_id=str(session_id),
        tenant_id=tenant_id,
        metadata={"course_code": session.course_code, "section": session.section},
    )
    return _session_read(session)


async def get_session_records(
    scope: AccessScope,
    user: User,
    session_id: PydanticObjectId,
) -> list[AttendanceRecordRead]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    session = await AttendanceSession.get(session_id)
    if session is None or str(session.tenant_id) != str(tenant_id) or str(session.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Attendance session not found", status_code=404)
    records = await AttendanceRecord.find({"session_id": session_id}).to_list()
    return [
        AttendanceRecordRead(
            student_user_id=str(r.student_user_id),
            status=r.status,
            remarks=r.remarks,
        )
        for r in records
    ]


async def _records_for_section(
    tenant_id: PydanticObjectId,
    course_code: str,
    section: str,
    faculty_user_id: PydanticObjectId,
) -> tuple[list[AttendanceRecord], list[AttendanceSession]]:
    sessions = await AttendanceSession.find(
        {
            "tenant_id": tenant_id,
            "course_code": course_code,
            "section": section,
            "faculty_user_id": faculty_user_id,
            "status": AttendanceSessionStatus.SUBMITTED,
        }
    ).to_list()
    if not sessions:
        return [], sessions
    session_ids = [s.id for s in sessions]
    records = await AttendanceRecord.find({"session_id": {"$in": session_ids}}).to_list()
    return records, sessions


async def student_summaries(
    scope: AccessScope,
    user: User,
    course_code: str,
    section: str,
) -> list[StudentAttendanceSummary]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    await require_course_access(tenant_id, user.id, course_code=course_code, section=section)
    policy = await _policy(tenant_id)
    records, sessions = await _records_for_section(tenant_id, course_code, section, user.id)
    by_student: dict[str, list[AttendanceRecord]] = {}
    for record in records:
        key = str(record.student_user_id)
        by_student.setdefault(key, []).append(record)
    summaries: list[StudentAttendanceSummary] = []
    for student_id, student_records in by_student.items():
        pct = calculate_percentage(student_records, policy.rules)
        summaries.append(
            StudentAttendanceSummary(
                student_user_id=student_id,
                total_sessions=len(sessions),
                percentage=pct,
                below_threshold=pct < policy.rules.min_percentage_required,
            )
        )
    return summaries


async def subject_summaries(
    scope: AccessScope,
    user: User,
    course_code: str,
    section: str,
) -> list[SubjectAttendanceSummary]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    student = await student_summaries(scope, user, course_code, section)
    if not student:
        return [
            SubjectAttendanceSummary(
                subject_id=None,
                course_code=course_code,
                section=section,
                average_percentage=0.0,
            )
        ]
    avg = round(sum(s.percentage for s in student) / len(student), 2)
    return [
        SubjectAttendanceSummary(
            subject_id=None,
            course_code=course_code,
            section=section,
            average_percentage=avg,
        )
    ]


async def attendance_shortages(
    scope: AccessScope,
    user: User,
    course_code: str,
    section: str,
) -> list[AttendanceShortageStudent]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    policy = await _policy(tenant_id)
    summaries = await student_summaries(scope, user, course_code, section)
    return [
        AttendanceShortageStudent(
            student_user_id=s.student_user_id,
            percentage=s.percentage,
            min_required=policy.rules.min_percentage_required,
        )
        for s in summaries
        if s.below_threshold
    ]


async def missing_submissions(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    pending = await PendingAttendanceSubmission.find(
        {"tenant_id": tenant_id, "faculty_user_id": user.id, "status": "pending"}
    ).sort("due_at").to_list()
    return [
        {
            "course_code": p.course_code,
            "section": p.section,
            "session_date": p.session_date.isoformat(),
            "due_at": p.due_at.isoformat(),
        }
        for p in pending
    ]


async def submit_correction_request(
    scope: AccessScope,
    user: User,
    payload: AttendanceCorrectionCreate,
) -> AttendanceCorrectionRead:
    authorize(scope, Permission.FACULTY_ATTENDANCE_MANAGE)
    tenant_id = require_faculty_scope(scope)
    session_id = to_object_id(payload.session_id, "session id")
    session = await AttendanceSession.get(session_id)
    if session is None or str(session.tenant_id) != str(tenant_id) or str(session.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Attendance session not found", status_code=404)
    if session.status == AttendanceSessionStatus.DRAFT:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Submit attendance before requesting corrections",
            status_code=422,
        )
    student_id = to_object_id(payload.student_user_id, "student id") if payload.student_user_id else None
    request = AttendanceCorrectionRequest(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        session_id=session_id,
        student_user_id=student_id,
        requested_status=payload.requested_status,
        reason=payload.reason,
        status=AttendanceCorrectionStatus.PENDING,
    )
    await request.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.attendance.correction_requested",
        resource_type="attendance_correction_request",
        resource_id=str(request.id),
        tenant_id=tenant_id,
    )
    return AttendanceCorrectionRead(
        id=str(request.id),
        session_id=str(session_id),
        status=request.status.value,
        reason=request.reason,
        created_at=request.created_at,
        resolved_at=request.resolved_at,
    )


async def list_correction_requests(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[AttendanceCorrectionRead]:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    query = AttendanceCorrectionRequest.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-created_at")
    total = await query.count()
    items = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            AttendanceCorrectionRead(
                id=str(i.id),
                session_id=str(i.session_id),
                status=i.status.value,
                reason=i.reason,
                created_at=i.created_at,
                resolved_at=i.resolved_at,
            )
            for i in items
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def attendance_report(
    scope: AccessScope,
    user: User,
    course_code: str,
    section: str,
) -> AttendanceReportRead:
    authorize(scope, Permission.FACULTY_ATTENDANCE_READ)
    tenant_id = require_faculty_scope(scope)
    policy = await _policy(tenant_id)
    summaries = await student_summaries(scope, user, course_code, section)
    shortages = await attendance_shortages(scope, user, course_code, section)
    return AttendanceReportRead(
        course_code=course_code,
        section=section,
        policy_min_percentage=policy.rules.min_percentage_required,
        student_summaries=summaries,
        shortages=shortages,
        generated_at=utcnow(),
    )


async def daily_attendance(
    scope: AccessScope,
    user: User,
    session_date: date,
) -> list[AttendanceSessionRead]:
    return await list_attendance_sessions(scope, user, session_date=session_date)
