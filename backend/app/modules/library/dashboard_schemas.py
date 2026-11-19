"""Library dashboard response schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.library.library_enums import LibraryCopyStatus, LibraryDashboardDateRange


class LibraryDashboardFilters(BaseModel):
    branch_code: str | None = None
    category: str | None = None
    copy_status: LibraryCopyStatus | None = None
    anchor_date: date
    date_range: LibraryDashboardDateRange


class CatalogueStats(BaseModel):
    total_titles: int


class CopyInventoryStats(BaseModel):
    total_copies: int
    available: int
    issued: int
    overdue_loans: int
    reserved: int
    lost: int
    damaged: int = Field(description="Physical copies in maintenance status (damaged/repair).")


class LibraryMemberStats(BaseModel):
    total: int
    active: int
    inactive: int
    suspended: int


class CirculationTodayStats(BaseModel):
    issues: int
    returns: int
    activity_date: date


class OutstandingFineSummary(BaseModel):
    open_count: int
    total_amount: float


class AcquisitionSummary(BaseModel):
    recent_count: int
    pending_procurement_count: int


class DigitalResourceStats(BaseModel):
    total: int
    published: int
    unpublished: int


class BranchInventorySummary(BaseModel):
    branch_code: str | None
    branch_name: str | None = None
    total_copies: int
    available: int
    issued: int


class UpcomingDueDateItem(BaseModel):
    circulation_id: str
    book_id: str
    copy_id: str
    title: str
    due_at: date
    student_user_id: str


class LibraryActivityItem(BaseModel):
    activity_id: str
    event_type: str
    summary: str
    branch_code: str | None = None
    actor_id: str | None = None
    created_at: datetime


class LibraryAlertItem(BaseModel):
    code: str
    severity: str
    message: str
    count: int


class LibraryDashboardDependencyNote(BaseModel):
    code: str
    message: str


class LibraryDashboardOverview(BaseModel):
    filters: LibraryDashboardFilters
    catalogue: CatalogueStats
    copies: CopyInventoryStats
    members: LibraryMemberStats
    circulation_today: CirculationTodayStats
    pending_reservations: int
    outstanding_fines: OutstandingFineSummary
    acquisitions: AcquisitionSummary
    digital: DigitalResourceStats
    branch_inventory: list[BranchInventorySummary]
    alerts: list[LibraryAlertItem]
    dependency_notes: list[LibraryDashboardDependencyNote] = Field(default_factory=list)