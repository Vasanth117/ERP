"""Library & branch management collections (librarian module)."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.library.facility_enums import (
    LibraryConfigEntityType,
    LibraryLocationLevel,
    LibraryOperatingStatus,
    LibraryStaffAssignmentStatus,
    LibraryStaffRole,
)


class OperatingSession(BaseModel):
    opens_at: str = Field(pattern=r"^\d{2}:\d{2}$", description="24h HH:MM")
    closes_at: str = Field(pattern=r"^\d{2}:\d{2}$", description="24h HH:MM")


class DayOperatingHours(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0=Monday")
    is_closed: bool = False
    sessions: list[OperatingSession] = Field(default_factory=list)


class InstitutionLibrary(Document):
    """Top-level institutional library (parent of branches)."""

    tenant_id: PydanticObjectId
    library_code: str = Field(max_length=32)
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    campus_id: PydanticObjectId | None = None
    address: str | None = Field(default=None, max_length=500)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=32)
    operating_status: LibraryOperatingStatus = LibraryOperatingStatus.ACTIVE
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_institutions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("library_code", ASCENDING)],
                unique=True,
                name="unique_library_per_tenant",
            ),
        ]


class LibraryOperatingHours(Document):
    tenant_id: PydanticObjectId
    library_code: str
    branch_code: str | None = None
    days: list[DayOperatingHours] = Field(default_factory=list)
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_operating_hours"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("library_code", ASCENDING), ("branch_code", ASCENDING)],
                unique=True,
                name="unique_operating_hours_scope",
            ),
        ]


class LibraryHoliday(Document):
    tenant_id: PydanticObjectId
    holiday_id: str
    library_code: str
    branch_code: str | None = None
    start_date: date
    end_date: date
    reason: str = Field(max_length=500)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_holidays"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("holiday_id", ASCENDING)],
                unique=True,
                name="unique_library_holiday",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("library_code", ASCENDING), ("start_date", ASCENDING)],
                name="library_holidays_by_library",
            ),
        ]


class LibraryStaffAssignment(Document):
    tenant_id: PydanticObjectId
    assignment_id: str
    employee_user_id: PydanticObjectId
    library_code: str
    branch_code: str | None = None
    staff_role: LibraryStaffRole = LibraryStaffRole.LIBRARIAN
    assigned_on: date
    status: LibraryStaffAssignmentStatus = LibraryStaffAssignmentStatus.ACTIVE
    notes: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_staff_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("assignment_id", ASCENDING)],
                unique=True,
                name="unique_library_staff_assignment",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("status", ASCENDING)],
                name="library_staff_by_branch",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("status", ASCENDING)],
                name="library_staff_by_employee",
            ),
        ]


class LibrarySection(Document):
    tenant_id: PydanticObjectId
    branch_code: str
    section_code: str = Field(max_length=32)
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_sections"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("section_code", ASCENDING)],
                unique=True,
                name="unique_library_section",
            ),
        ]


class LibraryShelfLocation(Document):
    tenant_id: PydanticObjectId
    branch_code: str
    location_code: str = Field(max_length=64)
    parent_location_code: str | None = Field(default=None, max_length=64)
    level: LibraryLocationLevel
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_shelf_locations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("location_code", ASCENDING)],
                unique=True,
                name="unique_shelf_location",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("parent_location_code", ASCENDING)],
                name="shelf_location_children",
            ),
        ]


class LibraryConfigurationHistory(Document):
    tenant_id: PydanticObjectId
    entity_type: LibraryConfigEntityType
    entity_key: str
    action: str
    actor_id: PydanticObjectId | None = None
    changes: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_configuration_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="library_config_history_recent"),
            IndexModel(
                [("tenant_id", ASCENDING), ("entity_type", ASCENDING), ("entity_key", ASCENDING)],
                name="library_config_history_entity",
            ),
        ]