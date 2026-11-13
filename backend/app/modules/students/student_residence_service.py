"""Student hostel and transport portal."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.hostel.hostel_enums import HostelRequestType
from app.modules.hostel.hostel_models import HostelServiceRequest
from app.modules.students.integrations import residence_reader
from app.modules.students.policy import require_student_scope
from app.modules.students.student_portal_enums import StudentServiceCategory, StudentServiceRequestStatus
from app.modules.students.student_portal_models import (
    StudentHostelRequestReference,
    StudentServiceRequest,
    StudentServiceRequestHistory,
    StudentTransportRequestReference,
)
from app.modules.students.student_portal_schemas import (
    HostelAllocationRead,
    HostelApplicationRead,
    HostelRequestInput,
    TransportAllocationRead,
    TransportRequestInput,
    TransportRouteRead,
    TransportStopRead,
)
from app.modules.transport.transport_enums import TransportRequestType
from app.modules.transport.transport_models import TransportServiceRequest


_HOSTEL_TYPES = frozenset(t.value for t in HostelRequestType)
_TRANSPORT_TYPES = frozenset(t.value for t in TransportRequestType)


async def hostel_application_status(scope: AccessScope, user: User) -> HostelApplicationRead | None:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    row = await residence_reader.hostel_application(tenant_id, user.id)
    if row is None:
        return None
    return HostelApplicationRead(application_id=row.application_id, status=row.status.value, submitted_at=row.submitted_at)


async def hostel_room_allocation(scope: AccessScope, user: User) -> HostelAllocationRead | None:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    row = await residence_reader.hostel_allocation(tenant_id, user.id)
    if row is None:
        return None
    return HostelAllocationRead(
        hostel_name=row.hostel_name,
        block=row.block,
        room_number=row.room_number,
        bed_label=row.bed_label,
        fee_amount=row.fee_amount,
    )


async def hostel_fee_details(scope: AccessScope, user: User) -> dict:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    alloc = await residence_reader.hostel_allocation(tenant_id, user.id)
    if alloc is None:
        return {"allocated": False, "fee_amount": 0}
    return {
        "allocated": True,
        "hostel_name": alloc.hostel_name,
        "fee_amount": alloc.fee_amount,
        "effective_from": alloc.effective_from,
    }


async def hostel_notices(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await residence_reader.hostel_notices(tenant_id)
    return [{"notice_id": r.notice_id, "title": r.title, "body": r.body[:500], "created_at": r.created_at} for r in rows]


async def submit_hostel_request(scope: AccessScope, user: User, payload: HostelRequestInput) -> dict:
    authorize(scope, Permission.STUDENT_RESIDENCE_MANAGE)
    tenant_id = require_student_scope(scope)
    if payload.request_type not in _HOSTEL_TYPES:
        raise AppError(code="VALIDATION_ERROR", message="Invalid hostel request type", status_code=422)
    portal_id = f"svr_{uuid4().hex}"
    official_id = f"hst_{uuid4().hex}"
    req_type = HostelRequestType(payload.request_type)
    await HostelServiceRequest(
        tenant_id=tenant_id,
        student_user_id=user.id,
        request_id=official_id,
        request_type=req_type,
        description=payload.description.strip(),
    ).insert()
    await StudentServiceRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=portal_id,
        category=StudentServiceCategory.HOSTEL,
        title=f"Hostel {req_type.value}",
        description=payload.description.strip(),
        status=StudentServiceRequestStatus.SUBMITTED,
        official_ref=official_id,
    ).insert()
    await StudentHostelRequestReference(
        tenant_id=tenant_id,
        user_id=user.id,
        portal_request_id=portal_id,
        official_request_id=official_id,
    ).insert()
    await StudentServiceRequestHistory(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=portal_id,
        from_status="",
        to_status=StudentServiceRequestStatus.SUBMITTED.value,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.hostel.request_submitted",
        resource_type="hostel_service_request",
        resource_id=official_id,
        tenant_id=tenant_id,
    )
    return {"request_id": portal_id, "official_request_id": official_id, "status": "submitted"}


async def hostel_request_status(scope: AccessScope, user: User, request_id: str) -> dict:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    portal = await StudentServiceRequest.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "request_id": request_id}
    )
    if portal is None:
        raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
    ref = await StudentHostelRequestReference.find_one({"tenant_id": tenant_id, "portal_request_id": request_id})
    official_status = portal.status.value
    if ref:
        official = await HostelServiceRequest.find_one({"tenant_id": tenant_id, "request_id": ref.official_request_id})
        if official:
            official_status = official.status.value
    return {"request_id": request_id, "status": official_status, "category": portal.category.value}


async def transport_routes(scope: AccessScope, user: User) -> list[TransportRouteRead]:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await residence_reader.transport_routes(tenant_id)
    return [TransportRouteRead(route_id=r.route_id, name=r.name, fee_amount=r.fee_amount) for r in rows]


async def transport_allocation(scope: AccessScope, user: User) -> TransportAllocationRead | None:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    row = await residence_reader.transport_allocation(tenant_id, user.id)
    if row is None:
        return None
    return TransportAllocationRead(
        route_id=row.route_id,
        route_name=row.route_name,
        pickup_stop=row.pickup_stop,
        drop_stop=row.drop_stop,
        fee_amount=row.fee_amount,
    )


async def transport_route_stops(scope: AccessScope, user: User, route_id: str) -> list[TransportStopRead]:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await residence_reader.transport_stops(tenant_id, route_id)
    return [
        TransportStopRead(
            stop_id=r.stop_id,
            name=r.name,
            pickup_time=r.pickup_time,
            drop_time=r.drop_time,
            sequence=r.sequence,
        )
        for r in rows
    ]


async def transport_schedules(scope: AccessScope, user: User, route_id: str | None = None) -> list[dict]:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    alloc = await residence_reader.transport_allocation(tenant_id, user.id)
    rid = route_id or (alloc.route_id if alloc else None)
    rows = await residence_reader.transport_schedules(tenant_id, rid)
    return [
        {
            "schedule_id": r.schedule_id,
            "route_id": r.route_id,
            "day_of_week": r.day_of_week,
            "departure_time": r.departure_time,
        }
        for r in rows
    ]


async def transport_fee_details(scope: AccessScope, user: User) -> dict:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    alloc = await residence_reader.transport_allocation(tenant_id, user.id)
    if alloc is None:
        return {"allocated": False, "fee_amount": 0}
    return {"allocated": True, "route_id": alloc.route_id, "fee_amount": alloc.fee_amount}


async def submit_transport_request(scope: AccessScope, user: User, payload: TransportRequestInput) -> dict:
    authorize(scope, Permission.STUDENT_RESIDENCE_MANAGE)
    tenant_id = require_student_scope(scope)
    if payload.request_type not in _TRANSPORT_TYPES:
        raise AppError(code="VALIDATION_ERROR", message="Invalid transport request type", status_code=422)
    portal_id = f"svr_{uuid4().hex}"
    official_id = f"trn_{uuid4().hex}"
    req_type = TransportRequestType(payload.request_type)
    await TransportServiceRequest(
        tenant_id=tenant_id,
        student_user_id=user.id,
        request_id=official_id,
        request_type=req_type,
        description=payload.description.strip(),
    ).insert()
    await StudentServiceRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=portal_id,
        category=StudentServiceCategory.TRANSPORT,
        title=f"Transport {req_type.value}",
        description=payload.description.strip(),
        status=StudentServiceRequestStatus.SUBMITTED,
        official_ref=official_id,
    ).insert()
    await StudentTransportRequestReference(
        tenant_id=tenant_id,
        user_id=user.id,
        portal_request_id=portal_id,
        official_request_id=official_id,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.transport.request_submitted",
        resource_type="transport_service_request",
        resource_id=official_id,
        tenant_id=tenant_id,
    )
    return {"request_id": portal_id, "status": "submitted"}


async def transport_notifications_feed(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.STUDENT_RESIDENCE_READ)
    tenant_id = require_student_scope(scope)
    alloc = await residence_reader.transport_allocation(tenant_id, user.id)
    route_id = alloc.route_id if alloc else None
    rows = await residence_reader.transport_notifications(tenant_id, route_id)
    return [{"notification_id": r.notification_id, "title": r.title, "body": r.body, "created_at": r.created_at} for r in rows]
