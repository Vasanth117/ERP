"""HR dashboard service."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.hr.dashboard_filters import build_hr_dashboard_context
from app.modules.hr.dashboard_repository import HrDashboardRepository
from app.modules.hr.dashboard_schemas import DashboardEmployeeListItem, HrDashboardFilters, HrDashboardOverview
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.enums import EmployeeAttendanceDayStatus, HrDashboardDateRange, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest
from app.modules.hr.operational_models import EmployeeDayAttendance
from app.modules.hr.policy import authorize_hr_dashboard, require_hr_tenant_scope

_repo = HrDashboardRepository()


async def _context(
    scope: AccessScope,
    *,
    department_id: str | None,
    campus_id: str | None,
    anchor_date: date | None,
    date_range: HrDashboardDateRange,
    date_from: date | None,
    date_to: date | None,
):
    tenant_id = require_hr_tenant_scope(scope)
    anchor = anchor_date or date.today()
    dept = to_object_id(department_id, "department_id") if department_id else None
    campus = to_object_id(campus_id, "campus_id") if campus_id else None
    return build_hr_dashboard_context(
        tenant_id,
        department_id=dept,
        campus_id=campus,
        anchor_date=anchor,
        date_range=date_range,
        date_from=date_from,
        date_to=date_to,
    )


def _filters_from_ctx(ctx) -> HrDashboardFilters:
    return HrDashboardFilters(
        department_id=str(ctx.department_id) if ctx.department_id else None,
        campus_id=str(ctx.campus_id) if ctx.campus_id else None,
        anchor_date=ctx.anchor_date,
        date_range=HrDashboardDateRange.WEEK,
        date_from=ctx.date_from,
        date_to=ctx.date_to,
    )


async def get_hr_dashboard_overview(
    scope: AccessScope,
    user: User,
    *,
    department_id: str | None = None,
    campus_id: str | None = None,
    anchor_date: date | None = None,
    date_range: HrDashboardDateRange = HrDashboardDateRange.WEEK,
    date_from: date | None = None,
    date_to: date | None = None,
) -> HrDashboardOverview:
    _ = user
    authorize_hr_dashboard(scope)
    ctx = await _context(
        scope,
        department_id=department_id,
        campus_id=campus_id,
        anchor_date=anchor_date,
        date_range=date_range,
        date_from=date_from,
        date_to=date_to,
    )
    filters = _filters_from_ctx(ctx)
    filters.date_range = date_range
    return HrDashboardOverview(
        filters=filters,
        employees=await _repo.employee_overview(ctx),
        attendance=await _repo.attendance_overview(ctx),
        leave=await _repo.leave_overview(ctx),
        recruitment=await _repo.recruitment_overview(ctx),
        onboarding=await _repo.onboarding_overview(ctx),
        payroll=await _repo.payroll_overview(ctx),
        alerts=await _repo.alerts(ctx),
        recent_activities=await _repo.recent_activities(ctx),
    )


async def get_recent_hr_activities(
    scope: AccessScope,
    *,
    department_id: str | None = None,
    campus_id: str | None = None,
    anchor_date: date | None = None,
    date_range: HrDashboardDateRange = HrDashboardDateRange.WEEK,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
):
    authorize_hr_dashboard(scope)
    ctx = await _context(
        scope,
        department_id=department_id,
        campus_id=campus_id,
        anchor_date=anchor_date,
        date_range=date_range,
        date_from=date_from,
        date_to=date_to,
    )
    return await _repo.recent_activities(ctx, limit=limit)


async def list_dashboard_employees(
    scope: AccessScope,
    metric: str,
    pagination: Pagination,
    *,
    department_id: str | None = None,
    campus_id: str | None = None,
    anchor_date: date | None = None,
) -> Page[DashboardEmployeeListItem]:
    authorize_hr_dashboard(scope)
    ctx = await _context(
        scope,
        department_id=department_id,
        campus_id=campus_id,
        anchor_date=anchor_date,
        date_range=HrDashboardDateRange.TODAY,
        date_from=None,
        date_to=None,
    )
    profiles_by_user: dict[str, HrEmployeeProfile] = {}
    for profile in await HrEmployeeProfile.find(Eq(HrEmployeeProfile.tenant_id, ctx.tenant_id)).to_list():
        profiles_by_user[str(profile.user_id)] = profile

    employees = await EmployeeRecord.find(
        {
            "tenant_id": ctx.tenant_id,
            **({"department_id": ctx.department_id} if ctx.department_id else {}),
            **({"campus_id": ctx.campus_id} if ctx.campus_id else {}),
        }
    ).to_list()

    items: list[DashboardEmployeeListItem] = []
    metric_key = metric.strip().lower()

    for emp in employees:
        profile = profiles_by_user.get(str(emp.user_id))
        name = f"{profile.first_name} {profile.last_name}".strip() if profile else None
        code = profile.employee_code if profile else emp.employee_id
        include = False
        detail: dict = {}

        if metric_key == "total":
            include = True
        elif metric_key == "active" and emp.employment_status == FacultyEmploymentStatus.ACTIVE:
            include = True
        elif metric_key == "inactive" and emp.employment_status == FacultyEmploymentStatus.INACTIVE:
            include = True
        elif metric_key == "probation" and emp.employment_status == FacultyEmploymentStatus.PROBATION:
            include = True
        elif metric_key == "awaiting_confirmation" and emp.employment_status == FacultyEmploymentStatus.AWAITING_CONFIRMATION:
            include = True
        elif metric_key == "notice_period" and emp.employment_status == FacultyEmploymentStatus.NOTICE_PERIOD:
            include = True
        elif metric_key == "resigned" and emp.employment_status == FacultyEmploymentStatus.RESIGNED:
            include = True
        elif metric_key == "terminated" and emp.employment_status == FacultyEmploymentStatus.TERMINATED:
            include = True
        elif metric_key == "recently_joined" and emp.joining_date and ctx.date_from <= emp.joining_date <= ctx.date_to:
            include = True
        elif metric_key.startswith("department:") and emp.department_id and str(emp.department_id) == metric_key.split(":", 1)[1]:
            include = True
        elif metric_key.startswith("designation:") and emp.designation == metric_key.split(":", 1)[1]:
            include = True
        elif metric_key.startswith("employment_type:") and emp.employment_type == metric_key.split(":", 1)[1]:
            include = True
        elif metric_key.startswith("campus:") and emp.campus_id and str(emp.campus_id) == metric_key.split(":", 1)[1]:
            include = True
        elif metric_key in {"present_today", "absent_today", "late_today", "early_departure_today", "on_leave_today", "missing_today"}:
            att = await EmployeeDayAttendance.find_one(
                Eq(EmployeeDayAttendance.tenant_id, ctx.tenant_id),
                Eq(EmployeeDayAttendance.employee_user_id, emp.user_id),
                Eq(EmployeeDayAttendance.attendance_date, ctx.anchor_date),
            )
            status_map = {
                "present_today": EmployeeAttendanceDayStatus.PRESENT,
                "absent_today": EmployeeAttendanceDayStatus.ABSENT,
                "late_today": EmployeeAttendanceDayStatus.LATE,
                "early_departure_today": EmployeeAttendanceDayStatus.EARLY_DEPARTURE,
                "on_leave_today": EmployeeAttendanceDayStatus.ON_LEAVE,
                "missing_today": EmployeeAttendanceDayStatus.MISSING,
            }
            if metric_key == "missing_today" and att is None:
                include = True
            elif att and att.status == status_map.get(metric_key):
                include = True
                detail = {"attendance_status": att.status.value}
        elif metric_key == "pending_leave":
            pending = await LeaveRequest.find_one(
                Eq(LeaveRequest.tenant_id, ctx.tenant_id),
                Eq(LeaveRequest.employee_user_id, emp.user_id),
                Eq(LeaveRequest.status, LeaveRequestStatus.SUBMITTED),
            )
            include = pending is not None

        if include:
            items.append(
                DashboardEmployeeListItem(
                    user_id=str(emp.user_id),
                    employee_code=code,
                    full_name=name,
                    department_id=str(emp.department_id) if emp.department_id else None,
                    designation=emp.designation,
                    employment_status=emp.employment_status.value,
                    detail=detail,
                )
            )

    total = len(items)
    page = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=page, total=total, limit=pagination.limit, offset=pagination.offset)


async def review_leave_request(scope: AccessScope, leave_request_id: str, decision: LeaveRequestStatus, note: str | None = None) -> dict:
    authorize(scope, Permission.HR_LEAVE_REVIEW)
    from app.common.time import utcnow
    from app.core.exceptions import AppError
    from app.modules.college_admin.hr_admin_models import EmployeeLeaveApproval
    from app.modules.hr.employee_sync import log_hr_activity
    from app.modules.hr.enums import HrStaffActivityType

    tenant_id = require_hr_tenant_scope(scope)
    if decision not in (LeaveRequestStatus.APPROVED, LeaveRequestStatus.REJECTED):
        raise AppError(code="VALIDATION_ERROR", message="Invalid leave decision", status_code=422)
    leave_id = to_object_id(leave_request_id, "leave_request_id")
    req = await LeaveRequest.get(leave_id)
    if req is None or req.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Leave request not found", status_code=404)
    if req.status not in {LeaveRequestStatus.SUBMITTED, LeaveRequestStatus.PENDING_HR, LeaveRequestStatus.PENDING_MANAGER}:
        raise AppError(code="CONFLICT", message="Leave request is not pending", status_code=409)
    if await EmployeeLeaveApproval.find_one(
        Eq(EmployeeLeaveApproval.tenant_id, tenant_id),
        Eq(EmployeeLeaveApproval.leave_request_id, leave_id),
    ):
        raise AppError(code="CONFLICT", message="Leave already reviewed", status_code=409)
    if decision == LeaveRequestStatus.APPROVED:
        from app.modules.hr.leave_schemas import LeaveApplicationReview
        from app.modules.hr.leave_service import review_leave_application

        reviewed = await review_leave_application(scope, leave_request_id, LeaveApplicationReview(decision="approve", note=note))
        return {"leave_request_id": reviewed.id, "decision": reviewed.status.value}
    req.status = decision
    req.approver_note = note
    req.updated_at = utcnow()
    await req.save()
    await EmployeeLeaveApproval(
        tenant_id=tenant_id,
        leave_request_id=leave_id,
        employee_user_id=req.employee_user_id,
        decision=decision,
        reviewer_id=scope.user_id,
        note=note,
    ).insert()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.LEAVE_APPLICATION,
        f"Leave request {decision.value}",
        actor_id=scope.user_id,
        employee_user_id=req.employee_user_id,
        resource_type="leave_request",
        resource_id=str(req.id),
        status_label=decision.value,
    )
    return {"leave_request_id": str(leave_id), "decision": decision.value}