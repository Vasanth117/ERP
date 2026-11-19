"""Library settings and borrowing policy management."""

from datetime import date
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.library_admin_models import LibraryBorrowingPolicy, LibraryBranch
from app.modules.college_admin.library_admin_schemas import BorrowingPolicyUpsert
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.policy import require_library_tenant_scope
from app.modules.library.policy_evaluation import resolve_borrowing_policy
from app.modules.library.settings_access import (
    authorize_settings_activate,
    authorize_settings_manage,
    authorize_settings_read,
)
from app.modules.library.settings_enums import LibraryPolicyStatus, LibraryResourceType
from app.modules.library.settings_models import LibraryBorrowingRule, LibraryPolicyHistory
from app.modules.library.settings_schemas import (
    BorrowingRuleCreate,
    BorrowingRuleRead,
    BorrowingRuleUpdate,
    EffectivePolicyPreview,
    PolicyHistoryEntry,
)


def _policy_id(custom: str | None) -> str:
    if custom and custom.strip():
        return custom.strip()
    return f"pol_{uuid4().hex[:12]}"


def _norm_branch(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().upper()


async def _assert_branch(tenant_id: PydanticObjectId, branch_code: str | None) -> None:
    if not branch_code:
        return
    exists = await LibraryBranch.find_one(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.branch_code, branch_code))
    if exists is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown branch", status_code=422)


async def _history(
    tenant_id: PydanticObjectId,
    *,
    policy_id: str,
    version: int,
    action: str,
    actor_id: PydanticObjectId | None,
    changes: dict[str, Any],
) -> None:
    await LibraryPolicyHistory(
        tenant_id=tenant_id,
        policy_id=policy_id,
        policy_type="borrowing",
        version=version,
        action=action,
        actor_id=actor_id,
        changes=changes,
    ).insert()


def _to_read(doc: LibraryBorrowingRule) -> BorrowingRuleRead:
    try:
        status = LibraryPolicyStatus(doc.status)
    except ValueError:
        status = LibraryPolicyStatus.DRAFT
    return BorrowingRuleRead(
        policy_id=doc.policy_id,
        version=doc.version,
        branch_code=doc.branch_code,
        member_category=doc.member_category,
        resource_type=doc.resource_type,
        status=status,
        effective_from=doc.effective_from,
        effective_until=doc.effective_until,
        max_books=doc.max_books,
        loan_days=doc.loan_days,
        renewal_limit=doc.renewal_limit,
        fine_per_day=doc.fine_per_day,
        grace_days=doc.grace_days,
        max_overdue_days=doc.max_overdue_days,
        max_reservations_per_member=doc.max_reservations_per_member,
        hold_hours=doc.hold_hours,
        reserve_only_when_unavailable=doc.reserve_only_when_unavailable,
        lost_book_charge=doc.lost_book_charge,
        damaged_book_charge=doc.damaged_book_charge,
        eligibility_restrictions=list(doc.eligibility_restrictions or []),
        borrowing_restrictions=dict(doc.borrowing_restrictions or {}),
        requires_approval=doc.requires_approval,
        notes=doc.notes,
        updated_at=doc.updated_at,
    )


