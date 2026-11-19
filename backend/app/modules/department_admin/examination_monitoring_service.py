"""Department Admin — examination schedule, readiness, pending tasks, coordination issues."""

from __future__ import annotations

from datetime import datetime, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.models import ExaminationSchedule, PendingAssignmentEvaluation
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.examination_admin_models import InstitutionExaminationSchedule
from app.modules.department_admin.assessment_monitoring_service import _context
from app.modules.department_admin.department_scope import assert_course_in_department, assert_faculty_visible_to_department
from app.modules.department_admin.examination_monitoring_logic import (
    ADVISORY_DISCLAIMER,
    READINESS_TYPE,
    all_required_met,
    pending_task_key,
    readiness_indicator,
)
from app.modules.department_admin.models import (
    DepartmentExaminationCoordinationIssue,
    DepartmentExaminationIssueStatus,
)
from app.modules.department_admin.phase5_schemas import (
    AssessmentMonitoringFilters,
    CoordinationIssueCreate,
    CoordinationIssueRead,
    CoordinationIssueUpdate,
    ExaminationPendingTaskRead,
    ExaminationReadinessRead,
    ExaminationScheduleItemRead,
)
from app.modules.examinations.enums import MarksBatchStatus
from app.modules.examinations.models import Assessment, AssessmentComponent, FacultyAssessmentAssignment, MarksSubmissionBatch
from app.modules.examinations.semester_examination_models import SemesterExaminationSession
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def list_examinations(
    scope: AccessScope,
    user: User,
    *,
    filters: AssessmentMonitoringFilters,
    pagination: Pagination,
    season_id: str | None = None,
) -> Page[ExaminationScheduleItemRead]:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, faculty_ids, course_codes, programme_codes = await _context(scope, user)
    if filters.programme_code and filters.programme_code.upper() not in programme_codes:
        raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    if filters.course_code:
        await assert_course_in_department(tenant_id, central_id, filters.course_code)
    items: list[ExaminationScheduleItemRead] = []
    faculty_list = list(faculty_ids) if faculty_ids else []
    course_list = list(course_codes)
    if faculty_list:
        exam_q: dict = {"tenant_id": tenant_id, "faculty_user_id": {"$in": faculty_list}}
        if filters.academic_year_label:
            exam_q["academic_year_label"] = filters.academic_year_label
        if filters.semester_label:
            exam_q["semester_label"] = filters.semester_label
        if filters.course_code:
            exam_q["course_code"] = filters.course_code.upper()
        if filters.date_from or filters.date_to:
            sched: dict = {}
            if filters.date_from:
                sched["$gte"] = filters.date_from
            if filters.date_to:
                sched["$lte"] = filters.date_to
            exam_q["scheduled_at"] = sched
        for row in await ExaminationSchedule.find(exam_q).sort("scheduled_at").limit(500).to_list():
            if row.course_code.upper() not in course_codes:
                continue
            items.append(
                ExaminationScheduleItemRead(
                    source="faculty_examination_schedule",
                    course_code=row.course_code,
                    section=row.section,
                    exam_type=row.exam_type,
                    title=row.title,
                    scheduled_at=row.scheduled_at,
                    scheduled_end=row.scheduled_end,
                    room=row.room,
                    centre_code=row.centre_code,
                    faculty_user_id=str(row.faculty_user_id) if row.faculty_user_id else None,
                    academic_year_label=row.academic_year_label,
                    semester_label=row.semester_label,
                    examination_session_code=row.examination_session_code,
                )
            )
    if course_list:
        session_q: dict = {
            "tenant_id": tenant_id,
            "course_code": {"$in": course_list},
            "published": True,
        }
        if season_id:
            session_q["season_id"] = season_id
        if filters.course_code:
            session_q["course_code"] = filters.course_code.upper()
        if filters.date_from or filters.date_to:
            start: dict = {}
            if filters.date_from:
                start["$gte"] = filters.date_from
            if filters.date_to:
                start["$lte"] = filters.date_to
            session_q["scheduled_start"] = start
        for row in await SemesterExaminationSession.find(session_q).sort("scheduled_start").limit(500).to_list():
            items.append(
                ExaminationScheduleItemRead(
                    source="semester_examination_session",
                    course_code=row.course_code,
                    section=row.section,
                    exam_type="semester",
                    title=row.course_name or row.course_code,
                    scheduled_at=row.scheduled_start,
                    scheduled_end=row.scheduled_end,
                    room=row.room,
                    centre_code=row.centre_code,
                    season_id=row.season_id,
                    session_code=row.session_code,
                )
            )
        college_q: dict = {"tenant_id": tenant_id, "course_code": {"$in": course_list}}
        if season_id:
            college_q["season_id"] = season_id
        if filters.course_code:
            college_q["course_code"] = filters.course_code.upper()
        for row in await InstitutionExaminationSchedule.find(college_q).sort("scheduled_start").limit(200).to_list():
            items.append(
                ExaminationScheduleItemRead(
                    source="college_examination_schedule",
                    course_code=row.course_code,
                    exam_type="college_log",
                    title=row.session_code,
                    scheduled_at=row.scheduled_start,
                    scheduled_end=row.scheduled_end,
                    room=row.room,
                    centre_code=row.centre_code,
                    season_id=row.season_id,
                    session_code=row.session_code,
                    published=row.published,
                )
            )
    items.sort(key=lambda r: r.scheduled_at or datetime.min.replace(tzinfo=timezone.utc))
    total = len(items)
    page = items[pagination.skip : pagination.skip + pagination.page_size]
    return Page(items=page, total=total, page=pagination.page, page_size=pagination.page_size)


