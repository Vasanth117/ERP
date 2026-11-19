"""Book issue, return and renewal."""

from datetime import date, timedelta
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
from app.modules.college_admin.library_admin_models import (
    LibraryBorrowingPolicy,
    LibraryBranch,
    LibraryCirculationRecord,
    LibraryInventoryHistory,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.circulation_access import authorize_circulation_read, require_circulation_manage
from app.modules.library.circulation_enums import ReturnDisposition
from app.modules.library.circulation_schemas import CirculationHistoryEntry, CirculationRead, IssueLoanRequest, ReturnLoanRequest
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyCondition, LibraryCopyStatus
from app.modules.library.library_models import LibraryCatalogItem, LibraryCirculation, LibraryCopy
from app.modules.library.member_service import assert_member_can_borrow
from app.modules.library.policy_evaluation import resolve_borrowing_policy, snapshot_from_loan
from app.modules.library.settings_enums import LibraryResourceType


def _norm_branch(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().upper()


async def _assert_branch_exists(tenant_id: PydanticObjectId, branch_code: str) -> None:
    exists = await LibraryBranch.find_one(
        Eq(LibraryBranch.tenant_id, tenant_id),
        Eq(LibraryBranch.branch_code, branch_code),
    )
    if exists is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown branch", status_code=422)


async def _policy_for_branch(tenant_id: PydanticObjectId, branch_code: str | None) -> LibraryBorrowingPolicy | None:
    if branch_code:
        doc = await LibraryBorrowingPolicy.find_one(
            Eq(LibraryBorrowingPolicy.tenant_id, tenant_id),
            Eq(LibraryBorrowingPolicy.branch_code, branch_code),
        )
        if doc:
            return doc
    return await LibraryBorrowingPolicy.find_one(
        Eq(LibraryBorrowingPolicy.tenant_id, tenant_id),
        Eq(LibraryBorrowingPolicy.branch_code, None),
    )


async def _active_loan_count(tenant_id: PydanticObjectId, member_user_id: PydanticObjectId) -> int:
    return await LibraryCirculation.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": member_user_id,
            "status": {"$in": [LibraryCirculationStatus.ACTIVE.value, LibraryCirculationStatus.OVERDUE.value]},
        }
    ).count()


def _loan_limit(policy: LibraryBorrowingPolicy | None, member_limit: int) -> int:
    policy_max = policy.max_books if policy else 5
    return min(policy_max, member_limit)


def _loan_days(policy: LibraryBorrowingPolicy | None) -> int:
    return policy.loan_days if policy else 14


def _renewal_limit(policy: LibraryBorrowingPolicy | None) -> int:
    return policy.renewal_limit if policy else 2


async def _sync_overdue(circ: LibraryCirculation) -> None:
    if circ.status != LibraryCirculationStatus.ACTIVE:
        return
    if circ.due_at < date.today():
        circ.status = LibraryCirculationStatus.OVERDUE
        circ.updated_at = utcnow()
        await circ.save()


def _to_read(circ: LibraryCirculation) -> CirculationRead:
    return CirculationRead(
        circulation_id=circ.circulation_id,
        member_user_id=str(circ.student_user_id),
        membership_number=circ.membership_number,
        book_id=circ.book_id,
        copy_id=circ.copy_id,
        branch_code=circ.branch_code,
        title=circ.title,
        issued_at=circ.issued_at,
        due_at=circ.due_at,
        returned_at=circ.returned_at,
        status=circ.status,
        renewal_count=circ.renewal_count,
        return_disposition=circ.return_disposition,
    )


