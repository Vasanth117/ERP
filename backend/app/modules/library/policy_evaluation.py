"""Resolve effective library policies with precedence and snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.college_admin.library_admin_models import LibraryBorrowingPolicy
from app.modules.library.fine_models import LibraryFinePolicy
from app.modules.library.reservation_models import LibraryReservationPolicy
from app.modules.library.settings_enums import LibraryPolicyStatus, LibraryResourceType
from app.modules.library.settings_models import LibraryBorrowingRule


@dataclass(frozen=True)
class BorrowingPolicySnapshot:
    policy_id: str | None
    version: int | None
    max_books: int
    loan_days: int
    renewal_limit: int
    fine_per_day: float
    grace_days: int
    max_overdue_days: int | None
    max_reservations_per_member: int
    hold_hours: int
    reserve_only_when_unavailable: bool
    lost_book_charge: float
    damaged_book_charge: float
    eligibility_restrictions: tuple[str, ...]
    borrowing_restrictions: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "max_books": self.max_books,
            "loan_days": self.loan_days,
            "renewal_limit": self.renewal_limit,
            "fine_per_day": self.fine_per_day,
            "grace_days": self.grace_days,
            "max_overdue_days": self.max_overdue_days,
            "max_reservations_per_member": self.max_reservations_per_member,
            "hold_hours": self.hold_hours,
            "reserve_only_when_unavailable": self.reserve_only_when_unavailable,
            "lost_book_charge": self.lost_book_charge,
            "damaged_book_charge": self.damaged_book_charge,
            "eligibility_restrictions": list(self.eligibility_restrictions),
            "borrowing_restrictions": dict(self.borrowing_restrictions),
        }


def snapshot_from_loan(circ) -> BorrowingPolicySnapshot | None:
    raw = getattr(circ, "applied_policy_snapshot", None) or {}
    if not raw:
        return None
    return BorrowingPolicySnapshot(
        policy_id=raw.get("policy_id"),
        version=raw.get("version"),
        max_books=int(raw.get("max_books", 5)),
        loan_days=int(raw.get("loan_days", 14)),
        renewal_limit=int(raw.get("renewal_limit", 2)),
        fine_per_day=float(raw.get("fine_per_day", 5.0)),
        grace_days=int(raw.get("grace_days", 0)),
        max_overdue_days=raw.get("max_overdue_days"),
        max_reservations_per_member=int(raw.get("max_reservations_per_member", 5)),
        hold_hours=int(raw.get("hold_hours", 72)),
        reserve_only_when_unavailable=bool(raw.get("reserve_only_when_unavailable", True)),
        lost_book_charge=float(raw.get("lost_book_charge", 500.0)),
        damaged_book_charge=float(raw.get("damaged_book_charge", 150.0)),
        eligibility_restrictions=tuple(raw.get("eligibility_restrictions") or ()),
        borrowing_restrictions=dict(raw.get("borrowing_restrictions") or {}),
    )


def _norm_branch(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().upper()


def _specificity(rule: LibraryBorrowingRule, *, branch: str | None, member_category: str | None, resource_type: str | None) -> int:
    score = 0
    if rule.branch_code:
        if branch and rule.branch_code == branch:
            score += 8
        else:
            return -1
    if rule.member_category:
        if member_category and rule.member_category == member_category:
            score += 4
        else:
            return -1
    if rule.resource_type and rule.resource_type != LibraryResourceType.ANY.value:
        if resource_type and rule.resource_type == resource_type:
            score += 2
        elif resource_type is None and rule.resource_type == LibraryResourceType.PHYSICAL.value:
            score += 1
        else:
            return -1
    return score


def _legacy_snapshot(
    borrowing: LibraryBorrowingPolicy | None,
    fine: LibraryFinePolicy | None,
    reservation: LibraryReservationPolicy | None,
) -> BorrowingPolicySnapshot:
    max_books = borrowing.max_books if borrowing else 5
    loan_days = borrowing.loan_days if borrowing else 14
    renewal_limit = borrowing.renewal_limit if borrowing else 2
    fine_per_day = fine.fine_per_day if fine else (borrowing.fine_per_day if borrowing else 5.0)
    return BorrowingPolicySnapshot(
        policy_id=borrowing.policy_id if hasattr(borrowing, "policy_id") else None,
        version=borrowing.version if borrowing else None,
        max_books=max_books,
        loan_days=loan_days,
        renewal_limit=renewal_limit,
        fine_per_day=fine_per_day,
        grace_days=fine.grace_days if fine else 0,
        max_overdue_days=fine.max_overdue_days if fine else 90,
        max_reservations_per_member=reservation.max_active_per_member if reservation else 5,
        hold_hours=reservation.hold_hours if reservation else 72,
        reserve_only_when_unavailable=reservation.reserve_only_when_unavailable if reservation else True,
        lost_book_charge=fine.lost_book_charge if fine else 500.0,
        damaged_book_charge=fine.damaged_book_charge if fine else 150.0,
        eligibility_restrictions=(),
        borrowing_restrictions={},
    )


async def resolve_borrowing_policy(
    tenant_id: PydanticObjectId,
    *,
    branch_code: str | None,
    member_category: str | None = None,
    resource_type: str | None = LibraryResourceType.PHYSICAL.value,
    as_of: date | None = None,
) -> BorrowingPolicySnapshot:
    ref = as_of or date.today()
    branch = _norm_branch(branch_code)
    rows = await LibraryBorrowingRule.find(
        {
            "tenant_id": tenant_id,
            "status": LibraryPolicyStatus.ACTIVE.value,
            "effective_from": {"$lte": ref},
            "$or": [{"effective_until": None}, {"effective_until": {"$gte": ref}}],
        }
    ).to_list()
    best: LibraryBorrowingRule | None = None
    best_score = -1
    for rule in rows:
        score = _specificity(rule, branch=branch, member_category=member_category, resource_type=resource_type)
        if score > best_score:
            best_score = score
            best = rule
    if best:
        return BorrowingPolicySnapshot(
            policy_id=best.policy_id,
            version=best.version,
            max_books=best.max_books,
            loan_days=best.loan_days,
            renewal_limit=best.renewal_limit,
            fine_per_day=best.fine_per_day,
            grace_days=best.grace_days,
            max_overdue_days=best.max_overdue_days,
            max_reservations_per_member=best.max_reservations_per_member,
            hold_hours=best.hold_hours,
            reserve_only_when_unavailable=best.reserve_only_when_unavailable,
            lost_book_charge=best.lost_book_charge,
            damaged_book_charge=best.damaged_book_charge,
            eligibility_restrictions=tuple(best.eligibility_restrictions),
            borrowing_restrictions=dict(best.borrowing_restrictions),
        )
    borrowing = None
    if branch:
        borrowing = await LibraryBorrowingPolicy.find_one(
            Eq(LibraryBorrowingPolicy.tenant_id, tenant_id),
            Eq(LibraryBorrowingPolicy.branch_code, branch),
        )
    if borrowing is None:
        borrowing = await LibraryBorrowingPolicy.find_one(
            Eq(LibraryBorrowingPolicy.tenant_id, tenant_id),
            Eq(LibraryBorrowingPolicy.branch_code, None),
        )
    fine = await LibraryFinePolicy.find_one(Eq(LibraryFinePolicy.tenant_id, tenant_id), Eq(LibraryFinePolicy.branch_code, branch))
    reservation = await LibraryReservationPolicy.find_one(
        Eq(LibraryReservationPolicy.tenant_id, tenant_id), Eq(LibraryReservationPolicy.branch_code, branch)
    )
    return _legacy_snapshot(borrowing, fine, reservation)