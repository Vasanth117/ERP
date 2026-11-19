"""Decimal salary structure calculations — no statutory rate hardcoding."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.modules.hr.enums import HrSalaryCalcType, HrSalaryComponentCategory


def _d(value: str | float | int) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_structure(
    *,
    component_defs: list[dict[str, Any]],
    amounts: dict[str, str],
) -> dict[str, str]:
    earnings = Decimal("0")
    deductions = Decimal("0")
    employer = Decimal("0")
    computed: dict[str, Decimal] = {}

    for line in component_defs:
        code = str(line["component_code"])
        category = line.get("category", HrSalaryComponentCategory.EARNING.value)
        calc_type = line.get("calc_type", HrSalaryCalcType.FIXED.value)
        if code in amounts:
            computed[code] = _d(amounts[code])
        elif calc_type == HrSalaryCalcType.PERCENTAGE.value:
            basis = line.get("percentage_of") or "basic"
            basis_amount = computed.get(basis, Decimal("0"))
            pct = _d(line.get("percentage", "0"))
            computed[code] = (basis_amount * pct / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            computed[code] = Decimal("0")

        if line.get("employer_contribution"):
            employer += computed[code]
        elif category == HrSalaryComponentCategory.DEDUCTION.value:
            deductions += computed[code]
        else:
            earnings += computed[code]

    gross = earnings
    net = earnings - deductions
    annual = gross * Decimal("12")
    return {
        "earnings_total": _money(earnings),
        "deductions_total": _money(deductions),
        "gross_salary": _money(gross),
        "net_salary": _money(net),
        "employer_contributions_total": _money(employer),
        "annual_compensation": _money(annual),
        "ctc": _money(annual + employer),
        "computed_amounts": {k: _money(v) for k, v in computed.items()},
    }


def diff_amounts(before: dict[str, str], after: dict[str, str]) -> dict[str, str]:
    keys = set(before) | set(after)
    diff: dict[str, str] = {}
    for key in keys:
        delta = _d(after.get(key, "0")) - _d(before.get(key, "0"))
        if delta != 0:
            diff[key] = _money(delta)
    return diff