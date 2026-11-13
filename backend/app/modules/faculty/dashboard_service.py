"""Faculty dashboard aggregation."""

from datetime import date, datetime, timezone

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.faculty.enums import DashboardDateRange
from app.modules.faculty.integrations.academic_reader import AcademicDataReader, resolve_date_window
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.profile_service import ensure_faculty_profile, _department_name
from app.modules.faculty.repositories import (
    FacultyActivityRepository,
    FacultyAssignmentRepository,
    FacultyDashboardPreferencesRepository,
    FacultyNotificationRepository,
    FacultyWorkloadRepository,
)
from app.modules.faculty.schemas import (
    AcademicTermInfo,
    CourseAssignmentSummary,
    DeadlineSummary,
    FacultyActivityRead,
    FacultyDashboardRead,
    FacultyDashboardStats,
    FacultyProfileSummary,
    NotificationSummary,
    PendingTaskSummary,
    QuickAction,
    TimetableSlotSummary,
    WorkloadSummary,
)
_academic = AcademicDataReader()
_assignment_repo = FacultyAssignmentRepository()
_workload_repo = FacultyWorkloadRepository()
_activity_repo = FacultyActivityRepository()
_notification_repo = FacultyNotificationRepository()
_prefs_repo = FacultyDashboardPreferencesRepository()


def _quick_actions() -> list[QuickAction]:
    return [
        QuickAction(code="submit_attendance", label="Submit attendance", href="/attendance", enabled=True),
        QuickAction(code="grade_assignments", label="Grade assignments", href="/examinations", enabled=True),
        QuickAction(code="view_timetable", label="View full timetable", href="/academics/timetable", enabled=True),
        QuickAction(code="edit_profile", label="Update profile", href="/faculty/me/profile", enabled=True),
    ]


def _today_weekday(anchor: date) -> int:
    return anchor.weekday()


async def get_faculty_dashboard(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
    date_range: DashboardDateRange = DashboardDateRange.WEEK,
) -> FacultyDashboardRead:
    authorize(scope, Permission.FACULTY_DASHBOARD_READ)
    tenant_id = require_faculty_scope(scope)
    profile_doc = await ensure_faculty_profile(scope, user)
    anchor = anchor_date or date.today()
    department_name = await _department_name(tenant_id, profile_doc.department_id)

    profile = FacultyProfileSummary(
        user_id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        employee_id=profile_doc.employee_id,
        faculty_code=profile_doc.faculty_code,
        designation=profile_doc.designation,
        department_id=str(profile_doc.department_id) if profile_doc.department_id else None,
        department_name=department_name,
        specialization=profile_doc.specialization,
    )

    context = await _academic.current_academic_context(tenant_id)
    academic_term = AcademicTermInfo(
        academic_year_label=context.academic_year_label if context else None,
        semester_label=context.semester_label if context else None,
    )

    year = context.academic_year_label if context else None
    semester = context.semester_label if context else None
    assignments = await _assignment_repo.list_active_for_user(
        tenant_id,
        user.id,
        academic_year_label=year,
        semester_label=semester,
    )
    assigned_courses = [
        CourseAssignmentSummary(
            course_code=item.course_code,
            course_name=item.course_name,
            subject_code=item.subject_code,
            subject_name=item.subject_name,
            section=item.section,
            assignment_role=item.assignment_role,
        )
        for item in assignments
    ]

    day = _today_weekday(anchor)
    timetable_today_raw = await _academic.timetable_for_faculty(tenant_id, user.id, day_of_week=day)
    timetable_week_raw = await _academic.weekly_timetable(tenant_id, user.id)

    def map_slots(entries) -> list[TimetableSlotSummary]:
        return [
            TimetableSlotSummary(
                day_of_week=e.day_of_week,
                start_time=e.start_time,
                end_time=e.end_time,
                course_code=e.course_code,
                course_name=e.course_name,
                section=e.section,
                room=e.room,
            )
            for e in entries
        ]

    pending_attendance_raw = await _academic.pending_attendance(tenant_id, user.id)
    pending_attendance = [
        PendingTaskSummary(
            task_type="attendance",
            title=f"Attendance — {item.class_label} {item.section}",
            due_at=item.due_at,
            reference_id=str(item.id),
        )
        for item in pending_attendance_raw
    ]

    window_start, _ = resolve_date_window(anchor=anchor, range_key=date_range.value)
    assessments_raw = await _academic.upcoming_assessments(
        tenant_id, user.id, from_time=window_start, limit=30
    )
    upcoming_assessments = [
        PendingTaskSummary(
            task_type="assessment",
            title=f"{item.title} ({item.course_code})",
            due_at=item.scheduled_at,
            reference_id=str(item.id),
        )
        for item in assessments_raw
    ]

    evaluations_raw = await _academic.pending_evaluations(tenant_id, user.id)
    pending_evaluations = [
        PendingTaskSummary(
            task_type="evaluation",
            title=f"Grade {item.title}",
            due_at=item.due_at,
            reference_id=item.assignment_id,
        )
        for item in evaluations_raw
    ]

    deadlines: list[DeadlineSummary] = []
    for task in pending_attendance + pending_evaluations:
        if task.due_at:
            deadlines.append(DeadlineSummary(title=task.title, due_at=task.due_at, category=task.task_type))
    for item in assessments_raw:
        deadlines.append(
            DeadlineSummary(title=item.title, due_at=item.scheduled_at, category="assessment")
        )
    deadlines.sort(key=lambda d: d.due_at)

    notifications_raw = await _notification_repo.list_for_user(tenant_id, user.id, limit=15)

    notifications = [
        NotificationSummary(
            id=str(n.id),
            title=n.title,
            body=n.body,
            category=n.category,
            created_at=n.created_at,
            read_at=n.read_at,
        )
        for n in notifications_raw
    ]

    workload: WorkloadSummary | None = None
    if year and semester:
        workload_doc = await _workload_repo.get_for_term(tenant_id, user.id, year, semester)
        if workload_doc is not None:
            workload = WorkloadSummary(
                academic_year_label=workload_doc.academic_year_label,
                semester_label=workload_doc.semester_label,
                lecture_hours=workload_doc.lecture_hours,
                lab_hours=workload_doc.lab_hours,
                tutorial_hours=workload_doc.tutorial_hours,
                total_hours=workload_doc.total_hours,
                credit_units=workload_doc.credit_units,
                active_course_count=workload_doc.active_course_count,
            )

    activities, _ = await _activity_repo.list_for_user(tenant_id, user.id, skip=0, limit=10)
    recent_activities = [FacultyActivityRead.from_document(item) for item in activities]

    events_raw = await _academic.academic_events(
        tenant_id,
        department_id=profile_doc.department_id,
        from_time=datetime.now(timezone.utc),
        limit=10,
    )
    upcoming_events = [
        PendingTaskSummary(
            task_type="event",
            title=item.title,
            due_at=item.event_at,
            reference_id=str(item.id),
        )
        for item in events_raw
    ]

    await _prefs_repo.get_or_create(tenant_id, user.id)

    return FacultyDashboardRead(
        profile=profile,
        academic_term=academic_term,
        assigned_courses=assigned_courses,
        timetable_today=map_slots(timetable_today_raw),
        timetable_week=map_slots(timetable_week_raw),
        pending_attendance=pending_attendance,
        upcoming_assessments=upcoming_assessments,
        pending_evaluations=pending_evaluations,
        upcoming_deadlines=deadlines[:20],
        notifications=notifications,
        workload=workload,
        recent_activities=recent_activities,
        upcoming_events=upcoming_events,
        quick_actions=_quick_actions(),
        date_filter=date_range,
        anchor_date=anchor,
    )


