"""Faculty student support, progress, and mentoring."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.examinations.grading import get_grading_policy, weighted_percentage
from app.modules.examinations.models import FacultyAssessmentAssignment, StudentAssessmentMark, MarksSubmissionBatch
from app.modules.examinations.enums import MarksBatchStatus, StudentMarkStatus
from app.modules.faculty.attendance_service import attendance_shortages, student_summaries
from app.modules.faculty.course_access import require_course_access
from app.modules.faculty.enums import FacultyActivityType
from app.modules.faculty.models import FacultyAssignment
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.repositories import FacultyActivityRepository
from app.modules.faculty.support_models import (
    AcademicPerformanceSnapshot,
    FacultyAcademicReport,
    StudentAcademicFollowup,
    StudentCounsellingSession,
    StudentImprovementPlan,
    StudentMentoringRecord,
)
from app.modules.faculty.support_schemas import (
    AcademicReportRead,
    CounsellingSessionCreate,
    CounsellingSessionRead,
    FollowupCreate,
    FollowupRead,
    FollowupUpdate,
    ImprovementPlanCreate,
    ImprovementPlanRead,
    MentoringRecordCreate,
    MentoringRecordRead,
    StudentPerformanceRead,
)
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.faculty.enums import AssignmentStatus

_activity_repo = FacultyActivityRepository()


async def _assigned_student_ids(tenant_id: PydanticObjectId, faculty_user_id: PydanticObjectId) -> dict[str, set[str]]:
    """Map course_code -> student user ids from active faculty assignments."""
    assignments = await FacultyAssignment.find(
        {"tenant_id": tenant_id, "user_id": faculty_user_id, "status": AssignmentStatus.ACTIVE}
    ).to_list()
    mapping: dict[str, set[str]] = {}
    for assignment in assignments:
        roster = await EnrollmentRosterEntry.find(
            {"tenant_id": tenant_id, "course_code": assignment.course_code, "section_code": assignment.section}
        ).to_list()
        bucket = mapping.setdefault(assignment.course_code, set())
        for entry in roster:
            bucket.add(str(entry.student_user_id))
    return mapping


async def assert_student_in_scope(
    tenant_id: PydanticObjectId,
    faculty_user_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    course_code: str | None = None,
) -> None:
    mapping = await _assigned_student_ids(tenant_id, faculty_user_id)
    if course_code:
        if str(student_user_id) not in mapping.get(course_code, set()):
            raise AppError(code="FORBIDDEN", message="Student is outside your authorized scope", status_code=403)
        return
    all_students = set().union(*mapping.values()) if mapping else set()
    if str(student_user_id) not in all_students:
        raise AppError(code="FORBIDDEN", message="Student is outside your authorized scope", status_code=403)


async def _assessment_average(
    tenant_id: PydanticObjectId, faculty_user_id: PydanticObjectId, student_user_id: PydanticObjectId
) -> float:
    assignments = await FacultyAssessmentAssignment.find(
        {"tenant_id": tenant_id, "faculty_user_id": faculty_user_id}
    ).to_list()
    if not assignments:
        return 0.0
    percentages: list[float] = []
    for row in assignments:
        batches = await MarksSubmissionBatch.find(
            {
                "tenant_id": tenant_id,
                "faculty_user_id": faculty_user_id,
                "assessment_id": row.assessment_id,
                "section": row.section,
                "status": MarksBatchStatus.APPROVED,
            }
        ).to_list()
        for batch in batches:
            mark = await StudentAssessmentMark.find_one(
                {
                    "batch_id": batch.id,
                    "student_user_id": student_user_id,
                    "status": StudentMarkStatus.APPROVED,
                }
            )
            if mark:
                percentages.append(weighted_percentage(mark.marks_obtained, mark.max_marks))
    if not percentages:
        return 0.0
    return round(sum(percentages) / len(percentages), 2)


async def student_performance_list(scope: AccessScope, user: User) -> list[StudentPerformanceRead]:
    authorize(scope, Permission.FACULTY_MENTORING_READ)
    tenant_id = require_faculty_scope(scope)
    policy = await get_grading_policy(tenant_id)
    assignments = await FacultyAssignment.find(
        {"tenant_id": tenant_id, "user_id": user.id, "status": AssignmentStatus.ACTIVE}
    ).to_list()
    results: list[StudentPerformanceRead] = []
    for assignment in assignments:
        summaries = await student_summaries(scope, user, assignment.course_code, assignment.section)
        for summary in summaries:
            avg = await _assessment_average(tenant_id, user.id, PydanticObjectId(summary.student_user_id))
            at_risk = summary.below_threshold or avg < policy.low_performance_threshold
            roster = await EnrollmentRosterEntry.find_one(
                {
                    "tenant_id": tenant_id,
                    "course_code": assignment.course_code,
                    "section_code": assignment.section,
                    "student_user_id": PydanticObjectId(summary.student_user_id),
                }
            )
            results.append(
                StudentPerformanceRead(
                    student_user_id=summary.student_user_id,
                    roll_number=roster.roll_number if roster else None,
                    display_name=roster.display_name if roster else None,
                    course_code=assignment.course_code,
                    attendance_percentage=summary.percentage,
                    assessment_average=avg,
                    at_risk=at_risk,
                )
            )
    return results


async def students_requiring_support(scope: AccessScope, user: User) -> list[StudentPerformanceRead]:
    rows = await student_performance_list(scope, user)
    return [r for r in rows if r.at_risk]


async def create_mentoring_record(
    scope: AccessScope, user: User, payload: MentoringRecordCreate
) -> MentoringRecordRead:
    authorize(scope, Permission.FACULTY_MENTORING_MANAGE)
    tenant_id = require_faculty_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student id")
    await assert_student_in_scope(tenant_id, user.id, student_id, payload.course_code)
    doc = StudentMentoringRecord(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        student_user_id=student_id,
        course_code=payload.course_code,
        notes=payload.notes.strip(),
    )
    await doc.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.mentoring.created",
        resource_type="student_mentoring_record",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    return MentoringRecordRead(
        id=str(doc.id),
        student_user_id=str(student_id),
        course_code=doc.course_code,
        notes=doc.notes,
        created_at=doc.created_at,
    )


async def record_counselling(
    scope: AccessScope, user: User, payload: CounsellingSessionCreate
) -> CounsellingSessionRead:
    authorize(scope, Permission.FACULTY_MENTORING_MANAGE)
    tenant_id = require_faculty_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student id")
    await assert_student_in_scope(tenant_id, user.id, student_id)
    doc = StudentCounsellingSession(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        student_user_id=student_id,
        session_at=payload.session_at,
        summary=payload.summary.strip(),
    )
    await doc.insert()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.OTHER,
        title="Counselling session recorded",
        metadata={"student_user_id": str(student_id)},
    )
    return CounsellingSessionRead(
        id=str(doc.id),
        student_user_id=str(student_id),
        session_at=doc.session_at,
        summary=doc.summary,
        created_at=doc.created_at,
    )


async def create_followup(scope: AccessScope, user: User, payload: FollowupCreate) -> FollowupRead:
    authorize(scope, Permission.FACULTY_MENTORING_MANAGE)
    tenant_id = require_faculty_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student id")
    await assert_student_in_scope(tenant_id, user.id, student_id)
    doc = StudentAcademicFollowup(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        student_user_id=student_id,
        title=payload.title,
        action_item=payload.action_item,
        due_date=payload.due_date,
    )
    await doc.insert()
    return FollowupRead(
        id=str(doc.id),
        student_user_id=str(student_id),
        title=doc.title,
        action_item=doc.action_item,
        due_date=doc.due_date,
        status=doc.status,
    )


async def update_followup(
    scope: AccessScope, user: User, followup_id: PydanticObjectId, payload: FollowupUpdate
) -> FollowupRead:
    authorize(scope, Permission.FACULTY_MENTORING_MANAGE)
    tenant_id = require_faculty_scope(scope)
    doc = await StudentAcademicFollowup.get(followup_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Follow-up not found", status_code=404)
    doc.status = payload.status
    if payload.status == "completed":
        doc.completed_at = utcnow()
    await doc.save()
    return FollowupRead(
        id=str(doc.id),
        student_user_id=str(doc.student_user_id),
        title=doc.title,
        action_item=doc.action_item,
        due_date=doc.due_date,
        status=doc.status,
    )


async def create_improvement_plan(
    scope: AccessScope, user: User, payload: ImprovementPlanCreate
) -> ImprovementPlanRead:
    authorize(scope, Permission.FACULTY_MENTORING_MANAGE)
    tenant_id = require_faculty_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student id")
    await assert_student_in_scope(tenant_id, user.id, student_id, payload.course_code)
    await require_course_access(tenant_id, user.id, course_code=payload.course_code)
    doc = StudentImprovementPlan(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        student_user_id=student_id,
        course_code=payload.course_code,
        goals=payload.goals,
        start_date=payload.start_date,
        target_date=payload.target_date,
    )
    await doc.insert()
    return ImprovementPlanRead(
        id=str(doc.id),
        student_user_id=str(student_id),
        course_code=doc.course_code,
        goals=doc.goals,
        start_date=doc.start_date,
        target_date=doc.target_date,
        status=doc.status,
    )


async def pending_followups(scope: AccessScope, user: User) -> list[FollowupRead]:
    authorize(scope, Permission.FACULTY_MENTORING_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await StudentAcademicFollowup.find(
        {"tenant_id": tenant_id, "faculty_user_id": user.id, "status": "pending"}
    ).sort("due_date").to_list()
    return [
        FollowupRead(
            id=str(r.id),
            student_user_id=str(r.student_user_id),
            title=r.title,
            action_item=r.action_item,
            due_date=r.due_date,
            status=r.status,
        )
        for r in rows
    ]


async def capture_performance_snapshot(
    scope: AccessScope,
    user: User,
    student_user_id: PydanticObjectId,
    course_code: str,
) -> AcademicPerformanceSnapshot:
    authorize(scope, Permission.FACULTY_MENTORING_MANAGE)
    tenant_id = require_faculty_scope(scope)
    await assert_student_in_scope(tenant_id, user.id, student_user_id, course_code)
    assignment = await FacultyAssignment.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "course_code": course_code, "status": AssignmentStatus.ACTIVE}
    )
    section = assignment.section if assignment else "A"
    summaries = await student_summaries(scope, user, course_code, section)
    match = next((s for s in summaries if s.student_user_id == str(student_user_id)), None)
    attendance_pct = match.percentage if match else 0.0
    assessment_avg = await _assessment_average(tenant_id, user.id, student_user_id)
    pending = await StudentAcademicFollowup.find(
        {"tenant_id": tenant_id, "faculty_user_id": user.id, "student_user_id": student_user_id, "status": "pending"}
    ).count()
    snap = AcademicPerformanceSnapshot(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        student_user_id=student_user_id,
        course_code=course_code,
        attendance_percentage=attendance_pct,
        assessment_average=assessment_avg,
        incomplete_tasks=pending,
    )
    await snap.insert()
    return snap


async def generate_course_report(scope: AccessScope, user: User, course_code: str) -> AcademicReportRead:
    authorize(scope, Permission.FACULTY_MENTORING_READ)
    tenant_id = require_faculty_scope(scope)
    await require_course_access(tenant_id, user.id, course_code=course_code)
    performances = await student_performance_list(scope, user)
    course_rows = [p.model_dump() for p in performances if p.course_code == course_code]
    shortages = []
    assignments = await FacultyAssignment.find(
        {"tenant_id": tenant_id, "user_id": user.id, "course_code": course_code, "status": AssignmentStatus.ACTIVE}
    ).to_list()
    for assignment in assignments:
        shortages.extend(
            [s.model_dump() for s in await attendance_shortages(scope, user, course_code, assignment.section)]
        )
    doc = FacultyAcademicReport(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        report_type="course_performance",
        course_code=course_code,
        payload={"students": course_rows, "attendance_shortages": shortages},
    )
    await doc.insert()
    return AcademicReportRead(
        id=str(doc.id),
        report_type=doc.report_type,
        course_code=doc.course_code,
        student_user_id=None,
        payload=doc.payload,
        generated_at=doc.generated_at,
    )


async def generate_student_report(
    scope: AccessScope, user: User, student_user_id: PydanticObjectId
) -> AcademicReportRead:
    authorize(scope, Permission.FACULTY_MENTORING_READ)
    tenant_id = require_faculty_scope(scope)
    await assert_student_in_scope(tenant_id, user.id, student_user_id)
    performances = [p for p in await student_performance_list(scope, user) if p.student_user_id == str(student_user_id)]
    mentoring = await StudentMentoringRecord.find(
        {"tenant_id": tenant_id, "faculty_user_id": user.id, "student_user_id": student_user_id}
    ).sort("-created_at").limit(20).to_list()
    doc = FacultyAcademicReport(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        report_type="student_progress",
        student_user_id=student_user_id,
        payload={
            "performance": [p.model_dump() for p in performances],
            "mentoring_records": [{"notes": m.notes, "created_at": m.created_at.isoformat()} for m in mentoring],
        },
    )
    await doc.insert()
    return AcademicReportRead(
        id=str(doc.id),
        report_type=doc.report_type,
        course_code=None,
        student_user_id=str(student_user_id),
        payload=doc.payload,
        generated_at=doc.generated_at,
    )
