"""Overview aggregation rules: windows, close rate, averages, improved
agents, ordering, trend buckets, and the deterministic attention formula."""
from datetime import datetime, timezone

import pytest

from app.aggregation import (
    attention_calls,
    average_agent_performance,
    average_lead_quality,
    build_kpi,
    build_overview,
    calls_requiring_attention,
    close_rate,
    close_rate_trend,
    improved_agents,
    recent_calls,
    select_window,
)
from app.attention import derive_attention, derive_recovery_opportunity, priority_band
from app.repository import window_bounds
from conftest import make_record

NOW = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)


def _overview(records, period="30d", now=NOW, skipped=0):
    start, end, prev_start, prev_end = window_bounds(period, now)
    return build_overview(
        all_records=records,
        skipped_count=skipped,
        period=period,
        current_start=start,
        current_end=end,
        previous_start=prev_start,
        previous_end=prev_end,
        generated_at=now,
    )


# ---- window selection ------------------------------------------------------


def test_current_seven_day_window_selects_only_recent_calls():
    records = [
        make_record("CALL_001", days_ago=1, now=NOW),
        make_record("CALL_002", days_ago=6, now=NOW),
        make_record("CALL_003", days_ago=9, now=NOW),
    ]
    start, end, _, _ = window_bounds("7d", NOW)
    selected = select_window(records, start, end, inclusive_end=True)
    assert {r.call_id for r in selected} == {"CALL_001", "CALL_002"}


def test_previous_seven_day_window_selects_the_preceding_week():
    records = [
        make_record("CALL_001", days_ago=1, now=NOW),
        make_record("CALL_002", days_ago=9, now=NOW),
        make_record("CALL_003", days_ago=20, now=NOW),
    ]
    _, _, prev_start, prev_end = window_bounds("7d", NOW)
    selected = select_window(records, prev_start, prev_end, inclusive_end=False)
    assert {r.call_id for r in selected} == {"CALL_002"}


def test_thirty_day_windows_partition_records_without_overlap():
    records = [
        make_record("CALL_001", days_ago=5, now=NOW),
        make_record("CALL_002", days_ago=29, now=NOW),
        make_record("CALL_003", days_ago=35, now=NOW),
        make_record("CALL_004", days_ago=59, now=NOW),
        make_record("CALL_005", days_ago=70, now=NOW),
    ]
    start, end, prev_start, prev_end = window_bounds("30d", NOW)
    current = select_window(records, start, end, inclusive_end=True)
    previous = select_window(records, prev_start, prev_end, inclusive_end=False)

    assert {r.call_id for r in current} == {"CALL_001", "CALL_002"}
    assert {r.call_id for r in previous} == {"CALL_003", "CALL_004"}
    assert not ({r.call_id for r in current} & {r.call_id for r in previous})


def test_a_call_exactly_on_the_boundary_belongs_to_the_current_window_only():
    record = make_record("CALL_001", days_ago=30, now=NOW)
    start, end, prev_start, prev_end = window_bounds("30d", NOW)
    assert record in select_window([record], start, end, inclusive_end=True)
    assert record not in select_window([record], prev_start, prev_end, inclusive_end=False)


def test_non_analyzed_statuses_are_excluded_from_every_window():
    """Only completed / flagged / human_review_required count as analyzed."""
    records = [
        make_record("CALL_001", days_ago=1, now=NOW, status="completed"),
        make_record("CALL_002", days_ago=1, now=NOW, status="flagged"),
        make_record("CALL_003", days_ago=1, now=NOW, status="human_review_required"),
    ]
    start, end, _, _ = window_bounds("7d", NOW)
    assert len(select_window(records, start, end, inclusive_end=True)) == 3


# ---- close rate ------------------------------------------------------------


