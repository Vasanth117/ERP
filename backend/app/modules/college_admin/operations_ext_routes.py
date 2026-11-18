"""Operations extensions routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
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
from app.modules.college_admin.operations_ext_service import (
    allocate_asset,
    assign_maintenance,
    create_maintenance,
    create_operational_incident,
    operations_report,
    record_stock_movement,
    upsert_asset,
    upsert_facility,
    upsert_inventory,
    upsert_service_contract,
)

router = APIRouter()


@router.put("/assets", response_model=ApiResponse[dict])
async def asset_upsert_route(payload: AssetUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await upsert_asset(scope, user, payload), request_id=get_request_id())


@router.post("/assets/{asset_id}/allocate", response_model=ApiResponse[dict])
async def asset_alloc_route(asset_id: str, payload: AssetAllocate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await allocate_asset(scope, user, asset_id, payload), request_id=get_request_id())


@router.put("/facilities", response_model=ApiResponse[dict])
async def facility_route(payload: FacilityUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await upsert_facility(scope, user, payload), request_id=get_request_id())


@router.post("/maintenance", response_model=ApiResponse[dict])
async def maintenance_create_route(payload: MaintenanceCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await create_maintenance(scope, user, payload), request_id=get_request_id())


@router.post("/maintenance/{request_id}/assign", response_model=ApiResponse[dict])
async def maintenance_assign_route(request_id: str, payload: MaintenanceAssign, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await assign_maintenance(scope, user, request_id, payload), request_id=get_request_id())


@router.put("/inventory", response_model=ApiResponse[dict])
async def inventory_route(payload: InventoryUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await upsert_inventory(scope, user, payload), request_id=get_request_id())


@router.post("/inventory/stock-movements", response_model=ApiResponse[dict])
async def stock_route(payload: StockMovementCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await record_stock_movement(scope, user, payload), request_id=get_request_id())


@router.put("/service-contracts", response_model=ApiResponse[dict])
async def contract_route(payload: ServiceContractUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await upsert_service_contract(scope, user, payload), request_id=get_request_id())


@router.post("/incidents", response_model=ApiResponse[dict])
async def incident_route(payload: OperationalIncidentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await create_operational_incident(scope, user, payload), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[OperationsReportRead])
async def ops_report_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[OperationsReportRead]:
    return success_response(await operations_report(scope), request_id=get_request_id())