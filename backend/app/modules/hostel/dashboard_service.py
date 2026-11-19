"""Hostel dashboard service layer."""

from datetime import date

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.dashboard_filters import build_hostel_dashboard_context
from app.modules.hostel.dashboard_repository import HostelDashboardRepository
from app.modules.hostel.dashboard_schemas import (
    HostelDashboardDependencyNote,
    HostelDashboardFilters,
    HostelDashboardOverview,
    HostelDrillDownRecord,
)
from app.modules.hostel.hostel_portal_enums import HostelDashboardDateRange, HostelDashboardDrillMetric
from app.modules.hostel.policy import authorize_hostel_dashboard, require_hostel_tenant_scope

_repo = HostelDashboardRepository()


def _dependency_notes() -> list[HostelDashboardDependencyNote]:
    return [
        HostelDashboardDependencyNote(
            code="mess_meal_schedule",
            message="Special meal schedules and weekly menu publication reports are basic; advanced analytics remain optional.",
        ),
        HostelDashboardDependencyNote(
            code="visitor_preapproval",
            message="Expected visitors and approval queue require visitor pre-registration (later phase).",
        ),
        HostelDashboardDependencyNote(
            code="hostel_assignment",
            message="Per-hostel-administrator scope assignment is not enforced yet; filters validate hostel existence only.",
        ),
    ]


async def _context(
    scope: AccessScope,
    *,
    academic_year_label: str | None,
    hostel_code: str | None,
    building_code: str | None,
    block_code: str | None,
    floor_id: str | None,
    room_type: str | None,
    department_id: str | None,
    resident_status: str | None,
    allocation_status: str | None,
    mess_status: str | None,
    maintenance_status: str | None,
    anchor_date: date,
    date_range: HostelDashboardDateRange,
):
    tenant_id = require_hostel_tenant_scope(scope)
    return build_hostel_dashboard_context(
        tenant_id,
        academic_year_label=academic_year_label,
        hostel_code=hostel_code,
        building_code=building_code,
        block_code=block_code,
        floor_id=floor_id,
        room_type=room_type,
        department_id=department_id,
        resident_status=resident_status,
        allocation_status=allocation_status,
        mess_status=mess_status,
        maintenance_status=maintenance_status,
        anchor_date=anchor_date,
        date_range=date_range,
    )


def _filters_from_ctx(ctx) -> HostelDashboardFilters:
    return HostelDashboardFilters(
        academic_year_label=ctx.academic_year_label,
        hostel_code=ctx.hostel_code,
        building_code=ctx.building_code,
        block_code=ctx.block_code,
        floor_id=ctx.floor_id,
        room_type=ctx.room_type,
        department_id=str(ctx.department_id) if ctx.department_id else None,
        resident_status=ctx.resident_status,
        allocation_status=ctx.allocation_status,
        mess_status=ctx.mess_status,
        maintenance_status=ctx.maintenance_status,
        anchor_date=ctx.anchor_date.isoformat(),
        date_range=ctx.date_range,
    )


async def get_hostel_dashboard_overview(
    scope: AccessScope,
    user: User,
    *,
    academic_year_label: str | None = None,
    hostel_code: str | None = None,
    building_code: str | None = None,
    block_code: str | None = None,
    floor_id: str | None = None,
    room_type: str | None = None,
    department_id: str | None = None,
    resident_status: str | None = None,
    allocation_status: str | None = None,
    mess_status: str | None = None,
    maintenance_status: str | None = None,
    anchor_date: date | None = None,
    date_range: HostelDashboardDateRange = HostelDashboardDateRange.WEEK,
) -> HostelDashboardOverview:
    _ = user
    authorize_hostel_dashboard(scope)
    ctx = await _context(
        scope,
        academic_year_label=academic_year_label,
        hostel_code=hostel_code,
        building_code=building_code,
        block_code=block_code,
        floor_id=floor_id,
        room_type=room_type,
        department_id=department_id,
        resident_status=resident_status,
        allocation_status=allocation_status,
        mess_status=mess_status,
        maintenance_status=maintenance_status,
        anchor_date=anchor_date or date.today(),
        date_range=date_range,
    )
    return HostelDashboardOverview(
        filters=_filters_from_ctx(ctx),
        hostel_overview=await _repo.hostel_overview(ctx),
        resident_overview=await _repo.resident_overview(ctx),
        allocation_overview=await _repo.allocation_overview(ctx),
        mess_overview=await _repo.mess_overview(ctx),
        visitor_overview=await _repo.visitor_overview(ctx),
        maintenance_overview=await _repo.maintenance_overview(ctx),
        leave_outpass_overview=await _repo.leave_outpass_overview(ctx),
        incident_overview=await _repo.incident_overview(ctx),
        recent_activities=await _repo.recent_activities(ctx),
        alerts=await _repo.alerts(ctx),
        dependency_notes=_dependency_notes(),
    )


async def get_dashboard_drill_down(
    scope: AccessScope,
    metric: HostelDashboardDrillMetric,
    pagination: Pagination,
    **filter_kwargs,
) -> Page[HostelDrillDownRecord]:
    authorize_hostel_dashboard(scope)
    ctx = await _context(
        scope,
        anchor_date=filter_kwargs.get("anchor_date") or date.today(),
        date_range=filter_kwargs.get("date_range") or HostelDashboardDateRange.WEEK,
        academic_year_label=filter_kwargs.get("academic_year_label"),
        hostel_code=filter_kwargs.get("hostel_code"),
        building_code=filter_kwargs.get("building_code"),
        block_code=filter_kwargs.get("block_code"),
        floor_id=filter_kwargs.get("floor_id"),
        room_type=filter_kwargs.get("room_type"),
        department_id=filter_kwargs.get("department_id"),
        resident_status=filter_kwargs.get("resident_status"),
        allocation_status=filter_kwargs.get("allocation_status"),
        mess_status=filter_kwargs.get("mess_status"),
        maintenance_status=filter_kwargs.get("maintenance_status"),
    )
    rows, total = await _repo.drill_down(ctx, metric.value, limit=pagination.limit, offset=pagination.offset)
    items = [
        HostelDrillDownRecord(
            record_type=metric.value,
            record_id=str(row.get("bed_id") or row.get("application_id") or row.get("visit_id") or row.get("request_id") or row.get("incident_id") or row.get("allocation_id") or row.get("hostel_code") or "unknown"),
            summary=str(row),
            status=row.get("status"),
            metadata=row,
        )
        for row in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)