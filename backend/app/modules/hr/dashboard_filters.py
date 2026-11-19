"""HR dashboard filter context."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId

from app.modules.hr.enums import HrDashboardDateRange


@dataclass
class HrDashboardContext:
    tenant_id: PydanticObjectId
    department_id: PydanticObjectId | None
    campus_id: PydanticObjectId | None
    anchor_date: date
    date_from: date
    date_to: date
    activity_from: datetime
    activity_to: datetime


def _utc_day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def resolve_date_range(anchor: date, date_range: HrDashboardDateRange, date_from: date | None, date_to: date | None) -> tuple[date, date]:
    if date_range == HrDashboardDateRange.CUSTOM and date_from and date_to:
        return date_from, date_to
    if date_range == HrDashboardDateRange.TODAY:
        return anchor, anchor
    if date_range == HrDashboardDateRange.WEEK:
        return anchor - timedelta(days=6), anchor
    if date_range == HrDashboardDateRange.MONTH:
        return anchor - timedelta(days=29), anchor
    if date_range == HrDashboardDateRange.QUARTER:
        return anchor - timedelta(days=89), anchor
    if date_range == HrDashboardDateRange.YEAR:
        return anchor - timedelta(days=364), anchor
    return anchor - timedelta(days=6), anchor


def build_hr_dashboard_context(
    tenant_id: PydanticObjectId,
    *,
    department_id: PydanticObjectId | None,
    campus_id: PydanticObjectId | None,
    anchor_date: date,
    date_range: HrDashboardDateRange,
    date_from: date | None,
    date_to: date | None,
) -> HrDashboardContext:
    start, end = resolve_date_range(anchor_date, date_range, date_from, date_to)
    act_start, _ = _utc_day_bounds(start)
    _, act_end = _utc_day_bounds(end)
    return HrDashboardContext(
        tenant_id=tenant_id,
        department_id=department_id,
        campus_id=campus_id,
        anchor_date=anchor_date,
        date_from=start,
        date_to=end,
        activity_from=act_start,
        activity_to=act_end,
    )


def employee_record_match(ctx: HrDashboardContext) -> dict:
    match: dict = {"tenant_id": ctx.tenant_id}
    if ctx.department_id:
        match["department_id"] = ctx.department_id
    if ctx.campus_id:
        match["campus_id"] = ctx.campus_id
    return match