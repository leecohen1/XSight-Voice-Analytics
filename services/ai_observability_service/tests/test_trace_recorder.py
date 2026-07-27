"""Unit tests for app/trace_recorder.py -- composes the Langfuse client
wrapper with the pricing engine to record one full call trace from a batch
of already-validated events. Uses a fake ObservabilityClient (no real SDK,
no network) so these tests exercise only this module's own branching
logic (generation-vs-span classification, cost lookup, error isolation)."""
from conftest import insert_pricing_row

from app.trace_recorder import record_call_trace
from app.validation import validate_event


def _validated(**overrides):
    raw = {
        "idempotency_key": "exec-1:stage",
        "provider": "gemini",
        "service": "generative_ai",
        "model": "gemini-test-model",
        "pipeline_stage": "information_extraction",
        "use_case": "analyze_sales_call",
        "input_tokens": 500,
        "output_tokens": 200,
        "total_tokens": 700,
        "audio_duration_seconds": None,
        "request_count": 1,
        "latency_ms": 800,
        "status": "success",
        "occurred_at": "2026-07-15T12:00:00Z",
        "metadata": {},
    }
    raw.update(overrides)
    event, reasons = validate_event(raw)
    assert not reasons, reasons
    return event


class FakeClient:
    """Records every call made to it, standing in for
    app.langfuse_client.ObservabilityClient. `.enabled` mirrors what a real
    disabled/enabled client would report."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.spans = []
        self.generations = []
        self.trace_updates = []
        self.flushed_timeout = None
        self._trace_id_for_seed = {}

    def create_trace_id(self, seed):
        self._trace_id_for_seed[seed] = f"trace-{seed}"
        return self._trace_id_for_seed[seed]

    def update_trace_attributes(self, **kwargs):
        self.trace_updates.append(kwargs)
        return True

    def record_span(self, **kwargs):
        self.spans.append(kwargs)
        return "span-id"

    def record_generation(self, **kwargs):
        self.generations.append(kwargs)
        return "gen-id"

    def flush(self, timeout_seconds):
        self.flushed_timeout = timeout_seconds


def test_trace_id_derived_deterministically_from_call_id(db_conn):
    client = FakeClient()
    result = record_call_trace(client, db_conn, "call-42", None, {}, [])
    assert result.trace_id == "trace-call-42"


def test_stage_with_model_and_tokens_recorded_as_generation(db_conn):
    insert_pricing_row(db_conn, model="gemini-test-model", input_price="0.10", output_price="0.40")
    client = FakeClient()
    event = _validated()
    result = record_call_trace(client, db_conn, "call-1", "exec-1", {}, [event])
    assert result.recorded_stage_names == ["information_extraction"]
    assert len(client.generations) == 1
    assert len(client.spans) == 0
    assert client.generations[0]["model"] == "gemini-test-model"
    assert client.generations[0]["usage_details"] == {"input": 500, "output": 200}
    # (500/1000 * 0.10) + (200/1000 * 0.40) = 0.05 + 0.08 = 0.13
    assert client.generations[0]["cost_details"] == {"total": "0.130"}


def test_stage_without_model_recorded_as_span(db_conn):
    client = FakeClient()
    event = _validated(
        model=None, provider="internal", service="call_signal_analyser", pipeline_stage="call_signal_analysis",
        input_tokens=None, output_tokens=None, total_tokens=None,
    )
    record_call_trace(client, db_conn, "call-1", None, {}, [event])
    assert len(client.spans) == 1
    assert len(client.generations) == 0


def test_stage_with_model_but_no_usage_signal_recorded_as_span(db_conn):
    """A model name alone isn't enough to be a "generation" -- there must
    also be a measurable usage signal (tokens or audio duration)."""
    client = FakeClient()
    event = _validated(input_tokens=None, output_tokens=None, total_tokens=None, audio_duration_seconds=None)
    record_call_trace(client, db_conn, "call-1", None, {}, [event])
    assert len(client.spans) == 1
    assert len(client.generations) == 0


def test_missing_pricing_row_yields_no_cost_details_never_fabricated(db_conn):
    client = FakeClient()
    event = _validated(model="unpriced-model")
    record_call_trace(client, db_conn, "call-1", None, {}, [event])
    assert client.generations[0]["cost_details"] is None


def test_audio_duration_used_for_generation_classification_and_usage(db_conn):
    insert_pricing_row(db_conn, provider="assemblyai", service="transcription", model=None, billing_unit="per_minute", unit_price="0.0001")
    client = FakeClient()
    event = _validated(
        provider="assemblyai", service="transcription", model="assemblyai-default", pipeline_stage="transcription",
        input_tokens=None, output_tokens=None, total_tokens=None, audio_duration_seconds=120.0,
    )
    record_call_trace(client, db_conn, "call-1", None, {}, [event])
    assert client.generations[0]["usage_details"] == {"duration_seconds": 120}


def test_observability_enabled_flag_reflects_client_state(db_conn):
    disabled_client = FakeClient(enabled=False)
    result = record_call_trace(disabled_client, db_conn, "call-1", None, {}, [_validated()])
    assert result.observability_enabled is False


def test_trace_metadata_includes_call_id_and_workflow_execution_id(db_conn):
    client = FakeClient()
    record_call_trace(client, db_conn, "call-1", "exec-99", {"environment": "development"}, [])
    trace_metadata = client.trace_updates[0]["metadata"]
    assert trace_metadata["call_id"] == "call-1"
    assert trace_metadata["n8n_execution_id"] == "exec-99"
    assert trace_metadata["environment"] == "development"


def test_tags_built_from_known_trace_metadata_fields(db_conn):
    client = FakeClient()
    record_call_trace(
        client, db_conn, "call-1", None,
        {"environment": "development", "workflow_version": "v3", "final_status": "pass", "use_case": "analyze_sales_call"},
        [],
    )
    tags = client.trace_updates[0]["tags"]
    assert set(tags) == {
        "env:development", "workflow_version:v3", "status:pass", "use_case:analyze_sales_call",
    }


def test_flush_called_with_default_timeout(db_conn):
    client = FakeClient()
    record_call_trace(client, db_conn, "call-1", None, {}, [])
    assert client.flushed_timeout == 3.0


def test_one_stage_failing_does_not_block_the_rest_of_the_batch(db_conn, monkeypatch):
    """A bug in this function's own branching (not a Langfuse network
    failure -- those never raise, see FakeClient) must not corrupt the
    rest of the batch."""
    client = FakeClient()

    original_is_generation = __import__("app.trace_recorder", fromlist=["_is_generation"])._is_generation
    call_count = {"n": 0}

    def _flaky_is_generation(event):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("simulated internal bug")
        return original_is_generation(event)

    monkeypatch.setattr("app.trace_recorder._is_generation", _flaky_is_generation)

    events = [_validated(idempotency_key="e1", pipeline_stage="stage_one"), _validated(idempotency_key="e2", pipeline_stage="stage_two")]
    result = record_call_trace(client, db_conn, "call-1", None, {}, events)
    assert result.failed_stage_names == ["stage_one"]
    assert result.recorded_stage_names == ["stage_two"]
