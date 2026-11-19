"""Hostel dashboard filter context."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId

from app.common.ids import to_object_id
from app.modules.hostel.hostel_portal_enums import HostelDashboardDateRange


@dataclass
class HostelDashboardContext:
    tenant_id: PydanticObjectId
    academic_year_label: str | None = None
    hostel_code: str | None = None
    building_code: str | None = None
    block_code: str | None = None
    floor_id: str | None = None
    room_type: str | None = None
    department_id: PydanticObjectId | None = None
    resident_status: str | None = None
    allocation_status: str | None = None
    mess_status: str | None = None
    maintenance_status: str | None = None
    anchor_date: date = field(default_factory=lambda: date.today())
    date_range: HostelDashboardDateRange = HostelDashboardDateRange.WEEK
    building_codes: list[str] = field(default_factory=list)

    @property
    def range_start(self) -> datetime:
        anchor = datetime.combine(self.anchor_date, datetime.min.time(), tzinfo=timezone.utc)
        if self.date_range == HostelDashboardDateRange.TODAY:
            return anchor
        if self.date_range == HostelDashboardDateRange.WEEK:
            return anchor - timedelta(days=7)
        if self.date_range == HostelDashboardDateRange.MONTH:
            return anchor - timedelta(days=30)
        return anchor - timedelta(days=120)

    @property
    def range_end(self) -> datetime:
        return datetime.combine(self.anchor_date, datetime.max.time(), tzinfo=timezone.utc)


def norm_filter_code(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().upper()


def build_hostel_dashboard_context(
    tenant_id: PydanticObjectId,
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
    building_codes: list[str] | None = None,
) -> HostelDashboardContext:
    dept = to_object_id(department_id, "department_id") if department_id else None
    return HostelDashboardContext(
        tenant_id=tenant_id,
        academic_year_label=academic_year_label,
        hostel_code=norm_filter_code(hostel_code),
        building_code=norm_filter_code(building_code),
        block_code=norm_filter_code(block_code),
        floor_id=norm_filter_code(floor_id),
        room_type=room_type,
        department_id=dept,
        resident_status=resident_status,
        allocation_status=allocation_status,
        mess_status=mess_status,
        maintenance_status=maintenance_status,
        anchor_date=anchor_date,
        date_range=date_range,
        building_codes=building_codes or [],
    )