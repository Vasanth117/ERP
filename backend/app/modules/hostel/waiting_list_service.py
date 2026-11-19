"""Hostel waiting list and allocation offers."""

from datetime import timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelWaitingListEntry
from app.modules.hostel.allocation_schemas import AllocationCreate
from app.modules.hostel.allocation_service import create_allocation_record
from app.modules.hostel.application_models import HostelAllocationOffer, HostelOfferStatus, HostelWaitingList
from app.modules.hostel.application_schemas import AllocationOfferCreate, OfferResponse, WaitingListAdd, WaitingListPriorityUpdate
from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.hostel_models import HostelApplication
from app.modules.hostel.hostel_notify import notify_hostel_student
from app.modules.hostel.infrastructure_validation import norm_code
from app.modules.hostel.policy import authorize_hostel_application_manage, authorize_hostel_application_read, require_hostel_tenant_scope
from app.modules.students.policy import require_student_scope
from app.authorization.policy import authorize
from app.authorization.permissions import Permission


async def ensure_default_waiting_list(
    tenant_id: PydanticObjectId,
    academic_year_label: str,
    hostel_code: str | None,
) -> str:
    list_id = f"wl_{academic_year_label}_{norm_code(hostel_code) if hostel_code else 'ANY'}"
    existing = await HostelWaitingList.find_one(Eq(HostelWaitingList.tenant_id, tenant_id), Eq(HostelWaitingList.list_id, list_id))
    if existing:
        return list_id
    await HostelWaitingList(
        tenant_id=tenant_id,
        list_id=list_id,
        title=f"Waiting list {academic_year_label}",
        hostel_code=norm_code(hostel_code) if hostel_code else None,
        academic_year_label=academic_year_label,
    ).insert()
    return list_id


async def add_application_to_waiting_list(
    tenant_id: PydanticObjectId,
    *,
    application: HostelApplication,
    list_id: str,
    hostel_code: str | None,
    room_type: str | None,
    priority_score: int = 0,
    priority_override_reason: str | None = None,
) -> HostelWaitingListEntry:
    existing = await HostelWaitingListEntry.find_one(
        Eq(HostelWaitingListEntry.tenant_id, tenant_id),
        Eq(HostelWaitingListEntry.application_id, application.application_id),
    )
    if existing:
        return existing
    pos = await HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, tenant_id), Eq(HostelWaitingListEntry.list_id, list_id)).count() + 1
    entry = HostelWaitingListEntry(
        tenant_id=tenant_id,
        list_id=list_id,
        student_user_id=application.student_user_id,
        application_id=application.application_id,
        hostel_code=norm_code(hostel_code) if hostel_code else None,
        room_type=room_type,
        position=pos,
        priority_score=priority_score,
        priority_override_reason=priority_override_reason,
    )
    await entry.insert()
    application.waitlist_list_id = list_id
    application.updated_at = utcnow()
    await application.save()
    return entry


