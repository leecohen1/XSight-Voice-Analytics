"""outcome_distribution: the Overview outcome-mix contract.

The one invariant every test here ultimately checks: the four/five buckets
always sum to len(records) for the same window. Nothing may be silently
excluded the way close_rate excludes "Uncertain" -- a call with an unknown
or missing outcome must still be counted, just under `unknown`, so the
frontend donut can always be reconciled against `calls_analyzed`.
"""
from datetime import datetime, timezone

from app.aggregation import build_overview, outcome_distribution
from app.repository import window_bounds
from conftest import make_record

NOW = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)


def _total(dist) -> int:
    return dist.sale + dist.no_sale + dist.follow_up + dist.uncertain + dist.unknown


def test_counts_each_known_outcome_into_its_own_bucket():
    records = [
        make_record("CALL_001", call_outcome="Sale"),
        make_record("CALL_002", call_outcome="No Sale"),
        make_record("CALL_003", call_outcome="Follow-up Needed"),
        make_record("CALL_004", call_outcome="Uncertain"),
    ]
    dist = outcome_distribution(records)
    assert dist.sale == 1
    assert dist.no_sale == 1
    assert dist.follow_up == 1
    assert dist.uncertain == 1
    assert dist.unknown == 0


def test_matching_is_case_insensitive():
    records = [make_record("CALL_001", call_outcome="Sale"), make_record("CALL_002", call_outcome="Sale")]
    dist = outcome_distribution(records)
    assert dist.sale == 2


def test_missing_outcome_counts_as_unknown_rather_than_being_dropped():
    records = [make_record("CALL_001", call_outcome=None), make_record("CALL_002", call_outcome="Sale")]
    dist = outcome_distribution(records)
    assert dist.unknown == 1
    assert dist.sale == 1
    # The invariant: nothing was silently excluded.
    assert _total(dist) == len(records)


def test_empty_window_is_all_zero_not_missing():
    dist = outcome_distribution([])
    assert dist.sale == dist.no_sale == dist.follow_up == dist.uncertain == dist.unknown == 0


def test_distribution_always_sums_to_the_record_count():
    records = [
        make_record("CALL_001", call_outcome="Sale"),
        make_record("CALL_002", call_outcome="No Sale"),
        make_record("CALL_003", call_outcome=None),
        make_record("CALL_004", call_outcome="Uncertain"),
        make_record("CALL_005", call_outcome="Follow-up Needed"),
    ]
    dist = outcome_distribution(records)
    assert _total(dist) == len(records)
    assert dist.unknown == 1  # only the None case


def test_build_overview_includes_outcome_distribution_reconciled_with_calls_analyzed():
    records = [
        make_record("CALL_001", call_outcome="Sale", days_ago=1),
        make_record("CALL_002", call_outcome="No Sale", days_ago=2),
        make_record("CALL_003", call_outcome="Follow-up Needed", days_ago=3),
    ]
    start, end, prev_start, prev_end = window_bounds("7d", NOW)
    overview = build_overview(
        all_records=records,
        skipped_count=0,
        period="7d",
        current_start=start,
        current_end=end,
        previous_start=prev_start,
        previous_end=prev_end,
        generated_at=NOW,
    )
    assert _total(overview.outcome_distribution) == overview.kpis.calls_analyzed.current_value
    assert overview.outcome_distribution.sale == 1
    assert overview.outcome_distribution.no_sale == 1
    assert overview.outcome_distribution.follow_up == 1


def test_build_overview_outcome_distribution_only_reflects_the_current_window():
    records = [
        make_record("CALL_001", call_outcome="Sale", days_ago=1),  # current 7d window
        make_record("CALL_002", call_outcome="No Sale", days_ago=20),  # previous window only
    ]
    start, end, prev_start, prev_end = window_bounds("7d", NOW)
    overview = build_overview(
        all_records=records,
        skipped_count=0,
        period="7d",
        current_start=start,
        current_end=end,
        previous_start=prev_start,
        previous_end=prev_end,
        generated_at=NOW,
    )
    assert overview.outcome_distribution.sale == 1
    assert overview.outcome_distribution.no_sale == 0
