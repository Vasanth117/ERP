"""Department Admin dashboard services."""

from datetime import date

from beanie import PydanticObjectId
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.integrations.operational_reader import _date_window
from app.modules.department_admin.integrations.department_data_reader import DepartmentDataReader
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.department_admin.schemas import (
    DepartmentAcademicSummaryRead,
    DepartmentActivityRead,
    DepartmentAlertRead,
    DepartmentAttendanceOverviewRead,
    DepartmentDashboardBundleRead,
    DepartmentDashboardFilters,
    DepartmentExaminationOverviewRead,
    DepartmentFacultyStatsRead,
    DepartmentOverviewRead,
    DepartmentStudentStatsRead,
    DepartmentTimetableOverviewRead,
    HeadOfDepartmentSummary,
)

_reader = DepartmentDataReader()


async def _head_summary(tenant_id: PydanticObjectId, head_user_id: PydanticObjectId | None) -> HeadOfDepartmentSummary | None:
    if head_user_id is None:
        return None
    user = await User.get(head_user_id)
    if user is None:
        return None
    return HeadOfDepartmentSummary(user_id=str(user.id), full_name=user.full_name, email=user.email)


async def _resolve_year_semester(
    tenant_id: PydanticObjectId, filters: DepartmentDashboardFilters
) -> tuple[str | None, str | None]:
    year, semester = await _reader.current_academic_term(tenant_id)
    if filters.academic_year_label:
        year = filters.academic_year_label
    if filters.semester_label:
        semester = filters.semester_label
    return year, semester


async def get_department_overview(
    scope: AccessScope,
    user: User,
    *,
    filters: DepartmentDashboardFilters | None = None,
) -> DepartmentOverviewRead:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    filters = filters or DepartmentDashboardFilters()
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    year, semester = await _resolve_year_semester(tenant_id, filters)
    batch_section = await _reader.batch_section_summary(tenant_id, central_id)
    student_stats = await _reader.student_statistics(tenant_id, central_id)
    faculty_stats = await _reader.faculty_statistics(tenant_id, central_id)
    college_name = await _reader.college_name(tenant_id)
    return DepartmentOverviewRead(
        department_id=str(central_id),
        institution_department_id=str(institution.id),
        department_code=institution.department_code,
        department_name=institution.name,
        college_name=college_name,
        status=institution.status,
        head_of_department=await _head_summary(tenant_id, institution.head_user_id),
        academic_year_label=year,
        semester_label=semester,
        programme_count=len(institution.programme_codes),
        batch_count=batch_section["batch_count"],
        section_count=batch_section["section_count"],
        total_active_students=student_stats["active_students"],
        total_active_faculty=faculty_stats["active_faculty"],
    )


async def get_student_dashboard_stats(
    scope: AccessScope,
    user: User,
    *,
    filters: DepartmentDashboardFilters | None = None,
) -> DepartmentStudentStatsRead:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    filters = filters or DepartmentDashboardFilters()
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    raw = await _reader.student_statistics(
        tenant_id,
        central_id,
        programme_code=filters.programme_code,
        batch_label=filters.batch_label,
        section_code=filters.section_code,
    )
    return DepartmentStudentStatsRead(**raw)


async def get_faculty_dashboard_stats(scope: AccessScope, user: User) -> DepartmentFacultyStatsRead:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    raw = await _reader.faculty_statistics(tenant_id, central_id)
    return DepartmentFacultyStatsRead(**raw)


async def get_academic_dashboard_summary(
    scope: AccessScope,
    user: User,
    *,
    filters: DepartmentDashboardFilters | None = None,
) -> DepartmentAcademicSummaryRead:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    filters = filters or DepartmentDashboardFilters()
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    year, semester = await _resolve_year_semester(tenant_id, filters)
    if filters.programme_code and filters.programme_code.upper() not in [c.upper() for c in institution.programme_codes]:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Programme is outside your department", status_code=403)
    raw = await _reader.academic_summary(
        tenant_id,
        institution.programme_codes,
        academic_year_label=year,
        semester_label=semester,
    )
    return DepartmentAcademicSummaryRead(**raw)


async def get_attendance_dashboard_summary(scope: AccessScope, user: User) -> DepartmentAttendanceOverviewRead:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    raw = await _reader.attendance_overview(tenant_id, central_id)
    return DepartmentAttendanceOverviewRead(**raw)


async def get_timetable_dashboard_summary(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
) -> DepartmentTimetableOverviewRead:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    anchor = anchor_date or date.today()
    raw = await _reader.timetable_overview(tenant_id, central_id, anchor=anchor)
    return DepartmentTimetableOverviewRead(**raw)


async def get_examination_dashboard_summary(
    scope: AccessScope,
    user: User,
    *,
    filters: DepartmentDashboardFilters | None = None,
) -> DepartmentExaminationOverviewRead:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    filters = filters or DepartmentDashboardFilters()
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    year, semester = await _resolve_year_semester(tenant_id, filters)
    raw = await _reader.examination_overview(tenant_id, central_id, academic_year_label=year, semester_label=semester)
    return DepartmentExaminationOverviewRead(**raw)


async def get_department_alerts(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
) -> Page[DepartmentAlertRead]:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    rows = await _reader.department_alerts(tenant_id, central_id, limit=pagination.limit + pagination.offset)
    sliced = rows[pagination.offset : pagination.offset + pagination.limit]
    items = [DepartmentAlertRead(**row) for row in sliced]
    return Page(items=items, total=len(rows), limit=pagination.limit, offset=pagination.offset)


async def get_department_activities(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
) -> Page[DepartmentActivityRead]:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    items_raw, total = await _reader.department_activities(
        tenant_id,
        central_id,
        limit=pagination.limit,
        skip=pagination.offset,
    )
    from datetime import datetime

    items = [
        DepartmentActivityRead(
            activity_type=row["activity_type"],
            summary=row["summary"],
            user_id=row["user_id"],
            occurred_at=datetime.fromisoformat(row["occurred_at"].replace("Z", "+00:00")),
        )
        for row in items_raw
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_department_dashboard_bundle(
    scope: AccessScope,
    user: User,
    *,
    filters: DepartmentDashboardFilters | None = None,
) -> DepartmentDashboardBundleRead:
    authorize(scope, Permission.DEPARTMENT_DASHBOARD_READ)
    filters = filters or DepartmentDashboardFilters()
    overview = await get_department_overview(scope, user, filters=filters)
    students = await get_student_dashboard_stats(scope, user, filters=filters)
    faculty = await get_faculty_dashboard_stats(scope, user)
    academics = await get_academic_dashboard_summary(scope, user, filters=filters)
    attendance = await get_attendance_dashboard_summary(scope, user)
    timetable = await get_timetable_dashboard_summary(scope, user, anchor_date=filters.anchor_date)
    examinations = await get_examination_dashboard_summary(scope, user, filters=filters)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    alert_rows = await _reader.department_alerts(tenant_id, central_id, limit=15)
    alerts = [DepartmentAlertRead(**row) for row in alert_rows]
    anchor = filters.anchor_date or date.today()
    window_start, window_end = _date_window(anchor, filters.date_range)
    events = await _reader.upcoming_department_events(
        tenant_id,
        central_id,
        from_time=window_start,
        to_time=window_end,
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.dashboard.view",
        resource_type="department",
        resource_id=str(central_id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={"bundle": True},
    )
    return DepartmentDashboardBundleRead(
        overview=overview,
        students=students,
        faculty=faculty,
        academics=academics,
        attendance=attendance,
        timetable=timetable,
        examinations=examinations,
        alerts=alerts,
        upcoming_events=events,
    )