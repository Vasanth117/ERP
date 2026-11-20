"""Campus buildings, contacts and facility showcase records."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class InstitutionCampusBuilding(Document):
    tenant_id: PydanticObjectId
    campus_id: PydanticObjectId
    building_id: str
    name: str = Field(max_length=200)
    floors: int = Field(default=0, ge=0)
    classroom_count: int = Field(default=0, ge=0)
    laboratory_count: int = Field(default=0, ge=0)
    departments_label: str = Field(default="", max_length=500)
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_campus_buildings"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("campus_id", ASCENDING), ("building_id", ASCENDING)],
                unique=True,
                name="unique_campus_building",
            ),
        ]


class InstitutionCampusOfficialContact(Document):
    tenant_id: PydanticObjectId
    campus_id: PydanticObjectId
    contact_id: str
    role_label: str = Field(max_length=120)
    name: str = Field(max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_campus_official_contacts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("campus_id", ASCENDING), ("contact_id", ASCENDING)],
                unique=True,
                name="unique_campus_official_contact",
            ),
        ]


class InstitutionCampusEmergencyContact(Document):
    tenant_id: PydanticObjectId
    campus_id: PydanticObjectId
    contact_id: str
    label: str = Field(max_length=200)
    phone: str = Field(max_length=64)
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_campus_emergency_contacts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("campus_id", ASCENDING), ("contact_id", ASCENDING)],
                unique=True,
                name="unique_campus_emergency_contact",
            ),
        ]


class InstitutionCampusFacilityShowcase(Document):
    tenant_id: PydanticObjectId
    campus_id: PydanticObjectId
    showcase_id: str
    title: str = Field(max_length=200)
    subtitle: str = Field(default="", max_length=500)
    status_code: str = Field(default="open", max_length=32)
    status_label: str = Field(default="Open", max_length=64)
    icon_slug: str = Field(default="landmark", max_length=64)
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_campus_facility_showcases"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("campus_id", ASCENDING), ("showcase_id", ASCENDING)],
                unique=True,
                name="unique_campus_facility_showcase",
            ),
        ]