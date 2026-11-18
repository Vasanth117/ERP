"""Book reservations and hold queue."""

from datetime import timedelta
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from pymongo import ReturnDocument

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.library_admin_models import LibraryBranch
from app.modules.college_admin.library_admin_models import LibraryMembershipReference
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.library_enums import LibraryCopyStatus, LibraryReservationStatus
from app.modules.library.library_models import LibraryCatalogItem, LibraryCopy, LibraryReservation
from app.modules.library.member_service import assert_member_can_borrow
from app.modules.library.reservation_access import authorize_reservation_read, require_reservation_manage
from app.modules.library.reservation_models import (
    LibraryReservationHistory,
    LibraryReservationPolicy,
)
from app.modules.library.reservation_schemas import (
    ReservationAllocateRequest,
    ReservationCancelRequest,
    ReservationCreateRequest,
    ReservationHistoryEntry,
    ReservationPolicyUpsert,
    ReservationRead,
)
from app.modules.library.policy import require_library_tenant_scope


def _norm_branch(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().upper()


def _reservation_id(custom: str | None) -> str:
    if custom and custom.strip():
        return custom.strip()
    return f"rsv_{uuid4().hex[:12]}"


async def _policy(tenant_id: PydanticObjectId, branch_code: str | None) -> LibraryReservationPolicy:
    branch = _norm_branch(branch_code)
    doc = await LibraryReservationPolicy.find_one(
        Eq(LibraryReservationPolicy.tenant_id, tenant_id),
        Eq(LibraryReservationPolicy.branch_code, branch),
    )
    if doc:
        return doc
    doc = await LibraryReservationPolicy.find_one(
        Eq(LibraryReservationPolicy.tenant_id, tenant_id),
        Eq(LibraryReservationPolicy.branch_code, None),
    )
    if doc:
        return doc
    return LibraryReservationPolicy(
        tenant_id=tenant_id,
        branch_code=branch,
    )


async def _history(
    tenant_id: PydanticObjectId,
    *,
    reservation_id: str,
    action: str,
    actor_id: PydanticObjectId | None,
    changes: dict[str, Any],
) -> None:
    await LibraryReservationHistory(
        tenant_id=tenant_id,
        reservation_id=reservation_id,
        action=action,
        actor_id=actor_id,
        changes=changes,
    ).insert()


async def _available_count(tenant_id: PydanticObjectId, book_id: str, branch_code: str | None) -> int:
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "book_id": book_id,
        "status": LibraryCopyStatus.AVAILABLE.value,
    }
    branch = _norm_branch(branch_code)
    if branch:
        filters["branch_code"] = branch
    return await LibraryCopy.find(filters).count()


def _to_read(doc: LibraryReservation) -> ReservationRead:
    return ReservationRead(
        reservation_id=doc.reservation_id,
        member_user_id=str(doc.student_user_id),
        membership_number=doc.membership_number,
        book_id=doc.book_id,
        title=doc.title,
        branch_code=doc.branch_code,
        copy_id=doc.copy_id,
        status=doc.status,
        queue_position=doc.queue_position,
        priority=doc.priority,
        ready_at=doc.ready_at,
        expires_at=doc.expires_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def _reindex_queue(tenant_id: PydanticObjectId, book_id: str, branch_code: str | None) -> None:
    branch = _norm_branch(branch_code)
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "book_id": book_id,
        "status": LibraryReservationStatus.QUEUED.value,
    }
    if branch:
        filters["branch_code"] = branch
    else:
        filters["branch_code"] = None
    rows = await LibraryReservation.find(filters).sort("+priority", "+created_at").to_list()
    for idx, row in enumerate(rows, start=1):
        if row.queue_position != idx:
            row.queue_position = idx
            row.updated_at = utcnow()
            await row.save()


