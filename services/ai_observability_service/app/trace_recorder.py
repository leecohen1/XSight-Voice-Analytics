"""Composes the Langfuse client wrapper with the retained pricing engine to
record one full call trace from a batch of already-validated stage events.

This is the write-path successor to the old usage_monitoring_service's
`repository.insert_event()` — instead of writing a row to a local
`usage_events` table, each event becomes a span or generation observation
nested under one deterministic trace per `call_id`. `pricing_config` (and
`app/pricing.py`'s formulas) are unchanged and still the only source of
cost figures — this module only decides *where the result goes*
(Langfuse `cost_details`, not a local column).

A stage is recorded as a Langfuse **generation** only if it names a model
AND has a usage-bearing signal (tokens or audio duration) — every other
stage (guardrails, routing, deterministic scoring/reasoning) is a **span**.
This mirrors the approved trace/observation map exactly and prevents a
deterministic step from ever being mis-recorded as a priced LLM call.
"""
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from app.langfuse_client import ObservabilityClient
from app.pricing import calculate_cost, find_active_pricing
from app.time_utils import parse_utc
from app.validation import ValidatedEvent

DEFAULT_TRACE_NAME = "xsight-call-analysis"
DEFAULT_FLUSH_TIMEOUT_SECONDS = 3.0


@dataclass
class TraceIngestResult:
    trace_id: str
    observability_enabled: bool
    recorded_stage_names: list[str]
    failed_stage_names: list[str]


def _is_generation(event: ValidatedEvent) -> bool:
    has_usage_signal = (
        event.input_tokens is not None or event.output_tokens is not None or event.audio_duration_seconds is not None
    )
    return event.model is not None and has_usage_signal


def _usage_details_for(event: ValidatedEvent) -> Optional[dict[str, int]]:
    """Only ever includes measured values — a None token/duration is
    simply omitted, never coerced to 0."""
    details: dict[str, int] = {}
    if event.input_tokens is not None:
        details["input"] = event.input_tokens
    if event.output_tokens is not None:
        details["output"] = event.output_tokens
    if event.audio_duration_seconds is not None:
        details["duration_seconds"] = round(event.audio_duration_seconds)
    if event.request_count is not None and not details:
        details["requests"] = event.request_count
    return details or None


def _cost_details_for(cost: Optional[Decimal]) -> Optional[dict[str, str]]:
    """A single 'total' key — an intentional MVP simplification (see
    service README "Known limitations"): Langfuse's own worked examples
    split cost per usage-type key (input/output separately); this project
    computes one combined figure per stage via app/pricing.py today. Cost
    is always a Decimal-precise string, never a float, and is only ever
    present when `calculate_cost` actually returned a value — never
    fabricated."""
    if cost is None:
        return None
    return {"total": str(cost)}


def record_call_trace(
    client: ObservabilityClient,
    conn: sqlite3.Connection,
    call_id: str,
    workflow_execution_id: Optional[str],
    trace_metadata: dict[str, Any],
    events: list[ValidatedEvent],
    flush_timeout_seconds: float = DEFAULT_FLUSH_TIMEOUT_SECONDS,
) -> TraceIngestResult:
    trace_id = client.create_trace_id(seed=call_id)

    full_metadata = {**trace_metadata, "call_id": call_id}
    if workflow_execution_id:
        full_metadata["n8n_execution_id"] = workflow_execution_id

    client.update_trace_attributes(
        trace_id=trace_id,
        name=DEFAULT_TRACE_NAME,
        tags=_build_tags(trace_metadata),
        metadata=full_metadata,
    )

    recorded: list[str] = []
    failed: list[str] = []

    for event in events:
        try:
            cost = None
            if event.input_tokens is not None or event.output_tokens is not None or event.audio_duration_seconds is not None:
                pricing = find_active_pricing(
                    conn, event.provider, event.service, event.model, parse_utc(event.occurred_at_utc)
                )
                cost = calculate_cost(
                    pricing,
                    input_tokens=event.input_tokens,
                    output_tokens=event.output_tokens,
                    audio_duration_seconds=event.audio_duration_seconds,
                    request_count=event.request_count,
                )

            usage_details = _usage_details_for(event)
            cost_details = _cost_details_for(cost)
            event_metadata = event.metadata_raw if isinstance(event.metadata_raw, dict) else {}

            if _is_generation(event):
                client.record_generation(
                    trace_id=trace_id,
                    name=event.pipeline_stage,
                    model=event.model,
                    usage_details=usage_details,
                    cost_details=cost_details,
                    metadata=event_metadata,
                    status=event.status,
                )
            else:
                client.record_span(
                    trace_id=trace_id,
                    name=event.pipeline_stage,
                    metadata=event_metadata,
                    status=event.status,
                )
            recorded.append(event.pipeline_stage)
        except Exception:
            # A bug in this function's own cost-calculation/branching logic
            # (not a Langfuse network failure -- those are already caught
            # and logged inside record_span/record_generation themselves)
            # must still not corrupt the rest of the batch.
            failed.append(event.pipeline_stage)

    client.flush(timeout_seconds=flush_timeout_seconds)

    return TraceIngestResult(
        trace_id=trace_id,
        observability_enabled=client.enabled,
        recorded_stage_names=recorded,
        failed_stage_names=failed,
    )


def _build_tags(trace_metadata: dict[str, Any]) -> list[str]:
    tags = []
    if "environment" in trace_metadata:
        tags.append(f"env:{trace_metadata['environment']}")
    if "workflow_version" in trace_metadata:
        tags.append(f"workflow_version:{trace_metadata['workflow_version']}")
    if "final_status" in trace_metadata:
        tags.append(f"status:{trace_metadata['final_status']}")
    if "use_case" in trace_metadata:
        tags.append(f"use_case:{trace_metadata['use_case']}")
    return tags
