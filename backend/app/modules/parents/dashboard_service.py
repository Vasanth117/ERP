"""Parent dashboard aggregation across verified linked students."""

from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.parents.enums import (
    PENDING_LINK_STATUSES,
    ParentDataPermission,
    ParentRelationshipStatus,
)
from app.modules.parents.models import ParentStudentLinkRequest
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.profile_service import ensure_parent_profile
from app.modules.parents.repositories import ParentRelationshipRepository
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.schemas import (
    LinkedStudentSummaryCard,
    ParentDashboardFilters,
    ParentDashboardRead,
    ParentProfileRead,
)
from app.modules.students.integrations.data_reader import StudentDataReader, resolve_date_window
from app.modules.students.integrations.residence_reader import hostel_allocation
from app.modules.students.integrations.student_finance_reader import demands_for_student, invoices_for_student
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.modules.students.repositories import StudentAcademicRecordRepository
from app.modules.tenants.models import Department

_reader = StudentDataReader()
_record_repo = StudentAcademicRecordRepository()
_relationship_repo = ParentRelationshipRepository()


async def _department_name(tenant_id: PydanticObjectId, department_id: PydanticObjectId | None) -> str | None:
    if department_id is None:
        return None
    department = await Department.get(department_id)
    if department is None or str(department.tenant_id) != str(tenant_id):
        return None
    return department.name


