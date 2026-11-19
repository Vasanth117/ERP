"""Hostel Admin infrastructure services."""

from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus, HostelBlock, HostelBuilding, HostelRoom
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.infrastructure_models import (
    HostelAddress,
    HostelContact,
    HostelFacility,
    HostelFacilityHistory,
    HostelFloor,
    HostelManagementHistory,
    InstitutionHostel,
)
from app.modules.hostel.infrastructure_schemas import (
    HostelBedPortalCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelBuildingUpdate,
    HostelCapacitySummary,
    HostelFacilityCreate,
    HostelFacilityUpdate,
    HostelFloorCreate,
    HostelManagementHistoryRead,
    HostelRoomCreate,
    InstitutionHostelCreate,
    InstitutionHostelRead,
    InstitutionHostelUpdate,
)
from app.modules.hostel.infrastructure_validation import (
    assert_hostel_capacity,
    assert_no_active_allocations_for_building,
    count_beds_for_hostel,
    get_hostel_block,
    get_hostel_building,
    get_hostel_room,
    norm_code,
    validate_room_capacities,
)
from app.modules.hostel.policy import authorize_hostel_infrastructure_manage, authorize_hostel_infrastructure_read, require_hostel_tenant_scope


async def _assert_campus(tenant_id: PydanticObjectId, campus_id: str | None) -> PydanticObjectId | None:
    if not campus_id:
        return None
    oid = to_object_id(campus_id, "campus_id")
    campus = await InstitutionCampus.find_one(Eq(InstitutionCampus.tenant_id, tenant_id), Eq(InstitutionCampus.id, oid))
    if campus is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown campus", status_code=422)
    return oid


