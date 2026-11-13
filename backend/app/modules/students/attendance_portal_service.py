"""Student attendance views and discrepancy workflow."""

from datetime import date, datetime, timezone

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.enums import StudentActivityType
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.student_schedule_enums import AttendanceDataStatus, AttendanceNotificationType, DiscrepancyRequestStatus
from app.modules.students.student_schedule_models import AttendanceNotificationRecord, StudentAttendanceDiscrepancyRequest
from app.modules.students.student_schedule_schemas import (
    AttendanceEligibilityRead,
    AttendanceMarkRead,
    AttendanceSemesterSummaryRead,
    AttendanceShortageRead,
    AttendanceSummaryExportRead,
    DiscrepancyRequestCreate,
    DiscrepancyRequestRead,
    SubjectAttendanceDetailRead,
)
from app.modules.students.policy import require_student_scope
from app.modules.students.repositories import StudentActivityRepository

_reader = StudentDataReader()
_activity_repo = StudentActivityRepository()


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _policy(tenant_id: PydanticObjectId) -> AttendancePolicyReference:
    doc = await AttendancePolicyReference.find_one({"tenant_id": tenant_id, "is_active": True})
    if doc is None:
        return AttendancePolicyReference(tenant_id=tenant_id, policy_code="default")
    return doc


def _data_status(sessions_held: int, sessions_recorded: int) -> AttendanceDataStatus:
    if sessions_held == 0:
        return AttendanceDataStatus.NOT_AVAILABLE
    if sessions_recorded >= sessions_held:
        return AttendanceDataStatus.AVAILABLE
    return AttendanceDataStatus.PARTIAL


async def _course_attendance(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    course_code: str,
    section: str,
    year: str,
    semester: str,
    policy: AttendancePolicyReference,
) -> SubjectAttendanceDetailRead:
    sessions = await AttendanceSession.find(
        {
            "tenant_id": tenant_id,
            "course_code": course_code,
            "section": section,
            "academic_year_label": year,
            "semester_label": semester,
            "status": {"$in": [AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED]},
        }
    ).to_list()
    session_ids = [s.id for s in sessions]
    records: list[AttendanceRecord] = []
    found: list[AttendanceRecord] = []
    if session_ids:
        found = await AttendanceRecord.find(
            {"tenant_id": tenant_id, "student_user_id": user_id, "session_id": {"$in": session_ids}}
        ).to_list()
        by_session = {r.session_id: r for r in found}
        for sid in session_ids:
            if sid in by_session:
                records.append(by_session[sid])
            else:
                records.append(
                    AttendanceRecord(
                        tenant_id=tenant_id,
                        session_id=sid,
                        student_user_id=user_id,
                        status=AttendanceMarkStatus.ABSENT,
                    )
                )
    pct = calculate_percentage(records, policy.rules) if sessions else None
    min_req = policy.rules.min_percentage_required
    ds = _data_status(len(sessions), len(records))
    below = pct is not None and pct < min_req
    return SubjectAttendanceDetailRead(
        course_code=course_code,
        section=section,
        percentage=pct,
        sessions_held=len(sessions),
        sessions_recorded=len(found) if session_ids else 0,
        min_required=min_req,
        below_threshold=below,
        data_status=ds,
    )


async def get_attendance_summary(scope: AccessScope, user: User) -> AttendanceSemesterSummaryRead:
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    policy = await _policy(tenant_id)
    roster = await _reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    subjects: list[SubjectAttendanceDetailRead] = []
    weighted_sum = 0.0
    weighted_sessions = 0
    warnings: list[str] = []
    any_data = False
    for entry in roster:
        detail = await _course_attendance(
            tenant_id,
            user.id,
            course_code=entry.course_code,
            section=entry.section_code,
            year=year,
            semester=semester,
            policy=policy,
        )
        subjects.append(detail)
        if detail.data_status != AttendanceDataStatus.NOT_AVAILABLE:
            any_data = True
        if detail.below_threshold:
            warnings.append(f"{detail.course_code}: {detail.percentage}% (min {detail.min_required}%)")
            await _maybe_shortage_notification(tenant_id, user.id, detail)
        if detail.percentage is not None and detail.sessions_held > 0:
            weighted_sum += detail.percentage * detail.sessions_held
            weighted_sessions += detail.sessions_held
    overall = round(weighted_sum / weighted_sessions, 2) if weighted_sessions else None
    ds = AttendanceDataStatus.AVAILABLE if any_data and all(s.data_status == AttendanceDataStatus.AVAILABLE for s in subjects if s.sessions_held) else (
        AttendanceDataStatus.PARTIAL if any_data else AttendanceDataStatus.NOT_AVAILABLE
    )
    return AttendanceSemesterSummaryRead(
        academic_year_label=year,
        semester_label=semester,
        overall_percentage=overall,
        min_required=policy.rules.min_percentage_required,
        data_status=ds,
        subjects=subjects,
        shortage_warnings=warnings,
    )


