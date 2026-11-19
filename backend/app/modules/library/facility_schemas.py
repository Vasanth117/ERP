"""Library & branch management API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.library.facility_enums import (
    LibraryLocationLevel,
    LibraryOperatingStatus,
    LibraryStaffAssignmentStatus,
    LibraryStaffRole,
)
from app.modules.library.facility_models import DayOperatingHours


class InstitutionLibraryCreate(BaseModel):
    library_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    campus_id: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_status: LibraryOperatingStatus = LibraryOperatingStatus.ACTIVE


class InstitutionLibraryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    campus_id: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_status: LibraryOperatingStatus | None = None
    is_active: bool | None = None


class InstitutionLibraryRead(BaseModel):
    library_code: str
    name: str
    description: str | None = None
    campus_id: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_status: LibraryOperatingStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LibraryBranchCreate(BaseModel):
    library_code: str = Field(min_length=2, max_length=32)
    branch_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    campus_id: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_status: LibraryOperatingStatus = LibraryOperatingStatus.ACTIVE


class LibraryBranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    campus_id: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_status: LibraryOperatingStatus | None = None
    is_active: bool | None = None


class LibraryBranchRead(BaseModel):
    library_code: str | None
    branch_code: str
    name: str
    description: str | None = None
    campus_id: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_status: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime


class BranchOperationalStats(BaseModel):
    branch_code: str
    total_copies: int
    available_copies: int
    issued_copies: int
    active_circulation: int
    open_fines: int


class OperatingHoursUpsert(BaseModel):
    library_code: str
    branch_code: str | None = None
    days: list[DayOperatingHours]


class OperatingHoursRead(BaseModel):
    library_code: str
    branch_code: str | None = None
    days: list[DayOperatingHours]
    updated_at: datetime


class LibraryHolidayCreate(BaseModel):
    holiday_id: str = Field(min_length=2, max_length=64)
    library_code: str
    branch_code: str | None = None
    start_date: date
    end_date: date
    reason: str = Field(min_length=2, max_length=500)


class LibraryHolidayUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = Field(default=None, min_length=2, max_length=500)
    is_active: bool | None = None


class LibraryHolidayRead(BaseModel):
    holiday_id: str
    library_code: str
    branch_code: str | None = None
    start_date: date
    end_date: date
    reason: str
    is_active: bool
    updated_at: datetime


class LibraryStaffAssignmentCreate(BaseModel):
    assignment_id: str = Field(min_length=2, max_length=64)
    employee_user_id: str
    library_code: str
    branch_code: str | None = None
    staff_role: LibraryStaffRole = LibraryStaffRole.LIBRARIAN
    assigned_on: date
    notes: str | None = None


class LibraryStaffAssignmentUpdate(BaseModel):
    staff_role: LibraryStaffRole | None = None
    branch_code: str | None = None
    status: LibraryStaffAssignmentStatus | None = None
    notes: str | None = None


class LibraryStaffAssignmentRead(BaseModel):
    assignment_id: str
    employee_user_id: str
    library_code: str
    branch_code: str | None = None
    staff_role: LibraryStaffRole
    assigned_on: date
    status: LibraryStaffAssignmentStatus
    notes: str | None = None
    updated_at: datetime


class LibrarySectionCreate(BaseModel):
    branch_code: str
    section_code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class LibrarySectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    is_active: bool | None = None


class LibrarySectionRead(BaseModel):
    branch_code: str
    section_code: str
    name: str
    description: str | None = None
    is_active: bool
    updated_at: datetime


class LibraryShelfLocationCreate(BaseModel):
    branch_code: str
    location_code: str = Field(min_length=1, max_length=64)
    parent_location_code: str | None = None
    level: LibraryLocationLevel
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class LibraryShelfLocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    is_active: bool | None = None


class LibraryShelfLocationRead(BaseModel):
    branch_code: str
    location_code: str
    parent_location_code: str | None = None
    level: LibraryLocationLevel
    name: str
    description: str | None = None
    is_active: bool
    updated_at: datetime


class LibraryConfigurationHistoryRead(BaseModel):
    entity_type: str
    entity_key: str
    action: str
    actor_id: str | None = None
    changes: dict
    created_at: datetime