async def add_to_waiting_list(scope: AccessScope, payload: WaitingListAdd) -> dict:
    authorize_hostel_application_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    app = await HostelApplication.find_one(
        Eq(HostelApplication.tenant_id, tenant_id),
        Eq(HostelApplication.application_id, payload.application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    list_id = payload.list_id or await ensure_default_waiting_list(tenant_id, app.academic_year_label, payload.hostel_code or app.preferred_hostel_code)
    entry = await add_application_to_waiting_list(
        tenant_id,
        application=app,
        list_id=list_id,
        hostel_code=payload.hostel_code or app.preferred_hostel_code,
        room_type=payload.room_type or app.preferred_room_type,
        priority_score=payload.priority_score,
        priority_override_reason=payload.priority_override_reason,
    )
    app.status = HostelApplicationStatus.WAITLISTED
    app.updated_at = utcnow()
    await app.save()
    return {"application_id": app.application_id, "list_id": list_id, "position": entry.position}


async def update_waiting_priority(scope: AccessScope, payload: WaitingListPriorityUpdate) -> dict:
    authorize_hostel_application_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    entry = await HostelWaitingListEntry.find_one(
        Eq(HostelWaitingListEntry.tenant_id, tenant_id),
        Eq(HostelWaitingListEntry.application_id, payload.application_id),
    )
    if entry is None:
        raise AppError(code="NOT_FOUND", message="Waiting list entry not found", status_code=404)
    entry.position = payload.position
    if payload.priority_score is not None:
        entry.priority_score = payload.priority_score
    if payload.priority_override_reason:
        entry.priority_override_reason = payload.priority_override_reason
    entry.updated_at = utcnow()
    await entry.save()
    return {"application_id": entry.application_id, "position": entry.position}


async def list_waiting_entries(scope: AccessScope, pagination: Pagination, *, list_id: str | None = None) -> Page[dict]:
    authorize_hostel_application_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    query = HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, tenant_id))
    if list_id:
        query = query.find(Eq(HostelWaitingListEntry.list_id, list_id))
    query = query.sort("position")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        {
            "application_id": r.application_id,
            "student_user_id": str(r.student_user_id),
            "list_id": r.list_id,
            "position": r.position,
            "priority_score": r.priority_score,
            "status": r.status,
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def issue_allocation_offer(scope: AccessScope, payload: AllocationOfferCreate) -> dict:
    authorize_hostel_application_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    app = await HostelApplication.find_one(
        Eq(HostelApplication.tenant_id, tenant_id),
        Eq(HostelApplication.application_id, payload.application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    if app.status not in (HostelApplicationStatus.APPROVED, HostelApplicationStatus.WAITLISTED):
        raise AppError(code="VALIDATION_ERROR", message="Application not eligible for offer", status_code=422)
    offer_id = f"hoff_{uuid4().hex[:10]}"
    deadline = utcnow() + timedelta(hours=payload.response_hours)
    from app.modules.college_admin.hostel_admin_models import HostelBed

    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant_id), Eq(HostelBed.bed_id, payload.bed_id))
    if bed is None:
        raise AppError(code="NOT_FOUND", message="Bed not found", status_code=404)
    hostel_code = bed.hostel_code or app.preferred_hostel_code
    if not hostel_code:
        raise AppError(code="VALIDATION_ERROR", message="Hostel code could not be resolved", status_code=422)
    offer = HostelAllocationOffer(
        tenant_id=tenant_id,
        offer_id=offer_id,
        application_id=app.application_id,
        student_user_id=app.student_user_id,
        hostel_code=norm_code(hostel_code),
        bed_id=payload.bed_id,
        building_code=bed.building_code,
        block_code=bed.block_code,
        room_code=bed.room_code,
        response_deadline=deadline,
        actor_id=scope.user_id,
    )
    await offer.insert()
    app.active_offer_id = offer_id
    app.status = HostelApplicationStatus.ALLOCATION_OFFERED
    app.updated_at = utcnow()
    await app.save()
    await notify_hostel_student(
        tenant_id,
        student_user_id=app.student_user_id,
        event_type="allocation_offer",
        title="Hostel accommodation offer",
        body=f"You have a hostel offer {offer_id}. Respond before {deadline.isoformat()}.",
        aggregate_id=offer_id,
    )
    return {"offer_id": offer_id, "response_deadline": deadline.isoformat()}


async def respond_to_offer(scope: AccessScope, user: User, payload: OfferResponse) -> dict:
    authorize(scope, Permission.STUDENT_RESIDENCE_MANAGE)
    tenant_id = require_student_scope(scope)
    offer = await HostelAllocationOffer.find_one(Eq(HostelAllocationOffer.tenant_id, tenant_id), Eq(HostelAllocationOffer.offer_id, payload.offer_id))
    if offer is None or offer.student_user_id != user.id:
        raise AppError(code="NOT_FOUND", message="Offer not found", status_code=404)
    if offer.status != HostelOfferStatus.OFFERED:
        raise AppError(code="CONFLICT", message="Offer is not open", status_code=409)
    if utcnow() > offer.response_deadline:
        offer.status = HostelOfferStatus.EXPIRED
        await offer.save()
        raise AppError(code="CONFLICT", message="Offer expired", status_code=409)
    app = await HostelApplication.find_one(Eq(HostelApplication.tenant_id, tenant_id), Eq(HostelApplication.application_id, offer.application_id))
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application missing", status_code=404)
    if not payload.accept:
        offer.status = HostelOfferStatus.DECLINED
        offer.responded_at = utcnow()
        await offer.save()
        app.status = HostelApplicationStatus.DECLINED
        app.active_offer_id = None
        app.updated_at = utcnow()
        await app.save()
        return {"offer_id": offer.offer_id, "status": offer.status.value}
    if not offer.bed_id:
        raise AppError(code="VALIDATION_ERROR", message="Offer has no bed", status_code=422)
    offer.status = HostelOfferStatus.ACCEPTED
    offer.responded_at = utcnow()
    await offer.save()
    app.status = HostelApplicationStatus.ACCEPTED
    app.updated_at = utcnow()
    await app.save()
    allocation = await create_allocation_record(
        tenant_id,
        user.id,
        AllocationCreate(
            student_user_id=str(user.id),
            application_id=app.application_id,
            hostel_code=offer.hostel_code,
            bed_id=offer.bed_id,
        ),
    )
    offer.allocation_id = allocation.allocation_id
    await offer.save()
    return {"offer_id": offer.offer_id, "status": offer.status.value, "allocation_id": allocation.allocation_id}


async def expire_stale_offers(tenant_id: PydanticObjectId) -> int:
    now = utcnow()
    offers = await HostelAllocationOffer.find(
        {"tenant_id": tenant_id, "status": HostelOfferStatus.OFFERED.value, "response_deadline": {"$lt": now}}
    ).to_list()
    count = 0
    for offer in offers:
        offer.status = HostelOfferStatus.EXPIRED
        await offer.save()
        app = await HostelApplication.find_one(Eq(HostelApplication.tenant_id, tenant_id), Eq(HostelApplication.application_id, offer.application_id))
        if app and app.status == HostelApplicationStatus.ALLOCATION_OFFERED:
            app.status = HostelApplicationStatus.EXPIRED
            app.active_offer_id = None
            app.updated_at = utcnow()
            await app.save()
        count += 1
    return count