async def get_dashboard_statistics(scope: AccessScope, user: User) -> FacultyDashboardStats:
    tenant_id = require_faculty_scope(scope)
    pending_attendance = await _academic.pending_attendance(tenant_id, user.id)
    assessments = await _academic.upcoming_assessments(
        tenant_id, user.id, from_time=datetime.now(timezone.utc), limit=100
    )
    evaluations = await _academic.pending_evaluations(tenant_id, user.id)
    notifications = await _notification_repo.list_for_user(tenant_id, user.id, limit=50)
    unread = sum(1 for n in notifications if n.read_at is None)
    day = _today_weekday(date.today())
    classes_today = len(await _academic.timetable_for_faculty(tenant_id, user.id, day_of_week=day))
    pending_count = len(pending_attendance) + len(evaluations)
    return FacultyDashboardStats(
        pending_task_count=pending_count,
        upcoming_assessment_count=len(assessments),
        pending_evaluation_count=len(evaluations),
        unread_notification_count=unread,
        classes_today=classes_today,
    )


async def get_pending_tasks(scope: AccessScope, user: User) -> list[PendingTaskSummary]:
    tenant_id = require_faculty_scope(scope)
    pending_attendance = await _academic.pending_attendance(tenant_id, user.id)
    evaluations = await _academic.pending_evaluations(tenant_id, user.id)
    tasks: list[PendingTaskSummary] = []
    tasks.extend(
        PendingTaskSummary(
            task_type="attendance",
            title=f"Attendance — {item.class_label} {item.section}",
            due_at=item.due_at,
            reference_id=str(item.id),
        )
        for item in pending_attendance
    )
    tasks.extend(
        PendingTaskSummary(
            task_type="evaluation",
            title=f"Grade {item.title}",
            due_at=item.due_at,
            reference_id=item.assignment_id,
        )
        for item in evaluations
    )
    tasks.sort(key=lambda t: t.due_at or datetime.max.replace(tzinfo=timezone.utc))
    return tasks


async def get_upcoming_deadlines(scope: AccessScope, user: User, pagination: Pagination) -> Page[DeadlineSummary]:
    tenant_id = require_faculty_scope(scope)
    pending_attendance = await _academic.pending_attendance(tenant_id, user.id)
    evaluations = await _academic.pending_evaluations(tenant_id, user.id)
    assessments = await _academic.upcoming_assessments(
        tenant_id, user.id, from_time=datetime.now(timezone.utc), limit=100
    )
    deadlines: list[DeadlineSummary] = []
    for item in pending_attendance:
        deadlines.append(
            DeadlineSummary(
                title=f"Attendance — {item.class_label} {item.section}",
                due_at=item.due_at,
                category="attendance",
            )
        )
    for item in evaluations:
        deadlines.append(DeadlineSummary(title=item.title, due_at=item.due_at, category="evaluation"))
    for item in assessments:
        deadlines.append(
            DeadlineSummary(title=item.title, due_at=item.scheduled_at, category="assessment")
        )
    deadlines.sort(key=lambda d: d.due_at)
    total = len(deadlines)
    slice_ = deadlines[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_recent_activities(scope: AccessScope, user: User, pagination: Pagination) -> Page[FacultyActivityRead]:
    tenant_id = require_faculty_scope(scope)
    items, total = await _activity_repo.list_for_user(
        tenant_id,
        user.id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[FacultyActivityRead.from_document(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
