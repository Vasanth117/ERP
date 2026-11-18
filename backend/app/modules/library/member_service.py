"""Library member management."""

from datetime import date
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionAccountStatus, InstitutionUser
from app.modules.college_admin.library_admin_models import LibraryBranch, LibraryMembershipReference
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCirculation, LibraryFine
from app.modules.library.member_enums import LibraryMemberCategory, LibraryMemberStatus
from app.modules.library.member_identity import assert_member_identity
from app.modules.library.member_models import LibraryMembershipHistory
from app.modules.library.member_schemas import (
    MemberBorrowingSummary,
    MemberHistoryEntry,
    MemberRead,
    MemberRegisterRequest,
    MemberSuspendRequest,
    MemberUpdateRequest,
)
from app.modules.library.policy import require_library_tenant_scope


def _membership_number() -> str:
    return f"MEM-{uuid4().hex[:10].upper()}"


def authorize_member_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_MEMBER_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_MEMBER_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_MEMBER_READ)


def authorize_member_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_MEMBER_MANAGE)


async def _assert_branch(tenant_id: PydanticObjectId, branch_code: str | None) -> None:
    if not branch_code:
        return
    exists = await LibraryBranch.find_one(
        Eq(LibraryBranch.tenant_id, tenant_id),
        Eq(LibraryBranch.branch_code, branch_code.strip().upper()),
    )
    if exists is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown branch", status_code=422)


async def _history(
    tenant_id: PydanticObjectId,
    *,
    member_user_id: PydanticObjectId,
    membership_number: str | None,
    action: str,
    actor_id: PydanticObjectId | None,
    changes: dict[str, Any],
) -> None:
    await LibraryMembershipHistory(
        tenant_id=tenant_id,
        member_user_id=member_user_id,
        membership_number=membership_number,
        action=action,
        actor_id=actor_id,
        changes=changes,
    ).insert()


def _validate_dates(activated_on: date | None, expires_on: date | None) -> None:
    if activated_on and expires_on and expires_on < activated_on:
        raise AppError(code="VALIDATION_ERROR", message="expires_on must be on or after activated_on", status_code=422)


async def _apply_expiry(doc: LibraryMembershipReference) -> None:
    if doc.expires_on and doc.expires_on < date.today() and doc.status == LibraryMemberStatus.ACTIVE.value:
        doc.status = LibraryMemberStatus.EXPIRED.value
        doc.eligible = False
        doc.updated_at = utcnow()
        await doc.save()


def _borrowing_eligible(doc: LibraryMembershipReference) -> bool:
    if not doc.eligible:
        return False
    if doc.status != LibraryMemberStatus.ACTIVE.value:
        return False
    if doc.expires_on and doc.expires_on < date.today():
        return False
    return True


async def assert_member_can_borrow(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> LibraryMembershipReference:
    """Validate membership exists and member may borrow (used by circulation)."""
    doc = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.member_user_id, user_id),
    )
    if doc is None:
        raise AppError(code="FORBIDDEN", message="Library membership required to borrow", status_code=403)
    await _apply_expiry(doc)
    if not _borrowing_eligible(doc):
        raise AppError(code="FORBIDDEN", message="Member is not eligible to borrow", status_code=403)
    if await _institution_blocks_borrow(tenant_id, user_id):
        raise AppError(code="FORBIDDEN", message="Institution account blocks borrowing", status_code=403)
    return doc