async def create_borrowing_rule(scope: AccessScope, payload: BorrowingRuleCreate) -> BorrowingRuleRead:
    authorize_settings_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    branch = _norm_branch(payload.branch_code)
    await _assert_branch(tenant_id, branch)
    pid = _policy_id(payload.policy_id)
    if await LibraryBorrowingRule.find_one(Eq(LibraryBorrowingRule.tenant_id, tenant_id), Eq(LibraryBorrowingRule.policy_id, pid)):
        raise AppError(code="CONFLICT", message="Policy id already used", status_code=409)
    eff_from = payload.effective_from or date.today()
    if payload.effective_until and payload.effective_until < eff_from:
        raise AppError(code="VALIDATION_ERROR", message="effective_until before effective_from", status_code=422)
    doc = LibraryBorrowingRule(
        tenant_id=tenant_id,
        policy_id=pid,
        version=1,
        branch_code=branch,
        member_category=payload.member_category.strip() if payload.member_category else None,
        resource_type=payload.resource_type.value,
        status=LibraryPolicyStatus.DRAFT.value,
        effective_from=eff_from,
        effective_until=payload.effective_until,
        max_books=payload.max_books,
        loan_days=payload.loan_days,
        renewal_limit=payload.renewal_limit,
        fine_per_day=payload.fine_per_day,
        grace_days=payload.grace_days,
        max_overdue_days=payload.max_overdue_days,
        max_reservations_per_member=payload.max_reservations_per_member,
        hold_hours=payload.hold_hours,
        reserve_only_when_unavailable=payload.reserve_only_when_unavailable,
        lost_book_charge=payload.lost_book_charge,
        damaged_book_charge=payload.damaged_book_charge,
        eligibility_restrictions=payload.eligibility_restrictions,
        borrowing_restrictions=payload.borrowing_restrictions,
        requires_approval=payload.requires_approval,
        notes=payload.notes,
        created_by=scope.user_id,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _history(tenant_id, policy_id=pid, version=1, action="create", actor_id=scope.user_id, changes=payload.model_dump(mode="json"))
    return _to_read(doc)


async def update_borrowing_rule(scope: AccessScope, policy_id: str, payload: BorrowingRuleUpdate) -> BorrowingRuleRead:
    authorize_settings_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await _latest_version(tenant_id, policy_id)
    if doc.status != LibraryPolicyStatus.DRAFT.value:
        raise AppError(code="CONFLICT", message="Only draft policies can be edited in place", status_code=409)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, key, value)
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, policy_id=policy_id, version=doc.version, action="update", actor_id=scope.user_id, changes=payload.model_dump(exclude_unset=True, mode="json"))
    return _to_read(doc)


async def _latest_version(tenant_id: PydanticObjectId, policy_id: str) -> LibraryBorrowingRule:
    rows = await LibraryBorrowingRule.find(
        Eq(LibraryBorrowingRule.tenant_id, tenant_id),
        Eq(LibraryBorrowingRule.policy_id, policy_id),
    ).sort("-version").limit(1).to_list()
    if not rows:
        raise AppError(code="NOT_FOUND", message="Policy not found", status_code=404)
    return rows[0]


async def activate_borrowing_rule(scope: AccessScope, policy_id: str) -> BorrowingRuleRead:
    if (await _latest_version(require_library_tenant_scope(scope), policy_id)).requires_approval:
        authorize_settings_activate(scope)
    else:
        authorize_settings_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await _latest_version(tenant_id, policy_id)
    if doc.status == LibraryPolicyStatus.ACTIVE.value:
        raise AppError(code="CONFLICT", message="Already active", status_code=409)
    if doc.status == LibraryPolicyStatus.RETIRED.value:
        raise AppError(code="CONFLICT", message="Cannot activate retired policy", status_code=409)
    siblings = await LibraryBorrowingRule.find(
        {
            "tenant_id": tenant_id,
            "status": LibraryPolicyStatus.ACTIVE.value,
            "branch_code": doc.branch_code,
            "member_category": doc.member_category,
            "resource_type": doc.resource_type,
        }
    ).to_list()
    for other in siblings:
        other.status = LibraryPolicyStatus.RETIRED.value
        other.effective_until = date.today()
        other.updated_at = utcnow()
        await other.save()
        await _history(
            tenant_id,
            policy_id=other.policy_id,
            version=other.version,
            action="retire",
            actor_id=scope.user_id,
            changes={"reason": "superseded", "by_policy": policy_id},
        )
    doc.status = LibraryPolicyStatus.ACTIVE.value
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _sync_legacy_borrowing_row(tenant_id, doc)
    await _history(tenant_id, policy_id=policy_id, version=doc.version, action="activate", actor_id=scope.user_id, changes={})
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_policy.activate",
        module="library_settings",
        resource_type="borrowing_policy",
        resource_id=policy_id,
    )
    return _to_read(doc)