async def expire_ready_holds(tenant_id: PydanticObjectId) -> int:
    now = utcnow()
    expired = await LibraryReservation.find(
        {
            "tenant_id": tenant_id,
            "status": LibraryReservationStatus.READY.value,
            "expires_at": {"$lt": now},
        }
    ).to_list()
    count = 0
    for res in expired:
        res.status = LibraryReservationStatus.EXPIRED
        res.updated_at = now
        await res.save()
        if res.copy_id:
            coll = LibraryCopy.get_motor_collection()
            await coll.update_one(
                {
                    "tenant_id": tenant_id,
                    "copy_id": res.copy_id,
                    "reserved_reservation_id": res.reservation_id,
                },
                {
                    "$set": {
                        "status": LibraryCopyStatus.AVAILABLE.value,
                        "reserved_reservation_id": None,
                        "updated_at": now,
                    },
                    "$inc": {"version": 1},
                },
            )
        await _history(tenant_id, reservation_id=res.reservation_id, action="expire", actor_id=None, changes={})
        count += 1
        await offer_next_for_book(tenant_id, res.book_id, res.branch_code, actor_id=None)
    return count


async def _notify_ready(tenant_id: PydanticObjectId, res: LibraryReservation) -> None:
    from app.modules.library.notification_triggers import on_reservation_ready

    await on_reservation_ready(tenant_id, res)


async def _queue_head(tenant_id: PydanticObjectId, book_id: str, branch_code: str | None) -> LibraryReservation | None:
    branch = _norm_branch(branch_code)
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "book_id": book_id,
        "status": LibraryReservationStatus.QUEUED.value,
    }
    if branch:
        filters["branch_code"] = branch
    rows = await LibraryReservation.find(filters).sort("-priority", "+created_at").limit(1).to_list()
    return rows[0] if rows else None