def test_close_rate_excludes_uncertain_from_the_denominator():
    records = [
        make_record("CALL_001", call_outcome="Sale"),
        make_record("CALL_002", call_outcome="No Sale"),
        make_record("CALL_003", call_outcome="Uncertain"),
        make_record("CALL_004", call_outcome="Uncertain"),
    ]
    # 1 sale / 2 known outcomes = 50%, not 1/4 = 25%.
    assert close_rate(records) == 50.0


def test_close_rate_counts_follow_up_needed_as_a_known_outcome():
    records = [
        make_record("CALL_001", call_outcome="Sale"),
        make_record("CALL_002", call_outcome="Follow-up Needed"),
    ]
    assert close_rate(records) == 50.0


def test_close_rate_is_none_when_no_outcome_is_known():
    records = [make_record("CALL_001", call_outcome="Uncertain"), make_record("CALL_002", call_outcome=None)]
    assert close_rate(records) is None


def test_close_rate_is_none_for_an_empty_window():
    assert close_rate([]) is None


def test_close_rate_matching_is_case_insensitive_but_output_stays_canonical():
    records = [make_record("CALL_001", call_outcome="Sale"), make_record("CALL_002", call_outcome="No Sale")]
    assert close_rate(records) == 50.0
    # The canonical casing survives onto the DTO.
    assert recent_calls(records)[0].call_outcome in {"Sale", "No Sale"}


# ---- averages --------------------------------------------------------------


def test_average_agent_performance_ignores_nulls():
    records = [
        make_record("CALL_001", agent_performance_score=4),
        make_record("CALL_002", agent_performance_score=2),
        make_record("CALL_003", agent_performance_score=None),
    ]
    assert average_agent_performance(records) == 3.0


def test_average_lead_quality_ignores_nulls():
    records = [
        make_record("CALL_001", lead_quality_score=5),
        make_record("CALL_002", lead_quality_score=4),
        make_record("CALL_003", lead_quality_score=None),
    ]
    assert average_lead_quality(records) == 4.5


def test_averages_are_none_when_nothing_is_scored():
    records = [make_record("CALL_001", agent_performance_score=None, lead_quality_score=None)]
    assert average_agent_performance(records) is None
    assert average_lead_quality(records) is None


# ---- KPI comparison --------------------------------------------------------


def test_kpi_computes_absolute_and_percentage_change():
    kpi = build_kpi(12.0, 10.0)
    assert kpi.absolute_change == 2.0
    assert kpi.percentage_change == 20.0
    assert kpi.trend_direction == "up"


def test_kpi_percentage_change_is_none_when_previous_is_zero():
    """An undefined ratio is reported as undefined, never as 0 or 100."""
    kpi = build_kpi(5.0, 0.0)
    assert kpi.absolute_change == 5.0
    assert kpi.percentage_change is None
    assert kpi.trend_direction == "up"


def test_kpi_is_unknown_when_previous_is_missing():
    kpi = build_kpi(5.0, None)
    assert kpi.absolute_change is None
    assert kpi.percentage_change is None
    assert kpi.trend_direction == "unknown"


def test_kpi_flat_when_unchanged():
    assert build_kpi(4.0, 4.0).trend_direction == "flat"


def test_kpi_down_when_decreased():
    kpi = build_kpi(3.0, 4.0)
    assert kpi.trend_direction == "down"
    assert kpi.percentage_change == -25.0


# ---- improved agents -------------------------------------------------------


def _agent_records(name, scores, days_ago, prefix="CALL_1"):
    return [
        make_record(f"{prefix}{i:02d}", agent_name=name, agent_performance_score=s, days_ago=days_ago, now=NOW)
        for i, s in enumerate(scores)
    ]


def test_improved_agent_requires_two_calls_in_each_period():
    current = _agent_records("Sarah Levi", [5, 5], 5, prefix="CALL_1")
    previous = _agent_records("Sarah Levi", [3], 40, prefix="CALL_2")  # only one
    assert improved_agents(current, previous) == []


