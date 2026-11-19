"""Hostel infrastructure API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.hostel.hostel_portal_enums import (
    HostelBuildingStatus,
    HostelCategory,
    HostelFacilityCondition,
    HostelFacilityType,
    HostelOperatingStatus,
    HostelRoomMaintenanceStatus,
    HostelRoomOperationalStatus,
    HostelRoomType,
)


class HostelAddressSchema(BaseModel):
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


class HostelContactSchema(BaseModel):
    email: str | None = None
    phone: str | None = None


class InstitutionHostelCreate(BaseModel):
    hostel_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    category: HostelCategory = HostelCategory.BOYS
    custom_category_label: str | None = None
    description: str | None = None
    campus_id: str | None = None
    address: HostelAddressSchema | None = None
    contact: HostelContactSchema | None = None
    warden_user_id: str | None = None
    configured_capacity: int = Field(ge=0, default=0)


class InstitutionHostelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    category: HostelCategory | None = None
    custom_category_label: str | None = None
    description: str | None = None
    campus_id: str | None = None
    address: HostelAddressSchema | None = None
    contact: HostelContactSchema | None = None
    warden_user_id: str | None = None
    configured_capacity: int | None = Field(default=None, ge=0)
    operating_status: HostelOperatingStatus | None = None
    is_active: bool | None = None


class InstitutionHostelRead(BaseModel):
    hostel_code: str
    name: str
    category: HostelCategory
    custom_category_label: str | None
    description: str | None
    campus_id: str | None
    address: HostelAddressSchema
    contact: HostelContactSchema
    warden_user_id: str | None
    configured_capacity: int
    operating_status: HostelOperatingStatus
    is_active: bool
    updated_at: datetime


class HostelBuildingCreate(BaseModel):
    hostel_code: str
    building_code: str
    name: str
    building_type: str | None = None
    campus_id: str | None = None
    facilities: list[str] = Field(default_factory=list)
    responsible_staff_user_id: str | None = None
    operating_status: HostelBuildingStatus = HostelBuildingStatus.ACTIVE


class HostelBuildingUpdate(BaseModel):
    name: str | None = None
    building_type: str | None = None
    facilities: list[str] | None = None
    responsible_staff_user_id: str | None = None
    operating_status: HostelBuildingStatus | None = None
    is_active: bool | None = None


class HostelBlockCreate(BaseModel):
    hostel_code: str
    building_code: str
    block_code: str
    name: str
    responsible_staff_user_id: str | None = None


class HostelFloorCreate(BaseModel):
    hostel_code: str
    building_code: str
    floor_id: str
    floor_number: int = Field(ge=0)
    name: str
    description: str | None = None
    sort_order: int = Field(ge=0, default=0)


class HostelFloorUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class HostelRoomCreate(BaseModel):
    hostel_code: str
    building_code: str
    block_code: str
    room_code: str
    floor_id: str | None = None
    floor_label: str | None = None
    room_type: HostelRoomType = HostelRoomType.DOUBLE
    capacity: int = Field(ge=1, default=2)
    bed_capacity: int = Field(ge=1, default=2)
    facilities: list[str] = Field(default_factory=list)
    description: str | None = None
    operational_status: HostelRoomOperationalStatus = HostelRoomOperationalStatus.ACTIVE
    maintenance_status: HostelRoomMaintenanceStatus = HostelRoomMaintenanceStatus.AVAILABLE
    gender_policy: str | None = None


class HostelBedPortalCreate(BaseModel):
    hostel_code: str
    bed_id: str
    building_code: str
    block_code: str
    room_code: str
    bed_label: str


class HostelFacilityCreate(BaseModel):
    hostel_code: str
    facility_id: str
    facility_type: HostelFacilityType
    title: str
    location_label: str | None = None
    building_code: str | None = None
    block_code: str | None = None
    floor_id: str | None = None
    is_available: bool = True
    condition: HostelFacilityCondition = HostelFacilityCondition.GOOD
    details: dict = Field(default_factory=dict)


class HostelFacilityUpdate(BaseModel):
    title: str | None = None
    location_label: str | None = None
    is_available: bool | None = None
    condition: HostelFacilityCondition | None = None
    details: dict | None = None


class HostelCapacitySummary(BaseModel):
    hostel_code: str
    configured_capacity: int
    total_beds: int
    available_beds: int
    occupied_beds: int
    maintenance_beds: int
    reserved_beds: int
    occupancy_percentage: float


class HostelManagementHistoryRead(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    metadata: dict
    actor_id: str | None
    created_at: datetime