async def _record(
    tenant_id: PydanticObjectId,
    *,
    circulation_id: str,
    branch_code: str | None,
    action: str,
    actor_id: PydanticObjectId | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    await LibraryCirculationRecord(
        tenant_id=tenant_id,
        circulation_id=circulation_id,
        branch_code=branch_code,
        action=action,
        actor_id=actor_id,
        metadata=metadata or {},
    ).insert()


async def _inventory_event(
    tenant_id: PydanticObjectId,
    *,
    copy_id: str,
    branch_code: str | None,
    event_type: str,
    actor_id: PydanticObjectId | None,
    metadata: dict[str, Any],
) -> None:
    await LibraryInventoryHistory(
        tenant_id=tenant_id,
        branch_code=branch_code,
        copy_id=copy_id,
        event_type=event_type,
        metadata=metadata,
        actor_id=actor_id,
    ).insert()


async def _claim_copy_atomic(
    tenant_id: PydanticObjectId,
    copy_id: str,
    actor_id: PydanticObjectId,
) -> dict[str, Any]:
    coll = LibraryCopy.get_motor_collection()
    now = utcnow()
    claimed = await coll.find_one_and_update(
        {
            "tenant_id": tenant_id,
            "copy_id": copy_id,
            "status": LibraryCopyStatus.AVAILABLE.value,
        },
        {
            "$set": {
                "status": LibraryCopyStatus.ISSUED.value,
                "updated_at": now,
                "updated_by": actor_id,
            },
            "$inc": {"version": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if claimed is None:
        raise AppError(code="CONFLICT", message="Copy not available", status_code=409)
    return claimed


def _resolve_branch(payload_branch: str | None, copy_branch: str | None) -> str:
    branch = _norm_branch(payload_branch) or _norm_branch(copy_branch)
    if not branch:
        raise AppError(code="VALIDATION_ERROR", message="branch_code required", status_code=422)
    return branch


async def issue_loan(scope: AccessScope, payload: IssueLoanRequest) -> CirculationRead:
    from app.modules.library.policy import require_library_tenant_scope

    tenant_id = require_library_tenant_scope(scope)
    member_uid = to_object_id(payload.member_user_id, "member_user_id")
    membership = await assert_member_can_borrow(tenant_id, member_uid)
    copy = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.copy_id, payload.copy_id.strip()))
    if copy is None:
        raise AppError(code="NOT_FOUND", message="Copy not found", status_code=404)
    branch = _resolve_branch(payload.branch_code, copy.branch_code)
    await require_circulation_manage(scope, branch_code=branch)
    await _assert_branch_exists(tenant_id, branch)
    snap = await resolve_borrowing_policy(
        tenant_id,
        branch_code=branch,
        member_category=membership.member_category,
        resource_type=LibraryResourceType.PHYSICAL.value,
    )
    policy = await _policy_for_branch(tenant_id, branch)
    limit = min(snap.max_books, membership.borrowing_limit)
    active = await _active_loan_count(tenant_id, member_uid)
    if active >= limit:
        raise AppError(code="CONFLICT", message="Member has reached borrowing limit", status_code=409)
    await _claim_copy_atomic(tenant_id, copy.copy_id, scope.user_id)
    item = await LibraryCatalogItem.find_one(Eq(LibraryCatalogItem.tenant_id, tenant_id), Eq(LibraryCatalogItem.book_id, copy.book_id))
    loan_days = snap.loan_days
    now = utcnow()
    due = (now + timedelta(days=loan_days)).date()
    circulation_id = f"circ_{uuid4().hex}"
    circ = LibraryCirculation(
        tenant_id=tenant_id,
        circulation_id=circulation_id,
        student_user_id=member_uid,
        book_id=copy.book_id,
        copy_id=copy.copy_id,
        branch_code=branch,
        membership_number=membership.membership_number,
        title=item.title if item else copy.book_id,
        issued_at=now,
        due_at=due,
        status=LibraryCirculationStatus.ACTIVE,
        applied_policy_id=snap.policy_id,
        applied_policy_version=snap.version,
        applied_policy_snapshot=snap.as_dict(),
        updated_by=scope.user_id,
    )
    try:
        await circ.insert()
    except Exception:
        coll = LibraryCopy.get_motor_collection()
        await coll.update_one(
            {"tenant_id": tenant_id, "copy_id": copy.copy_id, "status": LibraryCopyStatus.ISSUED.value},
            {
                "$set": {
                    "status": LibraryCopyStatus.AVAILABLE.value,
                    "updated_at": utcnow(),
                    "updated_by": scope.user_id,
                },
                "$inc": {"version": 1},
            },
        )
        raise
    await _record(
        tenant_id,
        circulation_id=circulation_id,
        branch_code=branch,
        action="issue",
        actor_id=scope.user_id,
        metadata={"member_user_id": payload.member_user_id, "copy_id": copy.copy_id, "due_at": due.isoformat()},
    )
    await _inventory_event(
        tenant_id,
        copy_id=copy.copy_id,
        branch_code=branch,
        event_type="circulation_issue",
        actor_id=scope.user_id,
        metadata={"circulation_id": circulation_id, "member_user_id": payload.member_user_id},
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_circulation.issue",
        module="library_circulation",
        resource_type="circulation",
        resource_id=circulation_id,
    )
    circ_doc = await LibraryCirculation.find_one(
        Eq(LibraryCirculation.tenant_id, tenant_id),
        Eq(LibraryCirculation.circulation_id, circulation_id),
    )
    if circ_doc:
        from app.modules.library.notification_triggers import on_loan_issued

        await on_loan_issued(tenant_id, circ_doc)
    return _to_read(circ)


def _copy_status_after_return(disposition: ReturnDisposition, condition: LibraryCopyCondition | None) -> LibraryCopyStatus:
    if disposition == ReturnDisposition.LOST:
        return LibraryCopyStatus.LOST
    if disposition == ReturnDisposition.DAMAGED:
        return LibraryCopyStatus.DAMAGED
    return LibraryCopyStatus.AVAILABLE


async def return_loan(scope: AccessScope, circulation_id: str, payload: ReturnLoanRequest) -> CirculationRead:
    from app.modules.library.policy import require_library_tenant_scope

    tenant_id = require_library_tenant_scope(scope)
    circ = await LibraryCirculation.find_one(
        Eq(LibraryCirculation.tenant_id, tenant_id),
        Eq(LibraryCirculation.circulation_id, circulation_id),
    )
    if circ is None:
        raise AppError(code="NOT_FOUND", message="Circulation not found", status_code=404)
    await require_circulation_manage(scope, branch_code=circ.branch_code)
    if circ.status == LibraryCirculationStatus.RETURNED:
        raise AppError(code="CONFLICT", message="Already returned", status_code=409)
    now = utcnow()
    circ.status = LibraryCirculationStatus.RETURNED
    circ.returned_at = now
    circ.return_disposition = payload.disposition.value
    circ.updated_at = now
    circ.updated_by = scope.user_id
    await circ.save()
    copy = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.copy_id, circ.copy_id))
    if copy:
        target = _copy_status_after_return(payload.disposition, payload.condition)
        copy.status = target
        copy.reserved_reservation_id = None
        if payload.condition is not None:
            copy.condition = payload.condition
        if payload.notes:
            copy.notes = payload.notes
        copy.updated_at = now
        copy.updated_by = scope.user_id
        copy.version += 1
        await copy.save()
        if target == LibraryCopyStatus.AVAILABLE:
            from app.modules.library.reservation_service import on_copy_available

            await on_copy_available(tenant_id, copy.book_id, copy.branch_code, actor_id=scope.user_id)
    from app.modules.library.fine_service import process_return_fines

    await process_return_fines(
        tenant_id,
        circulation_id=circ.circulation_id,
        disposition=payload.disposition,
        actor_id=scope.user_id,
    )
    await _record(
        tenant_id,
        circulation_id=circ.circulation_id,
        branch_code=circ.branch_code,
        action="return",
        actor_id=scope.user_id,
        metadata={
            "disposition": payload.disposition.value,
            "condition": payload.condition.value if payload.condition else None,
        },
    )
    await _inventory_event(
        tenant_id,
        copy_id=circ.copy_id,
        branch_code=circ.branch_code,
        event_type="circulation_return",
        actor_id=scope.user_id,
        metadata={"circulation_id": circ.circulation_id, "disposition": payload.disposition.value},
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_circulation.return",
        module="library_circulation",
        resource_type="circulation",
        resource_id=circ.circulation_id,
    )
    return _to_read(circ)


