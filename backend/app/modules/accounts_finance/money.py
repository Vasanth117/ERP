"""Monetary helpers — two-decimal INR amounts."""


def round_money(value: float) -> float:
    return round(float(value), 2)