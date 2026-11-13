"""Student dashboard aggregation."""

from datetime import date

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.enums import DashboardDateRange, StudentNotificationCategory
from app.modules.students.integrations.data_reader import StudentDataReader, resolve_date_window
from app.modules.students.policy import require_student_scope
from app.modules.students.profile_service import _department_name, ensure_student_profile
from app.modules.students.repositories import (
    StudentAcademicRecordRepository,
    StudentAcademicRequestRepository,
    StudentActivityRepository,
    StudentDashboardPreferencesRepository,
    StudentEnrollmentRepository,
)
from app.modules.students.schemas import (
    AcademicTermInfo,
    AttendanceCourseSummary,
    AttendanceSummaryRead,
    DeadlineSummary,
    EnrolledCourseSummary,
    FeeSummaryRead,
    NotificationSummary,
    PendingTaskSummary,
    ResultSummary,
    QuickAction,
    StudentActivityRead,
    StudentDashboardRead,
    StudentDashboardStats,
    StudentProfileSummary,
    TimetableSlotSummary,
)

_reader = StudentDataReader()
_enrollment_repo = StudentEnrollmentRepository()
_record_repo = StudentAcademicRecordRepository()
_request_repo = StudentAcademicRequestRepository()
_activity_repo = StudentActivityRepository()
_prefs_repo = StudentDashboardPreferencesRepository()


def _quick_actions() -> list[QuickAction]:
    return [
        QuickAction(code="view_timetable", label="View timetable", href="/students/me/academics", enabled=True),
        QuickAction(code="submit_assignment", label="Assignments", href="/lms", enabled=True),
        QuickAction(code="fee_status", label="Fee status", href="/finance", enabled=True),
        QuickAction(code="edit_profile", label="Update profile", href="/students/me/profile", enabled=True),
    ]


def _today_weekday(anchor: date) -> int:
    return anchor.weekday()