async def renew_loan(scope: AccessScope, circulation_id: str) -> CirculationRead:
    from app.modules.library.policy import require_library_tenant_scope

    tenant_id = require_library_tenant_scope(scope)
    circ = await LibraryCirculation.find_one(
        Eq(LibraryCirculation.tenant_id, tenant_id),
        Eq(LibraryCirculation.circulation_id, circulation_id),
    )
    if circ is None:
        raise AppError(code="NOT_FOUND", message="Circulation not found", status_code=404)
    await require_circulation_manage(scope, branch_code=circ.branch_code)
    if circ.status == LibraryCirculationStatus.RETURNED:
        raise AppError(code="CONFLICT", message="Cannot renew returned loan", status_code=409)
    await assert_member_can_borrow(tenant_id, circ.student_user_id)
    snap = snapshot_from_loan(circ)
    if snap is None:
        policy = await _policy_for_branch(tenant_id, circ.branch_code)
        renewal_cap = _renewal_limit(policy)
        loan_days = _loan_days(policy)
    else:
        renewal_cap = snap.renewal_limit
        loan_days = snap.loan_days
    if circ.renewal_count >= renewal_cap:
        raise AppError(code="CONFLICT", message="Renewal limit reached", status_code=409)
    base = max(circ.due_at, date.today())
    circ.due_at = base + timedelta(days=loan_days)
    circ.renewal_count += 1
    circ.status = LibraryCirculationStatus.ACTIVE
    circ.updated_at = utcnow()
    circ.updated_by = scope.user_id
    await circ.save()
    await _record(
        tenant_id,
        circulation_id=circ.circulation_id,
        branch_code=circ.branch_code,
        action="renew",
        actor_id=scope.user_id,
        metadata={"due_at": circ.due_at.isoformat(), "renewal_count": circ.renewal_count},
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_circulation.renew",
        module="library_circulation",
        resource_type="circulation",
        resource_id=circ.circulation_id,
    )
    return _to_read(circ)