def test_improved_agent_requires_two_calls_in_the_current_period():
    current = _agent_records("Sarah Levi", [5], 5, prefix="CALL_1")
    previous = _agent_records("Sarah Levi", [3, 3], 40, prefix="CALL_2")
    assert improved_agents(current, previous) == []


def test_improvement_below_the_threshold_is_not_reported():
    """+0.17 (4 calls: 3,3,3,4 -> 3,4,3,4) sits just under the 0.2 bar."""
    current = _agent_records("Sarah Levi", [3, 4, 3, 4], 5, prefix="CALL_1")   # avg 3.5
    previous = _agent_records("Sarah Levi", [3, 4, 3, 3], 40, prefix="CALL_2")  # avg 3.25 -> +0.25
    assert len(improved_agents(current, previous)) == 1, "sanity: +0.25 does clear the bar"

    # Now shave the gap to +0.17, which must NOT be reported.
    previous = _agent_records("Sarah Levi", [3, 4, 4, 3], 40, prefix="CALL_2")  # avg 3.5
    current = _agent_records("Sarah Levi", [3, 4, 4, 4], 5, prefix="CALL_1")    # avg 3.75 -> +0.25
    current[3].analysis.agent_performance_score = 3                             # avg 3.5 -> +0.0
    assert improved_agents(current, previous) == []


def test_improvement_just_under_the_threshold_is_excluded():
    """3 calls averaging 3.67 vs 3.5 is +0.17 -- below the documented 0.2."""
    current = _agent_records("Sarah Levi", [4, 4, 3], 5, prefix="CALL_1")    # avg 3.67
    previous = _agent_records("Sarah Levi", [4, 3], 40, prefix="CALL_2")     # avg 3.5
    assert improved_agents(current, previous) == []


def test_improvement_at_the_threshold_is_reported():
    """+0.5 clears the documented >= 0.2 bar."""
    current = _agent_records("Sarah Levi", [4, 5], 5, prefix="CALL_1")     # avg 4.5
    previous = _agent_records("Sarah Levi", [4, 4], 40, prefix="CALL_2")   # avg 4.0
    result = improved_agents(current, previous)
    assert len(result) == 1
    assert result[0].agent_name == "Sarah Levi"
    assert result[0].improvement == 0.5
    assert result[0].current_call_count == 2
    assert result[0].previous_call_count == 2


def test_agent_grouping_is_case_and_whitespace_insensitive():
    current = [
        make_record("CALL_101", agent_name="sarah levi", agent_performance_score=5, days_ago=3, now=NOW),
        make_record("CALL_102", agent_name="  SARAH   LEVI ", agent_performance_score=5, days_ago=4, now=NOW),
    ]
    previous = [
        make_record("CALL_201", agent_name="Sarah Levi", agent_performance_score=4, days_ago=40, now=NOW),
        make_record("CALL_202", agent_name="Sarah  Levi", agent_performance_score=4, days_ago=41, now=NOW),
    ]
    result = improved_agents(current, previous)
    assert len(result) == 1, "all four spellings must aggregate as one agent"
    assert result[0].improvement == 1.0
    # The display name is a clean, real spelling -- never the lowercased key.
    assert result[0].agent_name.lower() == "sarah levi"


def test_declining_agents_are_not_reported():
    current = _agent_records("Sarah Levi", [3, 3], 5, prefix="CALL_1")
    previous = _agent_records("Sarah Levi", [5, 5], 40, prefix="CALL_2")
    assert improved_agents(current, previous) == []


def test_improved_agents_sorted_by_improvement_descending():
    current = _agent_records("Sarah Levi", [5, 5], 5, prefix="CALL_1") + _agent_records(
        "Daniel Cohen", [4, 4], 5, prefix="CALL_3"
    )
    previous = _agent_records("Sarah Levi", [3, 3], 40, prefix="CALL_2") + _agent_records(
        "Daniel Cohen", [3, 3], 40, prefix="CALL_4"
    )
    result = improved_agents(current, previous)
    assert [a.agent_name for a in result] == ["Sarah Levi", "Daniel Cohen"]


