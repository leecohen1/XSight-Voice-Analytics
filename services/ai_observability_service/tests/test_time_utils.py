"""Tests for app/time_utils.py — UTC period boundaries, never server-local time."""
from datetime import datetime, timezone

from app.time_utils import days_in_month, month_bounds, resolve_period, today_bounds


def test_today_bounds_is_midnight_to_midnight_utc():
    now = datetime(2026, 7, 27, 15, 30, 0, tzinfo=timezone.utc)
    start, end = today_bounds(now)
    assert start == "2026-07-27T00:00:00+00:00"
    assert end == "2026-07-28T00:00:00+00:00"


def test_today_bounds_exact_midnight_belongs_to_that_day():
    now = datetime(2026, 7, 27, 0, 0, 0, tzinfo=timezone.utc)
    start, _ = today_bounds(now)
    assert start == "2026-07-27T00:00:00+00:00"


def test_month_bounds_mid_month():
    now = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    start, end = month_bounds(now)
    assert start == "2026-07-01T00:00:00+00:00"
    assert end == "2026-08-01T00:00:00+00:00"


def test_month_bounds_december_rolls_to_next_year():
    now = datetime(2026, 12, 15, 12, 0, 0, tzinfo=timezone.utc)
    start, end = month_bounds(now)
    assert start == "2026-12-01T00:00:00+00:00"
    assert end == "2027-01-01T00:00:00+00:00"


def test_month_bounds_first_of_month():
    now = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    start, end = month_bounds(now)
    assert start == "2026-07-01T00:00:00+00:00"
    assert end == "2026-08-01T00:00:00+00:00"


def test_resolve_period_explicit_range_wins_over_range_param():
    start, end = resolve_period("today", "2026-01-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00")
    assert start == "2026-01-01T00:00:00+00:00"
    assert end == "2026-02-01T00:00:00+00:00"


def test_days_in_month_february_non_leap():
    assert days_in_month("2026-02-01T00:00:00+00:00") == 28


def test_days_in_month_thirty_one_day_month():
    assert days_in_month("2026-07-01T00:00:00+00:00") == 31