async def get_loan(scope: AccessScope, circulation_id: str) -> CirculationRead:
    from app.modules.library.policy import require_library_tenant_scope

    authorize_circulation_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    circ = await LibraryCirculation.find_one(
        Eq(LibraryCirculation.tenant_id, tenant_id),
        Eq(LibraryCirculation.circulation_id, circulation_id),
    )
    if circ is None:
        raise AppError(code="NOT_FOUND", message="Circulation not found", status_code=404)
    await _sync_overdue(circ)
    return _to_read(circ)


async def search_loans(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str | None = None,
    member_user_id: str | None = None,
    status: LibraryCirculationStatus | None = None,
    copy_id: str | None = None,
) -> Page[CirculationRead]:
    from app.modules.library.policy import require_library_tenant_scope

    authorize_circulation_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    if branch_code:
        await require_circulation_read(scope, branch_code=branch_code)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if branch_code:
        filters["branch_code"] = _norm_branch(branch_code)
    if member_user_id:
        filters["student_user_id"] = to_object_id(member_user_id, "member_user_id")
    if status:
        filters["status"] = status.value
    if copy_id:
        filters["copy_id"] = copy_id.strip()
    query = LibraryCirculation.find(filters).sort("-issued_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[CirculationRead] = []
    for row in rows:
        await _sync_overdue(row)
        items.append(_to_read(row))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def loan_history(scope: AccessScope, circulation_id: str, pagination: Pagination) -> Page[CirculationHistoryEntry]:
    from app.modules.library.policy import require_library_tenant_scope

    authorize_circulation_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    circ = await LibraryCirculation.find_one(
        Eq(LibraryCirculation.tenant_id, tenant_id),
        Eq(LibraryCirculation.circulation_id, circulation_id),
    )
    if circ is None:
        raise AppError(code="NOT_FOUND", message="Circulation not found", status_code=404)
    query = LibraryCirculationRecord.find(
        Eq(LibraryCirculationRecord.tenant_id, tenant_id),
        Eq(LibraryCirculationRecord.circulation_id, circulation_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        CirculationHistoryEntry(
            action=r.action,
            branch_code=r.branch_code,
            actor_id=str(r.actor_id) if r.actor_id else None,
            metadata=r.metadata,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)