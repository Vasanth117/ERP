"""Read authoritative attendance for a student (parent portal)."""

from datetime import date

from beanie import PydanticObjectId

from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.student_schedule_enums import AttendanceDataStatus
from app.modules.students.student_schedule_schemas import (
    AttendanceMarkRead,
    AttendanceSemesterSummaryRead,
    AttendanceShortageRead,
    SubjectAttendanceDetailRead,
)

_reader = StudentDataReader()


async def academic_term(tenant_id: PydanticObjectId, *, year: str | None, semester: str | None) -> tuple[str, str]:
    if year and semester:
        return year, semester
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        from app.core.exceptions import AppError

        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def active_policy(tenant_id: PydanticObjectId) -> AttendancePolicyReference:
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


async def course_attendance_detail(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
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
    found: list[AttendanceRecord] = []
    records: list[AttendanceRecord] = []
    if session_ids:
        found = await AttendanceRecord.find(
            {"tenant_id": tenant_id, "student_user_id": student_user_id, "session_id": {"$in": session_ids}}
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
                        student_user_id=student_user_id,
                        status=AttendanceMarkStatus.ABSENT,
                    )
                )
    pct = calculate_percentage(records, policy.rules) if sessions else None
    min_req = policy.rules.min_percentage_required
    below = pct is not None and pct < min_req
    return SubjectAttendanceDetailRead(
        course_code=course_code,
        section=section,
        percentage=pct,
        sessions_held=len(sessions),
        sessions_recorded=len(found) if session_ids else 0,
        min_required=min_req,
        below_threshold=below,
        data_status=_data_status(len(sessions), len(found) if session_ids else 0),
        subject_id=None,
    )


async def semester_attendance_summary(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> tuple[AttendanceSemesterSummaryRead, dict[str, int]]:
    policy = await active_policy(tenant_id)
    roster = await _reader.roster_entries(tenant_id, student_user_id, academic_year_label=year, semester_label=semester)
    subjects: list[SubjectAttendanceDetailRead] = []
    weighted_sum = 0.0
    weighted_sessions = 0
    warnings: list[str] = []
    any_data = False
    present_total = absent_total = excused_total = 0
    for entry in roster:
        detail = await course_attendance_detail(
            tenant_id,
            student_user_id,
            course_code=entry.course_code,
            section=entry.section_code,
            year=year,
            semester=semester,
            policy=policy,
        )
        subjects.append(detail)
        if detail.data_status != AttendanceDataStatus.NOT_AVAILABLE:
            any_data = True
        if detail.below_threshold and detail.percentage is not None:
            warnings.append(f"{detail.course_code}: {detail.percentage}% (min {detail.min_required}%)")
        if detail.percentage is not None and detail.sessions_held > 0:
            weighted_sum += detail.percentage * detail.sessions_held
            weighted_sessions += detail.sessions_held
        sessions = await AttendanceSession.find(
            {
                "tenant_id": tenant_id,
                "course_code": entry.course_code,
                "section": entry.section_code,
                "academic_year_label": year,
                "semester_label": semester,
                "status": {"$in": [AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED]},
            }
        ).to_list()
        sids = [s.id for s in sessions]
        if sids:
            recs = await AttendanceRecord.find(
                {"tenant_id": tenant_id, "student_user_id": student_user_id, "session_id": {"$in": sids}}
            ).to_list()
            present_total += sum(1 for r in recs if r.status == AttendanceMarkStatus.PRESENT)
            present_total += sum(1 for r in recs if r.status == AttendanceMarkStatus.LATE)
            excused_total += sum(1 for r in recs if r.status == AttendanceMarkStatus.EXCUSED)
            absent_total += sum(1 for r in recs if r.status == AttendanceMarkStatus.ABSENT)
    overall = round(weighted_sum / weighted_sessions, 2) if weighted_sessions else None
    ds = (
        AttendanceDataStatus.AVAILABLE
        if any_data and all(s.data_status == AttendanceDataStatus.AVAILABLE for s in subjects if s.sessions_held)
        else (AttendanceDataStatus.PARTIAL if any_data else AttendanceDataStatus.NOT_AVAILABLE)
    )
    summary = AttendanceSemesterSummaryRead(
        academic_year_label=year,
        semester_label=semester,
        overall_percentage=overall,
        min_required=policy.rules.min_percentage_required,
        data_status=ds,
        subjects=subjects,
        shortage_warnings=warnings,
    )
    counts = {
        "working_sessions": weighted_sessions,
        "present_marks": present_total,
        "absent_marks": absent_total,
        "excused_marks": excused_total,
    }
    return summary, counts


async def shortage_list(summary: AttendanceSemesterSummaryRead) -> list[AttendanceShortageRead]:
    shortages: list[AttendanceShortageRead] = []
    for s in summary.subjects:
        if not s.below_threshold:
            continue
        remaining = None
        if s.percentage is not None and s.sessions_held > 0:
            need = (s.min_required / 100) * (s.sessions_held + 10) - (s.percentage / 100) * s.sessions_held
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


async def daily_marks(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    session_date: date,
    year: str,
    semester: str,
) -> list[AttendanceMarkRead]:
    sessions = await AttendanceSession.find(
        {
            "tenant_id": tenant_id,
            "session_date": session_date,
            "academic_year_label": year,
            "semester_label": semester,
            "status": {"$in": [AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED]},
        }
    ).to_list()
    roster = await _reader.roster_entries(tenant_id, student_user_id, academic_year_label=year, semester_label=semester)
    allowed = {(r.course_code, r.section_code) for r in roster}
    sessions = [s for s in sessions if (s.course_code, s.section) in allowed]
    results: list[AttendanceMarkRead] = []
    for sess in sessions:
        rec = await AttendanceRecord.find_one({"session_id": sess.id, "student_user_id": student_user_id})
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


async def attendance_history_marks(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    offset: int,
    limit: int,
) -> tuple[list[AttendanceMarkRead], int]:
    sessions = await AttendanceSession.find(
        {
            "tenant_id": tenant_id,
            "academic_year_label": year,
            "semester_label": semester,
            "status": {"$in": [AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED]},
        }
    ).sort("-session_date").to_list()
    roster = await _reader.roster_entries(tenant_id, student_user_id, academic_year_label=year, semester_label=semester)
    allowed = {(r.course_code, r.section_code) for r in roster}
    sessions = [s for s in sessions if (s.course_code, s.section) in allowed]
    session_ids = [s.id for s in sessions]
    records: list[AttendanceRecord] = []
    if session_ids:
        records = await AttendanceRecord.find(
            {"tenant_id": tenant_id, "student_user_id": student_user_id, "session_id": {"$in": session_ids}}
        ).to_list()
    record_by_session = {r.session_id: r for r in records}
    items: list[AttendanceMarkRead] = []
    for sess in sessions:
        rec = record_by_session.get(sess.id)
        verified = sess.status in {AttendanceSessionStatus.SUBMITTED, AttendanceSessionStatus.LOCKED}
        items.append(
            AttendanceMarkRead(
                session_id=str(sess.id),
                session_date=sess.session_date,
                course_code=sess.course_code,
                section=sess.section,
                status=rec.status if rec else None,
                verified=verified and rec is not None,
            )
        )
    chunk = items[offset : offset + limit]
    return chunk, len(items)