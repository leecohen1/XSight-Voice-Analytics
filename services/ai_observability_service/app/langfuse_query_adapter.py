"""Read-path adapter: normalizes Langfuse's public API responses into
XSight's own stable, product-specific response contracts.

**Status: mocked / not yet live-verified.** No real Langfuse account was
created as part of this task (per the task's explicit scope — Phase 1
foundation only, no live integration). The `fetch_*` functions below are
structurally ready (against the current, confirmed API surface — see
module docstring references) but have never been exercised against a real
Langfuse project. The `normalize_*` functions are the real, fully-tested
deliverable of this phase: given a Langfuse-API-shaped response (fixture
data in tests, standing in for what the real API will return), they
produce exactly the same response shapes the frontend already expects
from the pre-Langfuse design — the product contract does not change
just because the data source moved.

Confirmed-current API surface referenced here (Langfuse Python SDK v4,
`langfuse==4.14.1`, verified 2026-07-27): the public API client is
exposed as `client.api` on a constructed `Langfuse` instance, with
`api.metrics` for aggregate cost/usage/latency/volume queries (the
"Metrics API v2" — the current, non-deprecated path for dashboard-style
aggregation, avoiding downloading every raw observation), `api.observations`
for row-level trace/call detail, and `api.scores_v3` for evaluation
results. This module does not hardcode assumed request/response field
names beyond what was directly confirmed in the current documentation;
anywhere the exact shape is genuinely unverified, this is noted explicitly
rather than guessed at silently.
"""
import logging
from typing import Any, Optional

from app.langfuse_client import ObservabilityClient
from app.time_utils import parse_utc

logger = logging.getLogger("ai_observability_service")


class LangfuseQueryClient:
    """Thin wrapper around the real Langfuse SDK's `.api` sub-client for
    read queries. Every method follows the same error-isolation contract
    as app/langfuse_client.py: never raises, returns None/empty on any
    failure (network, auth, or a not-yet-verified response shape), and is
    a pure no-op when observability is disabled."""

    def __init__(self, observability_client: ObservabilityClient):
        self._observability_client = observability_client

    @property
    def _api(self):
        raw_client = getattr(self._observability_client, "_client", None)
        return getattr(raw_client, "api", None) if raw_client is not None else None

    def fetch_metrics(
        self, *, period_start: str, period_end: str, dimensions: Optional[list[str]] = None
    ) -> Optional[dict[str, Any]]:
        """NOT YET LIVE-VERIFIED — no real Langfuse project exists to
        confirm the exact request/response shape against. Structurally
        calls `client.api.metrics.metrics(...)` per the current documented
        API surface; returns None on any failure so callers always degrade
        gracefully to "no Langfuse data available" rather than erroring."""
        if not self._observability_client.enabled or self._api is None:
            return None
        try:
            return self._api.metrics.metrics(
                from_timestamp=period_start, to_timestamp=period_end, dimensions=dimensions or []
            )
        except Exception:
            logger.exception("Langfuse Metrics API call failed")
            return None

    def fetch_observations(
        self, *, period_start: str, period_end: str, trace_id: Optional[str] = None, limit: int = 100
    ) -> Optional[list[dict[str, Any]]]:
        """NOT YET LIVE-VERIFIED. Row-level observation data for call-level
        detail views."""
        if not self._observability_client.enabled or self._api is None:
            return None
        try:
            result = self._api.observations.get_many(
                from_start_time=parse_utc(period_start), to_start_time=parse_utc(period_end), trace_id=trace_id, limit=limit
            )
            return getattr(result, "data", result)
        except Exception:
            logger.exception("Langfuse Observations API call failed")
            return None

    def fetch_scores(self, *, trace_id: Optional[str] = None, limit: int = 100) -> Optional[list[dict[str, Any]]]:
        """NOT YET LIVE-VERIFIED. Evaluation scores for the future AI
        Evaluation page."""
        if not self._observability_client.enabled or self._api is None:
            return None
        try:
            result = self._api.scores_v3.get(trace_id=trace_id, limit=limit)
            return getattr(result, "data", result)
        except Exception:
            logger.exception("Langfuse Scores API call failed")
            return None


# --- Normalization: Langfuse-shaped response -> XSight product contract ----