async def _maybe_shortage_notification(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, detail: SubjectAttendanceDetailRead
) -> None:
    existing = await AttendanceNotificationRecord.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "course_code": detail.course_code,
            "notification_type": AttendanceNotificationType.SHORTAGE_WARNING,
            "read_at": None,
        }
    )
    if existing:
        return
    await AttendanceNotificationRecord(
        tenant_id=tenant_id,
        user_id=user_id,
        notification_type=AttendanceNotificationType.SHORTAGE_WARNING,
        title=f"Attendance shortage — {detail.course_code}",
        body=f"Your attendance is {detail.percentage}% (required {detail.min_required}%)",
        course_code=detail.course_code,
    ).insert()


async def get_subject_wise_attendance(scope: AccessScope, user: User) -> list[SubjectAttendanceDetailRead]:
    summary = await get_attendance_summary(scope, user)
    return summary.subjects


async def get_daily_attendance(scope: AccessScope, user: User, session_date: date) -> list[AttendanceMarkRead]:
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    sessions = await AttendanceSession.find(
        {
            "tenant_id": tenant_id,
            "session_date": session_date,
            "academic_year_label": year,
            "semester_label": semester,
            "status": {"$in": [AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED]},
        }
    ).to_list()
    roster = await _reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    allowed = {(r.course_code, r.section_code) for r in roster}
    sessions = [s for s in sessions if (s.course_code, s.section) in allowed]
    results: list[AttendanceMarkRead] = []
    for sess in sessions:
        rec = await AttendanceRecord.find_one({"session_id": sess.id, "student_user_id": user.id})
        verified = sess.status in {AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED} and rec is not None
        results.append(
            AttendanceMarkRead(
                session_id=str(sess.id),
                session_date=sess.session_date,
                course_code=sess.course_code,
                section=sess.section,
                status=rec.status if rec else None,
                verified=verified,
            )
        )
    return results


async def attendance_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[AttendanceMarkRead]:
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    sessions = await AttendanceSession.find(
        {
            "tenant_id": tenant_id,
            "academic_year_label": year,
            "semester_label": semester,
        }
    ).sort("-session_date").to_list()
    roster = await _reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    allowed = {(r.course_code, r.section_code) for r in roster}
    sessions = [s for s in sessions if (s.course_code, s.section) in allowed]
    session_ids = [s.id for s in sessions]
    if not session_ids:
        return Page(items=[], total=0, limit=pagination.limit, offset=pagination.offset)
    records = await AttendanceRecord.find(
        {"tenant_id": tenant_id, "student_user_id": user.id, "session_id": {"$in": session_ids}}
    ).to_list()
    record_by_session = {r.session_id: r for r in records}
    items: list[AttendanceMarkRead] = []
    for sess in sessions:
        rec = record_by_session.get(sess.id)
        verified = sess.status in {AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED} and rec is not None
        items.append(
            AttendanceMarkRead(
                session_id=str(sess.id),
                session_date=sess.session_date,
                course_code=sess.course_code,
                section=sess.section,
                status=rec.status if rec else None,
                verified=verified,
            )
        )
    chunk = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=chunk, total=len(items), limit=pagination.limit, offset=pagination.offset)


async def get_shortage_details(scope: AccessScope, user: User) -> list[AttendanceShortageRead]:
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    summary = await get_attendance_summary(scope, user)
    shortages: list[AttendanceShortageRead] = []
    for s in summary.subjects:
        if not s.below_threshold:
            continue
        remaining = None
        if s.percentage is not None and s.sessions_held > 0:
            min_req = s.min_required
            need = (min_req / 100) * (s.sessions_held + 10) - (s.percentage / 100) * s.sessions_held
            remaining = max(0, int(need * 10))
        shortages.append(
            AttendanceShortageRead(
                course_code=s.course_code,
                section=s.section,
                percentage=s.percentage,
                min_required=s.min_required,
                sessions_remaining_to_clear=remaining,
            )
        )
    return shortages


