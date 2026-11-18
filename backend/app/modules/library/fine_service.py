"""Fines, lost/damaged books and finance verification."""

from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.library_admin_models import LibraryBorrowingPolicy
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand, StudentFinancialLedgerEntry
from app.modules.library.circulation_enums import ReturnDisposition
from app.modules.library.fine_access import authorize_fine_approve, authorize_fine_read, require_fine_manage
from app.modules.library.fine_calculation import balance_for_fine, overdue_fine_amount
from app.modules.library.fine_enums import (
    LibraryFineApprovalStatus,
    LibraryFineApprovalType,
    LibraryFineRecoveryStatus,
    LibraryFineType,
)
from app.modules.library.fine_integration import on_demand_paid
from app.modules.library.fine_models import LibraryDamageReport, LibraryFineApproval, LibraryFineHistory, LibraryFinePolicy
from app.modules.library.fine_schemas import (
    DamageReportCreate,
    FineApprovalDecision,
    FineHistoryEntry,
    FinePaymentVerifyRequest,
    FinePolicyUpsert,
    FineRead,
    FineWaiverRequest,
)
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCirculation, LibraryCopy, LibraryFine
from app.modules.library.policy import require_library_tenant_scope


def _norm_branch(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().upper()


async def _policy(tenant_id: PydanticObjectId, branch_code: str | None) -> LibraryFinePolicy:
    branch = _norm_branch(branch_code)
    doc = await LibraryFinePolicy.find_one(Eq(LibraryFinePolicy.tenant_id, tenant_id), Eq(LibraryFinePolicy.branch_code, branch))
    if doc:
        return doc
    borrowing = await LibraryBorrowingPolicy.find_one(
        Eq(LibraryBorrowingPolicy.tenant_id, tenant_id),
        Eq(LibraryBorrowingPolicy.branch_code, branch),
    )
    base = LibraryFinePolicy(tenant_id=tenant_id, branch_code=branch)
    if borrowing:
        base.fine_per_day = borrowing.fine_per_day
    return base


async def _history(tenant_id: PydanticObjectId, *, fine_id: str, action: str, actor_id: PydanticObjectId | None, changes: dict[str, Any]) -> None:
    await LibraryFineHistory(
        tenant_id=tenant_id,
        fine_id=fine_id,
        action=action,
        actor_id=actor_id,
        changes=changes,
    ).insert()


def _effective_balance(doc: LibraryFine) -> float:
    bal = doc.balance if doc.balance is not None else balance_for_fine(
        amount=doc.amount, amount_waived=doc.amount_waived, amount_paid=doc.amount_paid
    )
    if bal <= 0 and doc.status == LibraryFineStatus.OPEN and doc.amount > 0:
        return round(float(doc.amount), 2)
    return bal


def _to_read(doc: LibraryFine) -> FineRead:
    return FineRead(
        fine_id=doc.fine_id,
        member_user_id=str(doc.student_user_id),
        fine_type=doc.fine_type,
        book_id=doc.book_id,
        copy_id=doc.copy_id,
        branch_code=doc.branch_code,
        circulation_id=doc.circulation_id,
        amount=doc.amount,
        amount_waived=doc.amount_waived,
        amount_paid=doc.amount_paid,
        balance=_effective_balance(doc),
        reason=doc.reason,
        status=doc.status,
        recovery_status=doc.recovery_status,
        demand_id=doc.demand_id,
        payment_transaction_id=doc.payment_transaction_id,
        due_date=doc.due_date,
        assessed_at=doc.assessed_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def _post_ledger_debit(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    amount: float,
    fine_id: str,
) -> None:
    last = (
        await StudentFinancialLedgerEntry.find({"tenant_id": tenant_id, "student_user_id": student_user_id})
        .sort("-posted_at")
        .limit(1)
        .to_list()
    )
    balance = last[0].balance_after if last else 0.0
    await StudentFinancialLedgerEntry(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        entry_id=f"led_{uuid4().hex}",
        entry_type="library_fine",
        description=f"Library fine {fine_id}",
        debit=amount,
        credit=0,
        balance_after=balance + amount,
        reference_id=fine_id,
        posted_at=utcnow(),
    ).insert()


async def upsert_fine_policy(scope: AccessScope, payload: FinePolicyUpsert) -> dict:
    tenant_id = require_library_tenant_scope(scope)
    await require_fine_manage(scope, branch_code=payload.branch_code)
    branch = _norm_branch(payload.branch_code)
    doc = await LibraryFinePolicy.find_one(Eq(LibraryFinePolicy.tenant_id, tenant_id), Eq(LibraryFinePolicy.branch_code, branch))
    if doc:
        doc.fine_per_day = payload.fine_per_day
        doc.grace_days = payload.grace_days
        doc.max_overdue_days = payload.max_overdue_days
        doc.lost_book_charge = payload.lost_book_charge
        doc.damaged_book_charge = payload.damaged_book_charge
        doc.replacement_charge = payload.replacement_charge
        doc.updated_at = utcnow()
        doc.updated_by = scope.user_id
        await doc.save()
    else:
        await LibraryFinePolicy(
            tenant_id=tenant_id,
            branch_code=branch,
            fine_per_day=payload.fine_per_day,
            grace_days=payload.grace_days,
            max_overdue_days=payload.max_overdue_days,
            lost_book_charge=payload.lost_book_charge,
            damaged_book_charge=payload.damaged_book_charge,
            replacement_charge=payload.replacement_charge,
            updated_by=scope.user_id,
        ).insert()
    return {"branch_code": branch}


async def assess_overdue_for_circulation(
    tenant_id: PydanticObjectId,
    circulation_id: str,
    *,
    actor_id: PydanticObjectId | None,
    returned_at: date | None = None,
) -> LibraryFine | None:
    circ = await LibraryCirculation.find_one(
        Eq(LibraryCirculation.tenant_id, tenant_id),
        Eq(LibraryCirculation.circulation_id, circulation_id),
    )
    if circ is None:
        return None
    as_of = returned_at or (circ.returned_at.date() if circ.returned_at else date.today())
    policy = await _policy(tenant_id, circ.branch_code)
    _, amount = overdue_fine_amount(
        due_at=circ.due_at,
        fine_per_day=policy.fine_per_day,
        grace_days=policy.grace_days,
        as_of=as_of,
        max_days=policy.max_overdue_days,
    )
    if amount <= 0:
        return None
    existing = await LibraryFine.find_one(
        {
            "tenant_id": tenant_id,
            "circulation_id": circulation_id,
            "fine_type": LibraryFineType.OVERDUE.value,
            "status": {"$nin": [LibraryFineStatus.WAIVED.value, LibraryFineStatus.WRITTEN_OFF.value]},
        }
    )
    if existing:
        if amount > existing.amount:
            existing.amount = amount
            existing.balance = balance_for_fine(amount=existing.amount, amount_waived=existing.amount_waived, amount_paid=existing.amount_paid)
            existing.updated_at = utcnow()
            await existing.save()
        return existing
    fine_id = f"fine_{uuid4().hex[:12]}"
    doc = LibraryFine(
        tenant_id=tenant_id,
        fine_id=fine_id,
        student_user_id=circ.student_user_id,
        circulation_id=circulation_id,
        book_id=circ.book_id,
        copy_id=circ.copy_id,
        branch_code=circ.branch_code,
        fine_type=LibraryFineType.OVERDUE.value,
        amount=amount,
        balance=amount,
        reason=f"Overdue return ({circ.title})",
        status=LibraryFineStatus.OPEN,
        recovery_status=LibraryFineRecoveryStatus.OPEN.value,
        due_date=as_of + timedelta(days=14),
        created_by=actor_id,
        updated_by=actor_id,
    )
    await doc.insert()
    await _history(tenant_id, fine_id=fine_id, action="assess_overdue", actor_id=actor_id, changes={"amount": amount})
    await _post_ledger_debit(tenant_id, student_user_id=circ.student_user_id, amount=amount, fine_id=fine_id)
    from app.modules.library.notification_triggers import on_fine_assessed

    await on_fine_assessed(tenant_id, doc)
    return doc


async def process_return_fines(
    tenant_id: PydanticObjectId,
    *,
    circulation_id: str,
    disposition: ReturnDisposition,
    actor_id: PydanticObjectId | None,
) -> None:
    circ = await LibraryCirculation.find_one(Eq(LibraryCirculation.tenant_id, tenant_id), Eq(LibraryCirculation.circulation_id, circulation_id))
    if circ is None:
        return
    returned_at = circ.returned_at.date() if circ.returned_at else date.today()
    if returned_at > circ.due_at or circ.status == LibraryCirculationStatus.OVERDUE:
        await assess_overdue_for_circulation(tenant_id, circulation_id, actor_id=actor_id, returned_at=returned_at)
    if disposition == ReturnDisposition.GOOD:
        return
    policy = await _policy(tenant_id, circ.branch_code)
    if disposition == ReturnDisposition.LOST:
        amount = policy.lost_book_charge
        fine_type = LibraryFineType.LOST
        reason = f"Lost book ({circ.title})"
    else:
        amount = policy.damaged_book_charge
        fine_type = LibraryFineType.DAMAGED
        reason = f"Damaged book ({circ.title})"
    fine_id = f"fine_{uuid4().hex[:12]}"
    doc = LibraryFine(
        tenant_id=tenant_id,
        fine_id=fine_id,
        student_user_id=circ.student_user_id,
        circulation_id=circulation_id,
        book_id=circ.book_id,
        copy_id=circ.copy_id,
        branch_code=circ.branch_code,
        fine_type=fine_type.value,
        amount=amount,
        balance=amount,
        reason=reason,
        status=LibraryFineStatus.OPEN,
        recovery_status=LibraryFineRecoveryStatus.OPEN.value,
        created_by=actor_id,
        updated_by=actor_id,
    )
    await doc.insert()
    from app.modules.library.notification_triggers import on_fine_assessed

    await on_fine_assessed(tenant_id, doc)
    report_id = f"dmg_{uuid4().hex[:10]}"
    await LibraryDamageReport(
        tenant_id=tenant_id,
        report_id=report_id,
        fine_id=fine_id,
        circulation_id=circulation_id,
        copy_id=circ.copy_id,
        book_id=circ.book_id,
        branch_code=circ.branch_code,
        member_user_id=circ.student_user_id,
        report_type=fine_type.value,
        description=reason,
        replacement_cost=amount,
        created_by=actor_id,
    ).insert()
    await _history(tenant_id, fine_id=fine_id, action="damage_report", actor_id=actor_id, changes={"report_id": report_id, "amount": amount})
    await _post_ledger_debit(tenant_id, student_user_id=circ.student_user_id, amount=amount, fine_id=fine_id)


async def create_damage_report(scope: AccessScope, payload: DamageReportCreate) -> FineRead:
    tenant_id = require_library_tenant_scope(scope)
    member_id = to_object_id(payload.member_user_id, "member_user_id")
    copy = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.copy_id, payload.copy_id.strip()))
    if copy is None:
        raise AppError(code="NOT_FOUND", message="Copy not found", status_code=404)
    await require_fine_manage(scope, branch_code=copy.branch_code)
    policy = await _policy(tenant_id, copy.branch_code)
    if payload.report_type == LibraryFineType.LOST:
        amount = payload.replacement_cost if payload.replacement_cost is not None else policy.lost_book_charge
    elif payload.report_type == LibraryFineType.DAMAGED:
        amount = payload.replacement_cost if payload.replacement_cost is not None else policy.damaged_book_charge
    else:
        amount = payload.replacement_cost if payload.replacement_cost is not None else policy.replacement_charge
    fine_id = f"fine_{uuid4().hex[:12]}"
    doc = LibraryFine(
        tenant_id=tenant_id,
        fine_id=fine_id,
        student_user_id=member_id,
        circulation_id=payload.circulation_id,
        book_id=copy.book_id,
        copy_id=copy.copy_id,
        branch_code=copy.branch_code,
        fine_type=payload.report_type.value,
        amount=amount,
        balance=amount,
        reason=payload.description.strip(),
        status=LibraryFineStatus.OPEN,
        recovery_status=LibraryFineRecoveryStatus.OPEN.value,
        created_by=scope.user_id,
        updated_by=scope.user_id,
    )
    await doc.insert()
    report_id = payload.report_id or f"dmg_{uuid4().hex[:10]}"
    await LibraryDamageReport(
        tenant_id=tenant_id,
        report_id=report_id,
        fine_id=fine_id,
        circulation_id=payload.circulation_id,
        copy_id=copy.copy_id,
        book_id=copy.book_id,
        branch_code=copy.branch_code,
        member_user_id=member_id,
        report_type=payload.report_type.value,
        description=payload.description.strip(),
        replacement_cost=amount,
        created_by=scope.user_id,
    ).insert()
    await _history(tenant_id, fine_id=fine_id, action="create_report", actor_id=scope.user_id, changes={"report_id": report_id})
    await _post_ledger_debit(tenant_id, student_user_id=member_id, amount=amount, fine_id=fine_id)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_fine.report",
        module="library_fines",
        resource_type="fine",
        resource_id=fine_id,
    )
    return _to_read(doc)