def normalize_summary(metrics_response: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Produces the token/event-count portion of the old UsageSummaryResponse
    shape from a Metrics API response. Returns all-None/zero (never a
    fabricated non-zero number) when no data is available — either because
    observability is disabled or the query genuinely returned nothing."""
    if not metrics_response or not metrics_response.get("data"):
        return {
            "total_input_tokens": None,
            "total_output_tokens": None,
            "total_tokens": None,
            "calls_analyzed": 0,
            "events_count": 0,
        }

    total_input = total_output = total_events = 0
    call_ids: set[str] = set()
    for row in metrics_response["data"]:
        total_input += row.get("usage_input", 0) or 0
        total_output += row.get("usage_output", 0) or 0
        total_events += row.get("count", 0) or 0
        if row.get("call_id"):
            call_ids.add(row["call_id"])

    return {
        "total_input_tokens": total_input or None,
        "total_output_tokens": total_output or None,
        "total_tokens": (total_input + total_output) or None,
        "calls_analyzed": len(call_ids),
        "events_count": total_events,
    }


def normalize_daily_buckets(metrics_response: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    """Produces one bucket per day from a Metrics API response grouped by
    a 'date' dimension."""
    if not metrics_response or not metrics_response.get("data"):
        return []

    buckets: dict[str, dict[str, Any]] = {}
    for row in metrics_response["data"]:
        date = row.get("date")
        if not date:
            continue
        bucket = buckets.setdefault(
            date, {"date": date, "input_tokens": 0, "output_tokens": 0, "calls_analyzed": 0, "_call_ids": set()}
        )
        bucket["input_tokens"] += row.get("usage_input", 0) or 0
        bucket["output_tokens"] += row.get("usage_output", 0) or 0
        if row.get("call_id"):
            bucket["_call_ids"].add(row["call_id"])

    result = []
    for date in sorted(buckets):
        b = buckets[date]
        result.append(
            {
                "date": b["date"],
                "input_tokens": b["input_tokens"] or None,
                "output_tokens": b["output_tokens"] or None,
                "total_tokens": (b["input_tokens"] + b["output_tokens"]) or None,
                "calls_analyzed": len(b["_call_ids"]),
            }
        )
    return result


def normalize_grouped_breakdown(metrics_response: Optional[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    """Shared normalizer for by-stage and by-provider breakdowns — both are
    "group Metrics API rows by one dimension key" in exactly the same
    shape, just a different dimension name (`pipeline_stage` vs `provider`)."""
    if not metrics_response or not metrics_response.get("data"):
        return []

    groups: dict[str, dict[str, Any]] = {}
    for row in metrics_response["data"]:
        key = row.get(group_key)
        if not key:
            continue
        group = groups.setdefault(key, {group_key: key, "input_tokens": 0, "output_tokens": 0, "events_count": 0})
        group["input_tokens"] += row.get("usage_input", 0) or 0
        group["output_tokens"] += row.get("usage_output", 0) or 0
        group["events_count"] += row.get("count", 0) or 0

    result = []
    for key in sorted(groups):
        g = groups[key]
        result.append(
            {
                group_key: g[group_key],
                "input_tokens": g["input_tokens"] or None,
                "output_tokens": g["output_tokens"] or None,
                "total_tokens": (g["input_tokens"] + g["output_tokens"]) or None,
                "events_count": g["events_count"],
            }
        )
    return result


def normalize_call_list(observations_response: Optional[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Groups row-level Observations API results by trace/call, into the
    same call-list shape the old SQLite-backed /usage/calls returned."""
    if not observations_response:
        return []

    by_trace: dict[str, dict[str, Any]] = {}
    for obs in observations_response:
        trace_id = obs.get("trace_id")
        if not trace_id:
            continue
        entry = by_trace.setdefault(
            trace_id,
            {"call_id": trace_id, "input_tokens": 0, "output_tokens": 0, "status": "success", "analyzed_at": obs.get("start_time")},
        )
        usage = obs.get("usage_details") or {}
        entry["input_tokens"] += usage.get("input", 0) or 0
        entry["output_tokens"] += usage.get("output", 0) or 0
        if obs.get("level") == "ERROR":
            entry["status"] = "failed"

    return [
        {
            **entry,
            "total_tokens": (entry["input_tokens"] + entry["output_tokens"]) or None,
            "input_tokens": entry["input_tokens"] or None,
            "output_tokens": entry["output_tokens"] or None,
        }
        for entry in by_trace.values()
    ]
