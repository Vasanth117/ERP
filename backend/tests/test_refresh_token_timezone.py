"""Refresh tokens: MongoDB stores naive UTC; comparisons must not raise."""

from datetime import datetime, timedelta, timezone

from app.common.time import utc_is_past, utcnow


def test_utc_is_past_handles_naive_stored_expiry() -> None:
    future_naive = datetime(2099, 1, 1, 0, 0, 0)
    assert not utc_is_past(future_naive)
    past_naive = datetime(2020, 1, 1, 0, 0, 0)
    assert utc_is_past(past_naive)


def test_utc_is_past_handles_aware_instants() -> None:
    now = utcnow()
    assert not utc_is_past(now + timedelta(days=1))
    assert utc_is_past(now - timedelta(days=1))
    aware = datetime(2099, 6, 1, tzinfo=timezone.utc)
    assert not utc_is_past(aware)