async def _sync_legacy_borrowing_row(tenant_id: PydanticObjectId, rule: LibraryBorrowingRule) -> None:
    """Keep legacy `library_borrowing_policies` aligned for readers not yet on rules engine."""
    branch = rule.branch_code
    legacy = await LibraryBorrowingPolicy.find_one(
        Eq(LibraryBorrowingPolicy.tenant_id, tenant_id),
        Eq(LibraryBorrowingPolicy.branch_code, branch),
    )
    if legacy is None:
        legacy = LibraryBorrowingPolicy(tenant_id=tenant_id, branch_code=branch)
    legacy.max_books = rule.max_books
    legacy.loan_days = rule.loan_days
    legacy.renewal_limit = rule.renewal_limit
    legacy.fine_per_day = rule.fine_per_day
    legacy.version = rule.version
    legacy.updated_by = rule.updated_by
    legacy.updated_at = utcnow()
    await legacy.save()


async def retire_borrowing_rule(scope: AccessScope, policy_id: str) -> BorrowingRuleRead:
    authorize_settings_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await _latest_version(tenant_id, policy_id)
    if doc.status != LibraryPolicyStatus.ACTIVE.value:
        raise AppError(code="CONFLICT", message="Only active policies can be retired", status_code=409)
    doc.status = LibraryPolicyStatus.RETIRED.value
    doc.effective_until = date.today()
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, policy_id=policy_id, version=doc.version, action="retire", actor_id=scope.user_id, changes={})
    return _to_read(doc)


async def get_borrowing_rule(scope: AccessScope, policy_id: str) -> BorrowingRuleRead:
    authorize_settings_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    return _to_read(await _latest_version(tenant_id, policy_id))


async def search_borrowing_rules(
    scope: AccessScope,
    pagination: Pagination,
    *,
    status: str | None = None,
    branch_code: str | None = None,
) -> Page[BorrowingRuleRead]:
    authorize_settings_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if status:
        filters["status"] = status
    if branch_code:
        filters["branch_code"] = _norm_branch(branch_code)
    query = LibraryBorrowingRule.find(filters).sort("-updated_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_to_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def policy_change_history(scope: AccessScope, policy_id: str, pagination: Pagination) -> Page[PolicyHistoryEntry]:
    authorize_settings_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    query = LibraryPolicyHistory.find(
        Eq(LibraryPolicyHistory.tenant_id, tenant_id),
        Eq(LibraryPolicyHistory.policy_id, policy_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        PolicyHistoryEntry(
            policy_id=r.policy_id,
            version=r.version,
            action=r.action,
            actor_id=str(r.actor_id) if r.actor_id else None,
            changes=r.changes,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def preview_effective_policy(
    scope: AccessScope,
    *,
    branch_code: str | None,
    member_category: str | None,
    resource_type: str | None,
) -> EffectivePolicyPreview:
    authorize_settings_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    snap = await resolve_borrowing_policy(
        tenant_id,
        branch_code=branch_code,
        member_category=member_category,
        resource_type=resource_type or LibraryResourceType.PHYSICAL.value,
    )
    return EffectivePolicyPreview(
        branch_code=branch_code,
        member_category=member_category,
        resource_type=resource_type,
        snapshot=snap.as_dict(),
    )


async def college_admin_upsert_borrowing_policy(scope: AccessScope, payload: BorrowingPolicyUpsert) -> dict:
    """Bridge legacy college-admin borrowing policy endpoint."""
    from app.authorization.permissions import Permission
    from app.authorization.policy import authorize

    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    tenant_id = require_library_tenant_scope(scope)
    branch = _norm_branch(payload.branch_code)
    await _assert_branch(tenant_id, branch)
    create = BorrowingRuleCreate(
        branch_code=branch,
        max_books=payload.max_books,
        loan_days=payload.loan_days,
        renewal_limit=payload.renewal_limit,
        fine_per_day=payload.fine_per_day,
        effective_from=date.today(),
        resource_type=LibraryResourceType.ANY,
    )
    read = await create_borrowing_rule(scope, create)
    activated = await activate_borrowing_rule(scope, read.policy_id)
    return {"policy_id": activated.policy_id, "version": activated.version, "branch_code": branch}