async def examination_readiness(
    scope: AccessScope,
    user: User,
    *,
    course_code: str,
    section: str | None,
    season_id: str | None,
) -> ExaminationReadinessRead:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, faculty_ids, course_codes, _ = await _context(scope, user)
    await assert_course_in_department(tenant_id, central_id, course_code)
    code = course_code.upper()
    indicators: list[dict] = []
    session = None
    if season_id:
        session = await SemesterExaminationSession.find_one(
            {"tenant_id": tenant_id, "season_id": season_id, "course_code": code, "published": True}
        )
    else:
        session = await SemesterExaminationSession.find_one(
            {"tenant_id": tenant_id, "course_code": code, "published": True}
        )
    indicators.append(
        readiness_indicator(
            "semester_session_scheduled",
            session is not None,
            "semester_examination_sessions",
        )
    )
    assign_filters: dict = {"tenant_id": tenant_id, "course_code": code}
    if section:
        assign_filters["section"] = section
    if faculty_ids:
        assign_filters["faculty_user_id"] = {"$in": list(faculty_ids)}
    assignment_count = await FacultyAssessmentAssignment.find(assign_filters).count()
    indicators.append(
        readiness_indicator(
            "faculty_assigned",
            assignment_count > 0,
            "faculty_assessment_assignments",
            detail=f"count={assignment_count}",
        )
    )
    marks_ok = True
    if section and faculty_ids:
        assignments = await FacultyAssessmentAssignment.find(assign_filters).to_list()
        for assign in assignments:
            components = await AssessmentComponent.find(
                {"tenant_id": tenant_id, "assessment_id": assign.assessment_id, "faculty_may_enter": True}
            ).to_list()
            for comp in components:
                batch = await MarksSubmissionBatch.find_one(
                    {
                        "tenant_id": tenant_id,
                        "faculty_user_id": assign.faculty_user_id,
                        "assessment_id": assign.assessment_id,
                        "component_id": comp.component_id,
                        "section": assign.section,
                    }
                )
                st = batch.status if batch else None
                if st not in {MarksBatchStatus.APPROVED}:
                    assessment = await Assessment.find_one({"tenant_id": tenant_id, "assessment_id": assign.assessment_id})
                    if assessment and (assessment.locked or assessment.final_results_published):
                        continue
                    marks_ok = False
                    break
            if not marks_ok:
                break
    indicators.append(
        readiness_indicator("internal_marks_approved", marks_ok, "marks_submission_batches")
    )
    open_issues = await DepartmentExaminationCoordinationIssue.find(
        Eq(DepartmentExaminationCoordinationIssue.tenant_id, tenant_id),
        Eq(DepartmentExaminationCoordinationIssue.central_department_id, central_id),
        Eq(DepartmentExaminationCoordinationIssue.status, DepartmentExaminationIssueStatus.OPEN),
    ).count()
    indicators.append(
        readiness_indicator(
            "no_open_coordination_issues",
            open_issues == 0,
            "department_examination_coordination_issues",
            detail=f"open={open_issues}",
        )
    )
    required = {"semester_session_scheduled", "faculty_assigned", "internal_marks_approved"}
    return ExaminationReadinessRead(
        course_code=code,
        section=section,
        season_id=season_id or (session.season_id if session else None),
        indicators=indicators,
        all_required_met=all_required_met(indicators, required),
        readiness_type=READINESS_TYPE,
        formal_approval_authority=ADVISORY_DISCLAIMER,
    )


