"""Persistence helpers for the data this service still owns directly:
fixed infrastructure cost allocation.

**Architecture note (Langfuse adoption):** this module previously also
contained `insert_event()` and a full set of SQL aggregation functions
(`get_summary`, `get_daily`, `get_by_stage`, `get_by_provider`,
`get_calls`, `get_call_detail`) built on a local `usage_events` table.
That table and all of these functions have been removed — Langfuse now
owns per-event token/cost/latency telemetry as the single source of truth
(see `app/trace_recorder.py` for the write path and
`app/langfuse_query_adapter.py` for the read path, which will call
Langfuse's Metrics/Observations/Scores APIs). Keeping both a local
`usage_events` table and Langfuse's own trace/generation store would
create two competing sources of truth for the same numbers — exactly what
the approved architecture explicitly rules out.

Fixed infrastructure cost (EC2, n8n subscription, etc.) has no Langfuse
equivalent at all — Langfuse only ever knows about cost attributable to a
specific generation, never a flat monthly spend independent of call
volume — so this remains entirely XSight-owned, unchanged in logic.
"""
import sqlite3
from decimal import Decimal

from app.pricing import to_decimal


def get_flat_monthly_infrastructure_cost(
    conn: sqlite3.Connection, period_start: str, period_end: str
) -> Decimal:
    """Sum of active infrastructure_cost_config rows whose effective window
    overlaps the given period, regardless of allocation_method — used for
    the `flat_monthly` view (the whole configured monthly cost shown as-is)."""
    rows = conn.execute(
        """
        SELECT monthly_cost_usd FROM infrastructure_cost_config
        WHERE is_active = 1
          AND effective_from < ?
          AND (effective_to IS NULL OR effective_to > ?)
        """,
        (period_end, period_start),
    ).fetchall()
    total = Decimal("0")
    for row in rows:
        value = to_decimal(row["monthly_cost_usd"])
        if value is not None:
            total += value
    return total


def get_per_call_share_infrastructure_cost(
    conn: sqlite3.Connection, period_start: str, period_end: str
) -> Decimal:
    """Sum of active infrastructure_cost_config rows specifically flagged
    `allocation_method = 'per_call_share'` — the caller (see
    app/main.py's usage_cost_breakdown) divides this by the period's
    distinct call count, never dividing by zero."""
    rows = conn.execute(
        """
        SELECT monthly_cost_usd FROM infrastructure_cost_config
        WHERE is_active = 1 AND allocation_method = 'per_call_share'
          AND effective_from < ? AND (effective_to IS NULL OR effective_to > ?)
        """,
        (period_end, period_start),
    ).fetchall()
    total = Decimal("0")
    for row in rows:
        value = to_decimal(row["monthly_cost_usd"])
        if value is not None:
            total += value
    return total
