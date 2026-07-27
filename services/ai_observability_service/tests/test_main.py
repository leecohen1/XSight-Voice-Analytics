"""Endpoint-level tests for the AI Observability Service.

Covers GET /health, the write path (POST /observability/events, backed by
app/trace_recorder.py + a mocked ObservabilityClient), and the read path
(GET /observability/summary|daily|by-stage|by-provider|calls|calls/{id}|
cost-breakdown, backed by a mocked LangfuseQueryClient). No real Langfuse
SDK or network call is ever made here -- see conftest.py's `client_with_observability`
fixture, which overrides both `get_observability_client` and `get_query_client`.
"""
from conftest import insert_infra_row, insert_pricing_row

VALID_EVENT = {
    "idempotency_key": "exec-1:information_extraction",
    "provider": "gemini",
    "service": "generative_ai",
    "model": "gemini-test-model",
    "pipeline_stage": "information_extraction",
    "use_case": "analyze_sales_call",
    "input_tokens": 501,
    "output_tokens": 30,
    "total_tokens": 531,
    "audio_duration_seconds": None,
    "request_count": 1,
    "latency_ms": 840,
    "status": "success",
    "occurred_at": "2026-07-27T12:00:00Z",
    "metadata": {},
}


def _batch(events, call_id="call-abc-123", workflow_execution_id="21", trace_metadata=None):
    return {
        "call_id": call_id,
        "workflow_execution_id": workflow_execution_id,
        "trace_metadata": trace_metadata or {},
        "events": events,
    }


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "ai_observability_service"


# --- Write path: POST /observability/events (observability disabled -- default) --