async def _resolve_enrollments(scope: AccessScope, user: User, year: str, semester: str) -> list[EnrolledCourseSummary]:
    tenant_id = require_student_scope(scope)
    rows = await _enrollment_repo.list_for_term(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    if rows:
        return [
            EnrolledCourseSummary(
                course_code=row.course_code,
                course_name=row.course_name,
                section_code=row.section_code,
                status=row.status.value,
            )
            for row in rows
        ]
    roster = await _reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    return [
        EnrolledCourseSummary(
            course_code=r.course_code,
            course_name=r.course_code,
            section_code=r.section_code,
            status="active",
        )
        for r in roster
    ]


def _fee_from_record(fee_snapshot: dict) -> FeeSummaryRead:
    if not fee_snapshot:
        return FeeSummaryRead(status="not_configured")
    amount = fee_snapshot.get("outstanding_amount")
    return FeeSummaryRead(
        status=fee_snapshot.get("status", "available"),
        outstanding_amount=float(amount) if amount is not None else None,
        currency=fee_snapshot.get("currency", "INR"),
        due_date=fee_snapshot.get("due_date"),
        details={k: v for k, v in fee_snapshot.items() if k not in {"outstanding_amount", "currency", "due_date", "status"}},
    )


async def get_student_dashboard(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
    date_range: DashboardDateRange = DashboardDateRange.WEEK,
) -> StudentDashboardRead:
    authorize(scope, Permission.STUDENT_DASHBOARD_READ)
    tenant_id = require_student_scope(scope)
    profile_doc = await ensure_student_profile(scope, user)
    anchor = anchor_date or date.today()
    department_name = await _department_name(tenant_id, profile_doc.department_id)

    profile = StudentProfileSummary(
        user_id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        student_id=profile_doc.student_id,
        roll_number=profile_doc.roll_number,
        admission_number=profile_doc.admission_number,
        admission_date=profile_doc.admission_date,
        department_id=str(profile_doc.department_id) if profile_doc.department_id else None,
        department_name=department_name,
        programme_code=profile_doc.programme_code,
        programme_name=profile_doc.programme_name,
        batch_label=profile_doc.batch_label,
        section_code=profile_doc.section_code,
    )

    context = await _reader.current_academic_context(tenant_id)
    year = context.academic_year_label if context else "N/A"
    semester = context.semester_label if context else "N/A"
    academic_term = AcademicTermInfo(academic_year_label=context.academic_year_label if context else None, semester_label=context.semester_label if context else None)

    enrolled_courses = (
        await _resolve_enrollments(scope, user, year, semester) if context else []
    )

    attendance_raw = (
        await _reader.attendance_summary(tenant_id, user.id, academic_year_label=year, semester_label=semester)
        if context
        else {"status": "not_configured", "courses": [], "overall_percentage": None}
    )
    attendance = AttendanceSummaryRead(
        status=attendance_raw.get("status", "not_configured"),
        overall_percentage=attendance_raw.get("overall_percentage"),
        min_required=attendance_raw.get("min_required"),
        courses=[AttendanceCourseSummary(**c) for c in attendance_raw.get("courses", [])],
    )

    day = _today_weekday(anchor)
    timetable_raw = (
        await _reader.timetable_for_student(
            tenant_id, user.id, academic_year_label=year, semester_label=semester, day_of_week=day
        )
        if context
        else []
    )
    timetable_today = [
        TimetableSlotSummary(
            day_of_week=e.day_of_week,
            start_time=e.start_time,
            end_time=e.end_time,
            course_code=e.course_code,
            course_name=e.course_name,
            section=e.section,
            room=e.room,
        )
        for e in timetable_raw
    ]

    window_start, _ = resolve_date_window(anchor=anchor, range_key=date_range.value)
    exams_raw = (
        await _reader.examination_schedule(
            tenant_id, user.id, academic_year_label=year, semester_label=semester, from_time=window_start, limit=15
        )
        if context
        else []
    )
    upcoming_examinations = [
        PendingTaskSummary(
            task_type="examination",
            title=f"{row.title} ({row.course_code})",
            due_at=row.scheduled_at,
            reference_id=str(row.id),
        )
        for row in exams_raw
    ]

    pending_assignments_raw = (
        await _reader.pending_assignments(tenant_id, user.id, academic_year_label=year, semester_label=semester)
        if context
        else []
    )
    pending_assignments = [
        PendingTaskSummary(
            task_type="assignment",
            title=item.title,
            due_at=item.deadline_at,
            reference_id=str(item.id),
        )
        for item in pending_assignments_raw
    ]

    marks = await _reader.published_results(tenant_id, user.id, limit=20)
    published_results = [
        ResultSummary(
            assessment_id=m.assessment_id,
            component_id=m.component_id,
            marks_obtained=m.marks_obtained,
            max_marks=m.max_marks,
            published_at=m.updated_at,
        )
        for m in marks
    ]

    record = (
        await _record_repo.get_current(tenant_id, user.id, academic_year_label=year, semester_label=semester)
        if context
        else None
    )
    fees = _fee_from_record(record.fee_snapshot if record else {})

    notif_raw = await _reader.academic_notifications(tenant_id, user.id, limit=10)
    notifications = [
        NotificationSummary(
            id=item["id"],
            title=item["title"],
            body=item["body"],
            category=StudentNotificationCategory.ACADEMIC,
            created_at=item["created_at"],
        )
        for item in notif_raw
    ]

    open_requests = await _request_repo.list_open(tenant_id, user.id)
    pending_requests = [
        PendingTaskSummary(
            task_type="academic_request",
            title=req.title,
            due_at=None,
            reference_id=str(req.id),
        )
        for req in open_requests
    ]

    deadlines_raw = await _reader.academic_deadlines(tenant_id, from_time=window_start, limit=10)
    deadlines = [
        DeadlineSummary(title=ev.title, due_at=ev.event_at, category=ev.event_type) for ev in deadlines_raw
    ]

    prefs = await _prefs_repo.get_or_create(tenant_id, user.id)
    preferences = {
        "default_date_range": prefs.default_date_range.value,
        "show_finance_summary": prefs.show_finance_summary,
        "show_attendance_summary": prefs.show_attendance_summary,
        "pinned_widgets": prefs.pinned_widgets,
    }

    return StudentDashboardRead(
        profile=profile,
        academic_term=academic_term,
        enrolled_courses=enrolled_courses,
        attendance=attendance,
        timetable_today=timetable_today,
        upcoming_examinations=upcoming_examinations,
        pending_assignments=pending_assignments,
        published_results=published_results,
        fees=fees,
        notifications=notifications,
        pending_requests=pending_requests,
        deadlines=deadlines,
        quick_actions=_quick_actions(),
        preferences=preferences,
    )


async def get_dashboard_statistics(scope: AccessScope, user: User) -> StudentDashboardStats:
    authorize(scope, Permission.STUDENT_DASHBOARD_READ)
    tenant_id = require_student_scope(scope)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        return StudentDashboardStats(
            enrolled_course_count=0,
            pending_assignment_count=0,
            pending_request_count=0,
            attendance_overall_percentage=None,
            unread_notification_count=0,
        )
    year, semester = context.academic_year_label, context.semester_label
    enrolled = await _resolve_enrollments(scope, user, year, semester)
    pending_assignments = await _reader.pending_assignments(
        tenant_id, user.id, academic_year_label=year, semester_label=semester
    )
    open_requests = await _request_repo.list_open(tenant_id, user.id)
    attendance_raw = await _reader.attendance_summary(
        tenant_id, user.id, academic_year_label=year, semester_label=semester
    )
    notif_raw = await _reader.academic_notifications(tenant_id, user.id, limit=50)
    return StudentDashboardStats(
        enrolled_course_count=len(enrolled),
        pending_assignment_count=len(pending_assignments),
        pending_request_count=len(open_requests),
        attendance_overall_percentage=attendance_raw.get("overall_percentage"),
        unread_notification_count=len(notif_raw),
    )


async def get_pending_tasks(scope: AccessScope, user: User) -> list[PendingTaskSummary]:
    authorize(scope, Permission.STUDENT_DASHBOARD_READ)
    tenant_id = require_student_scope(scope)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        return []
    year, semester = context.academic_year_label, context.semester_label
    assignments = await _reader.pending_assignments(
        tenant_id, user.id, academic_year_label=year, semester_label=semester
    )
    tasks = [
        PendingTaskSummary(
            task_type="assignment",
            title=a.title,
            due_at=a.deadline_at,
            reference_id=str(a.id),
        )
        for a in assignments
    ]
    open_requests = await _request_repo.list_open(tenant_id, user.id)
    tasks.extend(
        PendingTaskSummary(
            task_type="academic_request",
            title=r.title,
            reference_id=str(r.id),
        )
        for r in open_requests
    )
    return tasks


async def get_recent_activities(scope: AccessScope, user: User, pagination: Pagination) -> Page[StudentActivityRead]:
    authorize(scope, Permission.STUDENT_DASHBOARD_READ)
    tenant_id = require_student_scope(scope)
    skip = (pagination.page - 1) * pagination.page_size
    items, total = await _activity_repo.page_for_user(tenant_id, user.id, skip=skip, limit=pagination.page_size)
    return Page(
        items=[StudentActivityRead.from_document(row) for row in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


async def get_academic_notifications(scope: AccessScope, user: User, pagination: Pagination) -> Page[NotificationSummary]:
    authorize(scope, Permission.STUDENT_DASHBOARD_READ)
    tenant_id = require_student_scope(scope)
    raw = await _reader.academic_notifications(tenant_id, user.id, limit=pagination.page_size * pagination.page)
    start = (pagination.page - 1) * pagination.page_size
    chunk = raw[start : start + pagination.page_size]
    items = [
        NotificationSummary(
            id=item["id"],
            title=item["title"],
            body=item["body"],
            category=StudentNotificationCategory.ACADEMIC,
            created_at=item["created_at"],
        )
        for item in chunk
    ]
    return Page(items=items, page=pagination.page, page_size=pagination.page_size, total=len(raw))