async def create_finance_demand(scope: AccessScope, fine_id: str) -> FineRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryFine.find_one(Eq(LibraryFine.tenant_id, tenant_id), Eq(LibraryFine.fine_id, fine_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fine not found", status_code=404)
    await require_fine_manage(scope, branch_code=doc.branch_code)
    if doc.demand_id:
        return _to_read(doc)
    bal = _effective_balance(doc)
    if bal <= 0:
        raise AppError(code="CONFLICT", message="No balance to demand", status_code=409)
    demand_id = f"libfd_{uuid4().hex[:10]}"
    await StudentFeeDemand(
        tenant_id=tenant_id,
        student_user_id=doc.student_user_id,
        demand_id=demand_id,
        academic_year_label="library",
        semester_label="fine",
        description=f"Library fine {fine_id}: {doc.reason[:120]}",
        amount=bal,
        due_date=doc.due_date or (date.today() + timedelta(days=14)),
        status=FeeDemandStatus.OPEN,
    ).insert()
    doc.demand_id = demand_id
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await _history(tenant_id, fine_id=fine_id, action="create_demand", actor_id=scope.user_id, changes={"demand_id": demand_id})
    return _to_read(doc)


async def verify_fine_payment(scope: AccessScope, fine_id: str, payload: FinePaymentVerifyRequest) -> FineRead:
    """Mark paid only when finance has a verified successful transaction."""
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryFine.find_one(Eq(LibraryFine.tenant_id, tenant_id), Eq(LibraryFine.fine_id, fine_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fine not found", status_code=404)
    await require_fine_manage(scope, branch_code=doc.branch_code)
    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, payload.transaction_id.strip()),
    )
    if tx is None:
        raise AppError(code="NOT_FOUND", message="Payment transaction not found", status_code=404)
    if tx.status != PaymentTransactionStatus.SUCCESS or not tx.webhook_verified:
        raise AppError(code="CONFLICT", message="Payment not verified by finance", status_code=409)
    if doc.demand_id and tx.demand_id and tx.demand_id != doc.demand_id:
        raise AppError(code="VALIDATION_ERROR", message="Transaction demand mismatch", status_code=422)
    if tx.student_user_id != doc.student_user_id:
        raise AppError(code="VALIDATION_ERROR", message="Transaction member mismatch", status_code=422)
    if doc.demand_id:
        await on_demand_paid(tenant_id, doc.demand_id, payload.transaction_id)
    else:
        doc.amount_paid = round(doc.amount_paid + tx.amount, 2)
        doc.balance = balance_for_fine(amount=doc.amount, amount_waived=doc.amount_waived, amount_paid=doc.amount_paid)
        doc.payment_transaction_id = payload.transaction_id
        if doc.balance <= 0:
            doc.status = LibraryFineStatus.PAID
            doc.recovery_status = LibraryFineRecoveryStatus.RECOVERED.value
        doc.updated_at = utcnow()
        doc.updated_by = scope.user_id
        await doc.save()
    await _history(
        tenant_id,
        fine_id=fine_id,
        action="payment_record",
        actor_id=scope.user_id,
        changes={"transaction_id": payload.transaction_id},
    )
    refreshed = await LibraryFine.find_one(Eq(LibraryFine.tenant_id, tenant_id), Eq(LibraryFine.fine_id, fine_id))
    assert refreshed is not None
    return _to_read(refreshed)


async def request_waiver(scope: AccessScope, fine_id: str, payload: FineWaiverRequest, *, approval_type: LibraryFineApprovalType) -> FineRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryFine.find_one(Eq(LibraryFine.tenant_id, tenant_id), Eq(LibraryFine.fine_id, fine_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fine not found", status_code=404)
    await require_fine_manage(scope, branch_code=doc.branch_code)
    if doc.status not in (LibraryFineStatus.OPEN, LibraryFineStatus.PENDING_WAIVER, LibraryFineStatus.PENDING_WRITEOFF):
        raise AppError(code="CONFLICT", message="Fine cannot enter approval", status_code=409)
    approval_id = f"fap_{uuid4().hex[:10]}"
    pending = LibraryFineApprovalStatus.PENDING
    await LibraryFineApproval(
        tenant_id=tenant_id,
        approval_id=approval_id,
        fine_id=fine_id,
        approval_type=approval_type,
        status=pending,
        reason=payload.reason.strip(),
        requested_by=scope.user_id,
    ).insert()
    doc.status = (
        LibraryFineStatus.PENDING_WAIVER if approval_type == LibraryFineApprovalType.WAIVER else LibraryFineStatus.PENDING_WRITEOFF
    )
    doc.approval_id = approval_id
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await _history(tenant_id, fine_id=fine_id, action="approval_request", actor_id=scope.user_id, changes={"approval_id": approval_id})
    return _to_read(doc)


async def decide_approval(scope: AccessScope, fine_id: str, payload: FineApprovalDecision) -> FineRead:
    authorize_fine_approve(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryFine.find_one(Eq(LibraryFine.tenant_id, tenant_id), Eq(LibraryFine.fine_id, fine_id))
    if doc is None or not doc.approval_id:
        raise AppError(code="NOT_FOUND", message="Fine or approval not found", status_code=404)
    approval = await LibraryFineApproval.find_one(
        Eq(LibraryFineApproval.tenant_id, tenant_id),
        Eq(LibraryFineApproval.approval_id, doc.approval_id),
        Eq(LibraryFineApproval.status, LibraryFineApprovalStatus.PENDING),
    )
    if approval is None:
        raise AppError(code="CONFLICT", message="No pending approval", status_code=409)
    if approval.requested_by == scope.user_id:
        raise AppError(code="FORBIDDEN", message="Approver must differ from requester", status_code=403)
    now = utcnow()
    approval.decided_by = scope.user_id
    approval.decided_at = now
    approval.decision_note = payload.note
    if not payload.approved:
        approval.status = LibraryFineApprovalStatus.REJECTED
        doc.status = LibraryFineStatus.OPEN
        doc.approval_id = None
    else:
        approval.status = LibraryFineApprovalStatus.APPROVED
        if approval.approval_type == LibraryFineApprovalType.WAIVER:
            doc.amount_waived = doc.amount
            doc.balance = balance_for_fine(amount=doc.amount, amount_waived=doc.amount_waived, amount_paid=doc.amount_paid)
            doc.status = LibraryFineStatus.WAIVED
            doc.recovery_status = LibraryFineRecoveryStatus.RECOVERED.value
        else:
            doc.status = LibraryFineStatus.WRITTEN_OFF
            doc.recovery_status = LibraryFineRecoveryStatus.WRITTEN_OFF.value
            doc.balance = 0
        doc.approval_id = None
    await approval.save()
    doc.updated_at = now
    doc.updated_by = scope.user_id
    await doc.save()
    await _history(
        tenant_id,
        fine_id=fine_id,
        action="approval_decision",
        actor_id=scope.user_id,
        changes={"approved": payload.approved},
    )
    return _to_read(doc)


async def get_fine(scope: AccessScope, fine_id: str) -> FineRead:
    authorize_fine_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryFine.find_one(Eq(LibraryFine.tenant_id, tenant_id), Eq(LibraryFine.fine_id, fine_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fine not found", status_code=404)
    return _to_read(doc)


async def search_fines(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str | None = None,
    member_user_id: str | None = None,
    status: LibraryFineStatus | None = None,
) -> Page[FineRead]:
    authorize_fine_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if branch_code:
        filters["branch_code"] = _norm_branch(branch_code)
    if member_user_id:
        filters["student_user_id"] = to_object_id(member_user_id, "member_user_id")
    if status:
        filters["status"] = status.value
    query = LibraryFine.find(filters).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_to_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def fine_history(scope: AccessScope, fine_id: str, pagination: Pagination) -> Page[FineHistoryEntry]:
    authorize_fine_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    query = LibraryFineHistory.find(
        Eq(LibraryFineHistory.tenant_id, tenant_id),
        Eq(LibraryFineHistory.fine_id, fine_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        FineHistoryEntry(action=r.action, actor_id=str(r.actor_id) if r.actor_id else None, changes=r.changes, created_at=r.created_at)
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def assess_overdue_batch(scope: AccessScope, *, branch_code: str | None = None) -> dict:
    tenant_id = require_library_tenant_scope(scope)
    await require_fine_manage(scope, branch_code=branch_code)
    match: dict[str, Any] = {
        "tenant_id": tenant_id,
        "status": {"$in": [LibraryCirculationStatus.OVERDUE.value, LibraryCirculationStatus.ACTIVE.value]},
    }
    if branch_code:
        match["branch_code"] = _norm_branch(branch_code)
    rows = await LibraryCirculation.find(match).to_list()
    created = 0
    for row in rows:
        if row.due_at >= date.today():
            continue
        result = await assess_overdue_for_circulation(tenant_id, row.circulation_id, actor_id=scope.user_id)
        if result:
            created += 1
    return {"assessed": created}


async def college_admin_decide_fine(scope: AccessScope, fine_id: str, decision: LibraryFineStatus, note: str | None) -> dict:
    """Backward-compatible college admin endpoint."""
    tenant_id = require_library_tenant_scope(scope)
    if decision == LibraryFineStatus.WAIVED:
        authorize_fine_approve(scope)
        doc = await LibraryFine.find_one(Eq(LibraryFine.tenant_id, tenant_id), Eq(LibraryFine.fine_id, fine_id))
        if doc is None:
            raise AppError(code="NOT_FOUND", message="Fine not found", status_code=404)
        doc.amount_waived = doc.amount
        doc.balance = 0
        doc.status = LibraryFineStatus.WAIVED
        doc.recovery_status = LibraryFineRecoveryStatus.RECOVERED.value
        doc.updated_at = utcnow()
        doc.updated_by = scope.user_id
        await doc.save()
        await _history(tenant_id, fine_id=fine_id, action="waive", actor_id=scope.user_id, changes={"note": note})
        return {"fine_id": fine_id, "status": doc.status.value}
    if decision == LibraryFineStatus.PAID:
        raise AppError(code="VALIDATION_ERROR", message="Use payment verification with transaction_id", status_code=422)
    raise AppError(code="VALIDATION_ERROR", message="Unsupported decision", status_code=422)