async def _get_institution_hostel(tenant_id: PydanticObjectId, hostel_code: str) -> InstitutionHostel:
    doc = await InstitutionHostel.find_one(
        Eq(InstitutionHostel.tenant_id, tenant_id),
        Eq(InstitutionHostel.hostel_code, norm_code(hostel_code)),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Hostel not found", status_code=404)
    return doc


async def _record_history(
    tenant_id: PydanticObjectId,
    *,
    hostel_code: str,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: PydanticObjectId | None,
    metadata: dict | None = None,
) -> None:
    await HostelManagementHistory(
        tenant_id=tenant_id,
        hostel_code=norm_code(hostel_code),
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        metadata=metadata or {},
        actor_id=actor_id,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action=action,
        module="hostel",
        resource_type=entity_type,
        resource_id=entity_id,
        metadata={"hostel_code": norm_code(hostel_code), **(metadata or {})},
    )


def _hostel_read(doc: InstitutionHostel) -> InstitutionHostelRead:
    return InstitutionHostelRead(
        hostel_code=doc.hostel_code,
        name=doc.name,
        category=doc.category,
        custom_category_label=doc.custom_category_label,
        description=doc.description,
        campus_id=str(doc.campus_id) if doc.campus_id else None,
        address=doc.address.model_dump(),
        contact=doc.contact.model_dump(),
        warden_user_id=str(doc.warden_user_id) if doc.warden_user_id else None,
        configured_capacity=doc.configured_capacity,
        operating_status=doc.operating_status,
        is_active=doc.is_active,
        updated_at=doc.updated_at,
    )


async def create_hostel(scope: AccessScope, payload: InstitutionHostelCreate) -> InstitutionHostelRead:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    code = norm_code(payload.hostel_code)
    if await InstitutionHostel.find_one(Eq(InstitutionHostel.tenant_id, tenant_id), Eq(InstitutionHostel.hostel_code, code)):
        raise AppError(code="CONFLICT", message="Hostel code already exists", status_code=409)
    campus_id = await _assert_campus(tenant_id, payload.campus_id)
    warden = to_object_id(payload.warden_user_id, "warden_user_id") if payload.warden_user_id else None
    if warden:
        warden_user = await User.find_one(Eq(User.tenant_id, tenant_id), Eq(User.id, warden))
        if warden_user is None:
            raise AppError(code="VALIDATION_ERROR", message="Unknown warden user", status_code=422)
    doc = InstitutionHostel(
        tenant_id=tenant_id,
        hostel_code=code,
        name=payload.name.strip(),
        category=payload.category,
        custom_category_label=payload.custom_category_label,
        description=payload.description,
        campus_id=campus_id,
        address=HostelAddress(**(payload.address.model_dump() if payload.address else {})),
        contact=HostelContact(**(payload.contact.model_dump() if payload.contact else {})),
        warden_user_id=warden,
        configured_capacity=payload.configured_capacity,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _record_history(
        tenant_id,
        hostel_code=code,
        entity_type="hostel",
        entity_id=code,
        action="create",
        actor_id=scope.user_id,
    )
    return _hostel_read(doc)


async def list_hostels(scope: AccessScope, pagination: Pagination, *, active_only: bool = False) -> Page[InstitutionHostelRead]:
    authorize_hostel_infrastructure_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    query = InstitutionHostel.find(Eq(InstitutionHostel.tenant_id, tenant_id))
    if active_only:
        query = query.find(Eq(InstitutionHostel.is_active, True))
    total = await query.count()
    rows = await query.sort("-updated_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_hostel_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_hostel(scope: AccessScope, hostel_code: str) -> InstitutionHostelRead:
    authorize_hostel_infrastructure_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    return _hostel_read(await _get_institution_hostel(tenant_id, hostel_code))


async def update_hostel(scope: AccessScope, hostel_code: str, payload: InstitutionHostelUpdate) -> InstitutionHostelRead:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await _get_institution_hostel(tenant_id, hostel_code)
    if payload.name is not None:
        doc.name = payload.name.strip()
    if payload.category is not None:
        doc.category = payload.category
    if payload.custom_category_label is not None:
        doc.custom_category_label = payload.custom_category_label
    if payload.description is not None:
        doc.description = payload.description
    if payload.campus_id is not None:
        doc.campus_id = await _assert_campus(tenant_id, payload.campus_id)
    if payload.address is not None:
        doc.address = HostelAddress(**payload.address.model_dump())
    if payload.contact is not None:
        doc.contact = HostelContact(**payload.contact.model_dump())
    if payload.warden_user_id is not None:
        doc.warden_user_id = to_object_id(payload.warden_user_id, "warden_user_id")
    if payload.configured_capacity is not None:
        current_beds = await count_beds_for_hostel(tenant_id, doc.hostel_code)
        if payload.configured_capacity < current_beds:
            raise AppError(
                code="VALIDATION_ERROR",
                message="Configured capacity cannot be less than existing beds",
                status_code=422,
            )
        doc.configured_capacity = payload.configured_capacity
    if payload.operating_status is not None:
        doc.operating_status = payload.operating_status
    if payload.is_active is not None:
        doc.is_active = payload.is_active
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await _record_history(
        tenant_id,
        hostel_code=doc.hostel_code,
        entity_type="hostel",
        entity_id=doc.hostel_code,
        action="update",
        actor_id=scope.user_id,
        metadata=payload.model_dump(exclude_none=True),
    )
    return _hostel_read(doc)


async def create_building(scope: AccessScope, payload: HostelBuildingCreate) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    hostel = await _get_institution_hostel(tenant_id, payload.hostel_code)
    code = norm_code(payload.building_code)
    if await HostelBuilding.find_one(Eq(HostelBuilding.tenant_id, tenant_id), Eq(HostelBuilding.building_code, code)):
        raise AppError(code="CONFLICT", message="Building code exists", status_code=409)
    campus_id = await _assert_campus(tenant_id, payload.campus_id) if payload.campus_id else hostel.campus_id
    staff = to_object_id(payload.responsible_staff_user_id, "responsible_staff_user_id") if payload.responsible_staff_user_id else None
    await HostelBuilding(
        tenant_id=tenant_id,
        hostel_code=hostel.hostel_code,
        building_code=code,
        name=payload.name.strip(),
        building_type=payload.building_type,
        campus_id=campus_id,
        facilities=payload.facilities,
        responsible_staff_user_id=staff,
        operating_status=payload.operating_status.value,
    ).insert()
    await _record_history(
        tenant_id,
        hostel_code=hostel.hostel_code,
        entity_type="building",
        entity_id=code,
        action="create",
        actor_id=scope.user_id,
    )
    return {"hostel_code": hostel.hostel_code, "building_code": code}


async def update_building(scope: AccessScope, building_code: str, payload: HostelBuildingUpdate) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    building = await get_hostel_building(tenant_id, building_code)
    if payload.name is not None:
        building.name = payload.name.strip()
    if payload.building_type is not None:
        building.building_type = payload.building_type
    if payload.facilities is not None:
        building.facilities = payload.facilities
    if payload.responsible_staff_user_id is not None:
        building.responsible_staff_user_id = to_object_id(payload.responsible_staff_user_id, "responsible_staff_user_id")
    if payload.operating_status is not None:
        building.operating_status = payload.operating_status.value
    if payload.is_active is not None:
        building.is_active = payload.is_active
    building.updated_at = utcnow()
    await building.save()
    return {"building_code": building.building_code, "is_active": building.is_active}


async def create_block(scope: AccessScope, payload: HostelBlockCreate) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    hostel = await _get_institution_hostel(tenant_id, payload.hostel_code)
    building = await get_hostel_building(tenant_id, payload.building_code)
    if building.hostel_code and building.hostel_code != hostel.hostel_code:
        raise AppError(code="VALIDATION_ERROR", message="Building does not belong to hostel", status_code=422)
    bcode = norm_code(payload.block_code)
    if await HostelBlock.find_one(
        Eq(HostelBlock.tenant_id, tenant_id),
        Eq(HostelBlock.building_code, building.building_code),
        Eq(HostelBlock.block_code, bcode),
    ):
        raise AppError(code="CONFLICT", message="Block code exists for building", status_code=409)
    staff = to_object_id(payload.responsible_staff_user_id, "responsible_staff_user_id") if payload.responsible_staff_user_id else None
    await HostelBlock(
        tenant_id=tenant_id,
        hostel_code=hostel.hostel_code,
        building_code=building.building_code,
        block_code=bcode,
        name=payload.name.strip(),
        responsible_staff_user_id=staff,
    ).insert()
    return {"hostel_code": hostel.hostel_code, "building_code": building.building_code, "block_code": bcode}


async def create_floor(scope: AccessScope, payload: HostelFloorCreate) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    hostel = await _get_institution_hostel(tenant_id, payload.hostel_code)
    building = await get_hostel_building(tenant_id, payload.building_code)
    if building.hostel_code and building.hostel_code != hostel.hostel_code:
        raise AppError(code="VALIDATION_ERROR", message="Building does not belong to hostel", status_code=422)
    floor_id = norm_code(payload.floor_id)
    if await HostelFloor.find_one(
        Eq(HostelFloor.tenant_id, tenant_id),
        Eq(HostelFloor.hostel_code, hostel.hostel_code),
        Eq(HostelFloor.building_code, building.building_code),
        Eq(HostelFloor.floor_id, floor_id),
    ):
        raise AppError(code="CONFLICT", message="Floor id exists", status_code=409)
    await HostelFloor(
        tenant_id=tenant_id,
        hostel_code=hostel.hostel_code,
        building_code=building.building_code,
        floor_id=floor_id,
        floor_number=payload.floor_number,
        name=payload.name.strip(),
        description=payload.description,
        sort_order=payload.sort_order,
        updated_by=scope.user_id,
    ).insert()
    return {"floor_id": floor_id}


async def create_room(scope: AccessScope, payload: HostelRoomCreate) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    hostel = await _get_institution_hostel(tenant_id, payload.hostel_code)
    await get_hostel_block(tenant_id, payload.building_code, payload.block_code)
    validate_room_capacities(capacity=payload.capacity, bed_capacity=payload.bed_capacity)
    room_code = norm_code(payload.room_code)
    if await HostelRoom.find_one(
        Eq(HostelRoom.tenant_id, tenant_id),
        Eq(HostelRoom.building_code, norm_code(payload.building_code)),
        Eq(HostelRoom.block_code, norm_code(payload.block_code)),
        Eq(HostelRoom.room_code, room_code),
    ):
        raise AppError(code="CONFLICT", message="Room code exists", status_code=409)
    if payload.floor_id:
        floor = await HostelFloor.find_one(
            Eq(HostelFloor.tenant_id, tenant_id),
            Eq(HostelFloor.hostel_code, hostel.hostel_code),
            Eq(HostelFloor.floor_id, norm_code(payload.floor_id)),
        )
        if floor is None:
            raise AppError(code="VALIDATION_ERROR", message="Unknown floor", status_code=422)
    await assert_hostel_capacity(tenant_id, hostel.hostel_code, hostel.configured_capacity)
    await HostelRoom(
        tenant_id=tenant_id,
        hostel_code=hostel.hostel_code,
        building_code=norm_code(payload.building_code),
        block_code=norm_code(payload.block_code),
        floor_id=norm_code(payload.floor_id) if payload.floor_id else None,
        floor_label=payload.floor_label,
        room_code=room_code,
        room_type=payload.room_type.value,
        capacity=payload.capacity,
        bed_capacity=payload.bed_capacity,
        facilities=payload.facilities,
        description=payload.description,
        operational_status=payload.operational_status.value,
        maintenance_status=payload.maintenance_status.value,
        gender_policy=payload.gender_policy,
    ).insert()
    return {"room_code": room_code}


async def create_bed(scope: AccessScope, payload: HostelBedPortalCreate) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    hostel = await _get_institution_hostel(tenant_id, payload.hostel_code)
    room = await get_hostel_room(tenant_id, payload.building_code, payload.block_code, payload.room_code)
    bed_id = payload.bed_id.strip()
    if await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, bed_id)):
        raise AppError(code="CONFLICT", message="Bed id exists", status_code=409)
    existing_beds = await HostelBed.find(
        {
            "tenant_id": tenant_id,
            "building_code": room.building_code,
            "block_code": room.block_code,
            "room_code": room.room_code,
        }
    ).count()
    if existing_beds >= room.bed_capacity:
        raise AppError(code="VALIDATION_ERROR", message="Room bed capacity reached", status_code=422)
    await assert_hostel_capacity(tenant_id, hostel.hostel_code, hostel.configured_capacity, adding_beds=1)
    await HostelBed(
        tenant_id=tenant_id,
        hostel_code=hostel.hostel_code,
        bed_id=bed_id,
        building_code=room.building_code,
        block_code=room.block_code,
        room_code=room.room_code,
        bed_label=payload.bed_label.strip(),
    ).insert()
    return {"bed_id": bed_id}


async def create_facility(scope: AccessScope, payload: HostelFacilityCreate) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    hostel = await _get_institution_hostel(tenant_id, payload.hostel_code)
    facility_id = payload.facility_id.strip()
    if await HostelFacility.find_one(Eq(HostelFacility.tenant_id, tenant_id), Eq(HostelFacility.facility_id, facility_id)):
        raise AppError(code="CONFLICT", message="Facility id exists", status_code=409)
    await HostelFacility(
        tenant_id=tenant_id,
        facility_id=facility_id,
        hostel_code=hostel.hostel_code,
        facility_type=payload.facility_type,
        title=payload.title.strip(),
        location_label=payload.location_label,
        building_code=norm_code(payload.building_code) if payload.building_code else None,
        block_code=norm_code(payload.block_code) if payload.block_code else None,
        floor_id=norm_code(payload.floor_id) if payload.floor_id else None,
        is_available=payload.is_available,
        condition=payload.condition,
        details=payload.details,
        updated_by=scope.user_id,
    ).insert()
    await HostelFacilityHistory(
        tenant_id=tenant_id,
        facility_id=facility_id,
        event_type="create",
        condition=payload.condition,
        actor_id=scope.user_id,
    ).insert()
    return {"facility_id": facility_id}


async def update_facility(scope: AccessScope, facility_id: str, payload: HostelFacilityUpdate) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelFacility.find_one(Eq(HostelFacility.tenant_id, tenant_id), Eq(HostelFacility.facility_id, facility_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Facility not found", status_code=404)
    if payload.title is not None:
        doc.title = payload.title.strip()
    if payload.location_label is not None:
        doc.location_label = payload.location_label
    if payload.is_available is not None:
        doc.is_available = payload.is_available
    if payload.condition is not None:
        doc.condition = payload.condition
    if payload.details is not None:
        doc.details = payload.details
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await HostelFacilityHistory(
        tenant_id=tenant_id,
        facility_id=facility_id,
        event_type="update",
        condition=doc.condition,
        actor_id=scope.user_id,
    ).insert()
    return {"facility_id": facility_id}


async def deactivate_building(scope: AccessScope, building_code: str) -> dict[str, Any]:
    authorize_hostel_infrastructure_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    building = await get_hostel_building(tenant_id, building_code)
    await assert_no_active_allocations_for_building(tenant_id, building.building_code)
    building.is_active = False
    building.operating_status = "inactive"
    building.updated_at = utcnow()
    await building.save()
    return {"building_code": building.building_code, "is_active": False}


async def hostel_capacity_summary(scope: AccessScope, hostel_code: str) -> HostelCapacitySummary:
    authorize_hostel_infrastructure_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    hostel = await _get_institution_hostel(tenant_id, hostel_code)
    code = hostel.hostel_code
    building_codes = [
        b.building_code
        for b in await HostelBuilding.find({"tenant_id": tenant_id, "hostel_code": code}).to_list()
    ]
    bed_filter: dict[str, Any] = {"tenant_id": tenant_id}
    if building_codes:
        bed_filter["$or"] = [{"hostel_code": code}, {"building_code": {"$in": building_codes}}]
    else:
        bed_filter["hostel_code"] = code
    total = await HostelBed.find(bed_filter).count()
    available = await HostelBed.find({**bed_filter, "status": HostelBedStatus.AVAILABLE.value}).count()
    occupied = await HostelBed.find({**bed_filter, "status": HostelBedStatus.ALLOCATED.value}).count()
    maintenance = await HostelBed.find({**bed_filter, "status": HostelBedStatus.MAINTENANCE.value}).count()
    reserved = await HostelBed.find({**bed_filter, "status": HostelBedStatus.RESERVED.value}).count()
    denom = max(total, 1)
    return HostelCapacitySummary(
        hostel_code=code,
        configured_capacity=hostel.configured_capacity,
        total_beds=total,
        available_beds=available,
        occupied_beds=occupied,
        maintenance_beds=maintenance,
        reserved_beds=reserved,
        occupancy_percentage=round((occupied + reserved) / denom * 100, 2),
    )


async def list_management_history(scope: AccessScope, hostel_code: str, pagination: Pagination) -> Page[HostelManagementHistoryRead]:
    authorize_hostel_infrastructure_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    await _get_institution_hostel(tenant_id, hostel_code)
    query = HostelManagementHistory.find(
        Eq(HostelManagementHistory.tenant_id, tenant_id),
        Eq(HostelManagementHistory.hostel_code, norm_code(hostel_code)),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        HostelManagementHistoryRead(
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            action=r.action,
            metadata=r.metadata,
            actor_id=str(r.actor_id) if r.actor_id else None,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)