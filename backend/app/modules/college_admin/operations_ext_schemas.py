"""Operations extension API schemas."""

from pydantic import BaseModel, Field

from app.modules.college_admin.operations_ext_models import AssetStatus, MaintenanceStatus


class AssetUpsert(BaseModel):
    asset_id: str
    tag: str
    name: str
    category: str
    campus_id: str | None = None
    financial_value: float = Field(default=0, ge=0)
    owner_department_id: str | None = None


class AssetAllocate(BaseModel):
    allocation_id: str
    department_id: str | None = None
    assigned_to_user_id: str | None = None
    facility_id: str | None = None


class FacilityUpsert(BaseModel):
    facility_id: str
    name: str
    facility_type: str = "building"
    campus_id: str | None = None
    capacity: int | None = None


class MaintenanceCreate(BaseModel):
    request_id: str
    title: str
    description: str
    facility_id: str | None = None
    asset_id: str | None = None


class MaintenanceAssign(BaseModel):
    assigned_team: str
    status: MaintenanceStatus = MaintenanceStatus.ASSIGNED


class InventoryUpsert(BaseModel):
    item_id: str
    sku: str
    name: str
    quantity_on_hand: float = Field(ge=0)
    reorder_level: float = Field(default=0, ge=0)


class StockMovementCreate(BaseModel):
    movement_id: str
    item_id: str
    quantity: float = Field(gt=0)
    direction: str
    reference: str | None = None


class ServiceContractUpsert(BaseModel):
    contract_id: str
    vendor_id: str
    title: str
    start_date: str
    end_date: str


class OperationalIncidentCreate(BaseModel):
    incident_id: str
    title: str
    description: str
    facility_id: str | None = None
    severity: str = "medium"


class OperationsReportRead(BaseModel):
    assets_total: int
    open_maintenance: int
    low_stock_items: int
    open_incidents: int