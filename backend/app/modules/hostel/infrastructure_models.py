"""Hostel Admin infrastructure collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hostel.hostel_portal_enums import (
    HostelCategory,
    HostelFacilityCondition,
    HostelFacilityType,
    HostelOperatingStatus,
)


class HostelContact(BaseModel):
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=32)


class HostelAddress(BaseModel):
    line1: str | None = Field(default=None, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=80)


class InstitutionHostel(Document):
    """Top-level hostel facility (parent of buildings)."""

    tenant_id: PydanticObjectId
    hostel_code: str = Field(max_length=32)
    name: str = Field(max_length=200)
    category: HostelCategory = HostelCategory.BOYS
    custom_category_label: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    campus_id: PydanticObjectId | None = None
    address: HostelAddress = Field(default_factory=HostelAddress)
    contact: HostelContact = Field(default_factory=HostelContact)
    warden_user_id: PydanticObjectId | None = None
    configured_capacity: int = Field(ge=0, default=0)
    operating_status: HostelOperatingStatus = HostelOperatingStatus.ACTIVE
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "hostels"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("hostel_code", ASCENDING)],
                unique=True,
                name="unique_hostel_per_tenant",
            ),
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], name="hostels_active_by_tenant"),
            IndexModel([("tenant_id", ASCENDING), ("campus_id", ASCENDING)], name="hostels_by_campus"),
        ]


class HostelFloor(Document):
    tenant_id: PydanticObjectId
    hostel_code: str
    building_code: str
    floor_id: str = Field(max_length=32)
    floor_number: int = Field(ge=0)
    name: str = Field(max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    sort_order: int = Field(ge=0, default=0)
    is_active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "hostel_floors"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("hostel_code", ASCENDING), ("building_code", ASCENDING), ("floor_id", ASCENDING)],
                unique=True,
                name="unique_hostel_floor",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("hostel_code", ASCENDING), ("building_code", ASCENDING), ("sort_order", ASCENDING)],
                name="floors_by_order",
            ),
        ]


class HostelFacility(Document):
    tenant_id: PydanticObjectId
    facility_id: str = Field(max_length=40)
    hostel_code: str
    facility_type: HostelFacilityType
    title: str = Field(max_length=200)
    location_label: str | None = Field(default=None, max_length=200)
    building_code: str | None = None
    block_code: str | None = None
    floor_id: str | None = None
    is_available: bool = True
    condition: HostelFacilityCondition = HostelFacilityCondition.GOOD
    details: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "hostel_facilities"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("facility_id", ASCENDING)],
                unique=True,
                name="unique_hostel_facility",
            ),
            IndexModel([("tenant_id", ASCENDING), ("hostel_code", ASCENDING), ("facility_type", ASCENDING)], name="facilities_by_hostel"),
        ]


class HostelFacilityHistory(Document):
    tenant_id: PydanticObjectId
    facility_id: str
    event_type: str = Field(max_length=64)
    note: str | None = Field(default=None, max_length=2000)
    condition: HostelFacilityCondition | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_facility_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("facility_id", ASCENDING), ("created_at", DESCENDING)],
                name="facility_history",
            ),
        ]


class HostelManagementHistory(Document):
    tenant_id: PydanticObjectId
    hostel_code: str
    entity_type: str = Field(max_length=32)
    entity_id: str
    action: str = Field(max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_management_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("hostel_code", ASCENDING), ("created_at", DESCENDING)],
                name="hostel_mgmt_history",
            ),
        ]