"""Hostel dashboard schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.hostel.hostel_portal_enums import HostelDashboardDateRange


class HostelDashboardFilters(BaseModel):
    academic_year_label: str | None = None
    hostel_code: str | None = None
    building_code: str | None = None
    block_code: str | None = None
    floor_id: str | None = None
    room_type: str | None = None
    department_id: str | None = None
    resident_status: str | None = None
    allocation_status: str | None = None
    mess_status: str | None = None
    maintenance_status: str | None = None
    anchor_date: str
    date_range: HostelDashboardDateRange


class OccupancyBreakdownItem(BaseModel):
    key: str
    label: str | None = None
    total_beds: int = 0
    occupied_beds: int = 0
    available_beds: int = 0
    occupancy_percentage: float = 0.0


class HostelOverviewStats(BaseModel):
    total_hostels: int = 0
    active_hostels: int = 0
    inactive_hostels: int = 0
    total_buildings: int = 0
    total_blocks: int = 0
    total_floors: int = 0
    total_rooms: int = 0
    total_beds: int = 0
    occupied_beds: int = 0
    available_beds: int = 0
    reserved_beds: int = 0
    maintenance_beds: int = 0
    occupancy_percentage: float = 0.0
    by_hostel: list[OccupancyBreakdownItem] = Field(default_factory=list)
    by_block: list[OccupancyBreakdownItem] = Field(default_factory=list)
    by_floor: list[OccupancyBreakdownItem] = Field(default_factory=list)


class ResidentOverviewStats(BaseModel):
    total_registered_residents: int = 0
    checked_in_residents: int = 0
    awaiting_check_in: int = 0
    checked_out_residents: int = 0
    upcoming_checkouts: int = 0
    on_approved_outpass: int = 0
    overdue_outpasses: int = 0
    pending_applications: int = 0


class AllocationOverviewStats(BaseModel):
    pending_allocation_requests: int = 0
    approved_awaiting_allocation: int = 0
    waiting_list_students: int = 0
    rooms_awaiting_assignment: int = 0
    available_beds_by_type: dict[str, int] = Field(default_factory=dict)
    recent_allocations: int = 0
    pending_room_transfers: int = 0
    cancelled_allocations: int = 0


class MessOverviewStats(BaseModel):
    active_mess_plans: int = 0
    residents_enrolled: int = 0
    residents_without_mess: int = 0
    billing_period_label: str | None = None
    pending_billing_records: int = 0
    outstanding_mess_charges: float = 0.0
    plan_changes_pending_approval: int = 0


class VisitorOverviewStats(BaseModel):
    visitors_today: int = 0
    currently_inside: int = 0
    expected_visitors: int = 0
    awaiting_approval: int = 0
    incomplete_checkout: int = 0
    recent_activity_count: int = 0


class MaintenanceOverviewStats(BaseModel):
    open_complaints: int = 0
    high_priority: int = 0
    in_progress: int = 0
    pending_assignments: int = 0
    unavailable_rooms: int = 0
    unavailable_beds: int = 0
    overdue_tasks: int = 0
    recently_resolved: int = 0


class LeaveOutpassOverviewStats(BaseModel):
    pending_leave_requests: int = 0
    pending_outpass_approvals: int = 0
    approved_outpasses_active: int = 0
    students_returned: int = 0
    overdue_returns: int = 0


class IncidentOverviewStats(BaseModel):
    open_incidents: int = 0
    under_investigation: int = 0
    serious_incidents: int = 0
    pending_disciplinary_reviews: int = 0
    recent_incidents: int = 0


class HostelActivityItem(BaseModel):
    activity_id: str
    category: str
    title: str
    occurred_at: datetime
    metadata: dict = Field(default_factory=dict)


class HostelAlertItem(BaseModel):
    code: str
    severity: str = "info"
    title: str
    message: str


class HostelDashboardDependencyNote(BaseModel):
    code: str
    message: str


class HostelDashboardOverview(BaseModel):
    filters: HostelDashboardFilters
    hostel_overview: HostelOverviewStats
    resident_overview: ResidentOverviewStats
    allocation_overview: AllocationOverviewStats
    mess_overview: MessOverviewStats
    visitor_overview: VisitorOverviewStats
    maintenance_overview: MaintenanceOverviewStats
    leave_outpass_overview: LeaveOutpassOverviewStats
    incident_overview: IncidentOverviewStats
    recent_activities: list[HostelActivityItem] = Field(default_factory=list)
    alerts: list[HostelAlertItem] = Field(default_factory=list)
    dependency_notes: list[HostelDashboardDependencyNote] = Field(default_factory=list)


class HostelDrillDownRecord(BaseModel):
    record_type: str
    record_id: str
    summary: str
    status: str | None = None
    occurred_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)