async def _institution_blocks_borrow(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> bool:
    row = await InstitutionUser.find_one(Eq(InstitutionUser.tenant_id, tenant_id), Eq(InstitutionUser.user_id, user_id))
    if row is None:
        return False
    return row.account_status in (InstitutionAccountStatus.SUSPENDED, InstitutionAccountStatus.DEACTIVATED)


async def _to_read(tenant_id: PydanticObjectId, doc: LibraryMembershipReference) -> MemberRead:
    await _apply_expiry(doc)
    user = await User.get(doc.member_user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="Member user missing", status_code=404)
    blocked = await _institution_blocks_borrow(tenant_id, doc.member_user_id)
    borrowing_eligible = _borrowing_eligible(doc) and not blocked
    return MemberRead(
        membership_number=doc.membership_number,
        member_user_id=str(doc.member_user_id),
        member_category=LibraryMemberCategory(doc.member_category),
        display_name=user.full_name,
        email=user.email,
        branch_code=doc.branch_code,
        status=LibraryMemberStatus(doc.status),
        eligible=doc.eligible,
        borrowing_eligible=borrowing_eligible,
        borrowing_limit=doc.borrowing_limit,
        activated_on=doc.activated_on,
        expires_on=doc.expires_on,
        suspension_reason=doc.suspension_reason,
        suspended_at=doc.suspended_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def register_member(scope: AccessScope, payload: MemberRegisterRequest) -> MemberRead:
    authorize_member_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    uid = to_object_id(payload.member_user_id, "member_user_id")
    await assert_member_identity(tenant_id, uid, payload.member_category)
    if await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.member_user_id, uid),
    ):
        raise AppError(code="CONFLICT", message="User already has library membership", status_code=409)
    _validate_dates(payload.activated_on, payload.expires_on)
    await _assert_branch(tenant_id, payload.branch_code)
    number = _membership_number()
    status = LibraryMemberStatus.ACTIVE.value
    if payload.expires_on and payload.expires_on < date.today():
        status = LibraryMemberStatus.EXPIRED.value
    doc = LibraryMembershipReference(
        tenant_id=tenant_id,
        membership_number=number,
        member_user_id=uid,
        member_type=payload.member_category.value,
        member_category=payload.member_category.value,
        branch_code=payload.branch_code.upper() if payload.branch_code else None,
        eligible=payload.eligible,
        borrowing_limit=payload.borrowing_limit,
        status=status,
        activated_on=payload.activated_on or date.today(),
        expires_on=payload.expires_on,
        created_by=scope.user_id,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _history(
        tenant_id,
        member_user_id=uid,
        membership_number=number,
        action="register",
        actor_id=scope.user_id,
        changes=payload.model_dump(mode="json"),
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_member.register",
        module="library_members",
        resource_type="membership",
        resource_id=number,
    )
    return await _to_read(tenant_id, doc)


async def get_member_by_number(scope: AccessScope, membership_number: str) -> MemberRead:
    authorize_member_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.membership_number, membership_number.strip().upper()),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Member not found", status_code=404)
    return await _to_read(tenant_id, doc)


async def get_member_by_user(scope: AccessScope, member_user_id: str) -> MemberRead:
    authorize_member_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    uid = to_object_id(member_user_id, "member_user_id")
    doc = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.member_user_id, uid),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Member not found", status_code=404)
    return await _to_read(tenant_id, doc)


async def update_member(scope: AccessScope, membership_number: str, payload: MemberUpdateRequest) -> MemberRead:
    authorize_member_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.membership_number, membership_number.strip().upper()),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Member not found", status_code=404)
    changes = payload.model_dump(exclude_unset=True, mode="json")
    if not changes:
        raise AppError(code="VALIDATION_ERROR", message="No fields to update", status_code=422)
    activated = payload.activated_on if payload.activated_on is not None else doc.activated_on
    expires = payload.expires_on if payload.expires_on is not None else doc.expires_on
    _validate_dates(activated, expires)
    if payload.branch_code is not None:
        await _assert_branch(tenant_id, payload.branch_code)
        doc.branch_code = payload.branch_code.upper() if payload.branch_code else None
    if payload.borrowing_limit is not None:
        doc.borrowing_limit = payload.borrowing_limit
    if payload.activated_on is not None:
        doc.activated_on = payload.activated_on
    if payload.expires_on is not None:
        doc.expires_on = payload.expires_on
    if payload.eligible is not None:
        doc.eligible = payload.eligible
    if payload.status is not None:
        doc.status = payload.status.value
        if payload.status == LibraryMemberStatus.SUSPENDED:
            doc.suspended_at = utcnow()
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _history(
        tenant_id,
        member_user_id=doc.member_user_id,
        membership_number=doc.membership_number,
        action="update",
        actor_id=scope.user_id,
        changes=changes,
    )
    return await _to_read(tenant_id, doc)