async def get_attendance_eligibility(scope: AccessScope, user: User) -> AttendanceEligibilityRead:
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    summary = await get_attendance_summary(scope, user)
    reasons: list[str] = []
    if summary.data_status == AttendanceDataStatus.NOT_AVAILABLE:
        reasons.append("Attendance data is not yet available for all subjects")
    elif summary.data_status == AttendanceDataStatus.PARTIAL:
        reasons.append("Some attendance records are pending verification")
    eligible = False
    if summary.overall_percentage is None:
        reasons.append("Overall percentage cannot be verified yet")
    else:
        eligible = summary.overall_percentage >= summary.min_required and not summary.shortage_warnings
        if summary.shortage_warnings:
            reasons.extend(summary.shortage_warnings)
    return AttendanceEligibilityRead(
        eligible=eligible,
        overall_percentage=summary.overall_percentage,
        min_required=summary.min_required,
        reasons=reasons,
        data_status=summary.data_status,
    )


async def submit_discrepancy_request(
    scope: AccessScope, user: User, payload: DiscrepancyRequestCreate
) -> DiscrepancyRequestRead:
    authorize(scope, Permission.STUDENT_ATTENDANCE_DISCREPANCY)
    tenant_id = require_student_scope(scope)
    session_id = to_object_id(payload.session_id, "session id")
    session = await AttendanceSession.get(session_id)
    if session is None or str(session.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Attendance session not found", status_code=404)
    roster = await _reader.roster_entries(
        tenant_id, user.id, academic_year_label=session.academic_year_label, semester_label=session.semester_label
    )
    if not any(r.course_code == session.course_code and r.section_code == session.section for r in roster):
        raise AppError(code="FORBIDDEN", message="Session is outside your enrolled classes", status_code=403)
    record = await AttendanceRecord.find_one({"session_id": session_id, "student_user_id": user.id})
    doc = StudentAttendanceDiscrepancyRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        session_id=session_id,
        course_code=session.course_code,
        section=session.section,
        session_date=session.session_date,
        recorded_status=record.status if record else None,
        claimed_status=payload.claimed_status,
        reason=payload.reason.strip(),
        status=DiscrepancyRequestStatus.PENDING,
    )
    await doc.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.attendance.discrepancy_submitted",
        resource_type="student_attendance_discrepancy_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=StudentActivityType.OTHER,
        title="Attendance discrepancy submitted",
        description=session.course_code,
    )
    return _discrepancy_read(doc)


def _discrepancy_read(doc: StudentAttendanceDiscrepancyRequest) -> DiscrepancyRequestRead:
    return DiscrepancyRequestRead(
        id=str(doc.id),
        session_id=str(doc.session_id),
        course_code=doc.course_code,
        section=doc.section,
        session_date=doc.session_date,
        recorded_status=doc.recorded_status,
        claimed_status=doc.claimed_status,
        reason=doc.reason,
        status=doc.status,
        reviewer_note=doc.reviewer_note,
        submitted_at=doc.submitted_at,
        resolved_at=doc.resolved_at,
    )


async def get_discrepancy_status(scope: AccessScope, user: User, request_id: str) -> DiscrepancyRequestRead:
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    tenant_id = require_student_scope(scope)
    rid = to_object_id(request_id, "request id")
    doc = await StudentAttendanceDiscrepancyRequest.get(rid)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Discrepancy request not found", status_code=404)
    return _discrepancy_read(doc)


async def list_discrepancy_requests(scope: AccessScope, user: User, pagination: Pagination) -> Page[DiscrepancyRequestRead]:
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    tenant_id = require_student_scope(scope)
    query = StudentAttendanceDiscrepancyRequest.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-submitted_at")
    total = await query.count()
    items = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_discrepancy_read(i) for i in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def export_attendance_summary(scope: AccessScope, user: User) -> AttendanceSummaryExportRead:
    authorize(scope, Permission.STUDENT_ATTENDANCE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    summary = await get_attendance_summary(scope, user)
    lines = ["course_code,section,percentage,sessions_held,sessions_recorded,data_status,below_threshold"]
    for s in summary.subjects:
        lines.append(
            f"{s.course_code},{s.section},{s.percentage},{s.sessions_held},{s.sessions_recorded},{s.data_status.value},{s.below_threshold}"
        )
    return AttendanceSummaryExportRead(
        generated_at=utcnow(),
        academic_year_label=year,
        semester_label=semester,
        data_status=summary.data_status,
        csv_content="\n".join(lines),
    )
