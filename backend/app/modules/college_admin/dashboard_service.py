"""College admin dashboard aggregation."""

from datetime import date

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.modules.auth.models import User
from app.modules.college_admin.enums import DashboardDateRange, InstitutionActivityKind
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader, _date_window
from app.modules.college_admin.models import InstitutionActivityLog
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.repositories import InstitutionActivityRepository
from app.modules.college_admin.schemas import (
    AcademicTermSummary,
    ActivitySummary,
    CollegeDashboardOverview,
    CollegeDashboardStatsRead,
    DashboardFilterParams,
    OperationalSummariesRead,
    PendingApprovalItem,
)
from app.modules.audit.models import AuditLog

_reader = OperationalDataReader()
_activity_repo = InstitutionActivityRepository()


async def _resolve_filters(
    scope: AccessScope,
    *,
    anchor_date: date | None,
    date_range: DashboardDateRange,
    department_id: str | None,
    campus_id: str | None,
    academic_year_label: str | None,
) -> tuple[DashboardFilterParams, PydanticObjectId | None, PydanticObjectId | None, str | None]:
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    campus_oid = to_object_id(campus_id, "campus_id") if campus_id else None
    if dept_oid is not None:
        pass
    year_label = academic_year_label
    if year_label is None:
        year_label, _ = await _reader.current_academic_term(tenant_id)
    filters = DashboardFilterParams(
        anchor_date=anchor_date,
        date_range=date_range,
        department_id=department_id,
        campus_id=campus_id,
        academic_year_label=year_label,
    )
    return filters, dept_oid, campus_oid, year_label


async def get_dashboard_overview(
    scope: AccessScope,
    user: User,
    *,
    anchor_date: date | None = None,
    date_range: DashboardDateRange = DashboardDateRange.WEEK,
    department_id: str | None = None,
    campus_id: str | None = None,
    academic_year_label: str | None = None,
) -> CollegeDashboardOverview:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    filters, dept_oid, _campus_oid, year_label = await _resolve_filters(
        scope,
        anchor_date=anchor_date,
        date_range=date_range,
        department_id=department_id,
        campus_id=campus_id,
        academic_year_label=academic_year_label,
    )
    anchor = anchor_date or date.today()
    year, semester = await _reader.current_academic_term(tenant_id)
    if year_label:
        year = year_label

    statistics = await _reader.headcount_statistics(tenant_id, department_id=dept_oid)
    attendance = await _reader.attendance_summary(tenant_id)
    examinations = await _reader.examination_summary(tenant_id, academic_year_label=year, semester_label=semester)
    finance = await _reader.finance_summary(tenant_id)
    library_hostel = await _reader.library_hostel_summary(tenant_id)
    integration_health = await _reader.integration_health(tenant_id)
    window_start, window_end = _date_window(anchor, date_range)
    upcoming_events = await _reader.upcoming_events(tenant_id, from_time=window_start, to_time=window_end)
    notifications = await _reader.institutional_notifications(tenant_id)
    pending = await _reader.pending_approvals(tenant_id, department_id=dept_oid)
    support = await _reader.unresolved_support_requests(tenant_id)

    await InstitutionActivityLog(
        tenant_id=tenant_id,
        actor_id=user.id,
        activity_kind=InstitutionActivityKind.DASHBOARD_VIEW,
        resource_type="college_dashboard",
        resource_id=None,
        summary="College admin dashboard viewed",
        metadata={"filters": filters.model_dump(mode="json")},
    ).insert()

    return CollegeDashboardOverview(
        filters=filters,
        academic_term=AcademicTermSummary(academic_year_label=year, semester_label=semester),
        statistics=statistics,
        attendance=attendance,
        examinations=examinations,
        finance=finance,
        library_hostel=library_hostel,
        pending_approval_count=len(pending),
        unresolved_support_count=len(support),
        upcoming_events=upcoming_events,
        notifications=notifications,
        integration_health=integration_health,
    )


async def get_institutional_statistics(
    scope: AccessScope,
    *,
    department_id: str | None = None,
    academic_year_label: str | None = None,
) -> CollegeDashboardStatsRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    year, semester = await _reader.current_academic_term(tenant_id)
    if academic_year_label:
        year = academic_year_label
    statistics = await _reader.headcount_statistics(tenant_id, department_id=dept_oid)
    return CollegeDashboardStatsRead(
        academic_term=AcademicTermSummary(academic_year_label=year, semester_label=semester),
        statistics=statistics,
    )


async def get_operational_summaries(
    scope: AccessScope,
    *,
    academic_year_label: str | None = None,
) -> OperationalSummariesRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    year, semester = await _reader.current_academic_term(tenant_id)
    if academic_year_label:
        year = academic_year_label
    return OperationalSummariesRead(
        attendance=await _reader.attendance_summary(tenant_id),
        examinations=await _reader.examination_summary(tenant_id, academic_year_label=year, semester_label=semester),
        finance=await _reader.finance_summary(tenant_id),
        library_hostel=await _reader.library_hostel_summary(tenant_id),
        integration_health=await _reader.integration_health(tenant_id),
    )


async def get_pending_approvals(
    scope: AccessScope,
    *,
    department_id: str | None = None,
    pagination: Pagination,
) -> Page[PendingApprovalItem]:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    items = await _reader.pending_approvals(tenant_id, department_id=dept_oid, limit=pagination.limit + pagination.offset)
    slice_items = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_items, total=len(items), limit=pagination.limit, offset=pagination.offset)


async def get_recent_activities(
    scope: AccessScope,
    *,
    anchor_date: date | None = None,
    date_range: DashboardDateRange = DashboardDateRange.WEEK,
    pagination: Pagination,
) -> Page[ActivitySummary]:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    anchor = anchor_date or date.today()
    window_start, _ = _date_window(anchor, date_range)

    student_rows = await _reader.recent_student_activities(tenant_id, from_time=window_start, limit=50)
    faculty_rows = await _reader.recent_faculty_activities(tenant_id, from_time=window_start, limit=50)
    admission_rows = await _reader.recent_admissions(tenant_id, from_time=window_start, limit=20)
    admin_rows = await _activity_repo.list_recent(tenant_id, limit=20)
    admin_summaries = [
        ActivitySummary(
            activity_id=str(row.id),
            category="institution",
            title=row.summary,
            occurred_at=row.created_at,
            reference_id=row.resource_id,
        )
        for row in admin_rows
    ]

    audit_rows = await (
        AuditLog.find({"tenant_id": tenant_id, "created_at": {"$gte": window_start}})
        .sort("-created_at")
        .limit(20)
        .to_list()
    )
    audit_summaries = [
        ActivitySummary(
            activity_id=str(row.id),
            category="audit",
            title=row.action,
            occurred_at=row.created_at,
            reference_id=row.resource_id,
        )
        for row in audit_rows
    ]

    combined = student_rows + faculty_rows + admission_rows + admin_summaries + audit_summaries
    combined.sort(key=lambda item: item.occurred_at, reverse=True)
    total = len(combined)
    slice_items = combined[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_items, total=total, limit=pagination.limit, offset=pagination.offset)
