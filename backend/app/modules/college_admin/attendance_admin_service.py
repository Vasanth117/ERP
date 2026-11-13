"""Attendance administration services."""

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
from app.modules.academics.models import PendingAttendanceSubmission
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceSessionStatus
from app.modules.attendance.models import (
    AttendanceCorrectionRequest,
    AttendancePolicyReference,
    AttendanceRecord,
    AttendanceSession,
)
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.college_admin.attendance_admin_models import (
    AttendanceComplianceSnapshot,
    AttendanceCorrectionApproval,
    AttendancePolicyAudience,
    AttendanceSubmissionMonitoring,
    InstitutionAttendancePolicy,
)
from app.modules.college_admin.attendance_admin_schemas import (
    AttendancePolicyRead,
    AttendancePolicyUpsert,
    AttendanceReportGenerate,
    ComplianceSnapshotRead,
    CorrectionDecision,
    CorrectionRequestRead,
    DepartmentAttendanceSummary,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.faculty.models import FacultyProfile
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()


async def _sync_student_policy(tenant_id: PydanticObjectId, policy: InstitutionAttendancePolicy) -> None:
    if policy.audience != AttendancePolicyAudience.STUDENT or not policy.is_active:
        return
    ref = await AttendancePolicyReference.find_one(Eq(AttendancePolicyReference.tenant_id, tenant_id), Eq(AttendancePolicyReference.policy_code, policy.policy_code))
    if ref is None:
        ref = AttendancePolicyReference(tenant_id=tenant_id, policy_code=policy.policy_code)
    ref.rules = policy.rules
    ref.is_active = True
    ref.updated_at = utcnow()
    if ref.id is None:
        await ref.insert()
    else:
        await ref.save()


async def upsert_attendance_policy(scope: AccessScope, payload: AttendancePolicyUpsert) -> AttendancePolicyRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.policy_code.strip()
    existing = await InstitutionAttendancePolicy.find_one(
        Eq(InstitutionAttendancePolicy.tenant_id, tenant_id),
        Eq(InstitutionAttendancePolicy.policy_code, code),
        Eq(InstitutionAttendancePolicy.audience, payload.audience),
    )
    if existing:
        existing.title = payload.title
        existing.rules = payload.rules
        existing.submission_deadline_hours = payload.submission_deadline_hours
        existing.version += 1
        existing.updated_by = scope.user_id
        existing.updated_at = utcnow()
        await existing.save()
        doc = existing
    else:
        doc = InstitutionAttendancePolicy(
            tenant_id=tenant_id,
            policy_code=code,
            audience=payload.audience,
            title=payload.title,
            rules=payload.rules,
            submission_deadline_hours=payload.submission_deadline_hours,
            updated_by=scope.user_id,
        )
        await doc.insert()
    await _sync_student_policy(tenant_id, doc)
    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="college.attendance.policy_updated",
        resource_type="institution_attendance_policy",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    return AttendancePolicyRead.from_document(doc)


async def list_attendance_policies(scope: AccessScope) -> list[AttendancePolicyRead]:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await InstitutionAttendancePolicy.find(Eq(InstitutionAttendancePolicy.tenant_id, tenant_id)).sort("-updated_at").to_list()
    return [AttendancePolicyRead.from_document(r) for r in rows]


async def refresh_submission_monitoring(scope: AccessScope) -> dict:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    pending = await PendingAttendanceSubmission.find({"tenant_id": tenant_id, "status": "pending"}).to_list()
    await AttendanceSubmissionMonitoring.find(Eq(AttendanceSubmissionMonitoring.tenant_id, tenant_id), Eq(AttendanceSubmissionMonitoring.status, "pending")).delete()
    count = 0
    for row in pending:
        await AttendanceSubmissionMonitoring(
            tenant_id=tenant_id,
            faculty_user_id=row.faculty_user_id,
            course_code=row.course_code,
            section=row.section,
            session_date=row.session_date,
            due_at=row.due_at,
            status="pending",
        ).insert()
        count += 1
    return {"pending_count": count}


async def missing_submissions(scope: AccessScope, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = PendingAttendanceSubmission.find({"tenant_id": tenant_id, "status": "pending"}).sort("due_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        {
            "faculty_user_id": str(r.faculty_user_id),
            "course_code": r.course_code,
            "section": r.section,
            "session_date": r.session_date.isoformat(),
            "due_at": r.due_at.isoformat(),
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def department_summaries(scope: AccessScope) -> list[DepartmentAttendanceSummary]:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).to_list()
    by_dept: dict[str | None, DepartmentAttendanceSummary] = {}
    for profile in profiles:
        key = str(profile.department_id) if profile.department_id else None
        if key not in by_dept:
            by_dept[key] = DepartmentAttendanceSummary(
                department_id=key,
                sessions_submitted=0,
                pending_submissions=0,
                pending_corrections=0,
            )
    sessions = await AttendanceSession.find(Eq(AttendanceSession.tenant_id, tenant_id)).to_list()
    profile_by_user = {str(p.user_id): p for p in profiles}
    for session in sessions:
        profile = profile_by_user.get(str(session.faculty_user_id))
        key = str(profile.department_id) if profile and profile.department_id else None
        if key not in by_dept:
            by_dept[key] = DepartmentAttendanceSummary(department_id=key, sessions_submitted=0, pending_submissions=0, pending_corrections=0)
        if session.status == AttendanceSessionStatus.SUBMITTED:
            by_dept[key].sessions_submitted += 1
    pending = await PendingAttendanceSubmission.find({"tenant_id": tenant_id, "status": "pending"}).to_list()
    for row in pending:
        profile = profile_by_user.get(str(row.faculty_user_id))
        key = str(profile.department_id) if profile and profile.department_id else None
        if key not in by_dept:
            by_dept[key] = DepartmentAttendanceSummary(department_id=key, sessions_submitted=0, pending_submissions=0, pending_corrections=0)
        by_dept[key].pending_submissions += 1
    corrections = await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
    ).to_list()
    for corr in corrections:
        profile = profile_by_user.get(str(corr.faculty_user_id))
        key = str(profile.department_id) if profile and profile.department_id else None
        if key not in by_dept:
            by_dept[key] = DepartmentAttendanceSummary(department_id=key, sessions_submitted=0, pending_submissions=0, pending_corrections=0)
        by_dept[key].pending_corrections += 1
    return list(by_dept.values())


async def list_correction_requests(scope: AccessScope, pagination: Pagination) -> Page[CorrectionRequestRead]:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = AttendanceCorrectionRequest.find(Eq(AttendanceCorrectionRequest.tenant_id, tenant_id)).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            CorrectionRequestRead(
                request_id=str(r.id),
                faculty_user_id=str(r.faculty_user_id),
                session_id=str(r.session_id),
                student_user_id=str(r.student_user_id) if r.student_user_id else None,
                status=r.status.value,
                reason=r.reason,
                created_at=r.created_at,
                resolved_at=r.resolved_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def decide_correction(scope: AccessScope, payload: CorrectionDecision) -> dict:
    authorize(scope, Permission.ATTENDANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    if payload.decision not in (AttendanceCorrectionStatus.APPROVED, AttendanceCorrectionStatus.REJECTED):
        raise AppError(code="VALIDATION_ERROR", message="Decision must be approved or rejected", status_code=422)
    request_id = to_object_id(payload.request_id, "request_id")
    request = await AttendanceCorrectionRequest.get(request_id)
    if request is None or request.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    if request.status != AttendanceCorrectionStatus.PENDING:
        raise AppError(code="CONFLICT", message="Correction request is already resolved", status_code=409)
    if await AttendanceCorrectionApproval.find_one(
        Eq(AttendanceCorrectionApproval.tenant_id, tenant_id),
        Eq(AttendanceCorrectionApproval.correction_request_id, request_id),
    ):
        raise AppError(code="CONFLICT", message="Correction already reviewed", status_code=409)

    session = await AttendanceSession.get(request.session_id)
    if session is None or session.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Attendance session not found", status_code=404)
    if session.status == AttendanceSessionStatus.DRAFT:
        raise AppError(code="VALIDATION_ERROR", message="Session is not submitted", status_code=422)

    applied = False
    request.status = payload.decision
    request.reviewer_note = payload.reviewer_note
    request.resolved_at = utcnow()
    await request.save()

    if payload.decision == AttendanceCorrectionStatus.APPROVED and request.student_user_id and request.requested_status:
        record = await AttendanceRecord.find_one(
            Eq(AttendanceRecord.session_id, request.session_id),
            Eq(AttendanceRecord.student_user_id, request.student_user_id),
        )
        if record is None:
            record = AttendanceRecord(
                tenant_id=tenant_id,
                session_id=request.session_id,
                student_user_id=request.student_user_id,
                status=request.requested_status,
                remarks=f"Admin correction approval ({payload.reviewer_note or 'approved'})",
            )
            await record.insert()
        else:
            record.status = request.requested_status
            record.remarks = (record.remarks or "") + " | admin correction applied"
            record.updated_at = utcnow()
            await record.save()
        applied = True

    approval = AttendanceCorrectionApproval(
        tenant_id=tenant_id,
        correction_request_id=request_id,
        decision=payload.decision,
        reviewer_id=scope.user_id,
        reviewer_note=payload.reviewer_note,
        applied_to_record=applied,
    )
    await approval.insert()
    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="college.attendance.correction_decided",
        resource_type="attendance_correction_request",
        resource_id=str(request_id),
        tenant_id=tenant_id,
        metadata={"decision": payload.decision.value, "applied": applied},
    )
    return {"request_id": str(request_id), "decision": payload.decision.value, "applied_to_record": applied}


async def attendance_shortages(scope: AccessScope, *, course_code: str | None = None, section: str | None = None) -> list[dict]:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    policy_doc = await InstitutionAttendancePolicy.find_one(
        Eq(InstitutionAttendancePolicy.tenant_id, tenant_id),
        Eq(InstitutionAttendancePolicy.audience, AttendancePolicyAudience.STUDENT),
        Eq(InstitutionAttendancePolicy.is_active, True),
    )
    min_pct = policy_doc.rules.min_percentage_required if policy_doc else 75.0
    filters: dict = {"tenant_id": tenant_id, "status": AttendanceSessionStatus.SUBMITTED}
    if course_code:
        filters["course_code"] = course_code.upper()
    if section:
        filters["section"] = section.upper()
    sessions = await AttendanceSession.find(filters).to_list()
    shortages: list[dict] = []
    seen: set[str] = set()
    for session in sessions:
        records = await AttendanceRecord.find(Eq(AttendanceRecord.session_id, session.id)).to_list()
        by_student: dict[str, list] = {}
        for rec in records:
            by_student.setdefault(str(rec.student_user_id), []).append(rec)
        policy_rules = policy_doc.rules if policy_doc else None
        from app.modules.attendance.models import AttendancePolicyRules

        rules = policy_rules or AttendancePolicyRules()
        for student_id, recs in by_student.items():
            if student_id in seen:
                continue
            all_recs = await AttendanceRecord.find(
                Eq(AttendanceRecord.tenant_id, tenant_id),
                Eq(AttendanceRecord.student_user_id, to_object_id(student_id, "student_id")),
            ).to_list()
            pct = calculate_percentage(all_recs, rules)
            if pct < min_pct:
                seen.add(student_id)
                user = await _user_repo.get(to_object_id(student_id, "student_id"))
                shortages.append(
                    {
                        "student_user_id": student_id,
                        "display_name": user.full_name if user else None,
                        "percentage": pct,
                        "min_required": min_pct,
                    }
                )
    return shortages


async def generate_compliance_snapshot(scope: AccessScope, payload: AttendanceReportGenerate) -> ComplianceSnapshotRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    dept_id = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    summaries = await department_summaries(scope)
    match = next((s for s in summaries if s.department_id == (str(dept_id) if dept_id else None)), None)
    pending_sub = match.pending_submissions if match else await PendingAttendanceSubmission.find({"tenant_id": tenant_id, "status": "pending"}).count()
    pending_corr = match.pending_corrections if match else await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
    ).count()
    sessions_sub = match.sessions_submitted if match else await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).count()
    shortage_list = await attendance_shortages(scope)
    snap = AttendanceComplianceSnapshot(
        tenant_id=tenant_id,
        department_id=dept_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        pending_submissions=pending_sub,
        pending_corrections=pending_corr,
        sessions_submitted=sessions_sub,
        students_below_threshold=len(shortage_list),
        metrics={"shortage_sample_count": len(shortage_list)},
        generated_by=scope.user_id,
    )
    await snap.insert()
    return ComplianceSnapshotRead(
        snapshot_id=str(snap.id),
        department_id=str(dept_id) if dept_id else None,
        pending_submissions=snap.pending_submissions,
        pending_corrections=snap.pending_corrections,
        sessions_submitted=snap.sessions_submitted,
        students_below_threshold=snap.students_below_threshold,
        metrics=snap.metrics,
        generated_at=snap.generated_at,
    )


async def attendance_history(
    scope: AccessScope,
    *,
    faculty_user_id: str | None = None,
    session_date: date | None = None,
    pagination: Pagination,
) -> Page[dict]:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    filters: dict = {"tenant_id": tenant_id}
    if faculty_user_id:
        filters["faculty_user_id"] = to_object_id(faculty_user_id, "faculty_user_id")
    if session_date:
        filters["session_date"] = session_date
    query = AttendanceSession.find(filters).sort("-session_date")
    total = await query.count()
    sessions = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        {
            "session_id": str(s.id),
            "faculty_user_id": str(s.faculty_user_id),
            "course_code": s.course_code,
            "section": s.section,
            "session_date": s.session_date.isoformat(),
            "status": s.status.value,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        }
        for s in sessions
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)
