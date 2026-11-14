"""Hostel administration services."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from pymongo.errors import DuplicateKeyError

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.hostel_admin_models import (
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBedStatus,
    HostelBlock,
    HostelBuilding,
    HostelIncident,
    HostelMaintenanceRequest,
    HostelMessPlan,
    HostelOutpassRequest,
    HostelResidentHistory,
    HostelRoom,
    HostelRule,
    HostelVisitorLog,
    HostelWaitingListEntry,
)
from app.modules.college_admin.hostel_admin_schemas import (
    AllocationApprove,
    CheckInOut,
    HostelApplicationReview,
    HostelBedCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelRoomCreate,
    HostelRuleUpsert,
    IncidentCreate,
    MaintenanceCreate,
    MessPlanUpsert,
    OutpassDecision,
    VisitorLogCreate,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.hostel_models import HostelApplication, HostelRoomAllocation


async def create_building(scope: AccessScope, payload: HostelBuildingCreate) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.building_code.upper()
    if await HostelBuilding.find_one(Eq(HostelBuilding.tenant_id, tenant_id), Eq(HostelBuilding.building_code, code)):
        raise AppError(code="CONFLICT", message="Building code exists", status_code=409)
    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    await HostelBuilding(tenant_id=tenant_id, building_code=code, name=payload.name, campus_id=campus_id).insert()
    return {"building_code": code}


async def create_block(scope: AccessScope, payload: HostelBlockCreate) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    bcode = payload.building_code.upper()
    block = payload.block_code.upper()
    await HostelBlock(tenant_id=tenant_id, building_code=bcode, block_code=block, name=payload.name).insert()
    return {"block_code": block}


async def create_room(scope: AccessScope, payload: HostelRoomCreate) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    await HostelRoom(
        tenant_id=tenant_id,
        building_code=payload.building_code.upper(),
        block_code=payload.block_code.upper(),
        room_code=payload.room_code.upper(),
        capacity=payload.capacity,
        gender_policy=payload.gender_policy,
    ).insert()
    return {"room_code": payload.room_code.upper()}


async def create_bed(scope: AccessScope, payload: HostelBedCreate) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    bed_id = payload.bed_id.strip()
    if await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, bed_id)):
        raise AppError(code="CONFLICT", message="Bed id exists", status_code=409)
    await HostelBed(
        tenant_id=tenant_id,
        bed_id=bed_id,
        building_code=payload.building_code.upper(),
        block_code=payload.block_code.upper(),
        room_code=payload.room_code.upper(),
        bed_label=payload.bed_label,
    ).insert()
    return {"bed_id": bed_id}


async def review_application(scope: AccessScope, payload: HostelApplicationReview) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    app = await HostelApplication.find_one(Eq(HostelApplication.tenant_id, tenant_id), Eq(HostelApplication.application_id, payload.application_id))
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    app.status = payload.decision
    app.updated_at = utcnow()
    await app.save()
    if payload.decision == HostelApplicationStatus.WAITLISTED:
        pos = await HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, tenant_id)).count() + 1
        await HostelWaitingListEntry(
            tenant_id=tenant_id,
            student_user_id=app.student_user_id,
            application_id=app.application_id,
            position=pos,
        ).insert()
    return {"application_id": app.application_id, "status": app.status.value}


async def approve_allocation(scope: AccessScope, payload: AllocationApprove) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_ALLOCATE)
    tenant_id = require_college_tenant_scope(scope)
    app = await HostelApplication.find_one(Eq(HostelApplication.tenant_id, tenant_id), Eq(HostelApplication.application_id, payload.application_id))
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    if app.status not in (HostelApplicationStatus.APPROVED, HostelApplicationStatus.SUBMITTED):
        raise AppError(code="VALIDATION_ERROR", message="Application not eligible for allocation", status_code=422)
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, payload.bed_id))
    if bed is None:
        raise AppError(code="NOT_FOUND", message="Bed not found", status_code=404)
    if bed.status != HostelBedStatus.AVAILABLE:
        raise AppError(code="CONFLICT", message="Bed is not available", status_code=409)
    existing_student = await HostelAllocation.find_one(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.student_user_id, app.student_user_id),
        Eq(HostelAllocation.status, HostelAllocationStatus.ACTIVE),
    )
    if existing_student:
        raise AppError(code="CONFLICT", message="Student already has an active allocation", status_code=409)
    bed.status = HostelBedStatus.ALLOCATED
    bed.updated_at = utcnow()
    await bed.save()
    allocation_id = f"hall_{uuid4().hex[:12]}"
    allocation = HostelAllocation(
        tenant_id=tenant_id,
        allocation_id=allocation_id,
        student_user_id=app.student_user_id,
        bed_id=bed.bed_id,
        building_code=bed.building_code,
        block_code=bed.block_code,
        room_code=bed.room_code,
        bed_label=bed.bed_label,
        status=HostelAllocationStatus.PENDING,
        actor_id=scope.user_id,
    )
    try:
        await allocation.insert()
    except DuplicateKeyError:
        bed.status = HostelBedStatus.AVAILABLE
        bed.updated_at = utcnow()
        await bed.save()
        raise AppError(code="CONFLICT", message="Bed or student already allocated", status_code=409)
    app.status = HostelApplicationStatus.APPROVED
    app.updated_at = utcnow()
    await app.save()
    return {"allocation_id": allocation_id}


async def check_in(scope: AccessScope, payload: CheckInOut) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    alloc = await HostelAllocation.find_one(Eq(HostelAllocation.tenant_id, tenant_id), Eq(HostelAllocation.allocation_id, payload.allocation_id))
    if alloc is None:
        raise AppError(code="NOT_FOUND", message="Allocation not found", status_code=404)
    if alloc.status != HostelAllocationStatus.PENDING:
        raise AppError(code="CONFLICT", message="Allocation is not pending check-in", status_code=409)
    alloc.status = HostelAllocationStatus.ACTIVE
    alloc.checked_in_at = utcnow()
    alloc.updated_at = utcnow()
    await alloc.save()
    auth_id = f"hra_{uuid4().hex[:12]}"
    building = await HostelBuilding.find_one(Eq(HostelBuilding.tenant_id, tenant_id), Eq(HostelBuilding.building_code, alloc.building_code))
    hostel_name = building.name if building else alloc.building_code
    authoritative = HostelRoomAllocation(
        tenant_id=tenant_id,
        student_user_id=alloc.student_user_id,
        allocation_id=auth_id,
        hostel_name=hostel_name,
        block=alloc.block_code,
        room_number=alloc.room_code,
        bed_label=alloc.bed_label,
        published=True,
        effective_from=utcnow().date(),
    )
    await authoritative.insert()
    alloc.authoritative_allocation_id = auth_id
    await alloc.save()
    await HostelResidentHistory(
        tenant_id=tenant_id,
        student_user_id=alloc.student_user_id,
        allocation_id=alloc.allocation_id,
        event_type="check_in",
        actor_id=scope.user_id,
    ).insert()
    return {"allocation_id": alloc.allocation_id, "status": alloc.status.value}


async def check_out(scope: AccessScope, payload: CheckInOut) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    alloc = await HostelAllocation.find_one(Eq(HostelAllocation.tenant_id, tenant_id), Eq(HostelAllocation.allocation_id, payload.allocation_id))
    if alloc is None or alloc.status != HostelAllocationStatus.ACTIVE:
        raise AppError(code="NOT_FOUND", message="Active allocation not found", status_code=404)
    alloc.status = HostelAllocationStatus.CHECKED_OUT
    alloc.checked_out_at = utcnow()
    alloc.updated_at = utcnow()
    await alloc.save()
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, alloc.bed_id))
    if bed:
        bed.status = HostelBedStatus.AVAILABLE
        bed.updated_at = utcnow()
        await bed.save()
    if alloc.authoritative_allocation_id:
        auth = await HostelRoomAllocation.find_one(
            Eq(HostelRoomAllocation.tenant_id, tenant_id),
            Eq(HostelRoomAllocation.allocation_id, alloc.authoritative_allocation_id),
        )
        if auth:
            auth.published = False
            await auth.save()
    await HostelResidentHistory(
        tenant_id=tenant_id,
        student_user_id=alloc.student_user_id,
        allocation_id=alloc.allocation_id,
        event_type="check_out",
        actor_id=scope.user_id,
    ).insert()
    return {"allocation_id": alloc.allocation_id}


async def log_visitor(scope: AccessScope, payload: VisitorLogCreate) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    visit_id = f"vis_{uuid4().hex[:10]}"
    await HostelVisitorLog(
        tenant_id=tenant_id,
        visit_id=visit_id,
        resident_user_id=to_object_id(payload.resident_user_id, "resident_user_id"),
        visitor_name=payload.visitor_name,
        purpose=payload.purpose,
        actor_id=scope.user_id,
    ).insert()
    return {"visit_id": visit_id}


async def decide_outpass(scope: AccessScope, payload: OutpassDecision) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    req = await HostelOutpassRequest.find_one(Eq(HostelOutpassRequest.tenant_id, tenant_id), Eq(HostelOutpassRequest.request_id, payload.request_id))
    if req is None:
        raise AppError(code="NOT_FOUND", message="Outpass not found", status_code=404)
    req.status = "approved" if payload.approved else "rejected"
    req.approver_id = scope.user_id
    await req.save()
    return {"request_id": req.request_id, "status": req.status}


async def create_maintenance(scope: AccessScope, payload: MaintenanceCreate) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    request_id = f"mnt_{uuid4().hex[:10]}"
    await HostelMaintenanceRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        building_code=payload.building_code.upper(),
        room_code=payload.room_code.upper(),
        description=payload.description,
        actor_id=scope.user_id,
    ).insert()
    return {"request_id": request_id}


async def create_incident(scope: AccessScope, payload: IncidentCreate) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    if await HostelIncident.find_one(Eq(HostelIncident.tenant_id, tenant_id), Eq(HostelIncident.incident_id, payload.incident_id)):
        raise AppError(code="CONFLICT", message="Incident id exists", status_code=409)
    await HostelIncident(
        tenant_id=tenant_id,
        incident_id=payload.incident_id,
        building_code=payload.building_code.upper() if payload.building_code else None,
        description=payload.description,
        severity=payload.severity,
        actor_id=scope.user_id,
    ).insert()
    return {"incident_id": payload.incident_id}


async def upsert_rule(scope: AccessScope, payload: HostelRuleUpsert) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await HostelRule.find_one(Eq(HostelRule.tenant_id, tenant_id), Eq(HostelRule.rule_code, payload.rule_code))
    if doc:
        doc.title = payload.title
        doc.body = payload.body
        doc.version += 1
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await HostelRule(tenant_id=tenant_id, rule_code=payload.rule_code, title=payload.title, body=payload.body).insert()
    return {"rule_code": payload.rule_code}


async def upsert_mess_plan(scope: AccessScope, payload: MessPlanUpsert) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await HostelMessPlan.find_one(Eq(HostelMessPlan.tenant_id, tenant_id), Eq(HostelMessPlan.plan_code, payload.plan_code))
    if doc:
        doc.title = payload.title
        doc.monthly_amount = payload.monthly_amount
        doc.finance_reference = payload.finance_reference
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await HostelMessPlan(
            tenant_id=tenant_id,
            plan_code=payload.plan_code,
            title=payload.title,
            monthly_amount=payload.monthly_amount,
            finance_reference=payload.finance_reference,
        ).insert()
    return {"plan_code": payload.plan_code}


async def occupancy_report(scope: AccessScope, *, building_code: str | None = None) -> dict:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    bed_filter: dict = {"tenant_id": tenant_id}
    if building_code:
        bed_filter["building_code"] = building_code.upper()
    total = await HostelBed.find(bed_filter).count()
    available = await HostelBed.find({**bed_filter, "status": HostelBedStatus.AVAILABLE.value}).count()
    allocated = await HostelBed.find({**bed_filter, "status": HostelBedStatus.ALLOCATED.value}).count()
    active_residents = await HostelAllocation.find(
        Eq(HostelAllocation.tenant_id, tenant_id),
        Eq(HostelAllocation.status, HostelAllocationStatus.ACTIVE),
    ).count()
    waiting = await HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, tenant_id)).count()
    return {
        "building_code": building_code,
        "total_beds": total,
        "available_beds": available,
        "allocated_beds": allocated,
        "active_residents": active_residents,
        "waiting_list": waiting,
    }


async def list_waiting(scope: AccessScope, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, tenant_id)).sort("position")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[{"application_id": r.application_id, "position": r.position, "student_user_id": str(r.student_user_id)} for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )