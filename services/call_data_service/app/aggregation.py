"""Overview aggregation.

Every business calculation the Overview screen shows is computed here, in
the backend, over stored records. The frontend receives finished numbers and
renders them -- it never averages, filters by period, or computes a close
rate itself.

All functions are pure: they take records plus explicit window boundaries
and return DTOs. That makes each aggregation rule directly unit-testable
without S3, HTTP, or a clock.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Optional

from app.models import (
    AnalyzedCallRecord,
    AttentionCall,
    CallSummary,
    DataQuality,
    ImprovedAgent,
    KpiMetric,
    OutcomeDistribution,
    OverviewKpis,
    OverviewResponse,
    PeriodWindow,
    RecentCall,
    TrendBucket,
)

# A record counts toward "calls analyzed" in any of these states. `failed`
# is not a valid stored status at all (see models.CallStatus) -- a call that
# never produced an analysis is never persisted as one.
ANALYZED_STATUSES = {"completed", "flagged", "human_review_required"}

# Outcomes that carry a decided result. "Uncertain" is deliberately excluded
# from the close-rate denominator: counting it would silently depress the
# rate with calls the system explicitly declined to judge.
KNOWN_OUTCOMES = {"sale", "no sale", "follow-up needed"}
SALE_OUTCOME = "sale"

IMPROVED_AGENT_MIN_CALLS_PER_PERIOD = 2
IMPROVED_AGENT_MIN_IMPROVEMENT = 0.2

TREND_BUCKET_COUNT = 4


def _normalized_outcome(record: AnalyzedCallRecord) -> Optional[str]:
    """Case-insensitive outcome for matching; canonical casing is preserved
    on the record itself and in every DTO returned to the client."""
    outcome = record.analysis.call_outcome
    return outcome.strip().lower() if outcome else None


def is_analyzed(record: AnalyzedCallRecord) -> bool:
    return record.status in ANALYZED_STATUSES


def in_window(record: AnalyzedCallRecord, start: datetime, end: datetime, *, inclusive_end: bool) -> bool:
    created = record.created_at
    if inclusive_end:
        return start <= created <= end
    return start <= created < end


def select_window(
    records: Iterable[AnalyzedCallRecord], start: datetime, end: datetime, *, inclusive_end: bool
) -> list[AnalyzedCallRecord]:
    return [r for r in records if is_analyzed(r) and in_window(r, start, end, inclusive_end=inclusive_end)]


# ---- individual metrics ----------------------------------------------------


def calls_analyzed(records: list[AnalyzedCallRecord]) -> int:
    return len(records)


def close_rate(records: list[AnalyzedCallRecord]) -> Optional[float]:
    """Sale / calls-with-a-known-outcome * 100.

    Returns None (never 0.0) when nothing in the window had a decided
    outcome -- an undefined rate is reported as undefined so the UI can say
    so rather than showing a misleading 0%.
    """
    known = [o for o in (_normalized_outcome(r) for r in records) if o in KNOWN_OUTCOMES]
    if not known:
        return None
    sales = sum(1 for o in known if o == SALE_OUTCOME)
    return round(sales / len(known) * 100, 1)


def outcome_distribution(records: list[AnalyzedCallRecord]) -> OutcomeDistribution:
    """Count every call in the window by outcome.

    Unlike `close_rate`, nothing is excluded here. A call with no recorded
    outcome lands in `unknown` rather than being dropped, so the returned
    counts always sum to `calls_analyzed` for the same window and the
    frontend's chart can be reconciled against the headline KPI. Silently
    omitting undecided calls would make the mix look more decisive than the
    corpus actually is.
    """
    counts = OutcomeDistribution()
    for record in records:
        outcome = _normalized_outcome(record)
        if outcome == SALE_OUTCOME:
            counts.sale += 1
        elif outcome == "no sale":
            counts.no_sale += 1
        elif outcome == "follow-up needed":
            counts.follow_up += 1
        elif outcome == "uncertain":
            counts.uncertain += 1
        else:
            counts.unknown += 1
    return counts


def _average(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def average_agent_performance(records: list[AnalyzedCallRecord]) -> Optional[float]:
    return _average([r.analysis.agent_performance_score for r in records if r.analysis.agent_performance_score is not None])


def average_lead_quality(records: list[AnalyzedCallRecord]) -> Optional[float]:
    return _average([r.analysis.lead_quality_score for r in records if r.analysis.lead_quality_score is not None])


def calls_requiring_attention(records: list[AnalyzedCallRecord]) -> int:
    return sum(1 for r in records if r.analysis.attention.required)


def build_kpi(current: Optional[float], previous: Optional[float]) -> KpiMetric:
    """Assemble one KPI with its comparison.

    `percentage_change` stays None when the previous value is zero or
    unknown -- dividing by zero has no defined answer, and reporting a
    fabricated 0% or 100% would misrepresent it.
    """
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    direction = "unknown"

    if current is not None and previous is not None:
        absolute_change = round(current - previous, 2)
        if previous != 0:
            percentage_change = round((current - previous) / abs(previous) * 100, 1)
        if absolute_change > 0:
            direction = "up"
        elif absolute_change < 0:
            direction = "down"
        else:
            direction = "flat"

    return KpiMetric(
        current_value=current,
        previous_value=previous,
        absolute_change=absolute_change,
        percentage_change=percentage_change,
        trend_direction=direction,
    )


# ---- improved agents -------------------------------------------------------


def improved_agents(
    current: list[AnalyzedCallRecord], previous: list[AnalyzedCallRecord]
) -> list[ImprovedAgent]:
    """Agents whose average performance rose by >= 0.2 between the windows.

    Both windows must contain at least 2 scored calls for that agent --
    without a floor, a single lucky call would read as "improvement".
    Grouping is by the normalized (trimmed, case-insensitive) name; the
    display name is the most recent spelling actually recorded.
    """
    def group(records: list[AnalyzedCallRecord]) -> dict[str, list[AnalyzedCallRecord]]:
        out: dict[str, list[AnalyzedCallRecord]] = {}
        for record in records:
            if record.analysis.agent_performance_score is None:
                continue
            out.setdefault(record.agent_name_normalized, []).append(record)
        return out

    current_groups = group(current)
    previous_groups = group(previous)

    results: list[ImprovedAgent] = []
    for key, current_records in current_groups.items():
        previous_records = previous_groups.get(key, [])
        if (
            len(current_records) < IMPROVED_AGENT_MIN_CALLS_PER_PERIOD
            or len(previous_records) < IMPROVED_AGENT_MIN_CALLS_PER_PERIOD
        ):
            continue
        current_avg = _average([r.analysis.agent_performance_score for r in current_records])
        previous_avg = _average([r.analysis.agent_performance_score for r in previous_records])
        if current_avg is None or previous_avg is None:
            continue
        improvement = round(current_avg - previous_avg, 2)
        if improvement < IMPROVED_AGENT_MIN_IMPROVEMENT:
            continue
        display_name = max(current_records, key=lambda r: r.created_at).agent_name
        results.append(
            ImprovedAgent(
                agent_name=display_name,
                current_average_score=current_avg,
                previous_average_score=previous_avg,
                improvement=improvement,
                current_call_count=len(current_records),
                previous_call_count=len(previous_records),
            )
        )

    results.sort(key=lambda a: (-a.improvement, a.agent_name.lower()))
    return results


# ---- trend buckets ---------------------------------------------------------


def close_rate_trend(
    records: list[AnalyzedCallRecord], start: datetime, end: datetime, buckets: int = TREND_BUCKET_COUNT
) -> list[TrendBucket]:
    """Split [start, end] into `buckets` contiguous, non-overlapping ranges.

    Boundaries are computed from the exact window duration rather than from
    calendar weeks, so a 7-day period splits as cleanly as a 30-day one and
    the result is deterministic for any window length.
    """
    total = (end - start).total_seconds()
    if total <= 0 or buckets <= 0:
        return []

    step = total / buckets
    out: list[TrendBucket] = []
    for i in range(buckets):
        bucket_start = start + timedelta(seconds=step * i)
        bucket_end = start + timedelta(seconds=step * (i + 1))
        is_last = i == buckets - 1
        # Half-open [start, end) for every bucket except the last, which
        # closes on the window end so the final instant is never dropped.
        in_bucket = [
            r
            for r in records
            if bucket_start <= r.created_at
            and (r.created_at <= bucket_end if is_last else r.created_at < bucket_end)
        ]
        known = [o for o in (_normalized_outcome(r) for r in in_bucket) if o in KNOWN_OUTCOMES]
        sales = sum(1 for o in known if o == SALE_OUTCOME)
        out.append(
            TrendBucket(
                label=f"{bucket_start.date().isoformat()} to {bucket_end.date().isoformat()}",
                start_date=bucket_start.date(),
                end_date=bucket_end.date(),
                calls_analyzed=len(in_bucket),
                known_outcomes=len(known),
                sales=sales,
                close_rate=round(sales / len(known) * 100, 1) if known else None,
            )
        )
    return out


# ---- list projections ------------------------------------------------------


def to_summary(record: AnalyzedCallRecord) -> CallSummary:
    a = record.analysis
    return CallSummary(
        call_id=record.call_id,
        source=record.source,
        created_at=record.created_at,
        call_date=record.call_date,
        agent_name=record.agent_name,
        customer_name=record.customer_name,
        status=record.status,
        call_outcome=a.call_outcome,
        agent_performance_score=a.agent_performance_score,
        lead_quality_score=a.lead_quality_score,
        confidence=a.confidence,
        risk_level=a.risk_level,
        guardrail_status=a.guardrail_status,
        attention_required=a.attention.required,
        attention_priority=a.attention.priority,
        attention_priority_score=a.attention.priority_score,
        attention_category=a.attention.category,
    )


def attention_calls(records: list[AnalyzedCallRecord], limit: int = 5) -> list[AttentionCall]:
    """Highest priority first, then most recent. Backend-sorted so the
    frontend renders the list as given without reordering it."""
    flagged = [r for r in records if r.analysis.attention.required]
    # One sort, descending on both keys: highest priority_score first, and
    # most recent first among equal scores.
    flagged.sort(key=lambda r: (r.analysis.attention.priority_score, r.created_at), reverse=True)
    return [
        AttentionCall(
            call_id=r.call_id,
            created_at=r.created_at,
            call_date=r.call_date,
            agent_name=r.agent_name,
            customer_name=r.customer_name,
            call_outcome=r.analysis.call_outcome,
            lead_quality_score=r.analysis.lead_quality_score,
            agent_performance_score=r.analysis.agent_performance_score,
            priority=r.analysis.attention.priority,
            priority_score=r.analysis.attention.priority_score,
            category=r.analysis.attention.category,
            reason=r.analysis.attention.reason,
            guardrail_status=r.analysis.guardrail_status,
        )
        for r in flagged[:limit]
    ]


def recent_calls(records: list[AnalyzedCallRecord], limit: int = 6) -> list[RecentCall]:
    ordered = sorted(records, key=lambda r: r.created_at, reverse=True)
    return [
        RecentCall(
            call_id=r.call_id,
            created_at=r.created_at,
            call_date=r.call_date,
            agent_name=r.agent_name,
            customer_name=r.customer_name,
            call_outcome=r.analysis.call_outcome,
            agent_performance_score=r.analysis.agent_performance_score,
            lead_quality_score=r.analysis.lead_quality_score,
            guardrail_status=r.analysis.guardrail_status,
            source=r.source,
        )
        for r in ordered[:limit]
    ]


# ---- executive summary -----------------------------------------------------


def executive_summary(
    period_label: str,
    current: list[AnalyzedCallRecord],
    rate: Optional[float],
    attention_count: int,
    improved_count: int,
) -> str:
    """A deterministic, backend-owned sentence -- no LLM, no template the
    frontend has to assemble."""
    if not current:
        return f"No calls were analyzed in the last {period_label}."

    parts = [f"{len(current)} call{'s' if len(current) != 1 else ''} analyzed in the last {period_label}"]
    if rate is not None:
        parts.append(f"a {rate}% close rate")
    if attention_count > 0:
        parts.append(f"{attention_count} call{'s' if attention_count != 1 else ''} needing attention")
    else:
        parts.append("nothing currently needing attention")
    if improved_count > 0:
        parts.append(f"{improved_count} agent{'s' if improved_count != 1 else ''} improving")
    return ", ".join(parts) + "."


# ---- top-level assembly ----------------------------------------------------


def build_overview(
    *,
    all_records: list[AnalyzedCallRecord],
    skipped_count: int,
    period: str,
    current_start: datetime,
    current_end: datetime,
    previous_start: datetime,
    previous_end: datetime,
    generated_at: datetime,
) -> OverviewResponse:
    current = select_window(all_records, current_start, current_end, inclusive_end=True)
    previous = select_window(all_records, previous_start, previous_end, inclusive_end=False)

    current_rate = close_rate(current)
    previous_rate = close_rate(previous)
    improved = improved_agents(current, previous)
    attention_count = calls_requiring_attention(current)

    kpis = OverviewKpis(
        calls_analyzed=build_kpi(float(len(current)), float(len(previous))),
        close_rate=build_kpi(current_rate, previous_rate),
        average_agent_performance=build_kpi(
            average_agent_performance(current), average_agent_performance(previous)
        ),
        average_lead_quality=build_kpi(average_lead_quality(current), average_lead_quality(previous)),
        calls_requiring_attention=build_kpi(
            float(attention_count), float(calls_requiring_attention(previous))
        ),
        # There is no defined "previously improved agents" figure without a
        # third window, so the comparison is reported as unknown rather than
        # invented.
        improved_agents_count=build_kpi(float(len(improved)), None),
    )

    period_label = "7 days" if period == "7d" else "30 days"

    return OverviewResponse(
        period=PeriodWindow(
            period=period,
            current_start=current_start,
            current_end=current_end,
            previous_start=previous_start,
            previous_end=previous_end,
        ),
        generated_at=generated_at,
        executive_summary=executive_summary(
            period_label, current, current_rate, attention_count, len(improved)
        ),
        kpis=kpis,
        outcome_distribution=outcome_distribution(current),
        close_rate_trend=close_rate_trend(current, current_start, current_end),
        improved_agents=improved,
        attention_calls=attention_calls(current),
        recent_calls=recent_calls(current),
        data_quality=DataQuality(
            loaded_records=len(all_records),
            skipped_malformed_records=skipped_count,
            current_period_records=len(current),
            previous_period_records=len(previous),
        ),
    )
