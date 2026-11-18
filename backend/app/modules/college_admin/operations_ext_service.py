"""Institutional operations extensions service."""

from datetime import datetime
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.operations_ext_models import (
    AssetStatus,
    InstitutionAssetAllocation,
    InstitutionAssetRecord,
    InstitutionFacility,
    InstitutionInventoryItem,
    InstitutionMaintenanceRequest,
    InstitutionOperationalIncident,
    InstitutionOperationsHistory,
    InstitutionServiceContract,
    InstitutionStockMovement,
    MaintenanceStatus,
)
from app.modules.college_admin.operations_ext_schemas import (
    AssetAllocate,
    AssetUpsert,
    FacilityUpsert,
    InventoryUpsert,
    MaintenanceAssign,
    MaintenanceCreate,
    OperationalIncidentCreate,
    OperationsReportRead,
    ServiceContractUpsert,
    StockMovementCreate,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.security_admin_service import append_institution_audit


async def _ops_history(
    tenant_id: PydanticObjectId,
    resource_type: str,
    resource_id: str,
    action: str,
    actor_id: PydanticObjectId | None,
    summary: str,
) -> None:
    await InstitutionOperationsHistory(
        tenant_id=tenant_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        actor_id=actor_id,
        summary=summary,
    ).insert()


async def upsert_asset(scope: AccessScope, user: User, payload: AssetUpsert) -> dict:
    authorize(scope, Permission.OPS_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    aid = payload.asset_id.strip()
    campus = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    dept = to_object_id(payload.owner_department_id, "department_id") if payload.owner_department_id else None
    doc = await InstitutionAssetRecord.find_one(Eq(InstitutionAssetRecord.tenant_id, tenant_id), Eq(InstitutionAssetRecord.asset_id, aid))
    if doc is None:
        doc = InstitutionAssetRecord(
            tenant_id=tenant_id,
            asset_id=aid,
            tag=payload.tag,
            name=payload.name,
            category=payload.category,
            campus_id=campus,
            financial_value=payload.financial_value,
            owner_department_id=dept,
        )
        await doc.insert()
    else:
        doc.tag = payload.tag
        doc.name = payload.name
        doc.category = payload.category
        doc.campus_id = campus
        doc.financial_value = payload.financial_value
        doc.owner_department_id = dept
        doc.updated_at = utcnow()
        await doc.save()
    await _ops_history(tenant_id, "asset", aid, "upsert", user.id, "Asset record saved")
    return {"asset_id": aid}


async def allocate_asset(scope: AccessScope, user: User, asset_id: str, payload: AssetAllocate) -> dict:
    authorize(scope, Permission.OPS_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    asset = await InstitutionAssetRecord.find_one(
        Eq(InstitutionAssetRecord.tenant_id, tenant_id),
        Eq(InstitutionAssetRecord.asset_id, asset_id),
    )
    if asset is None:
        raise AppError(code="NOT_FOUND", message="Asset not found", status_code=404)
    await InstitutionAssetAllocation.find(
        Eq(InstitutionAssetAllocation.tenant_id, tenant_id),
        Eq(InstitutionAssetAllocation.asset_id, asset_id),
        Eq(InstitutionAssetAllocation.active, True),
    ).update({"$set": {"active": False}})
    alloc_id = payload.allocation_id.strip()
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    user_oid = to_object_id(payload.assigned_to_user_id, "assigned_to_user_id") if payload.assigned_to_user_id else None
    await InstitutionAssetAllocation(
        tenant_id=tenant_id,
        allocation_id=alloc_id,
        asset_id=asset_id,
        assigned_to_user_id=user_oid,
        department_id=dept,
        facility_id=payload.facility_id,
    ).insert()
    asset.status = AssetStatus.ALLOCATED
    asset.updated_at = utcnow()
    await asset.save()
    await _ops_history(tenant_id, "asset", asset_id, "allocate", user.id, f"Allocation {alloc_id}")
    return {"allocation_id": alloc_id}


async def upsert_facility(scope: AccessScope, user: User, payload: FacilityUpsert) -> dict:
    authorize(scope, Permission.OPS_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    fid = payload.facility_id.strip()
    campus = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    doc = await InstitutionFacility.find_one(Eq(InstitutionFacility.tenant_id, tenant_id), Eq(InstitutionFacility.facility_id, fid))
    if doc is None:
        await InstitutionFacility(
            tenant_id=tenant_id,
            facility_id=fid,
            name=payload.name,
            facility_type=payload.facility_type,
            campus_id=campus,
            capacity=payload.capacity,
        ).insert()
    else:
        doc.name = payload.name
        doc.facility_type = payload.facility_type
        doc.campus_id = campus
        doc.capacity = payload.capacity
        doc.updated_at = utcnow()
        await doc.save()
    return {"facility_id": fid}


async def create_maintenance(scope: AccessScope, user: User, payload: MaintenanceCreate) -> dict:
    authorize(scope, Permission.OPS_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rid = payload.request_id.strip()
    await InstitutionMaintenanceRequest(
        tenant_id=tenant_id,
        request_id=rid,
        facility_id=payload.facility_id,
        asset_id=payload.asset_id,
        title=payload.title,
        description=payload.description,
        actor_id=user.id,
    ).insert()
    await _ops_history(tenant_id, "maintenance", rid, "create", user.id, payload.title)
    return {"request_id": rid, "status": MaintenanceStatus.OPEN.value}


async def assign_maintenance(scope: AccessScope, user: User, request_id: str, payload: MaintenanceAssign) -> dict:
    authorize(scope, Permission.OPS_EXT_MAINTENANCE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionMaintenanceRequest.find_one(
        Eq(InstitutionMaintenanceRequest.tenant_id, tenant_id),
        Eq(InstitutionMaintenanceRequest.request_id, request_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Maintenance request not found", status_code=404)
    doc.assigned_team = payload.assigned_team
    doc.status = payload.status
    doc.updated_at = utcnow()
    await doc.save()
    await append_institution_audit(tenant_id, actor_id=user.id, action="ops.maintenance.assign", module="operations_ext", resource_type="maintenance", resource_id=request_id)
    return {"request_id": request_id, "status": doc.status.value}


async def upsert_inventory(scope: AccessScope, user: User, payload: InventoryUpsert) -> dict:
    authorize(scope, Permission.OPS_EXT_INVENTORY)
    tenant_id = require_college_tenant_scope(scope)
    iid = payload.item_id.strip()
    doc = await InstitutionInventoryItem.find_one(Eq(InstitutionInventoryItem.tenant_id, tenant_id), Eq(InstitutionInventoryItem.item_id, iid))
    if doc is None:
        await InstitutionInventoryItem(
            tenant_id=tenant_id,
            item_id=iid,
            sku=payload.sku,
            name=payload.name,
            quantity_on_hand=payload.quantity_on_hand,
            reorder_level=payload.reorder_level,
        ).insert()
    else:
        doc.sku = payload.sku
        doc.name = payload.name
        doc.quantity_on_hand = payload.quantity_on_hand
        doc.reorder_level = payload.reorder_level
        doc.updated_at = utcnow()
        await doc.save()
    return {"item_id": iid}


async def record_stock_movement(scope: AccessScope, user: User, payload: StockMovementCreate) -> dict:
    authorize(scope, Permission.OPS_EXT_INVENTORY)
    tenant_id = require_college_tenant_scope(scope)
    item = await InstitutionInventoryItem.find_one(
        Eq(InstitutionInventoryItem.tenant_id, tenant_id),
        Eq(InstitutionInventoryItem.item_id, payload.item_id),
    )
    if item is None:
        raise AppError(code="NOT_FOUND", message="Inventory item not found", status_code=404)
    if payload.direction == "out" and item.quantity_on_hand < payload.quantity:
        raise AppError(code="VALIDATION_ERROR", message="Insufficient stock", status_code=422)
    delta = payload.quantity if payload.direction == "in" else -payload.quantity
    item.quantity_on_hand += delta
    item.updated_at = utcnow()
    await item.save()
    await InstitutionStockMovement(
        tenant_id=tenant_id,
        movement_id=payload.movement_id.strip(),
        item_id=payload.item_id,
        quantity=payload.quantity,
        direction=payload.direction,
        reference=payload.reference,
        actor_id=user.id,
    ).insert()
    await _ops_history(tenant_id, "inventory", payload.item_id, "stock_move", user.id, f"{payload.direction} {payload.quantity}")
    return {"item_id": payload.item_id, "quantity_on_hand": item.quantity_on_hand}


async def upsert_service_contract(scope: AccessScope, user: User, payload: ServiceContractUpsert) -> dict:
    authorize(scope, Permission.OPS_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    cid = payload.contract_id.strip()
    doc = await InstitutionServiceContract.find_one(
        Eq(InstitutionServiceContract.tenant_id, tenant_id),
        Eq(InstitutionServiceContract.contract_id, cid),
    )
    start = datetime.fromisoformat(payload.start_date.replace("Z", "+00:00"))
    end = datetime.fromisoformat(payload.end_date.replace("Z", "+00:00"))
    if doc is None:
        await InstitutionServiceContract(
            tenant_id=tenant_id,
            contract_id=cid,
            vendor_id=payload.vendor_id,
            title=payload.title,
            start_date=start,
            end_date=end,
        ).insert()
    else:
        doc.vendor_id = payload.vendor_id
        doc.title = payload.title
        doc.start_date = start
        doc.end_date = end
        doc.updated_at = utcnow()
        await doc.save()
    return {"contract_id": cid}


async def create_operational_incident(scope: AccessScope, user: User, payload: OperationalIncidentCreate) -> dict:
    authorize(scope, Permission.OPS_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    iid = payload.incident_id.strip()
    await InstitutionOperationalIncident(
        tenant_id=tenant_id,
        incident_id=iid,
        facility_id=payload.facility_id,
        severity=payload.severity,
        title=payload.title,
        description=payload.description,
        actor_id=user.id,
    ).insert()
    return {"incident_id": iid}


async def operations_report(scope: AccessScope) -> OperationsReportRead:
    authorize(scope, Permission.OPS_EXT_READ)
    tenant_id = require_college_tenant_scope(scope)
    assets = await InstitutionAssetRecord.find(Eq(InstitutionAssetRecord.tenant_id, tenant_id)).count()
    maint = await InstitutionMaintenanceRequest.find(
        Eq(InstitutionMaintenanceRequest.tenant_id, tenant_id),
        Eq(InstitutionMaintenanceRequest.status, MaintenanceStatus.OPEN),
    ).count()
    items = await InstitutionInventoryItem.find(Eq(InstitutionInventoryItem.tenant_id, tenant_id)).to_list()
    low = sum(1 for i in items if i.quantity_on_hand <= i.reorder_level)
    incidents = await InstitutionOperationalIncident.find(
        Eq(InstitutionOperationalIncident.tenant_id, tenant_id),
        Eq(InstitutionOperationalIncident.resolved, False),
    ).count()
    return OperationsReportRead(assets_total=assets, open_maintenance=maint, low_stock_items=low, open_incidents=incidents)