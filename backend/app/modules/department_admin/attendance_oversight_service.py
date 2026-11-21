"""Department Admin attendance oversight (read-only + delegated correction review)."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.models import ClassSession, PendingAttendanceSubmission
from app.modules.department_admin.attendance_eligibility import filter_pending_requiring_submission, is_attendance_submission_expected
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceCorrectionRequest, AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.attendance_admin_models import AttendanceCorrectionApproval, AttendancePolicyAudience, InstitutionAttendancePolicy
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.department_admin.department_scope import faculty_user_ids_in_department
from app.modules.department_admin.integrations.department_data_reader import DepartmentDataReader
from app.modules.department_admin.models import DepartmentAttendanceDiscrepancy
from app.modules.department_admin.phase4_schemas import (
    AttendanceClassSummary,
    AttendanceCorrectionRead,
    AttendanceCorrectionReview,
    AttendanceDiscrepancyRead,
    AttendanceFacultySubmissionRead,
    AttendanceMissingSessionRead,
    AttendanceOverviewFilters,
    AttendanceOverviewRead,
    AttendanceShortageRead,
    AttendanceStudentSummary,
    AttendanceSubjectSummary,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.faculty.models import FacultyAssignment

_reader = DepartmentDataReader()


async def _active_policy(tenant_id: PydanticObjectId):
    inst = await InstitutionAttendancePolicy.find_one(
        Eq(InstitutionAttendancePolicy.tenant_id, tenant_id),
        Eq(InstitutionAttendancePolicy.audience, AttendancePolicyAudience.STUDENT),
        Eq(InstitutionAttendancePolicy.is_active, True),
    )
    if inst:
        return inst.rules, "institution_attendance_policies"
    ref = await AttendancePolicyReference.find_one(Eq(AttendancePolicyReference.tenant_id, tenant_id), Eq(AttendancePolicyReference.is_active, True))
    if ref:
        return ref.rules, "attendance_policy_references"
    return None, "default"


async def _dept_faculty_ids(scope: AccessScope, user: User) -> tuple[PydanticObjectId, PydanticObjectId, set[PydanticObjectId]]:
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_ids = await faculty_user_ids_in_department(tenant_id, central_id)
    return tenant_id, central_id, faculty_ids


async def _count_missing_submissions(tenant_id: PydanticObjectId, faculty_ids: set[PydanticObjectId]) -> int:
    if not faculty_ids:
        return 0
    pending = await PendingAttendanceSubmission.find(
        {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
    ).to_list()
    filtered = await filter_pending_requiring_submission(tenant_id, pending)
    return len(filtered)


async def attendance_overview(scope: AccessScope, user: User, filters: AttendanceOverviewFilters) -> AttendanceOverviewRead:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_READ)
    tenant_id, central_id, faculty_ids = await _dept_faculty_ids(scope, user)
    raw = await _reader.attendance_overview(tenant_id, central_id)
    missing = await _count_missing_submissions(tenant_id, faculty_ids)
    rules, source = await _active_policy(tenant_id)
    return AttendanceOverviewRead(
        sessions_submitted=raw["sessions_submitted"],
        pending_submissions=missing,
        correction_requests_open=raw["correction_requests_open"],
        missing_submission_count=missing,
        policy_min_percentage=rules.min_percentage_required if rules else None,
        threshold_source=source,
    )


async def attendance_classes(scope: AccessScope, user: User, filters: AttendanceOverviewFilters) -> list[AttendanceClassSummary]:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_READ)
    tenant_id, central_id, faculty_ids = await _dept_faculty_ids(scope, user)
    if not faculty_ids:
        return []
    session_filters: dict = {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
    if filters.date_from:
        session_filters.setdefault("session_date", {})["$gte"] = filters.date_from
    if filters.date_to:
        session_filters.setdefault("session_date", {})["$lte"] = filters.date_to
    sessions = await AttendanceSession.find(session_filters).to_list()
    summaries: dict[tuple[str, str], AttendanceClassSummary] = {}
    for s in sessions:
        key = (s.course_code, s.section)
        item = summaries.get(key)
        if item is None:
            item = AttendanceClassSummary(
                course_code=s.course_code,
                section=s.section,
                sessions_scheduled=0,
                sessions_submitted=0,
                sessions_missing=0,
            )
            summaries[key] = item
        item.sessions_scheduled += 1
        if s.status == AttendanceSessionStatus.SUBMITTED:
            item.sessions_submitted += 1
    pending = await PendingAttendanceSubmission.find(
        {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
    ).to_list()
    pending = await filter_pending_requiring_submission(tenant_id, pending)
    for p in pending:
        key = (p.class_label, p.section)
        if key not in summaries:
            summaries[key] = AttendanceClassSummary(
                course_code=p.class_label,
                section=p.section,
                sessions_scheduled=0,
                sessions_submitted=0,
                sessions_missing=0,
            )
        summaries[key].sessions_missing += 1
    return list(summaries.values())


async def attendance_subjects(scope: AccessScope, user: User) -> list[AttendanceSubjectSummary]:
    classes = await attendance_classes(scope, user, AttendanceOverviewFilters())
    by_course: dict[str, AttendanceSubjectSummary] = {}
    for row in classes:
        item = by_course.get(row.course_code)
        if item is None:
            item = AttendanceSubjectSummary(course_code=row.course_code, sections=[], submitted_count=0, missing_count=0)
            by_course[row.course_code] = item
        if row.section not in item.sections:
            item.sections.append(row.section)
        item.submitted_count += row.sessions_submitted
        item.missing_count += row.sessions_missing
    return list(by_course.values())


async def attendance_students(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[AttendanceStudentSummary]:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_READ)
    tenant_id, central_id, faculty_ids = await _dept_faculty_ids(scope, user)
    rules, _ = await _active_policy(tenant_id)
    threshold = rules.min_percentage_required if rules else 75.0
    records = await StudentRecord.find({"tenant_id": tenant_id, "department_id": central_id}).skip(pagination.offset).limit(pagination.limit).to_list()
    total = await StudentRecord.find({"tenant_id": tenant_id, "department_id": central_id}).count()
    items: list[AttendanceStudentSummary] = []
    for record in records:
        recs = await AttendanceRecord.find(Eq(AttendanceRecord.tenant_id, tenant_id), Eq(AttendanceRecord.student_user_id, record.user_id)).to_list()
        if faculty_ids:
            session_ids = [r.session_id for r in recs]
            if session_ids:
                sessions = await AttendanceSession.find(
                    {"_id": {"$in": session_ids}, "faculty_user_id": {"$in": list(faculty_ids)}}
                ).to_list()
                allowed = {s.id for s in sessions}
                recs = [r for r in recs if r.session_id in allowed]
        pct = calculate_percentage(recs, rules) if rules and recs else (calculate_percentage(recs, rules) if recs else 0.0)
        items.append(
            AttendanceStudentSummary(
                student_user_id=str(record.user_id),
                roll_number=record.roll_number,
                percentage=pct,
                threshold=threshold,
                below_threshold=pct < threshold,
                sessions_counted=len(recs),
            )
        )
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def faculty_submissions(scope: AccessScope, user: User) -> list[AttendanceFacultySubmissionRead]:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_READ)
    tenant_id, _, faculty_ids = await _dept_faculty_ids(scope, user)
    items: list[AttendanceFacultySubmissionRead] = []
    for fid in faculty_ids:
        submitted = await AttendanceSession.find(
            Eq(AttendanceSession.tenant_id, tenant_id),
            Eq(AttendanceSession.faculty_user_id, fid),
            Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
        ).count()
        pending_rows = await PendingAttendanceSubmission.find(
            Eq(PendingAttendanceSubmission.tenant_id, tenant_id),
            Eq(PendingAttendanceSubmission.faculty_user_id, fid),
        ).to_list()
        pending = len(await filter_pending_requiring_submission(tenant_id, pending_rows))
        faculty_user = await User.get(fid)
        items.append(
            AttendanceFacultySubmissionRead(
                faculty_user_id=str(fid),
                full_name=faculty_user.full_name if faculty_user else None,
                submitted_sessions=submitted,
                pending_sessions=pending,
                late_submissions=0,
            )
        )
    return items


async def missing_attendance(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[AttendanceMissingSessionRead]:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_READ)
    tenant_id, _, faculty_ids = await _dept_faculty_ids(scope, user)
    all_pending = await PendingAttendanceSubmission.find(
        {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
    ).sort("-session_date").to_list()
    rows = await filter_pending_requiring_submission(tenant_id, all_pending)
    total = len(rows)
    rows = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[
            AttendanceMissingSessionRead(
                faculty_user_id=str(r.faculty_user_id),
                course_code=r.class_label,
                section=r.section,
                session_date=r.session_date,
                status=r.status,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def attendance_shortages(scope: AccessScope, user: User) -> list[AttendanceShortageRead]:
    page = await attendance_students(scope, user, pagination=Pagination(limit=500, offset=0))
    rules, _ = await _active_policy(scope.tenant_id)
    assert scope.tenant_id is not None
    threshold = rules.min_percentage_required if rules else 75.0
    shortages: list[AttendanceShortageRead] = []
    for student in page.items:
        if not student.below_threshold:
            continue
        shortages.append(
            AttendanceShortageRead(
                student_user_id=student.student_user_id,
                course_code="all",
                section="all",
                percentage=student.percentage,
                threshold=threshold,
                attended_weight=student.percentage,
                eligible_sessions=student.sessions_counted,
            )
        )
    return shortages


async def _upsert_discrepancy(
    *,
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    discrepancy_type: str,
    summary: str,
    session_id: PydanticObjectId | None = None,
    faculty_user_id: PydanticObjectId | None = None,
    student_user_id: PydanticObjectId | None = None,
) -> DepartmentAttendanceDiscrepancy:
    if session_id is not None:
        existing = await DepartmentAttendanceDiscrepancy.find_one(
            Eq(DepartmentAttendanceDiscrepancy.tenant_id, tenant_id),
            Eq(DepartmentAttendanceDiscrepancy.central_department_id, central_id),
            Eq(DepartmentAttendanceDiscrepancy.discrepancy_type, discrepancy_type),
            Eq(DepartmentAttendanceDiscrepancy.session_id, session_id),
        )
        if existing:
            return existing
    doc = DepartmentAttendanceDiscrepancy(
        tenant_id=tenant_id,
        central_department_id=central_id,
        discrepancy_type=discrepancy_type,
        summary=summary,
        session_id=session_id,
        faculty_user_id=faculty_user_id,
        student_user_id=student_user_id,
    )
    try:
        await doc.insert()
    except Exception:
        existing = await DepartmentAttendanceDiscrepancy.find_one(
            Eq(DepartmentAttendanceDiscrepancy.tenant_id, tenant_id),
            Eq(DepartmentAttendanceDiscrepancy.central_department_id, central_id),
            Eq(DepartmentAttendanceDiscrepancy.discrepancy_type, discrepancy_type),
            Eq(DepartmentAttendanceDiscrepancy.session_id, session_id),
        )
        if existing:
            return existing
        raise
    return doc


def _discrepancy_read(doc: DepartmentAttendanceDiscrepancy) -> AttendanceDiscrepancyRead:
    return AttendanceDiscrepancyRead(
        discrepancy_id=str(doc.id),
        discrepancy_type=doc.discrepancy_type,
        summary=doc.summary,
        session_id=str(doc.session_id) if doc.session_id else None,
        status=doc.status,
        detected_at=doc.detected_at,
    )


async def scan_discrepancies(scope: AccessScope, user: User) -> list[AttendanceDiscrepancyRead]:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_MANAGE)
    tenant_id, central_id, faculty_ids = await _dept_faculty_ids(scope, user)
    found: list[AttendanceDiscrepancyRead] = []
    pending = await PendingAttendanceSubmission.find(
        {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
    ).limit(200).to_list()
    for row in pending:
        expected, reason = await is_attendance_submission_expected(
            tenant_id,
            faculty_user_id=row.faculty_user_id,
            course_code=row.class_label,
            section=row.section,
            session_date=row.session_date,
        )
        if not expected:
            continue
        summary = f"Pending attendance for {row.class_label}/{row.section} on {row.session_date}"
        existing = await DepartmentAttendanceDiscrepancy.find_one(
            {
                "tenant_id": tenant_id,
                "central_department_id": central_id,
                "discrepancy_type": "missing_attendance_submission",
                "summary": summary,
            }
        )
        if existing:
            found.append(_discrepancy_read(existing))
            continue
        doc = await _upsert_discrepancy(
            tenant_id=tenant_id,
            central_id=central_id,
            discrepancy_type="missing_attendance_submission",
            summary=summary,
            faculty_user_id=row.faculty_user_id,
        )
        found.append(_discrepancy_read(doc))

    completed = await ClassSession.find(
        {
            "tenant_id": tenant_id,
            "faculty_user_id": {"$in": list(faculty_ids)},
            "status": "completed",
        }
    ).limit(200).to_list()
    for class_session in completed:
        session_date = class_session.scheduled_start.date()
        att = await AttendanceSession.find_one(
            {
                "tenant_id": tenant_id,
                "faculty_user_id": class_session.faculty_user_id,
                "course_code": class_session.course_code,
                "section": class_session.section,
                "session_date": session_date,
                "status": AttendanceSessionStatus.SUBMITTED,
            }
        )
        if att is not None:
            continue
        expected, _ = await is_attendance_submission_expected(
            tenant_id,
            faculty_user_id=class_session.faculty_user_id,
            course_code=class_session.course_code,
            section=class_session.section,
            session_date=session_date,
        )
        if not expected:
            continue
        summary = f"Completed class {class_session.course_code}/{class_session.section} on {session_date} id={class_session.id}"
        existing = await DepartmentAttendanceDiscrepancy.find_one(
            {
                "tenant_id": tenant_id,
                "central_department_id": central_id,
                "discrepancy_type": "completed_session_no_attendance",
                "summary": summary,
            }
        )
        if existing:
            found.append(_discrepancy_read(existing))
            continue
        doc = await _upsert_discrepancy(
            tenant_id=tenant_id,
            central_id=central_id,
            discrepancy_type="completed_session_no_attendance",
            summary=summary,
            faculty_user_id=class_session.faculty_user_id,
        )
        found.append(_discrepancy_read(doc))

    sessions = await AttendanceSession.find({"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}).limit(200).to_list()
    for session in sessions:
        assign = await FacultyAssignment.find_one(
            Eq(FacultyAssignment.tenant_id, tenant_id),
            Eq(FacultyAssignment.user_id, session.faculty_user_id),
            Eq(FacultyAssignment.course_code, session.course_code),
            Eq(FacultyAssignment.section, session.section),
        )
        if assign is None:
            doc = await _upsert_discrepancy(
                tenant_id=tenant_id,
                central_id=central_id,
                discrepancy_type="faculty_not_assigned_subject",
                summary=f"Faculty not assigned to {session.course_code}/{session.section}",
                session_id=session.id,
                faculty_user_id=session.faculty_user_id,
            )
            found.append(_discrepancy_read(doc))
    return found


async def list_discrepancies(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[AttendanceDiscrepancyRead]:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_READ)
    tenant_id, central_id, _ = await _dept_faculty_ids(scope, user)
    query = DepartmentAttendanceDiscrepancy.find(
        Eq(DepartmentAttendanceDiscrepancy.tenant_id, tenant_id),
        Eq(DepartmentAttendanceDiscrepancy.central_department_id, central_id),
    )
    total = await query.count()
    rows = await query.sort("-detected_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            AttendanceDiscrepancyRead(
                discrepancy_id=str(r.id),
                discrepancy_type=r.discrepancy_type,
                summary=r.summary,
                session_id=str(r.session_id) if r.session_id else None,
                status=r.status,
                detected_at=r.detected_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def list_correction_requests(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[AttendanceCorrectionRead]:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_READ)
    tenant_id, _, faculty_ids = await _dept_faculty_ids(scope, user)
    query = AttendanceCorrectionRequest.find(
        {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            AttendanceCorrectionRead(
                request_id=str(r.id),
                faculty_user_id=str(r.faculty_user_id),
                session_id=str(r.session_id),
                student_user_id=str(r.student_user_id) if r.student_user_id else None,
                status=r.status.value,
                reason=r.reason,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_correction_request(scope: AccessScope, user: User, request_id: str) -> AttendanceCorrectionRead:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_READ)
    tenant_id, _, faculty_ids = await _dept_faculty_ids(scope, user)
    doc = await AttendanceCorrectionRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.faculty_user_id not in faculty_ids:
        raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    return AttendanceCorrectionRead(
        request_id=str(doc.id),
        faculty_user_id=str(doc.faculty_user_id),
        session_id=str(doc.session_id),
        student_user_id=str(doc.student_user_id) if doc.student_user_id else None,
        status=doc.status.value,
        reason=doc.reason,
        created_at=doc.created_at,
    )


async def review_correction_request(
    scope: AccessScope,
    user: User,
    request_id: str,
    payload: AttendanceCorrectionReview,
) -> AttendanceCorrectionRead:
    authorize(scope, Permission.DEPARTMENT_ATTENDANCE_MANAGE)
    tenant_id, central_id, faculty_ids = await _dept_faculty_ids(scope, user)
    doc = await AttendanceCorrectionRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.faculty_user_id not in faculty_ids:
        raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    if doc.status != AttendanceCorrectionStatus.PENDING:
        return await get_correction_request(scope, user, request_id)
    if await AttendanceCorrectionApproval.find_one(
        Eq(AttendanceCorrectionApproval.tenant_id, tenant_id),
        Eq(AttendanceCorrectionApproval.correction_request_id, doc.id),
    ):
        raise AppError(code="CONFLICT", message="Correction already reviewed", status_code=409)
    from app.modules.college_admin.models import InstitutionSettings

    inst_settings = await InstitutionSettings.find_one({"tenant_id": tenant_id})
    requires_college = bool((inst_settings.settings or {}).get("attendance_correction_requires_college_approval", False))
    decision = AttendanceCorrectionStatus.APPROVED if payload.decision == "approve" else AttendanceCorrectionStatus.REJECTED
    if requires_college and decision == AttendanceCorrectionStatus.APPROVED:
        doc.department_endorsed_at = utcnow()
        doc.department_endorsed_by = user.id
        await doc.save()
        await record_department_audit(
            actor_id=user.id,
            action="department.attendance.correction_endorsed",
            resource_type="attendance_correction_request",
            resource_id=str(doc.id),
            tenant_id=tenant_id,
            central_department_id=central_id,
            metadata={"decision": decision.value, "requires_college_approval": True},
        )
        return await get_correction_request(scope, user, request_id)
    session = await AttendanceSession.get(doc.session_id)
    if session is None or session.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Attendance session not found", status_code=404)
    applied = False
    doc.status = decision
    doc.reviewer_note = payload.reviewer_note
    doc.resolved_at = utcnow()
    await doc.save()
    if decision == AttendanceCorrectionStatus.APPROVED and doc.student_user_id and doc.requested_status:
        record = await AttendanceRecord.find_one(
            Eq(AttendanceRecord.session_id, doc.session_id),
            Eq(AttendanceRecord.student_user_id, doc.student_user_id),
        )
        if record is None:
            record = AttendanceRecord(
                tenant_id=tenant_id,
                session_id=doc.session_id,
                student_user_id=doc.student_user_id,
                status=doc.requested_status,
                remarks=f"Dept correction ({payload.reviewer_note or 'approved'})",
            )
            await record.insert()
        else:
            record.status = doc.requested_status
            record.updated_at = utcnow()
            await record.save()
        applied = True
    await AttendanceCorrectionApproval(
        tenant_id=tenant_id,
        correction_request_id=doc.id,
        decision=decision,
        reviewer_id=user.id,
        reviewer_note=payload.reviewer_note,
        applied_to_record=applied,
    ).insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.attendance.correction_review",
        resource_type="attendance_correction_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={"decision": decision.value, "applied": applied, "department_id": str(central_id)},
    )
    return await get_correction_request(scope, user, request_id)