async def _claim_copy_for_reservation(
    tenant_id: PydanticObjectId,
    *,
    book_id: str,
    branch_code: str | None,
    reservation_id: str,
    copy_id: str | None,
) -> str | None:
    coll = LibraryCopy.get_motor_collection()
    now = utcnow()
    base_filter: dict[str, Any] = {
        "tenant_id": tenant_id,
        "book_id": book_id,
        "status": LibraryCopyStatus.AVAILABLE.value,
    }
    branch = _norm_branch(branch_code)
    if branch:
        base_filter["branch_code"] = branch
    if copy_id:
        base_filter["copy_id"] = copy_id.strip()
    claimed = await coll.find_one_and_update(
        base_filter,
        {
            "$set": {
                "status": LibraryCopyStatus.RESERVED.value,
                "reserved_reservation_id": reservation_id,
                "updated_at": now,
            },
            "$inc": {"version": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if claimed is None:
        return None
    return claimed["copy_id"]


async def allocate_reservation(
    tenant_id: PydanticObjectId,
    reservation_id: str,
    *,
    actor_id: PydanticObjectId | None,
    copy_id: str | None = None,
) -> LibraryReservation | None:
    await expire_ready_holds(tenant_id)
    res_coll = LibraryReservation.get_motor_collection()
    now = utcnow()
    head = await LibraryReservation.find_one(
        Eq(LibraryReservation.tenant_id, tenant_id),
        Eq(LibraryReservation.reservation_id, reservation_id),
    )
    if head is None or head.status != LibraryReservationStatus.QUEUED:
        return None
    policy = await _policy(tenant_id, head.branch_code)
    claimed_copy = await _claim_copy_for_reservation(
        tenant_id,
        book_id=head.book_id,
        branch_code=head.branch_code,
        reservation_id=reservation_id,
        copy_id=copy_id,
    )
    if not claimed_copy:
        return None
    expires_at = now + timedelta(hours=policy.hold_hours)
    updated = await res_coll.find_one_and_update(
        {
            "tenant_id": tenant_id,
            "reservation_id": reservation_id,
            "status": LibraryReservationStatus.QUEUED.value,
        },
        {
            "$set": {
                "status": LibraryReservationStatus.READY.value,
                "copy_id": claimed_copy,
                "ready_at": now,
                "expires_at": expires_at,
                "updated_at": now,
                "updated_by": actor_id,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        coll = LibraryCopy.get_motor_collection()
        await coll.update_one(
            {"tenant_id": tenant_id, "copy_id": claimed_copy},
            {"$set": {"status": LibraryCopyStatus.AVAILABLE.value, "reserved_reservation_id": None, "updated_at": now}, "$inc": {"version": 1}},
        )
        return None
    res = await LibraryReservation.find_one(Eq(LibraryReservation.tenant_id, tenant_id), Eq(LibraryReservation.reservation_id, reservation_id))
    if res is None:
        return None
    await _history(
        tenant_id,
        reservation_id=reservation_id,
        action="allocate",
        actor_id=actor_id,
        changes={"copy_id": claimed_copy, "expires_at": expires_at.isoformat()},
    )
    await _notify_ready(tenant_id, res)
    await _reindex_queue(tenant_id, res.book_id, res.branch_code)
    return res


async def offer_next_for_book(
    tenant_id: PydanticObjectId,
    book_id: str,
    branch_code: str | None,
    *,
    actor_id: PydanticObjectId | None,
) -> LibraryReservation | None:
    head = await _queue_head(tenant_id, book_id, branch_code)
    if head is None:
        return None
    return await allocate_reservation(tenant_id, head.reservation_id, actor_id=actor_id)


async def create_reservation_core(
    tenant_id: PydanticObjectId,
    *,
    member_user_id: PydanticObjectId,
    book_id: str,
    branch_code: str | None,
    reservation_id: str,
    priority: int,
    actor_id: PydanticObjectId | None,
    skip_unavailable_check: bool = False,
    require_membership: bool = True,
) -> LibraryReservation:
    if await LibraryReservation.find_one(
        Eq(LibraryReservation.tenant_id, tenant_id),
        Eq(LibraryReservation.reservation_id, reservation_id),
    ):
        raise AppError(code="CONFLICT", message="Reservation id already used", status_code=409)
    item = await LibraryCatalogItem.find_one(Eq(LibraryCatalogItem.tenant_id, tenant_id), Eq(LibraryCatalogItem.book_id, book_id))
    if item is None or not item.published:
        raise AppError(code="NOT_FOUND", message="Book not found", status_code=404)
    branch = _norm_branch(branch_code)
    if branch:
        exists = await LibraryBranch.find_one(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.branch_code, branch))
        if exists is None:
            raise AppError(code="VALIDATION_ERROR", message="Unknown branch", status_code=422)
    membership = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.member_user_id, member_user_id),
    )
    if require_membership and membership is None:
        raise AppError(code="FORBIDDEN", message="Library membership required", status_code=403)
    policy = await _policy(tenant_id, branch)
    active = await LibraryReservation.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": member_user_id,
            "status": {"$in": [LibraryReservationStatus.QUEUED.value, LibraryReservationStatus.READY.value]},
        }
    ).count()
    if active >= policy.max_active_per_member:
        raise AppError(code="CONFLICT", message="Maximum active reservations reached", status_code=409)
    dup = await LibraryReservation.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": member_user_id,
            "book_id": book_id,
            "branch_code": branch,
            "status": {"$in": [LibraryReservationStatus.QUEUED.value, LibraryReservationStatus.READY.value]},
        }
    )
    if dup:
        raise AppError(code="CONFLICT", message="Already reserved this title", status_code=409)
    if not skip_unavailable_check and policy.reserve_only_when_unavailable:
        if await _available_count(tenant_id, book_id, branch) > 0:
            raise AppError(code="CONFLICT", message="Copies are available; borrow directly", status_code=409)
    queue_len = await LibraryReservation.find(
        {
            "tenant_id": tenant_id,
            "book_id": book_id,
            "branch_code": branch,
            "status": LibraryReservationStatus.QUEUED.value,
        }
    ).count()
    doc = LibraryReservation(
        tenant_id=tenant_id,
        reservation_id=reservation_id,
        student_user_id=member_user_id,
        membership_number=membership.membership_number if membership else None,
        book_id=book_id,
        title=item.title,
        branch_code=branch,
        queue_position=queue_len + 1,
        priority=priority,
        updated_by=actor_id,
    )
    await doc.insert()
    await _history(
        tenant_id,
        reservation_id=reservation_id,
        action="create",
        actor_id=actor_id,
        changes={"book_id": book_id, "branch_code": branch},
    )
    return doc