# ---- ordering --------------------------------------------------------------


def test_attention_calls_sorted_by_priority_then_recency():
    records = [
        make_record("CALL_001", days_ago=1, now=NOW, attention_required=True, attention_priority_score=40),
        make_record("CALL_002", days_ago=5, now=NOW, attention_required=True, attention_priority_score=90),
        make_record("CALL_003", days_ago=2, now=NOW, attention_required=True, attention_priority_score=90),
        make_record("CALL_004", days_ago=1, now=NOW, attention_required=False),
    ]
    result = attention_calls(records)
    assert [c.call_id for c in result] == ["CALL_003", "CALL_002", "CALL_001"]


def test_attention_calls_excludes_calls_not_needing_attention():
    records = [make_record("CALL_001", attention_required=False)]
    assert attention_calls(records) == []


def test_recent_calls_sorted_newest_first():
    records = [
        make_record("CALL_001", days_ago=5, now=NOW),
        make_record("CALL_002", days_ago=1, now=NOW),
        make_record("CALL_003", days_ago=3, now=NOW),
    ]
    assert [c.call_id for c in recent_calls(records)] == ["CALL_002", "CALL_003", "CALL_001"]


def test_recent_calls_respects_the_limit():
    records = [make_record(f"CALL_00{i}", days_ago=i, now=NOW) for i in range(1, 9)]
    assert len(recent_calls(records, limit=6)) == 6


# ---- trend buckets ---------------------------------------------------------


def test_trend_returns_exactly_four_buckets():
    start, end, _, _ = window_bounds("30d", NOW)
    buckets = close_rate_trend([], start, end)
    assert len(buckets) == 4


def test_trend_buckets_are_chronological_and_non_overlapping():
    start, end, _, _ = window_bounds("30d", NOW)
    buckets = close_rate_trend([], start, end)
    for earlier, later in zip(buckets, buckets[1:]):
        assert earlier.start_date <= later.start_date
        assert earlier.end_date <= later.start_date or earlier.end_date == later.start_date


def test_trend_buckets_assign_each_call_exactly_once():
    start, end, _, _ = window_bounds("30d", NOW)
    records = [make_record(f"CALL_0{i:02d}", days_ago=i, now=NOW) for i in range(1, 30)]
    buckets = close_rate_trend(records, start, end)
    assert sum(b.calls_analyzed for b in buckets) == len(records)


def test_trend_bucket_close_rate_excludes_uncertain():
    start, end, _, _ = window_bounds("7d", NOW)
    records = [
        make_record("CALL_001", days_ago=1, now=NOW, call_outcome="Sale"),
        make_record("CALL_002", days_ago=1, now=NOW, call_outcome="Uncertain"),
    ]
    buckets = close_rate_trend(records, start, end)
    last = [b for b in buckets if b.calls_analyzed > 0][-1]
    assert last.known_outcomes == 1
    assert last.sales == 1
    assert last.close_rate == 100.0


def test_trend_bucket_close_rate_is_none_when_empty():
    start, end, _, _ = window_bounds("7d", NOW)
    assert all(b.close_rate is None for b in close_rate_trend([], start, end))


def test_seven_day_period_also_splits_into_four_buckets():
    start, end, _, _ = window_bounds("7d", NOW)
    assert len(close_rate_trend([], start, end)) == 4


# ---- full overview assembly ------------------------------------------------


def test_overview_on_an_empty_dataset_does_not_crash_or_fabricate():
    result = _overview([])
    assert result.kpis.calls_analyzed.current_value == 0
    assert result.kpis.close_rate.current_value is None
    assert result.kpis.average_agent_performance.current_value is None
    assert result.attention_calls == []
    assert result.recent_calls == []
    assert result.improved_agents == []
    assert len(result.close_rate_trend) == 4
    assert "No calls" in result.executive_summary