async def suspend_member(scope: AccessScope, membership_number: str, payload: MemberSuspendRequest) -> MemberRead:
    authorize_member_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.membership_number, membership_number.strip().upper()),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Member not found", status_code=404)
    doc.status = LibraryMemberStatus.SUSPENDED.value
    doc.eligible = False
    doc.suspension_reason = payload.reason.strip()
    doc.suspended_at = utcnow()
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _history(
        tenant_id,
        member_user_id=doc.member_user_id,
        membership_number=doc.membership_number,
        action="suspend",
        actor_id=scope.user_id,
        changes={"reason": doc.suspension_reason},
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_member.suspend",
        module="library_members",
        resource_type="membership",
        resource_id=doc.membership_number,
    )
    return await _to_read(tenant_id, doc)


async def reactivate_member(scope: AccessScope, membership_number: str) -> MemberRead:
    authorize_member_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.membership_number, membership_number.strip().upper()),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Member not found", status_code=404)
    if doc.status not in (LibraryMemberStatus.SUSPENDED.value, LibraryMemberStatus.INACTIVE.value):
        raise AppError(code="CONFLICT", message="Member is not suspended or inactive", status_code=409)
    doc.status = LibraryMemberStatus.ACTIVE.value
    doc.eligible = True
    doc.suspension_reason = None
    doc.suspended_at = None
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _history(
        tenant_id,
        member_user_id=doc.member_user_id,
        membership_number=doc.membership_number,
        action="reactivate",
        actor_id=scope.user_id,
        changes={},
    )
    return await _to_read(tenant_id, doc)


async def search_members(
    scope: AccessScope,
    pagination: Pagination,
    *,
    q: str | None = None,
    category: LibraryMemberCategory | None = None,
    status: LibraryMemberStatus | None = None,
    branch_code: str | None = None,
    eligible: bool | None = None,
) -> Page[MemberRead]:
    authorize_member_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if category:
        filters["member_category"] = category.value
    if status:
        filters["status"] = status.value
    if branch_code:
        filters["branch_code"] = branch_code.strip().upper()
    if eligible is not None:
        filters["eligible"] = eligible
    rows = await LibraryMembershipReference.find(filters).sort("membership_number").to_list()
    if q:
        term = q.strip().lower()
        user_ids = set()
        users = await User.find({"tenant_id": tenant_id}).to_list()
        for user in users:
            if term in user.full_name.lower() or term in user.email.lower():
                user_ids.add(user.id)
        rows = [
            r
            for r in rows
            if r.member_user_id in user_ids or term in r.membership_number.lower()
        ]
    total = len(rows)
    page = rows[pagination.offset : pagination.offset + pagination.limit]
    items = [await _to_read(tenant_id, r) for r in page]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def member_borrowing_summary(scope: AccessScope, membership_number: str) -> MemberBorrowingSummary:
    authorize_member_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.membership_number, membership_number.strip().upper()),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Member not found", status_code=404)
    uid = doc.member_user_id
    today = date.today()
    active = await LibraryCirculation.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": uid,
            "status": {"$in": [LibraryCirculationStatus.ACTIVE.value, LibraryCirculationStatus.OVERDUE.value]},
        }
    ).count()
    overdue = await LibraryCirculation.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": uid,
            "status": {"$in": [LibraryCirculationStatus.ACTIVE.value, LibraryCirculationStatus.OVERDUE.value]},
            "due_at": {"$lt": today},
        }
    ).count()
    fines = await LibraryFine.find(
        Eq(LibraryFine.tenant_id, tenant_id),
        Eq(LibraryFine.student_user_id, uid),
        Eq(LibraryFine.status, LibraryFineStatus.OPEN),
    ).to_list()
    history = await LibraryCirculation.find(Eq(LibraryCirculation.tenant_id, tenant_id), Eq(LibraryCirculation.student_user_id, uid)).count()
    return MemberBorrowingSummary(
        active_loans=active,
        overdue_loans=overdue,
        open_fines=len(fines),
        outstanding_fine_amount=round(sum(f.amount for f in fines), 2),
        total_loan_history=history,
    )


async def member_history(
    scope: AccessScope,
    membership_number: str,
    pagination: Pagination,
) -> Page[MemberHistoryEntry]:
    authorize_member_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.membership_number, membership_number.strip().upper()),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Member not found", status_code=404)
    query = LibraryMembershipHistory.find(
        Eq(LibraryMembershipHistory.tenant_id, tenant_id),
        Eq(LibraryMembershipHistory.member_user_id, doc.member_user_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        MemberHistoryEntry(
            action=r.action,
            changes=r.changes,
            actor_id=str(r.actor_id) if r.actor_id else None,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)