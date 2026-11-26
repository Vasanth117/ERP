"""Shared payroll section navigation (CA 11 — Payroll)."""

from __future__ import annotations

from decimal import Decimal

from app.modules.college_admin.schemas import HrRecruitmentSubNavItem

HR_PAYROLL_SUB_NAV: list[HrRecruitmentSubNavItem] = [
    HrRecruitmentSubNavItem(
        key="salary-structure",
        label="Salary structure",
        href="/college-admin/hr/salary-structure-management",
    ),
    HrRecruitmentSubNavItem(
        key="payroll-processing",
        label="Payroll processing",
        href="/college-admin/hr/payroll-processing",
    ),
    HrRecruitmentSubNavItem(
        key="salary-slips",
        label="Salary slips",
        href="/college-admin/hr/salary-slip-management",
    ),
]

_EXCEPTION_LABELS: dict[str, str] = {
    "missing_salary_structure": "Missing salary structure",
    "negative_net_salary": "Negative net salary",
    "unapproved_absence": "Unapproved absence",
    "probation_confirmation": "Probation confirmation",
}


def humanize_payroll_exception(code: str) -> str:
    cleaned = (code or "").strip()
    if not cleaned:
        return "Payroll exception"
    if cleaned in _EXCEPTION_LABELS:
        return _EXCEPTION_LABELS[cleaned]
    return cleaned.replace("_", " ").strip().capitalize()


def format_inr_compact(amount: Decimal | float) -> str:
    value = float(amount)
    if value >= 10_000_000:
        return f"₹{value / 10_000_000:.2f} Cr"
    if value >= 100_000:
        return f"₹{value / 100_000:.1f} L"
    rupees = int(round(value))
    s = str(rupees)
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    rest = s[:-3]
    groups: list[str] = []
    while rest:
        take = 2 if len(rest) > 2 else len(rest)
        groups.insert(0, rest[-take:])
        rest = rest[:-take]
    return f"₹{','.join(groups + [last3])}"