async def _build_student_card(
    tenant_id: PydanticObjectId,
    parent_user_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> LinkedStudentSummaryCard:
    rel, perms = await require_student_access(
        tenant_id, parent_user_id, student_user_id, ParentDataPermission.VIEW_PROFILE
    )
    grants = perms.grants if perms else {}

    student_user = await User.get(student_user_id)
    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": student_user_id})
    department_name = await _department_name(tenant_id, profile.department_id if profile else None)

    attendance_summary = None
    if grants.get(ParentDataPermission.VIEW_ATTENDANCE.value, False):
        attendance_summary = await _reader.attendance_summary(
            tenant_id, student_user_id, academic_year_label=year, semester_label=semester
        )

    academic_performance_summary = None
    upcoming_examinations: list[dict] = []
    if grants.get(ParentDataPermission.VIEW_RESULTS.value, False):
        marks = await _reader.published_results(tenant_id, student_user_id, limit=5)
        academic_performance_summary = {
            "published_components": len(marks),
            "latest": [
                {
                    "assessment_id": m.assessment_id,
                    "component_id": m.component_id,
                    "marks_obtained": m.marks_obtained,
                    "max_marks": m.max_marks,
                }
                for m in marks[:3]
            ],
        }
    if grants.get(ParentDataPermission.VIEW_EXAM_TIMETABLE.value, False):
        exams = await _reader.examination_schedule(
            tenant_id,
            student_user_id,
            academic_year_label=year,
            semester_label=semester,
            from_time=datetime.now(timezone.utc),
            limit=5,
        )
        upcoming_examinations = [
            {
                "course_code": e.course_code,
                "scheduled_at": e.scheduled_at.isoformat(),
                "room": e.room,
            }
            for e in exams
        ]

    fee_summary = None
    if grants.get(ParentDataPermission.VIEW_FEES.value, False):
        record = await _record_repo.get_current(
            tenant_id, student_user_id, academic_year_label=year, semester_label=semester
        )
        if record and record.fee_snapshot:
            fee_summary = dict(record.fee_snapshot)
        else:
            demands = await demands_for_student(tenant_id, student_user_id)
            from app.modules.finance.finance_enums import FeeDemandStatus

            outstanding = sum(float(d.amount or 0) for d in demands[:20] if d.status == FeeDemandStatus.OPEN)
            fee_summary = {"status": "available", "outstanding_amount": outstanding, "currency": "INR"}
        if grants.get(ParentDataPermission.VIEW_RECEIPTS.value, False):
            inv = await invoices_for_student(tenant_id, student_user_id)
            fee_summary["recent_receipt_count"] = len(inv[:5])

    important_alerts: list[str] = []
    pending_parent_actions: list[str] = []
    if rel.status == ParentRelationshipStatus.SUSPENDED:
        important_alerts.append("Relationship access is suspended")

    if grants.get(ParentDataPermission.VIEW_HOSTEL.value, False):
        allocation = await hostel_allocation(tenant_id, student_user_id)
        if allocation:
            important_alerts.append(f"Hostel: {allocation.hostel_name} / {allocation.room_number}")

    enrollment_status = None
    record = await StudentAcademicRecord.find_one(
        {"tenant_id": tenant_id, "user_id": student_user_id, "academic_year_label": year, "semester_label": semester}
    )
    if record:
        enrollment_status = record.enrollment_status.value if hasattr(record.enrollment_status, "value") else str(
            record.enrollment_status
        )

    return LinkedStudentSummaryCard(
        student_user_id=str(student_user_id),
        student_id=profile.student_id if profile else None,
        roll_number=profile.roll_number if profile else None,
        full_name=student_user.full_name if student_user else "Student",
        profile_photo_ref=profile.profile_photo_ref if profile else None,
        programme_code=profile.programme_code if profile else None,
        programme_name=profile.programme_name if profile else None,
        department_name=department_name,
        batch_label=profile.batch_label if profile else None,
        semester_label=semester,
        academic_year_label=year,
        enrollment_status=enrollment_status,
        attendance_summary=attendance_summary,
        academic_performance_summary=academic_performance_summary,
        upcoming_examinations=upcoming_examinations,
        fee_summary=fee_summary,
        important_alerts=important_alerts,
        pending_parent_actions=pending_parent_actions,
    )


async def get_parent_dashboard(
    scope: AccessScope,
    user: User,
    filters: ParentDashboardFilters,
) -> ParentDashboardRead:
    authorize(scope, Permission.PARENT_DASHBOARD_READ)
    tenant_id = require_parent_scope(scope)
    profile_doc = await ensure_parent_profile(scope, user)
    parent_read = ParentProfileRead.from_parts(profile_doc, email=user.email, full_name=user.full_name)

    active = await _relationship_repo.list_active_for_parent(tenant_id, user.id)
    all_rels = await _relationship_repo.list_for_parent(tenant_id, user.id)
    rejected_suspended = sum(
        1
        for r in all_rels
        if r.status
        in {
            ParentRelationshipStatus.REJECTED,
            ParentRelationshipStatus.SUSPENDED,
            ParentRelationshipStatus.REVOKED,
        }
    )
    pending_requests = await ParentStudentLinkRequest.find(
        {
            "tenant_id": tenant_id,
            "parent_user_id": user.id,
            "status": {"$in": [s.value for s in PENDING_LINK_STATUSES]},
        }
    ).count()

    ctx = await _reader.current_academic_context(tenant_id)
    year = filters.academic_year_label or (ctx.academic_year_label if ctx else None)
    semester = filters.semester_label or (ctx.semester_label if ctx else None)
    if not year or not semester:
        year = year or "N/A"
        semester = semester or "N/A"

    selected = filters.student_user_id
    if selected is not None:
        sid = PydanticObjectId(selected)
        if not any(str(r.student_user_id) == str(sid) for r in active):
            raise AppError(code="FORBIDDEN", message="Student not in verified linked list", status_code=403)

    targets = active
    if selected is not None:
        targets = [r for r in active if str(r.student_user_id) == selected]

    summaries: list[LinkedStudentSummaryCard] = []
    for rel in targets:
        card = await _build_student_card(
            tenant_id, user.id, rel.student_user_id, year=year, semester=semester
        )
        summaries.append(card)

    announcements: list[dict] = []
    unread_notifications = 0
    if active:
        first = active[0]
        rel, perms = await require_student_access(tenant_id, user.id, first.student_user_id)
        grants = perms.grants if perms else {}
        if grants.get(ParentDataPermission.RECEIVE_ANNOUNCEMENTS.value, False):
            for item in await _reader.academic_notifications(tenant_id, first.student_user_id, limit=10):
                announcements.append(item)
                unread_notifications += 1

    return ParentDashboardRead(
        parent=parent_read,
        linked_student_count=len(all_rels),
        verified_linked_students=len(active),
        pending_link_requests=pending_requests,
        rejected_or_suspended_relationships=rejected_suspended,
        selected_student_user_id=selected,
        student_summaries=summaries,
        unread_notifications=unread_notifications,
        announcements=announcements,
        academic_term={"academic_year_label": year, "semester_label": semester},
        filters_applied=filters.model_dump(),
    )