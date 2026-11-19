"""Overdue fine calculation from circulation data."""

from datetime import date, datetime


def overdue_days(*, due_at: date, as_of: date | None = None) -> int:
    ref = as_of or date.today()
    if due_at >= ref:
        return 0
    return (ref - due_at).days


def overdue_fine_amount(
    *,
    due_at: date,
    fine_per_day: float,
    grace_days: int,
    as_of: date | None = None,
    max_days: int | None = None,
) -> tuple[int, float]:
    days = overdue_days(due_at=due_at, as_of=as_of)
    chargeable = max(0, days - grace_days)
    if max_days is not None:
        chargeable = min(chargeable, max_days)
    amount = round(chargeable * fine_per_day, 2)
    return chargeable, amount


def balance_for_fine(*, amount: float, amount_waived: float, amount_paid: float) -> float:
    return round(max(0.0, amount - amount_waived - amount_paid), 2)