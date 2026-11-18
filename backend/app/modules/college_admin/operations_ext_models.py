"""Institutional operations extensions (assets, facilities, inventory)."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class AssetStatus(str, Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class MaintenanceStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InstitutionAssetRecord(Document):
    tenant_id: PydanticObjectId
    asset_id: str
    tag: str
    name: str
    category: str
    campus_id: PydanticObjectId | None = None
    financial_value: float = Field(default=0, ge=0)
    status: AssetStatus = AssetStatus.AVAILABLE
    owner_department_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_asset_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("asset_id", ASCENDING)], unique=True, name="unique_asset"),
            IndexModel([("tenant_id", ASCENDING), ("tag", ASCENDING)], unique=True, name="unique_asset_tag"),
        ]


class InstitutionAssetAllocation(Document):
    tenant_id: PydanticObjectId
    allocation_id: str
    asset_id: str
    assigned_to_user_id: PydanticObjectId | None = None
    department_id: PydanticObjectId | None = None
    facility_id: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_asset_allocations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("allocation_id", ASCENDING)], unique=True, name="unique_asset_allocation"),
        ]


class InstitutionFacility(Document):
    tenant_id: PydanticObjectId
    facility_id: str
    name: str
    campus_id: PydanticObjectId | None = None
    facility_type: str = "building"
    capacity: int | None = None
    utilization_percent: float = Field(default=0, ge=0, le=100)
    active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_facilities"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("facility_id", ASCENDING)], unique=True, name="unique_facility"),
        ]


class InstitutionMaintenanceRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str
    facility_id: str | None = None
    asset_id: str | None = None
    title: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    status: MaintenanceStatus = MaintenanceStatus.OPEN
    assigned_team: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_maintenance_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_campus_maintenance"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="maintenance_by_status"),
        ]


class InstitutionInventoryItem(Document):
    tenant_id: PydanticObjectId
    item_id: str
    sku: str
    name: str
    quantity_on_hand: float = Field(ge=0)
    reorder_level: float = Field(default=0, ge=0)
    unit: str = "ea"
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_inventory_items"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("item_id", ASCENDING)], unique=True, name="unique_inventory_item"),
            IndexModel([("tenant_id", ASCENDING), ("sku", ASCENDING)], unique=True, name="unique_inventory_sku"),
        ]


class InstitutionStockMovement(Document):
    tenant_id: PydanticObjectId
    movement_id: str
    item_id: str
    quantity: float
    direction: str
    reference: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_stock_movements"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("item_id", ASCENDING), ("created_at", DESCENDING)], name="stock_movements"),
        ]


class InstitutionServiceContract(Document):
    tenant_id: PydanticObjectId
    contract_id: str
    vendor_id: str
    title: str
    start_date: datetime
    end_date: datetime
    active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_service_contracts"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("contract_id", ASCENDING)], unique=True, name="unique_service_contract"),
        ]


class InstitutionOperationalIncident(Document):
    tenant_id: PydanticObjectId
    incident_id: str
    facility_id: str | None = None
    severity: str = "medium"
    title: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    resolved: bool = False
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_operational_incidents"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("incident_id", ASCENDING)], unique=True, name="unique_ops_incident"),
        ]


class InstitutionOperationsHistory(Document):
    tenant_id: PydanticObjectId
    resource_type: str
    resource_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    summary: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_operations_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="ops_history"),
        ]