async def examination_pending_tasks(
    scope: AccessScope,
    user: User,
    *,
    filters: AssessmentMonitoringFilters,
    pagination: Pagination,
) -> Page[ExaminationPendingTaskRead]:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, faculty_ids, course_codes, _ = await _context(scope, user)
    tasks: list[ExaminationPendingTaskRead] = []
    batch_q: dict = {
        "tenant_id": tenant_id,
        "course_code": {"$in": list(course_codes)},
        "status": {"$in": [MarksBatchStatus.DRAFT, MarksBatchStatus.SUBMITTED, MarksBatchStatus.PENDING_APPROVAL]},
    }
    if faculty_ids:
        batch_q["faculty_user_id"] = {"$in": list(faculty_ids)}
    if filters.course_code:
        batch_q["course_code"] = filters.course_code.upper()
    for b in await MarksSubmissionBatch.find(batch_q).sort("-updated_at").limit(200).to_list():
        tasks.append(
            ExaminationPendingTaskRead(
                task_type="pending_marks_batch",
                title=f"Marks batch {b.status.value} — {b.course_code} {b.section}",
                reference_id=str(b.id),
                course_code=b.course_code,
                section=b.section,
                faculty_user_id=str(b.faculty_user_id),
                status=b.status.value,
            )
        )
    if faculty_ids:
        for row in await PendingAssignmentEvaluation.find(
            {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
        ).limit(100).to_list():
            if row.course_code.upper() not in course_codes:
                continue
            tasks.append(
                ExaminationPendingTaskRead(
                    task_type="pending_assignment_evaluation",
                    title=row.title,
                    reference_id=row.assignment_id,
                    course_code=row.course_code,
                    faculty_user_id=str(row.faculty_user_id),
                    due_at=row.due_at,
                    status="pending",
                )
            )
    for issue in await DepartmentExaminationCoordinationIssue.find(
        Eq(DepartmentExaminationCoordinationIssue.tenant_id, tenant_id),
        Eq(DepartmentExaminationCoordinationIssue.central_department_id, central_id),
        In(
            DepartmentExaminationCoordinationIssue.status,
            [DepartmentExaminationIssueStatus.OPEN, DepartmentExaminationIssueStatus.IN_PROGRESS],
        ),
    ).limit(100).to_list():
        tasks.append(
            ExaminationPendingTaskRead(
                task_type="open_coordination_issue",
                title=issue.title,
                reference_id=str(issue.id),
                course_code=issue.references.get("course_code"),
                faculty_user_id=str(issue.assigned_faculty_user_id) if issue.assigned_faculty_user_id else None,
                status=issue.status.value,
                severity=issue.severity,
            )
        )
    seen: set[str] = set()
    unique: list[ExaminationPendingTaskRead] = []
    for t in tasks:
        key = pending_task_key(t.task_type, t.reference_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(t)
    total = len(unique)
    page = unique[pagination.skip : pagination.skip + pagination.page_size]
    return Page(items=page, total=total, page=pagination.page, page_size=pagination.page_size)


def _issue_read(doc: DepartmentExaminationCoordinationIssue) -> CoordinationIssueRead:
    return CoordinationIssueRead(
        issue_id=str(doc.id),
        issue_type=doc.issue_type,
        severity=doc.severity,
        title=doc.title,
        description=doc.description,
        references=doc.references,
        assigned_faculty_user_id=str(doc.assigned_faculty_user_id) if doc.assigned_faculty_user_id else None,
        due_date=doc.due_date,
        status=doc.status.value,
        resolution_notes=doc.resolution_notes,
        created_by=str(doc.created_by),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def create_coordination_issue(
    scope: AccessScope,
    user: User,
    payload: CoordinationIssueCreate,
) -> CoordinationIssueRead:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_MANAGE)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    if payload.references.course_code:
        await assert_course_in_department(tenant_id, central_id, payload.references.course_code)
    if payload.assigned_faculty_user_id:
        await assert_faculty_visible_to_department(
            tenant_id, central_id, PydanticObjectId(payload.assigned_faculty_user_id)
        )
    if payload.idempotency_key:
        existing = await DepartmentExaminationCoordinationIssue.find_one(
            Eq(DepartmentExaminationCoordinationIssue.tenant_id, tenant_id),
            Eq(DepartmentExaminationCoordinationIssue.idempotency_key, payload.idempotency_key),
        )
        if existing and existing.central_department_id == central_id:
            return _issue_read(existing)
    refs = payload.references.model_dump(exclude_none=True)
    doc = DepartmentExaminationCoordinationIssue(
        tenant_id=tenant_id,
        central_department_id=central_id,
        issue_type=payload.issue_type,
        severity=payload.severity,
        title=payload.title,
        description=payload.description,
        references=refs,
        assigned_faculty_user_id=(
            PydanticObjectId(payload.assigned_faculty_user_id) if payload.assigned_faculty_user_id else None
        ),
        due_date=payload.due_date,
        idempotency_key=payload.idempotency_key,
        created_by=user.id,
    )
    try:
        await doc.insert()
    except Exception:
        if payload.idempotency_key:
            dup = await DepartmentExaminationCoordinationIssue.find_one(
                Eq(DepartmentExaminationCoordinationIssue.tenant_id, tenant_id),
                Eq(DepartmentExaminationCoordinationIssue.idempotency_key, payload.idempotency_key),
            )
            if dup:
                return _issue_read(dup)
        raise
    await record_department_audit(
        actor_id=scope.user_id,
        action="department.examination_issue.created",
        resource_type="department_examination_coordination_issue",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _issue_read(doc)


async def list_coordination_issues(
    scope: AccessScope,
    user: User,
    *,
    status: str | None,
    pagination: Pagination,
) -> Page[CoordinationIssueRead]:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    filters = [
        Eq(DepartmentExaminationCoordinationIssue.tenant_id, tenant_id),
        Eq(DepartmentExaminationCoordinationIssue.central_department_id, central_id),
    ]
    if status:
        filters.append(Eq(DepartmentExaminationCoordinationIssue.status, DepartmentExaminationIssueStatus(status)))
    query = DepartmentExaminationCoordinationIssue.find(*filters).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.skip).limit(pagination.page_size).to_list()
    return Page(
        items=[_issue_read(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


async def update_coordination_issue(
    scope: AccessScope,
    user: User,
    issue_id: str,
    payload: CoordinationIssueUpdate,
) -> CoordinationIssueRead:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_MANAGE)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    doc = await DepartmentExaminationCoordinationIssue.get(to_object_id(issue_id, "issue_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Coordination issue not found", status_code=404)
    if payload.assigned_faculty_user_id:
        await assert_faculty_visible_to_department(
            tenant_id, central_id, PydanticObjectId(payload.assigned_faculty_user_id)
        )
    if payload.status:
        doc.status = DepartmentExaminationIssueStatus(payload.status)
    if payload.resolution_notes is not None:
        doc.resolution_notes = payload.resolution_notes
    if payload.assigned_faculty_user_id is not None:
        doc.assigned_faculty_user_id = (
            PydanticObjectId(payload.assigned_faculty_user_id) if payload.assigned_faculty_user_id else None
        )
    if payload.due_date is not None:
        doc.due_date = payload.due_date
    doc.updated_at = utcnow()
    await doc.save()
    await record_department_audit(
        actor_id=scope.user_id,
        action="department.examination_issue.updated",
        resource_type="department_examination_coordination_issue",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _issue_read(doc)


async def send_coordination_reminder(
    scope: AccessScope,
    user: User,
    issue_id: str,
    *,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_MANAGE)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    doc = await DepartmentExaminationCoordinationIssue.get(to_object_id(issue_id, "issue_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Coordination issue not found", status_code=404)
    if doc.assigned_faculty_user_id is None:
        raise AppError(code="VALIDATION_ERROR", message="Issue has no assigned faculty", status_code=422)
    key = idempotency_key or f"exam_coordination_reminder:{doc.id}"
    existing = await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id),
        Eq(DomainOutboxEvent.idempotency_key, key),
    )
    if existing:
        return {"event_id": str(existing.id), "status": "duplicate_skipped"}
    event = DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="department.examination_coordination.reminder",
        aggregate_type="department_examination_coordination_issue",
        aggregate_id=str(doc.id),
        payload={
            "issue_id": str(doc.id),
            "faculty_user_id": str(doc.assigned_faculty_user_id),
            "title": doc.title,
        },
        idempotency_key=key,
        status=OutboxEventStatus.PENDING,
    )
    await event.insert()
    await record_department_audit(
        actor_id=scope.user_id,
        action="department.examination_issue.reminder_enqueued",
        resource_type="domain_outbox_event",
        resource_id=str(event.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return {"event_id": str(event.id), "status": "enqueued"}