async def create_reservation(scope: AccessScope, payload: ReservationCreateRequest) -> ReservationRead:
    tenant_id = require_library_tenant_scope(scope)
    await require_reservation_manage(scope, branch_code=payload.branch_code)
    member_uid = to_object_id(payload.member_user_id, "member_user_id")
    await assert_member_can_borrow(tenant_id, member_uid)
    rid = _reservation_id(payload.reservation_id)
    doc = await create_reservation_core(
        tenant_id,
        member_user_id=member_uid,
        book_id=payload.book_id.strip(),
        branch_code=payload.branch_code,
        reservation_id=rid,
        priority=payload.priority,
        actor_id=scope.user_id,
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_reservation.create",
        module="library_reservations",
        resource_type="reservation",
        resource_id=rid,
    )
    offered = await allocate_reservation(tenant_id, rid, actor_id=scope.user_id)
    if offered is not None:
        return _to_read(offered)
    return _to_read(doc)


async def cancel_reservation(scope: AccessScope, reservation_id: str, payload: ReservationCancelRequest) -> ReservationRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryReservation.find_one(
        Eq(LibraryReservation.tenant_id, tenant_id),
        Eq(LibraryReservation.reservation_id, reservation_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Reservation not found", status_code=404)
    await require_reservation_manage(scope, branch_code=doc.branch_code)
    if doc.status in (LibraryReservationStatus.CANCELLED, LibraryReservationStatus.FULFILLED, LibraryReservationStatus.EXPIRED):
        raise AppError(code="CONFLICT", message="Reservation already closed", status_code=409)
    now = utcnow()
    released_copy = doc.copy_id
    doc.status = LibraryReservationStatus.CANCELLED
    doc.cancel_reason = payload.reason.strip()
    doc.cancelled_at = now
    doc.updated_at = now
    doc.updated_by = scope.user_id
    doc.copy_id = None
    await doc.save()
    if released_copy:
        await LibraryCopy.get_motor_collection().update_one(
            {
                "tenant_id": tenant_id,
                "copy_id": released_copy,
                "reserved_reservation_id": reservation_id,
            },
            {
                "$set": {"status": LibraryCopyStatus.AVAILABLE.value, "reserved_reservation_id": None, "updated_at": now},
                "$inc": {"version": 1},
            },
        )
        await offer_next_for_book(tenant_id, doc.book_id, doc.branch_code, actor_id=scope.user_id)
    await _history(tenant_id, reservation_id=reservation_id, action="cancel", actor_id=scope.user_id, changes={"reason": doc.cancel_reason})
    await _reindex_queue(tenant_id, doc.book_id, doc.branch_code)
    return _to_read(doc)


async def fulfill_reservation_record(scope: AccessScope, reservation_id: str) -> ReservationRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryReservation.find_one(
        Eq(LibraryReservation.tenant_id, tenant_id),
        Eq(LibraryReservation.reservation_id, reservation_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Reservation not found", status_code=404)
    await require_reservation_manage(scope, branch_code=doc.branch_code)
    if doc.status != LibraryReservationStatus.READY:
        raise AppError(code="CONFLICT", message="Reservation is not ready for fulfilment", status_code=409)
    now = utcnow()
    doc.status = LibraryReservationStatus.FULFILLED
    doc.updated_at = now
    doc.updated_by = scope.user_id
    await doc.save()
    if doc.copy_id:
        await LibraryCopy.get_motor_collection().update_one(
            {"tenant_id": tenant_id, "copy_id": doc.copy_id},
            {"$set": {"reserved_reservation_id": None, "updated_at": now}, "$inc": {"version": 1}},
        )
    await _history(tenant_id, reservation_id=reservation_id, action="fulfill", actor_id=scope.user_id, changes={})
    return _to_read(doc)


async def manual_allocate(scope: AccessScope, reservation_id: str, payload: ReservationAllocateRequest) -> ReservationRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryReservation.find_one(
        Eq(LibraryReservation.tenant_id, tenant_id),
        Eq(LibraryReservation.reservation_id, reservation_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Reservation not found", status_code=404)
    await require_reservation_manage(scope, branch_code=doc.branch_code)
    await assert_member_can_borrow(tenant_id, doc.student_user_id)
    allocated = await allocate_reservation(tenant_id, reservation_id, actor_id=scope.user_id, copy_id=payload.copy_id)
    if allocated is None:
        raise AppError(code="CONFLICT", message="No copy available to allocate", status_code=409)
    return _to_read(allocated)


async def get_reservation(scope: AccessScope, reservation_id: str) -> ReservationRead:
    authorize_reservation_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    await expire_ready_holds(tenant_id)
    doc = await LibraryReservation.find_one(
        Eq(LibraryReservation.tenant_id, tenant_id),
        Eq(LibraryReservation.reservation_id, reservation_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Reservation not found", status_code=404)
    return _to_read(doc)


async def search_reservations(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str | None = None,
    member_user_id: str | None = None,
    book_id: str | None = None,
    status: LibraryReservationStatus | None = None,
) -> Page[ReservationRead]:
    authorize_reservation_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    await expire_ready_holds(tenant_id)
    if branch_code:
        from app.modules.library.reservation_access import require_reservation_read

        await require_reservation_read(scope, branch_code=branch_code)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if branch_code:
        filters["branch_code"] = _norm_branch(branch_code)
    if member_user_id:
        filters["student_user_id"] = to_object_id(member_user_id, "member_user_id")
    if book_id:
        filters["book_id"] = book_id.strip()
    if status:
        filters["status"] = status.value
    query = LibraryReservation.find(filters).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_to_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def queue_for_book(scope: AccessScope, book_id: str, *, branch_code: str | None) -> list[ReservationRead]:
    authorize_reservation_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    await expire_ready_holds(tenant_id)
    branch = _norm_branch(branch_code)
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "book_id": book_id.strip(),
        "status": LibraryReservationStatus.QUEUED.value,
    }
    if branch:
        filters["branch_code"] = branch
    rows = await LibraryReservation.find(filters).sort("-priority", "+created_at").to_list()
    return [_to_read(r) for r in rows]


async def reservation_history(scope: AccessScope, reservation_id: str, pagination: Pagination) -> Page[ReservationHistoryEntry]:
    authorize_reservation_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    query = LibraryReservationHistory.find(
        Eq(LibraryReservationHistory.tenant_id, tenant_id),
        Eq(LibraryReservationHistory.reservation_id, reservation_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        ReservationHistoryEntry(
            action=r.action,
            actor_id=str(r.actor_id) if r.actor_id else None,
            changes=r.changes,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def upsert_reservation_policy(scope: AccessScope, payload: ReservationPolicyUpsert) -> dict:
    tenant_id = require_library_tenant_scope(scope)
    await require_reservation_manage(scope, branch_code=payload.branch_code)
    branch = _norm_branch(payload.branch_code)
    doc = await LibraryReservationPolicy.find_one(
        Eq(LibraryReservationPolicy.tenant_id, tenant_id),
        Eq(LibraryReservationPolicy.branch_code, branch),
    )
    if doc:
        doc.hold_hours = payload.hold_hours
        doc.max_active_per_member = payload.max_active_per_member
        doc.reserve_only_when_unavailable = payload.reserve_only_when_unavailable
        doc.updated_at = utcnow()
        doc.updated_by = scope.user_id
        await doc.save()
    else:
        await LibraryReservationPolicy(
            tenant_id=tenant_id,
            branch_code=branch,
            hold_hours=payload.hold_hours,
            max_active_per_member=payload.max_active_per_member,
            reserve_only_when_unavailable=payload.reserve_only_when_unavailable,
            updated_by=scope.user_id,
        ).insert()
    return {"branch_code": branch, "hold_hours": payload.hold_hours}


async def on_copy_available(tenant_id: PydanticObjectId, book_id: str, branch_code: str | None, *, actor_id: PydanticObjectId | None) -> None:
    await offer_next_for_book(tenant_id, book_id, branch_code, actor_id=actor_id)