def test_valid_batch_recorded_with_observability_disabled(client, db_conn):
    """No Langfuse credentials configured (this task's default state) --
    the trace/events are still accepted and "recorded" locally (spans/
    generations are no-ops, but the response reports the deterministic
    fallback trace_id and the stage names as recorded, not rejected)."""
    insert_pricing_row(db_conn, model="gemini-test-model")
    resp = client.post("/observability/events", json=_batch([VALID_EVENT]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["observability_enabled"] is False
    assert body["recorded_count"] == 1
    assert body["rejected_count"] == 0
    assert body["recorded_stage_names"] == ["information_extraction"]
    assert body["trace_id"]  # deterministic local fallback ID, never empty


def test_trace_id_is_deterministic_per_call_id(client):
    first = client.post("/observability/events", json=_batch([VALID_EVENT], call_id="same-call")).json()
    second = client.post("/observability/events", json=_batch([VALID_EVENT], call_id="same-call")).json()
    assert first["trace_id"] == second["trace_id"]


def test_negative_token_rejected_without_failing_batch(client, db_conn):
    insert_pricing_row(db_conn, model="gemini-test-model")
    bad_event = {**VALID_EVENT, "idempotency_key": "bad-1", "input_tokens": -5}
    good_event = {**VALID_EVENT, "idempotency_key": "good-1"}
    resp = client.post("/observability/events", json=_batch([bad_event, good_event]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded_count"] == 1
    assert body["rejected_count"] == 1
    assert body["rejected"][0]["idempotency_key"] == "bad-1"
    assert any("negative" in r for r in body["rejected"][0]["reasons"])


def test_negative_duration_rejected(client):
    bad_event = {**VALID_EVENT, "idempotency_key": "bad-dur", "audio_duration_seconds": -1.0}
    resp = client.post("/observability/events", json=_batch([bad_event]))
    body = resp.json()
    assert resp.status_code == 200
    assert body["rejected_count"] == 1
    assert any("audio_duration_seconds" in r for r in body["rejected"][0]["reasons"])


def test_inconsistent_total_tokens_rejected_via_api(client):
    bad_event = {**VALID_EVENT, "idempotency_key": "bad-total", "total_tokens": 99999}
    resp = client.post("/observability/events", json=_batch([bad_event]))
    body = resp.json()
    assert body["rejected_count"] == 1
    assert any("total_tokens" in r for r in body["rejected"][0]["reasons"])


def test_missing_token_fields_do_not_crash_non_llm_stage(client):
    """A non-LLM stage (e.g. the Call Signal Analyser) has no model and no
    token counts -- it must be recorded as a span, not rejected or crashed on."""
    event = {
        **VALID_EVENT,
        "idempotency_key": "non-token-1",
        "provider": "internal",
        "service": "call_signal_analyser",
        "model": None,
        "pipeline_stage": "call_signal_analysis",
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
    }
    resp = client.post("/observability/events", json=_batch([event]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded_count"] == 1
    assert body["rejected_count"] == 0


def test_missing_pricing_does_not_fail_the_event(client):
    """No pricing_config row exists for this model -- the event is still
    recorded (cost is simply omitted, never fabricated as zero)."""
    event = {**VALID_EVENT, "idempotency_key": "no-pricing-1", "model": "totally-unpriced-model"}
    resp = client.post("/observability/events", json=_batch([event]))
    body = resp.json()
    assert resp.status_code == 200
    assert body["recorded_count"] == 1
    assert body["rejected_count"] == 0


def test_partial_failed_event_still_recorded(client, db_conn):
    """A status='failed' event (e.g. an upstream call that errored) is
    still recorded -- usage up to the point of failure isn't discarded."""
    insert_pricing_row(db_conn, model="gemini-test-model")
    event = {**VALID_EVENT, "idempotency_key": "failed-1", "status": "failed", "output_tokens": None, "total_tokens": None}
    resp = client.post("/observability/events", json=_batch([event]))
    assert resp.status_code == 200
    assert resp.json()["recorded_count"] == 1


def test_batch_size_limit_enforced(client, monkeypatch):
    import dataclasses

    import app.main as main_module

    # Settings is a frozen dataclass (immutable by design) -- replace the
    # module-level instance wholesale rather than mutating a field.
    monkeypatch.setattr(main_module, "settings", dataclasses.replace(main_module.settings, max_events_per_batch=2))
    events = [{**VALID_EVENT, "idempotency_key": f"e-{i}"} for i in range(3)]
    resp = client.post("/observability/events", json=_batch(events))
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "BATCH_TOO_LARGE"


def test_structured_error_shape_on_missing_required_field(client):
    resp = client.post("/observability/events", json={"events": [VALID_EVENT]})  # call_id missing entirely
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["details"], list)


def test_structured_error_shape_on_unknown_route(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "HTTP_ERROR"


def test_empty_events_list_rejected_at_schema_level(client):
    resp = client.post("/observability/events", json=_batch([]))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_deprecated_usage_events_alias_removed(client):
    """The old /usage/events write endpoint no longer exists -- write
    traffic must go through /observability/events."""
    resp = client.post("/usage/events", json=_batch([VALID_EVENT]))
    assert resp.status_code == 404


# --- Read path: observability disabled (default state) -----------------------


def test_summary_with_observability_disabled_reports_no_llm_usage(client, db_conn):
    insert_infra_row(db_conn, monthly_cost_usd="30.00", allocation_method="flat_monthly")
    resp = client.get("/observability/summary", params={"range": "month"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["observability_enabled"] is False
    assert body["total_tokens"] is None
    assert body["allocated_fixed_cost_usd"] == "30.00"


def test_daily_with_observability_disabled_returns_empty_days(client):
    resp = client.get("/observability/daily", params={"range": "month"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["days"] == []
    assert body["observability_enabled"] is False


def test_calls_detail_404_when_no_trace_found(client):
    resp = client.get("/observability/calls/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "HTTP_ERROR"


# --- Read path: observability enabled, mocked Langfuse data -------------------


def test_summary_uses_mocked_metrics_when_enabled(client_with_mocked_langfuse):
    client, query_client = client_with_mocked_langfuse
    query_client.metrics_response = {
        "data": [
            {"usage_input": 500, "usage_output": 200, "count": 3, "call_id": "call-1"},
            {"usage_input": 100, "usage_output": 50, "count": 1, "call_id": "call-2"},
        ]
    }
    resp = client.get("/observability/summary", params={"range": "month"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["observability_enabled"] is True
    assert body["total_input_tokens"] == 600
    assert body["total_output_tokens"] == 250
    assert body["calls_analyzed"] == 2
    assert body["events_count"] == 4


def test_by_stage_groups_mocked_metrics(client_with_mocked_langfuse):
    client, query_client = client_with_mocked_langfuse
    query_client.metrics_response = {
        "data": [
            {"pipeline_stage": "information_extraction", "usage_input": 100, "usage_output": 40, "count": 1},
            {"pipeline_stage": "final_analysis", "usage_input": 300, "usage_output": 120, "count": 1},
        ]
    }
    resp = client.get("/observability/by-stage", params={"range": "month"})
    assert resp.status_code == 200
    stages = resp.json()["stages"]
    assert {s["pipeline_stage"] for s in stages} == {"information_extraction", "final_analysis"}


def test_by_provider_groups_mocked_metrics(client_with_mocked_langfuse):
    client, query_client = client_with_mocked_langfuse
    query_client.metrics_response = {
        "data": [
            {"provider": "gemini", "usage_input": 100, "usage_output": 40, "count": 1},
            {"provider": "assemblyai", "usage_input": 0, "usage_output": 0, "count": 1},
        ]
    }
    resp = client.get("/observability/by-provider", params={"range": "month"})
    assert resp.status_code == 200
    providers = resp.json()["providers"]
    assert {p["provider"] for p in providers} == {"gemini", "assemblyai"}


def test_calls_list_uses_mocked_observations(client_with_mocked_langfuse):
    client, query_client = client_with_mocked_langfuse
    query_client.observations_response = [
        {"trace_id": "call-1", "usage_details": {"input": 100, "output": 40}, "level": "DEFAULT", "start_time": "2026-07-15T12:00:00+00:00"},
        {"trace_id": "call-2", "usage_details": {"input": 10, "output": 5}, "level": "ERROR", "start_time": "2026-07-16T12:00:00+00:00"},
    ]
    resp = client.get("/observability/calls")
    assert resp.status_code == 200
    calls = {c["call_id"]: c for c in resp.json()["calls"]}
    assert calls["call-1"]["status"] == "success"
    assert calls["call-2"]["status"] == "failed"


def test_calls_list_filters_by_status(client_with_mocked_langfuse):
    client, query_client = client_with_mocked_langfuse
    query_client.observations_response = [
        {"trace_id": "call-1", "usage_details": {}, "level": "DEFAULT", "start_time": "2026-07-15T12:00:00+00:00"},
        {"trace_id": "call-2", "usage_details": {}, "level": "ERROR", "start_time": "2026-07-16T12:00:00+00:00"},
    ]
    resp = client.get("/observability/calls", params={"status": "failed"})
    calls = resp.json()["calls"]
    assert len(calls) == 1
    assert calls[0]["call_id"] == "call-2"


def test_call_detail_returns_events_from_mocked_observations(client_with_mocked_langfuse):
    client, query_client = client_with_mocked_langfuse
    query_client.observations_response = [
        {
            "trace_id": "call-1",
            "name": "information_extraction",
            "provider": "gemini",
            "service": "generative_ai",
            "model": "gemini-test-model",
            "usage_details": {"input": 500, "output": 200},
            "cost_details": {"total": "0.0012"},
            "level": "DEFAULT",
            "start_time": "2026-07-15T12:00:00+00:00",
            "metadata": {},
        }
    ]
    resp = client.get("/observability/calls/call-1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["call_id"] == "call-1"
    assert len(body["events"]) == 1
    assert body["events"][0]["pipeline_stage"] == "information_extraction"
    assert body["total_input_tokens"] == 500


def test_cost_breakdown_flat_monthly(client_with_mocked_langfuse, db_conn):
    client, query_client = client_with_mocked_langfuse
    insert_infra_row(db_conn, monthly_cost_usd="30.00", allocation_method="flat_monthly")
    query_client.metrics_response = {"data": [{"usage_input": 100, "usage_output": 40, "count": 1, "call_id": "c1"}]}
    resp = client.get("/observability/cost-breakdown", params={"range": "month"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["allocated_fixed_cost_usd"] == "30.00"
    assert body["fixed_cost_allocation_method"] == "flat_monthly"
    assert len(body["labels"]) == 3


def test_cost_breakdown_per_call_share_zero_calls_does_not_divide_by_zero(client_with_mocked_langfuse, db_conn):
    client, query_client = client_with_mocked_langfuse
    insert_infra_row(db_conn, monthly_cost_usd="30.00", allocation_method="per_call_share")
    query_client.metrics_response = None  # zero calls this period
    resp = client.get("/observability/cost-breakdown", params={"range": "month", "allocation_method": "per_call_share"})
    assert resp.status_code == 200
    assert resp.json()["allocated_fixed_cost_usd"] == "0"