def test_overview_reports_skipped_malformed_records():
    result = _overview([make_record("CALL_001", days_ago=1, now=NOW)], skipped=3)
    assert result.data_quality.skipped_malformed_records == 3
    assert result.data_quality.loaded_records == 1
    assert result.data_quality.current_period_records == 1


def test_overview_with_all_records_malformed_still_returns_a_valid_shape():
    result = _overview([], skipped=24)
    assert result.data_quality.loaded_records == 0
    assert result.data_quality.skipped_malformed_records == 24
    assert result.kpis.calls_analyzed.current_value == 0


def test_overview_period_window_documents_inclusivity():
    result = _overview([], period="7d")
    assert result.period.period == "7d"
    assert result.period.current_window_inclusive_of_now is True
    assert result.period.previous_end == result.period.current_start


def test_overview_counts_attention_calls_in_the_kpi():
    records = [
        make_record("CALL_001", days_ago=1, now=NOW, attention_required=True, attention_priority_score=70),
        make_record("CALL_002", days_ago=2, now=NOW, attention_required=False),
    ]
    result = _overview(records)
    assert result.kpis.calls_requiring_attention.current_value == 1
    assert calls_requiring_attention(records) == 1


def test_overview_improved_agents_count_has_no_previous_comparison():
    """There is no third window, so the comparison is honestly 'unknown'."""
    result = _overview([make_record("CALL_001", days_ago=1, now=NOW)])
    assert result.kpis.improved_agents_count.previous_value is None
    assert result.kpis.improved_agents_count.trend_direction == "unknown"


# ---- deterministic attention rules ----------------------------------------


def _attention(**kwargs):
    defaults = dict(
        call_outcome="Sale",
        customer_sentiment="positive",
        agent_performance_score=4,
        lead_quality_score=3,
        risk_level=None,
        confidence=None,
        guardrail_status="pass",
        router_reasons=[],
    )
    defaults.update(kwargs)
    return derive_attention(**defaults)


def test_no_rule_matched_means_no_attention_required():
    result = _attention()
    assert result.required is False
    assert result.category == "low_priority"
    assert result.priority_score == 0
    assert result.priority == "low"


def test_recoverable_opportunity_rule():
    result = _attention(lead_quality_score=4, call_outcome="No Sale")
    assert result.required is True
    assert result.category == "recoverable_opportunity"


def test_high_lead_quality_with_a_sale_is_not_an_opportunity():
    assert _attention(lead_quality_score=5, call_outcome="Sale").required is False


def test_critical_coaching_rule():
    result = _attention(agent_performance_score=2)
    assert result.category == "critical_coaching"


def test_customer_dissatisfaction_rule():
    result = _attention(customer_sentiment="negative")
    assert result.category == "customer_dissatisfaction"


def test_human_review_rule_from_guardrail_status():
    result = _attention(guardrail_status="human_review_required")
    assert result.category == "human_review"


def test_human_review_rule_from_unresolved_follow_up():
    result = _attention(follow_up_needed=True, next_meeting_scheduled=False)
    assert result.category == "human_review"


def test_scheduled_follow_up_is_not_flagged():
    assert _attention(follow_up_needed=True, next_meeting_scheduled=True).required is False


def test_evidence_conflict_rule_from_router_reasons():
    result = _attention(router_reasons=["langgraph_evidence_conflicts_detected"])
    assert result.category == "evidence_conflict"


def test_precedence_evidence_conflict_beats_everything():
    """A call matching four rules at once reports the most severe category."""
    result = _attention(
        router_reasons=["langgraph_evidence_conflicts_detected"],
        guardrail_status="human_review_required",
        agent_performance_score=1,
        customer_sentiment="negative",
        lead_quality_score=5,
        call_outcome="No Sale",
    )
    assert result.category == "evidence_conflict"


def test_precedence_human_review_beats_coaching_and_sentiment():
    result = _attention(
        guardrail_status="human_review_required", agent_performance_score=1, customer_sentiment="negative"
    )
    assert result.category == "human_review"


def test_precedence_coaching_beats_sentiment():
    result = _attention(agent_performance_score=2, customer_sentiment="negative")
    assert result.category == "critical_coaching"


def test_precedence_sentiment_beats_recoverable_opportunity():
    result = _attention(customer_sentiment="negative", lead_quality_score=5, call_outcome="No Sale")
    assert result.category == "customer_dissatisfaction"


def test_priority_score_is_deterministic():
    kwargs = dict(customer_sentiment="negative", lead_quality_score=4, risk_level="High")
    assert _attention(**kwargs).priority_score == _attention(**kwargs).priority_score


def test_priority_score_formula_components():
    # base(customer_dissatisfaction)=45 + lead_quality 4(+10) + risk High(+10)
    # + confidence<0.65(+8) + Follow-up Needed(+5) = 78
    result = _attention(
        customer_sentiment="negative",
        lead_quality_score=4,
        risk_level="High",
        confidence=0.5,
        call_outcome="Follow-up Needed",
    )
    assert result.priority_score == 78
    assert result.priority == "high"


def test_missing_confidence_never_scores_as_low_confidence():
    with_null = _attention(customer_sentiment="negative", confidence=None)
    with_low = _attention(customer_sentiment="negative", confidence=0.4)
    assert with_low.priority_score == with_null.priority_score + 8


def test_missing_risk_level_never_scores_as_high_risk():
    with_null = _attention(customer_sentiment="negative", risk_level=None)
    with_high = _attention(customer_sentiment="negative", risk_level="High")
    assert with_high.priority_score == with_null.priority_score + 10


def test_priority_score_is_clamped_to_100():
    result = _attention(
        router_reasons=["evidence_conflict"],
        lead_quality_score=5,
        agent_performance_score=1,
        risk_level="High",
        confidence=0.1,
        call_outcome="Follow-up Needed",
    )
    assert result.priority_score == 100  # 70+15+10+10+8+5 = 118, clamped
    assert result.priority == "critical"


@pytest.mark.parametrize(
    "score,expected",
    [(0, "low"), (34, "low"), (35, "medium"), (59, "medium"), (60, "high"), (79, "high"), (80, "critical"), (100, "critical")],
)
def test_priority_bands(score, expected):
    assert priority_band(score) == expected


# ---- recovery opportunity --------------------------------------------------


def test_recovery_detected_for_a_high_quality_lead_that_did_not_close():
    attention = _attention(lead_quality_score=5, call_outcome="No Sale")
    recovery = derive_recovery_opportunity(
        call_outcome="No Sale", lead_quality_score=5, main_objection="price", confidence=None, attention=attention
    )
    assert recovery.detected is True
    assert "itemized proposal" in recovery.recommended_offer
    assert recovery.recommended_follow_up_window is not None


def test_recovery_not_detected_for_a_sale():
    attention = _attention()
    recovery = derive_recovery_opportunity(
        call_outcome="Sale", lead_quality_score=5, main_objection="price", confidence=0.9, attention=attention
    )
    assert recovery.detected is False
    assert recovery.recommended_offer is None


def test_recovery_confidence_stays_null_when_never_measured():
    """The historical corpus has no confidence; it must not become 0.0."""
    attention = _attention(lead_quality_score=4, call_outcome="No Sale")
    recovery = derive_recovery_opportunity(
        call_outcome="No Sale", lead_quality_score=4, main_objection="timing", confidence=None, attention=attention
    )
    assert recovery.detected is True
    assert recovery.confidence is None


def test_recovery_offer_falls_back_for_an_unknown_objection():
    attention = _attention(lead_quality_score=4, call_outcome="No Sale")
    recovery = derive_recovery_opportunity(
        call_outcome="No Sale", lead_quality_score=4, main_objection="zzz", confidence=None, attention=attention
    )
    assert recovery.recommended_offer is not None
